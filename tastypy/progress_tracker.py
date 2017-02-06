"""
The ``ProgressTracker`` is a specialized ``PersistentOrderedDict`` that offers a 
few extra methods for the common usecase of keeping track of progress in
long-running processes and resuming the work where it was left off after a
crash or suspension.
"""


import tastypy



# TODO: override setitem so that new top-level keys can't be added without an
# explicit call to ``.add()``.
class ProgressTracker(tastypy.PersistentOrderedDict):

	"""
	A specialized subclass of ``POD`` for tracking tasks, whose values are
	dicts representing whether the task has been done and how many times it has
	been tried.  

	Transprantly aynchronizes to disk using files stored under ``path``.  
	Specify the maximum number of times a task should be tried using 
	``max_tries``, which influences which tasks are tried under certain
	iteration modes.  If ``max_tries`` is ``0`` no limit is applied.

	Provide initial data to initialize (or update) the mapping using the
	``init`` parameter.  The argument should be an iterable of key-value tuples
	or should implement ``iteritems()`` yielding such an iterable.  This is
	equivalent to calling ``update(init_arg)`` after creating the ``POD``.	

	The JSON-formatted persistence files are gzipped if ``gzipped`` is
	``True``.    Each file stores a number of values given by ``file_size``.
	Smaller values give faster synchronization but create more files.  Data is
	automatically synchronized to disk when the number of "dirty" values
	reaches ``sync_at``, or if the program terminates.
	"""

	def __init__(
		self, 
		path,
		max_tries=0,
		init={},
		gzipped=False,
		file_size=tastypy.DEFAULT_FILE_SIZE,
		sync_at=tastypy.DEFAULT_SYNC_AT,
	):
		super(ProgressTracker, self).__init__(
			path, init, gzipped, file_size, sync_at)
		self.max_tries = max_tries


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
			self.maybe_sync()


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
			self.maybe_sync()


	def is_aborted(self, key):
		return self._values[key]['_aborted']


	def todo_keys(self):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.
		"""
		for key in self._keys:
			val = self._values[key]
			worth_trying = self.max_tries < 1 or val['_tries'] < self.max_tries
			if not val['_done'] and worth_trying:
				yield key

	def todo_items(self):
		"""
		Provide an iterator of key-value tuples for keys not yet marked done and 
		with fewer than max_tries.
		"""
		for key in self.todo_keys:
			yield key, self._values[key]

	def todo_values(self):
		"""
		Provide an iterator over values corresponding to keys not yet marked 
		done and with fewer than max_tries.
		"""
		for key in self.todo_keys:
			yield key, self._values[key]

	def try_keys(self):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.  Increment the number of tries for each key yielded.
		"""
		for key in self.todo_keys:
			self.increment_tries(key)
			yield key

	def try_items(self):
		"""
		Provide an iterator over keys  not yet marked done and with fewer tries
		than max_tries. Increment the number of tries for each item yielded.
		"""
		for key in self.try_keys():
			return key, self._values[key]

	def try_values(self):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.  Increment the number of tries for each value yielded.
		"""
		for key in self.try_keys():
			return self._values[key]

	def check_or_add(self, key):
		"""
		checks if there is an entry for key already marked as done
		(returns True if so).  If no entry exists for key, it makes one
		and provides it with a defualt value of _done:False and _tries:0
		"""
		key = self._ensure_unicode(key)
		if key in self:
			if self[key]['_done']:
				return True
			else:
				return False
		else:
			self[key] = {'_done':False, '_tries':0}
			return False


	def check(self, key):
		"""
		Returns ``True`` if ``key`` is done.
		"""
		key = self._ensure_unicode(key)
		if key in self:
			if self[key]['_done']:
				return True
			else:
				return False
		else:
			return False


	def add(self, key):
		"""
		Add a key to the tracker, initialized as not done, with zero tries.
		"""
		key = self._ensure_unicode(key)
		if key in self:
			raise tastypy.DuplicateKeyError(
				'ProgressTracker: key "%s" already exists.' % key)
		else:
			self[key] = {'_done':False, '_tries':0}


	def add_if_absent(self, key):
		"""
		Same as add, but don't raise an error if the key exists, just do nothing.
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
		Same as add_many, but silently skip keys that are already in the
		tracker.
		"""
		for key in keys_iterable:
			self.add_if_absent(key)


	def _read(self):
		# Perform ``_read()`` as for POD, but first initialize counters for the
		# number of keys that are done and number of keys that have been tried.
		self._num_done = 0
		self._num_tried = 0
		self._num_aborted = 0
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
		self.maybe_sync()


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
		self.maybe_sync()


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
		self.maybe_sync()


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
			self.maybe_sync()


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
			self.maybe_sync()


	def num_done(self):
		"""
		Returns the number of entries that are done.
		"""
		return self._num_done

	def num_tried(self):
		"""
		Returns the number of entries that have been tried at least once.
		"""
		return self._num_tried

	def fraction_done(self):
		"""
		Returns the fraction (between 0 and 1) of entries that are done.
		"""
		return self._num_done / float(len(self))

	def fraction_tried(self):
		"""
		Returns the fraction (between 0 and 1) of entries that have been tried
		at least once.
		"""
		return self._num_tried / float(len(self))

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

	def percent(self, fraction, decimals):
		"""
		Return a string representing the percentage, corresponding to the
		fraction given.  E.g.: ``'34.70 %'``.  Includes ``decimal`` number of 
		decimals in the percentage representation (default 2).
		"""
		formatter = '%.' + str(decimals) + 'f %%'
		return formatter % (100 * fraction)


Tracker = ProgressTracker
