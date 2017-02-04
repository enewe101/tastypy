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
import signal
import sys


DEFAULT_FILE_SIZE = 1000
DEFAULT_SYNC_AT = 1000

def tuplify_lists(obj):
	if isinstance(obj, list):
		for i, element in enumerate(obj):
			obj[i] = tuplify_lists(element)
		obj = tuple(obj)
	return obj


def _deep_setitem(container, key_tuple, value):
	owner = _deep_getitem(container, key_tuple[:-1])
	owner[key_tuple[-1]] = value


def _deep_getitem(container, key_tuple):
	value = container
	for key in key_tuple:
		value = value[key]
	return value


class DeepKey(object):

	def __init__(
		self, 
		callback=None,
		parent_deepkey=None,
		parent_key=None
	):
		self.callback = callback
		self.parent_deepkey = parent_deepkey
		self.parent_key = parent_key

		validates_as_root_key = (
			callback is not None and parent_key is None
		)
		validates_as_deep_key = (
			callback is None and parent_key is not None
		)
		if validates_as_root_key:
			self.placement = 'root'
		elif validates_as_deep_key:
			self.placement = 'deep'
		else:
			raise ValueError(
				'Either provide callback or provide both parent_deepkey '
				'and parent_key'
			)

	def __getitem__(self, key):
		return DeepKey(parent_deepkey=self, parent_key=key)

	def __setitem__(self, key, val):
		if self.placement == 'deep':
			self.parent_deepkey.setitem((self.parent_key, key,), val)

		else:
			self.callback((key,), val)

	def setitem(self, keys, val):
		if self.placement == 'deep':
			self.parent_deepkey.setitem((self.parent_key,) + keys, val)
		else:
			self.callback(keys, val)



class Mutator(object):
	def __init__(self, client):
		self.client = client

	def __getitem__(self, key):
		val = self.client[key]
		self.client.update(key)
		return val


class SingletonDecorator:
    def __init__(self,klass):
        self.klass = klass
        self.instance = None
    def __call__(self,*args,**kwds):
        if self.instance == None:
            self.instance = self.klass(*args,**kwds)
        return self.instance



class PersistentOrderedDict(object):
	""" 
	A key-value mapping container that synchronizes transparently to disk at
	the location given by ``path``.  Data will persist after program
	interruption and can be accessed by creating a new instance directed at the
	same path.  The JSON-formatted persistence files are gzipped if ``gzipped`` 
	is ``True``.  Each files stores a number of values given by
	``file_size``.  Smaller values give faster synchronization but create 
	more files.  Synchronization automatically occurs when the number of
	values that are out of sync with those stored on disk reaches ``sync_at``
	or if the program terminates.
	"""

	_ESCAPE_TAB_PATTERN = re.compile('\t')
	_UNESCAPE_TAB_PATTERN = re.compile(r'(?P<prefix>^|[^\\])\\t')
	_ESCAPE_SLASH_PATTERN = re.compile(r'\\')
	_UNESCAPE_SLASH_PATTERN = re.compile(r'\\\\')

	_SHARED_STATE = {}

	def __init__(
		self, 
		path,
		gzipped=False,
		file_size=DEFAULT_FILE_SIZE,
		sync_at=DEFAULT_SYNC_AT
	):

		path = tastypy.normalize_path(path)
		if path not in self._SHARED_STATE:
			self._SHARED_STATE[path] = {}
		self.__dict__ = self._SHARED_STATE[path]

		self.path = path
		self.file_size = file_size
		self.gzipped = gzipped
		self.sync_at = sync_at

		self._set_write_method(gzipped)

		# Make the path in which files will be written.  If there's going to be
		# a problem with writing, it should arise now
		self._ensure_path(path)

		# Load values from disk into memory.
		self.revert()

		# Hold is off by default, meaning that the record on disk is sync'ed
		# automatically
		self._hold = False

		# Always be sure to synchronize before the script exits
		atexit.register(self.sync)
		signal.signal(signal.SIGTERM, self._sync_on_terminate)


	def _sync_on_terminate(self, sig_num, frame):
		# Wraps sync() so that it can be registered as a SIGTERM handler
		self.sync()
		sys.exit(0)


	def keys(self):
		"""
		Return a list of the keys, matching the order in which they were added.
		"""
		return [key for key in self._keys]


	def values(self):
		"""
		Return a list of the ``POD``'s values.  The order of values is
		guaranteed to match the order of ``self.keys()``
		"""
		return [self.__getitem__(key) for key in self._keys]



	def items(self):
		"""
		Return a list of key-value pairs, matching the order in which keys were 
		added.
		"""
		return [(key, self.__getitem__(key)) for key in self._keys]


	def iteritems(self):
		"""
		Return an iterator that yields key-value pairs, matching the order
		in which keys were added.
		"""
		for key in self._keys:
			yield key, self.__getitem__(key)


	def mark_dirty(self, key):
		"""
		Force ``key`` to be considered out of sync.  The data associated to
		this key will be re-written to file during the next synchronization.
		"""
		key = self._ensure_unicode(key)
		self._dirty.add(key)


	def update(self, key):
		'''
		Force ``key`` to be synchronized to disk immediately.
		'''
		key = self._ensure_unicode(key)
		self.mark_dirty(key)
		self.sync()


	def set(self, key_tuple, value):
		main_key = self._ensure_unicode(key_tuple[0])
		key_tuple = (main_key,) + key_tuple[1:]
		_deep_setitem(self, key_tuple, value)
		self.mark_dirty(key_tuple[0])
		self._maybe_sync()


	def sync(self):
		"""
		Force synchronization of all "dirty" values (which have changed from
		the values stored on disk).
		"""
		dirty_files = set()
		for key in self._dirty:
			index = self.index_lookup[key]
			file_num = index / self.file_size
			dirty_files.add(file_num)

		# The write directory should exist, but ensure it.
		self._ensure_path(self.path)

		# Rewrite all the dirty files
		for file_num in dirty_files:

			# Get the dirty file
			path =  self._path_from_int(file_num)
			f = self.open(path, 'w')

			# Go through keys mapped to this file and re-write them
			start = file_num * self.file_size
			stop = start + self.file_size
			for key in self._keys[start:stop]:

				value = self._values[key]
				# Escape tabs in key, and encode using utf8
				serialized_key = self._serialize_key(key)
				serialized_value = self._serialize_value(value)
				f.write('%s\t%s\n' % (serialized_key, serialized_value))

		# No more dirty keys
		self._dirty = set()


	def hold(self):
		"""
		Suspend automatic synchronization to disk.
		"""
		self._hold = True

	
	def unhold(self):
		"""
		Resume automatic synchronization to disk.
		"""
		self._hold = False
		self.maybe_sync()


	def revert(self):
		"""
		Load values from disk into memory, discarding any unsynchronized changes.
		Forget any files have been marked "dirty".
		"""

		# read in all data (if any)
		self._read()

		# Keep track of files whose contents don't match values in memory
		self._dirty = set()


	def copy(self, path, file_size, gzipped=False):
		"""
		Synchronize the POD to a new location on disk specified by ``path``.  
		Future synchronization will also take place at this new location.  
		The old location on disk will be left as-is and will no longer be 
		synchronized.  When synchronizing store ``file_size`` number of
		values per file, and keep files gzipped if ``gzipped`` is ``True``.
		This is not affected by ``hold()``.
		"""

		self.gzipped = gzipped
		self.path = path
		self.file_size = file_size

		self._set_write_method(gzipped)
		self._ensure_path(path)

		num_files = int(math.ceil(
			len(self._values) / float(self.file_size)
		))
		self._dirty_files = set(range(num_files))
		self.sync()


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

		for i, fname in enumerate(
			tastypy.ls(self.path, dirs=False, absolute=True
		)):

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
				if num_lines_prev_file != self.file_size:
					raise tastypy.PersistentOrderedDictIntegrityError(
						"PersistentOrderedDict: "
						"A file on disk appears to be corrupted, because "
						"it has the wrong number of lines: %s " % prev_file_path
					)

			for entry in self.open(os.path.join(fname)):

				# skip blank lines (there's always one at end of file)
				if entry=='':
					continue

				# remove the newline of the end of serialized_value, and read it
				try:
					serialized_key, serialized_value = entry.split('\t', 1)
					key = self._deserialize_key(serialized_key)
					value = self._deserialize_value(serialized_value[:-1])

				except ValueError:
					raise tastypy.PersistentOrderedDictIntegrityError(
						'PersistentOrderedDict: A file on disk appears to be '
						'corrupted, because it has malformed JSON: %s' 
						% self._path_from_int(i)
 
					)

				# This is a hook for subclasses to intercept and re-interpret
				# loaded data without fully re-implementing ``_read()``.
				key, value = self._read_intercept(key, value)

				self._values[key] = value
				self._keys.append(key)
				self.index_lookup[key] = len(self._keys)-1


	def _serialize_key(self, key, recursed=False):

		# Recursively ensure that strings are encoded
		if isinstance(key, tuple):
			temp_key = []
			for item in key:
				temp_key.append(self._serialize_key(item, recursed=True))
			key = tuple(temp_key)

		# Base call for recursion
		elif isinstance(key, basestring):
			key = key.encode('utf8')

		# Do the actual serialization in the root call
		if not recursed:
			key = json.dumps(key)
			key = self._ESCAPE_SLASH_PATTERN.sub(r'\\\\', key)
			key = self._ESCAPE_TAB_PATTERN.sub(r'\\t', key)

		return key


	def _deserialize_key(self, serialized_key):
		key = self._UNESCAPE_TAB_PATTERN.sub('\g<prefix>\t', serialized_key)
		key = self._UNESCAPE_SLASH_PATTERN.sub(r'\\', key)
		key = json.loads(key)
		key = tuplify_lists(key)
		return key


	def _serialize_value(self, value):
		return json.dumps(value)


	def _deserialize_value(self, serialized_value):
		return json.loads(serialized_value)


	def _read_intercept(self, key, val):
		return key, val


	#def __del__(self):
	#	self.sync()


	def _maybe_sync(self, preemptive=0):
		"""Synchronize if not currently on ``hold()``."""
		if self._hold:
			return
		if len(self._dirty) < self.sync_at - preemptive:
			return
		self.sync()



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


	def __contains__(self, key):
		key = self._ensure_unicode(key)
		return key in self.index_lookup


	def __len__(self):
		return len(self._keys)


	def __getitem__(self, key):

		# Ensure main key is unicode
		key = self._ensure_unicode(key)

		# If we accessed a key that exists, it may be about to be mutated
		# So, we'll cautiously mark it as dirty, and possibly trigger a
		# synchronization.  However, there is a gotcha: assignment would happen
		# after this function returns, so, if synchronization is triggered, we
		# within this function, we actually still want this key to be dirty.
		# Therefore we trigger synchronization preemptively and mark the key
		# dirty after.
		if self.__contains__(key):
			self._maybe_sync(preemptive=True)
			self.mark_dirty(key)

		return self._values[key]


	def _ensure_unicode(self, key):
		# Forces str-like keys to be unicode

		# ensure that the key is a valid type
		if not isinstance(key, (basestring, tuple, int)):
			raise ValueError(
				'Keys must be strings, integers, or (arbitrarily nested) '
				'tuples of them.'
			)

		# Recurse if necessary
		if isinstance(key, tuple):
			temp_key = []
			for item in key:
				temp_key.append(self._ensure_unicode(item))
			key = tuple(temp_key)

		# Ensure that strings are unicode
		elif isinstance(key, basestring) and not isinstance(key, unicode):
			key = key.decode('utf8')

		return key



	def __setitem__(self, key, val):

		# Ensure key is unicode
		key = self._ensure_unicode(key)

		# If we're making a new key, do so.
		if key not in self._values:
			self._keys.append(key)
			self.index_lookup[key] = len(self._keys)-1

		# Update the value held at ``key``
		self._values[key] = val
		self.mark_dirty(key)
		self._maybe_sync()
		

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


# Make a shorter alias
POD = PersistentOrderedDict
