"""
The ``ProgressTracker`` is a specialized ``PersistentOrderedDict`` that offers a 
few extra methods for the common usecase of keeping track of progress in
long-running processes and resuming the work where it was left off after a
crash or suspension.
"""


import tastypy
DEFAULT_PROGRESS_TRACKER_MAPPING = (
	('_tries', 0),
	('_done', False),
	('_aborted', False)
)


# TODO: override setitem so that new top-level keys can't be added without an
# explicit call to ``.add()``.
class ProgressTracker(tastypy.PersistentOrderedDict):

	"""
	A specialized subclass of ``POD`` for tracking tasks, whose values are
	dicts representing whether the task has been done or aborted, and how many 
	times it has been tried.  

	Transprantly aynchronizes to disk using files stored under ``path``.  
	Specify the maximum number of times a task should be tried using 
	``max_tries``, which influences the behaviour of gates_ and iterators_.
	If ``max_tries`` is ``0`` no limit is applied.

	Optionally provide data to initialize (or update) the mapping using the
	``init`` parameter.  The argument should be an iterable of key-value tuples
	or should implement ``iteritems()`` yielding such an iterable.  This is
	equivalent to calling ``update(init_arg)`` after creating the ``POD``.	

	The JSON-formatted persistence files are gzipped if ``gzipped`` is
	``True``.    Each file stores a number of values given by ``file_size``.
	Smaller values give faster synchronization but create more files.  Data is
	automatically synchronized to disk when the number of "dirty" values
	reaches ``sync_at``, or if the program terminates.
	"""

	_SHARED_TRACKER_STATE = {}

	def __init__(
		self, 
		path,
		max_tries=0,
		init={},
		gzipped=False,
		file_size=tastypy.DEFAULT_FILE_SIZE,
		sync_at=tastypy.DEFAULT_SYNC_AT,
		clone=True
	):
		super(ProgressTracker, self).__init__(
			path, init, gzipped, file_size, sync_at, clone)
		self.max_tries = max_tries


	# Trackers can share state with one another, but their shared state is
	# separated from PODs'
	def _get_shared_state(self):
		return self._SHARED_TRACKER_STATE

	def _shared_attrs(self, path, gzipped, file_size):
		attrs = super(ProgressTracker, self)._shared_attrs(
			path, gzipped, file_size)
		attrs.update({
			'_num_done': 0,
			'_num_tried': 0,
			'_num_aborted': 0
		})
		return attrs


	def update(self, *mappings, **kwargs):
		"""
		Similar to :py:func:`POD.update <PersistentOrderedDict.update>`, the
		mappings and keyword arguments should provide key-value pairs, but the
		values should be ``dict``\ s.  The provided values are used to
		``dict.update()`` the existing values.  If the key didn't exist,
		:py:meth:`add(key) <add()>` is called before attempting to mixin the
		supplied value.  Therefore it is never necessary to provide special
		keys (``'_done'``, ``'_tries'``, ``'_aborted'``) in update dictionaries
		unless you actually want to mutate those values.
		"""
		for key, val in self._iterate_updates(*mappings, **kwargs):
			if key not in self._values:
				self.add(key)
			self[key].update(val)


	def _iterate_updates(self, *mappings, **kwargs):
		# This is used to simplify the code for ``update()``.  It considers the
		# various locations that updates can be commingn from and yields them
		# in a standardized way, respecting the order of precedence for
		# updates.
		for mapping in mappings:
			if hasattr(mapping, 'iteritems'):
				for key, val in mapping.iteritems():
					yield key, mapping[key]
			else:
				for key, val in mapping:
					yield key, val

		for key in kwargs:
			yield key, kwargs[key]


	def abort(self, key):
		"""
		Mark the ``key`` aborted.
		"""
		key = self._ensure_unicode(key)

		# If the key wasn't already marked aborted, then increment the total
		# number of aborted keys, and mark this key aborted.
		if not self[key]['_aborted']:
			self._num_aborted += 1
			self[key]['_aborted'] = True
			self.mark_dirty(key)
			self._maybe_sync()


	def unabort(self, key):
		"""
		Mark the ``key`` not aborted.
		"""
		key = self._ensure_unicode(key)

		# If the key was aborted, then decremet the total number of aborted
		# keys, and update this key to be not aborted.
		if self[key]['_aborted']:
			self._num_aborted -= 1
			self[key]['_aborted'] = False
			self.mark_dirty(key)
			self._maybe_sync()


	def aborted(self, key):
		"""
		Returns ``True`` if ``key`` was aborted.
		"""
		return self._values[key]['_aborted']


	def todo_keys(self, allow_aborted=False):
		"""
		Provides an iterator over keys that are not done, not
		aborted, and have been tried fewer than ``max_tries`` times.  
		If ``allow_aborted`` is ``True``, then yield aborted keys that meet the
		other criteria.
		Iteration order matches the order in which keys were added.
		"""
		for key in self._keys:
			val = self._values[key]
			if self.should_do(key, allow_aborted):
				yield key

	def todo_items(self, allow_aborted=False):
		"""
		Provides an iterator of key-value tuples for keys that are not done, not
		aborted, and have been tried fewer than ``max_tries`` times.  
		If ``allow_aborted`` is ``True``, then yield aborted items that meet the
		other criteria.
		Iteration order matches the order in which keys were added.
		"""
		for key in self.todo_keys(allow_aborted):
			yield key, self._values[key]

	def todo_values(self, allow_aborted=False):
		"""
		Provides an iterator over values corresponding to keys that are not
		done, not aborted, and have been tried fewer than ``max_tries`` times.
		If ``allow_aborted`` is ``True``, then yield aborted values that meet the
		other criteria.
		Iteration order matches the order in which keys were added.
		"""
		for key in self.todo_keys(allow_aborted):
			yield key, self._values[key]

	def try_keys(self, allow_aborted=False):
		"""
		Provides an iterator over keys that are not
		done, not aborted, and have been tried fewer than ``max_tries`` times.
		If ``allow_aborted`` is ``True``, then yield aborted keys that meet the
		other criteria.
		Increment the number of tries for each key yielded.
		Iteration order matches the order in which keys were added.
		"""
		for key in self.todo_keys(allow_aborted):
			self.increment_tries(key)
			yield key

	def try_items(self, allow_aborted=False):
		"""
		Provides an iterator of key-value tuples for keys that are not
		done, not aborted, and have been tried fewer than ``max_tries`` times.
		If ``allow_aborted`` is ``True``, then yield aborted items that meet the
		other criteria.
		Increment the number of tries for each key yielded.
		Iteration order matches the order in which keys were added.
		"""
		for key in self.try_keys(allow_aborted):
			return key, self._values[key]

	def try_values(self, allow_aborted=False):
		"""
		Provides an iterator over values corresponding to keys that are not
		done, not aborted, and have been tried fewer than ``max_tries`` times.
		If ``allow_aborted`` is ``True``, then yield aborted values that meet the
		other criteria.
		Increment the number of tries for the key corresponding to each value
		yeilded.
		Iteration order matches the order in which keys were added.
		"""
		for key in self.try_keys(allow_aborted):
			return self._values[key]


	def done(self, key):
		"""
		Returns ``True`` if ``key`` is done.  Does not raise ``KeyError`` if
		key does not exist, just returns ``False``.
		"""
		try:
			val = self[key]
		except KeyError:
			return False
		else:
			return val['_done']


	def should_do(self, key, allow_aborted=False):
		"""
		Returns ``True`` if ``key`` is not done, not aborted, and not tried
		more than ``max_tries`` times.  If ``allow_aborted`` is ``True``, then
		return ``True`` for keys that would otherwise return ``False`` only
		because they are aborted.
		"""
		val = self[key]
		return (
			not val['_done']
			and (self.max_tries < 1 or val['_tries'] < self.max_tries)
			and (allow_aborted or not val['_aborted'])
		)

	def should_do_add(self, key, allow_aborted=False):
		"""
		Similar to :py:meth:`should_do`, but if the key doesn't exist, it will
		be added and ``True`` will be returned.
		"""
		if key not in self:
			self.add(key)
		return self.should_do(key)


	def should_try(self, key, allow_aborted=False):
		"""
		Similar to :py:meth:`should_do`, but increments the number of tries on
		keys for which ``True`` will be returned.
		"""
		if self.should_do(key, allow_aborted):
			self.increment_tries(key)
			return True
		return False


	def should_try_add(self, key, allow_aborted=False):
		"""
		Similar to :py:meth:`should_try`, but if the key doesn't exist, it will
		be added and ``True`` will be returned.
		"""
		if key not in self:
			self.add(key)
		return self.should_try(key)


	def add(self, key):
		"""
		Add a key to the tracker, initialized as not done, not aborted, and
		with zero tries.  Attempting to add an already-existing key will raise
		``tastypy.DuplicateKeyError``.
		"""
		key = self._ensure_unicode(key)
		if key in self:
			raise tastypy.DuplicateKeyError(
				'ProgressTracker: key "%s" already exists.' % key)
		else:
			self[key] = dict(DEFAULT_PROGRESS_TRACKER_MAPPING)


	def add_if_absent(self, key):
		"""
		Same as :py:meth:`add`, but don't raise an error if the key exists,
		just do nothing.
		"""
		try:
			self.add(key)
		except tastypy.DuplicateKeyError:
			pass


	def add_many(self, keys_iterable):
		"""
		Add each key yielded by keys iterator, initialized as not done, 
		with zero tries.
		"""
		for key in keys_iterable:
			self.add(key)


	def add_many_if_absent(self, keys_iterable):
		"""
		Same as :py:meth:`add_many`, but silently skip keys that are already in
		the tracker.
		"""
		for key in keys_iterable:
			self.add_if_absent(key)


	def revert(self):
		# initialize counters for the number of items that are done / tried
		self._num_done = 0
		self._num_tried = 0
		self._num_aborted = 0
		super(ProgressTracker, self).revert()


	def _read(self):
		super(ProgressTracker, self)._read()


	def _read_intercept(self, key, value):
		# During reading, count the number of keys that are marked done
		if value['_done']:
			self._num_done += 1
		if value['_tries'] > 0:
			self._num_tried += 1
		return key, value


	def decrement_tries(self, key):
		"""
		Decrement the tries counter for ``key``.
		"""
		key = self._ensure_unicode(key)

		# If this key originally had one try, decrement the count of the
		# number of keys that has at least one try
		if self[key]['_tries'] == 1:
			self._num_tried -= 1

		self[key]['_tries'] -= 1
		self.mark_dirty(key)
		self._maybe_sync()


	def increment_tries(self, key):
		"""
		Increment the tries counter for ``key``.
		"""
		key = self._ensure_unicode(key)

		# If this key originally had zero tries, increment the count of the
		# number of keys that has at least one try
		if self[key]['_tries'] == 0:
			self._num_tried += 1

		self[key]['_tries'] += 1
		self.mark_dirty(key)
		self._maybe_sync()


	def reset_tries(self, key):
		"""
		Reset the tries counter for ``key`` to zero.
		"""
		key = self._ensure_unicode(key)

		# If this key originally had some tries, decrement the count of the
		# number of keys that has at least one try
		if self[key]['_tries'] > 0:
			self._num_tried -= 1

		self[key]['_tries'] = 0
		self.mark_dirty(key)
		self._maybe_sync()


	def tries(self, key):
		"""
		Retrieve the number of times ``key`` has been tried.
		"""
		key = self._ensure_unicode(key)
		return self[key]['_tries']


	def mark_done(self, key):
		"""
		Mark the ``key`` as done.
		"""
		key = self._ensure_unicode(key)

		# If the key wasn't already marked done, then increment the total
		# number of done keys, and update this key to be done
		if not self[key]['_done']:
			self._num_done += 1
			self[key]['_done'] = True
			self.mark_dirty(key)
			self._maybe_sync()


	def mark_not_done(self, key):
		"""
		Mark the ``key`` as not done.
		"""
		key = self._ensure_unicode(key)

		# If the key was already marked done, then decremet the total
		# number of done keys, and update this key to be not done
		if self[key]['_done']:
			self._num_done -= 1
			self[key]['_done'] = False
			self.mark_dirty(key)
			self._maybe_sync()


	def num_done(self):
		"""
		Returns the number of entries that are done.  
		Recall that ``len(tracker)`` returns the total number of entries.
		"""
		return self._num_done

	def fraction_done(self):
		"""
		Returns the fraction (between 0 and 1) of entries that are done.
		"""
		return self._num_done / float(len(self))

	def percent_not_done(self, decimals=2):
		"""
		Return a string representing the percentage of entries *not* done,
		E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in the
		percentage representation (default 2).
		"""
		return percent(1-self.fraction_done, decimals)

	def percent_done(self, decimals=2):
		"""
		Return a string representing the percentage of entries done,
		E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in the
		percentage representation (default 2).
		"""
		return self.percent(self.fraction_done(), decimals)

	def num_tried(self):
		"""
		Returns the number of entries that have been tried at least once.
		Recall that ``len(tracker)`` returns the total number of entries.
		"""
		return self._num_tried

	def fraction_tried(self):
		"""
		Returns the fraction (between 0 and 1) of entries that have been tried
		at least once.
		"""
		return self._num_tried / float(len(self))

	def percent_not_tried(self, decimals=2):
		"""
		Return a string representing the percentage of entries tried at least
		once, E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in
		the percentage representation (default 2).
		"""
		return self.percent(1-self.fraction_tried(), decimals)

	def percent_tried(self, decimals=2):
		"""
		Return a string representing the percentage of entries tried at least
		once, E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in
		the percentage representation (default 2).
		"""
		return self.percent(self.fraction_tried(), decimals)

	def num_aborted(self):
		"""
		Returns the number of entries that have been aborted.
		Recall that ``len(tracker)`` returns the total number of entries.
		"""
		return self._num_aborted

	def fraction_aborted(self):
		"""
		Returns the fraction (between 0 and 1) of entries that have been
		aborted.
		"""
		return self._num_aborted / float(len(self))

	def percent_not_aborted(self, decimals=2):
		"""
		Return a string representing the percentage of entries aborted, 
		E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in
		the percentage representation (default 2).
		"""
		return self.percent(1-self.fraction_aborted(), decimals)

	def percent_aborted(self, decimals=2):
		"""
		Return a string representing the percentage of entries aborted, 
		E.g.: ``'34.70 %'``.  Includes ``decimal`` number of decimals in
		the percentage representation (default 2).
		"""
		return self.percent(self.fraction_aborted(), decimals)

	def percent(self, fraction, decimals):
		"""
		Return a string representing the percentage, corresponding to the
		fraction given.  E.g.: ``'34.70 %'``.  Includes ``decimal`` number of 
		decimals in the percentage representation (default 2).
		"""
		formatter = '%.' + str(decimals) + 'f %%'
		return formatter % (100 * fraction)


Tracker = ProgressTracker
