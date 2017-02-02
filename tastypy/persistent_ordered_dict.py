'''
The persistent ordered dict is a data struture that can be interacted with
like a python dict, and which is easy to keep synced with an on-disk copy

This allows you to easily persist data between non-concurrent runs of a
program.  It's useful for keeping track of progress in long jobs.
'''

import tastypy
import math
import atexit
import json
import os
import re
import copy
import gzip


DEFAULT_LINES_PER_FILE = 1000


class PersistentOrderedDict(object):
	""" 
	Create (or re-establish) a ``PersistentOrderedDict``, synchronizing to disk
	using files stored under ``path``.  If ``gzipped`` is ``True``, then gzip
	the persistence files.  ``lines_per_file`` determines how many of the
	``POD``'s values are stored in a single before creating a new one.  A large
	number reduces the total number of files crated, whereas a smaller number
	makes for faster synchronization because a smaller amount of data needs to
	be written to update a single change.
	"""

	_ESCAPE_TAB_PATTERN = re.compile('\t')
	_UNESCAPE_TAB_PATTERN = re.compile(r'(?P<prefix>^|[^\\])\\t')
	_ESCAPE_SLASH_PATTERN = re.compile(r'\\')
	_UNESCAPE_SLASH_PATTERN = re.compile(r'\\\\')

	def __init__(
		self, 
		path,
		gzipped=False,
		lines_per_file=DEFAULT_LINES_PER_FILE,
		verbose=False
	):

		self.path = path
		self.lines_per_file = lines_per_file
		self.gzipped = gzipped
		self.verbose = verbose

		self._set_write_method(gzipped)
		self._ensure_path(path)

		# read in all data (if any)
		self._read()

		# Hold is off by default -> updates are immediately written to file
		self._hold = False

		# Keep track of files whose contents don't match values in memory
		self._dirty_files = set()

		# Always be sure to synchronize before the script exits
		atexit.register(self.unhold)


	def _set_write_method(self, gzipped):

		if gzipped:
			self.open = gzip.open
		else:
			self.open = open


	def _ensure_path(self, path):

		# if the path doesn't exist, make it
		if not os.path.exists(path):
			os.makedirs(path)

		# if the path exists but points to a file, raise
		elif os.path.isfile(path):
			raise IOError(
				'The path given to PersistentOrderedDict should correspond '
				'to a folder.  A file was found instead: %s' % path
			)


	def copy(self, path, lines_per_file, gzipped=False):
		"""
		Synchronize the POD to a new location on disk specified by ``path``.  
		Future synchronization will also take place at this new location.  
		The old location on disk will be left as-is and will no longer be 
		synchronized.  When synchronizing store ``lines_per_file`` number of
		values per file, and keep files gzipped if ``gzipped`` is ``True``.
		This is not affected by ``hold()``.
		"""

		self.gzipped = gzipped
		self.path = path
		self.lines_per_file = lines_per_file

		self._set_write_method(gzipped)
		self._ensure_path(path)

		num_files = int(math.ceil(
			len(self._values) / float(self.lines_per_file)
		))
		self._dirty_files = set(range(num_files))
		self.sync()


	def hold(self):
		"""
		Suspend automatic synchronization to disk.
		"""
		self._hold = True

	
	def unhold(self):
		"""
		Resume automatic synchronization to disk, and synchronize immediately.
		"""
		self._hold = False
		self.sync()


	def _path_from_int(self, i):
		# Get the ith synchronization file's full path.
		if self.gzipped:
			return os.path.join(self.path, '%d.json.gz' % i)
		else:
			return os.path.join(self.path, '%d.json' % i)


	def _read(self):
		# Read persisted data from disk.  This is when the POD is initialized.
		self._keys = []
		self.index_lookup = {}
		self._values = {}

		for i, fname in enumerate(tastypy.ls(self.path, dirs=False)):

			if self.verbose:
				print fname

			# ensure that files are in expected order,
			# that none are missing, and that no lines are missing.
			if fname != self._path_from_int(i):
				raise tastypy.PersistentOrderedDictIntegrityError(
					'Expected %s but found %s.' 
					% (self._path_from_int(i), fname)
				)

			if i > 0:
				prev_file_path = self._path_from_int(i-1)
				num_lines_prev_file = len(
					self.open(prev_file_path, 'r').readlines()
				)
				if num_lines_prev_file != self.lines_per_file:
					raise tastypy.PersistentOrderedDictIntegrityError(
						"PersistentOrderedDict: "
						"A file on disk appears to be corrupted, because "
						"it has the wrong number of lines: %s " % prev_file_path
					)

			for entry in self.open(os.path.join(fname)):

				# skip blank lines (there's always one at end of file)
				if entry=='':
					continue

				# remove the newline of the end of json_record, and read it
				try:
					key, json_record = entry.split('\t', 1)
					key = self._UNESCAPE_TAB_PATTERN.sub('\g<prefix>\t', key)
					key = self._UNESCAPE_SLASH_PATTERN.sub(r'\\', key)
					key = key.decode('utf8')
					value = json.loads(json_record[:-1])
				except ValueError:
					raise tastypy.PersistentOrderedDictIntegrityError(
						'PersistentOrderedDict: A file on disk appears to be '
						'corrupted, because it has malformed JSON: %s' 
						% self._path_from_int(i)
 
					)

				# This is a hook for subclasses to intercept and re-interpret
				# loaded data without re-implementing ``_read()``.
				key, value = self._read_intercept(key, value)

				self._values[key] = value
				self._keys.append(key)
				self.index_lookup[key] = len(self._keys)-1


	def _read_intercept(self, key, val):
		return key, val


	def mark_dirty(self, key):
		"""
		Force a specific ``key`` in the persistent ordered dict to be
		considered out of sync, but do not synchronize it immediately.  The data 
		associated to this key will be re-written to file during the next
		synchronization.
		"""

		key = self._ensure_unicode(key)
		index = self.index_lookup[key]
		file_num = index / self.lines_per_file
		self._dirty_files.add(file_num)


	def maybe_sync(self):
		"""
		Synchronize all values that have changed if the ``POD`` is not currently
		on ``hold()``.
		"""
		if not self._hold:
			self.sync()


	def sync(self):
		"""
		Force synchronization of all values that have changed from those stored
		on disk.
		"""

		for file_num in self._dirty_files:

			# Get the dirty file
			try:
				path =  self._path_from_int(file_num)
			except TypeError:
				print file_num
				raise
			f = self.open(path, 'w')

			# Go through keys mapped to this file and re-write them
			start = file_num * self.lines_per_file
			stop = start + self.lines_per_file
			for key in self._keys[start:stop]:

				record = self._values[key]
				# Escape tabs in key, and encode using utf8
				key = self._escape_key(key)
				f.write('%s\t%s\n' % (key, json.dumps(record)))

		# No more dirty files
		self._dirty_files = set()


	def _escape_key(self, key):
		key = key.encode('utf8')
		key = self._ESCAPE_SLASH_PATTERN.sub(r'\\\\', key)
		key = self._ESCAPE_TAB_PATTERN.sub(r'\\t', key)
		return key


	def __iter__(self):
		self.pointer = 0
		return self


	def next(self):
		try:
			key = self._keys[self.pointer]
		except IndexError:
			raise StopIteration

		self.pointer += 1

		return key


	def items(self):
		"""
		Returns a list of key-value pairs matching the order in which keys were 
		added.
		"""
		return [(key, self.__getitem__(key)) for key in self._keys]


	def iteritems(self):
		"""
		Returns an iterator that yields key-value pairs, matching the order
		in which keys were added.
		"""
		for key in self._keys:
			yield key, self.__getitem__(key)

	def keys(self):
		"""
		Returns a list of the ``POD``'s keys.  The order matches the order
		in which keys were originally added, and matches the order of all
		iterables / iterators provided.
		"""
		return [key for key in self._keys]


	def values(self):
		"""
		Returns a list of the ``POD``'s values.  The order of values is
		guaranteed to match the order of ``self.keys()``
		"""
		return [self.__getitem__(key) for key in self._keys]


	def __contains__(self, key):
		key = self._ensure_unicode(key)
		return key in self.index_lookup


	def __len__(self):
		return len(self._keys)


	def __getitem__(self, key):
		key = self._ensure_unicode(key)
		return self._values[key]


	def _ensure_unicode(self, key):
		# Forces str-like keys to be unicode
		# ensure that the key is string-like
		if not isinstance(key, basestring):
			raise ValueError(
				'Keys must be str or unicode, and will be converted to '
				'unicode type internally.'
			)

		# cast the key into unicode if necessary
		if not isinstance(key, unicode):
			key = key.decode('utf8')

		return key


	def update(self, key):
		'''
		Forces a ``key`` to be synchronized to disk.  If ``hold()`` has been 
		called to suspend synchronization, then ``key`` will be marked for
		synchronization but will not be sync'd immediately.
		'''
		key = self._ensure_unicode(key)
		self.mark_dirty(key)
		self.maybe_sync()


	def __setitem__(self, key, val):

		key = self._ensure_unicode(key)

		# if there isn't already an entry, we need to allocate a new slot
		if key not in self._values:
			self._keys.append(key)
			self.index_lookup[key] = len(self._keys)-1

		# update the value held at <key>
		self._values[key] = val
		self.mark_dirty(key)
		self.maybe_sync()


	def set(self, key, subkey, value):
		"""
		Modify fields of dict-valued keys in such a way that the change is 
		registered for synchronization.  Recall that a POD is not aware of
		modifications made directly to values that are mutable objects.
		Equivalent to:

		.. code-block:: python
			my_pod[key][subkey] = value
			self.update(key)

		"""
		key = self._ensure_unicode(key)
		self[key][subkey] = value
		self.update(key)


	def convert_to_tracker(self):

		# Rewrite every value to satisfy the form of a progress tracker
		self.hold()
		for key, spec in self.iteritems():

			# Ensure the value at key is a dict, and add special keys
			if not isinstance(spec, dict):
				self[key] = {'val':spec, '_done':False, '_tries':0}
			else:
				self[key].update({'_done':False, '_tries':0})

			# Mark the key as updated
			self.update(key)

		self.unhold()

