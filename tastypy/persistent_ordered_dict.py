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
	A key-value mapping that synchronizes transparently to disk at the location
	given by ``path``.  When treated as an iterable, it yields keys in the
	order in which they were originally added. Data will persist after program
	interruption and can be accessed by creating a new instance directed at the
	same path.  

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

	_ESCAPE_TAB_PATTERN = re.compile('\t')
	_UNESCAPE_TAB_PATTERN = re.compile(r'(?P<prefix>^|[^\\])\\t')
	_ESCAPE_SLASH_PATTERN = re.compile(r'\\')
	_UNESCAPE_SLASH_PATTERN = re.compile(r'\\\\')
	_SHARED_STATE = {}

	def __init__(
		self, 
		path,
		init={},
		gzipped=False,
		file_size=DEFAULT_FILE_SIZE,
		sync_at=DEFAULT_SYNC_AT,
	):
		# In addition to initializing some of the attributes fo the POD, we'll
		# also identify many of them with class attributes, which produces
		# singleton-like behavior, and protects against stale overwrites if
		# multiple PODs are created that point at the same location on disk
		path = tastypy.normalize_path(path)
		self._ensure_path(path)
		self._borgify(path, gzipped, file_size)

		# Different clones can have different sync_at and _hold values.
		self.sync_at = sync_at
		self._hold = False

		# Mix in any data specified to the init keyword argument
		self.update(init)

		self.set = tastypy._DeepProxy(
			#self._set_deep,
			self._call_deep
		)


	#def _set_deep(self, key_tuple, val):
	#	_deep_setitem(self, key_tuple, val)
	#	#print 'POD:', key_tuple, '<--', val
	def _call_deep(self, key_tuple, method_name, *args, **kwargs):
		target = _deep_getitem(self, key_tuple)
		getattr(target, method_name)(*args, **kwargs)
		if len(key_tuple):
			self.mark_dirty(key_tuple[0])
			self._maybe_sync()


	#def set(self, key_tuple, value):
	#	main_key = self._ensure_unicode(key_tuple[0])
	#	key_tuple = (main_key,) + key_tuple[1:]
	#	_deep_setitem(self, key_tuple, value)
	#	self.mark_dirty(key_tuple[0])
	#	self._maybe_sync()


	def _borgify(self, path, gzipped, file_size):
		# If an instance of this class has already been made, pointing at the
		# same location on disk, then the new instance should share the same
		# data and file-writing options.  In otherwords, multiple instances
		# open to the same location on disk are really just interfaces to the
		# same underlying data.  This makes stale-overriting a non-problem
		# We use an approach inspired by Alex Martelli's "Borg" idea -- use
		# class variables to create memory shared by all instances.  Instances
		# can still differ in certain attributes, like how often they they
		# synchronize to disk.

		# We use the class_variable _SHARED_STATE to keep track of what PODs
		# have been made (pointing to what locations on disk).  Check here to
		# see if a POD pointing to this location has been made before, if so,
		# we're making a "clone"
		is_a_clone = path in self._SHARED_STATE

		# If this instance is a clone, inherit data from the existing instnace 
		if is_a_clone:
			for key in self._SHARED_STATE[path]:
				setattr(self, key, self._SHARED_STATE[path][key])

			# Validate against the existing parameters that must be shared
			if gzipped != self._gzipped:
				raise ValueError(
					'A POD instance pointed at the same location '
					'exists and has a conflicting value for ``gzipped``.'
				)

			# Validate against the existing parameters that must be shared
			if file_size != self._file_size:
				raise ValueError(
					'A POD instance pointed at the same location '
					'exists and has a conflicting value for ``file_size``.'
				)
			
		# Otherwise identify this objects data with the shared space
		else:

			# Create the shared space for PODs to this disk location
			self._SHARED_STATE[path] = {
				'_path': path,
				'_values': {},
				'_keys': [],
				'_index_lookup': {},
				'_dirty': set(),
				'_open': open,
				'_gzipped': gzipped,
				'_file_size': file_size
			}

			# Identify with the shared space
			for key in self._SHARED_STATE[path]:
				setattr(self, key, self._SHARED_STATE[path][key])

			# Load values from disk into memory.
			self.revert()

			# Register to synchronize before the script exits
			atexit.register(self.sync)
			signal.signal(signal.SIGTERM, self._sync_on_terminate)


	def update(self, *mappings, **kwargs):
		"""
		Update self to reflect key-value mappings, and reflect key-value pairs
		provided as keyword arguments.  Arguments closer to the right take 
		precedence.  Mapping objects must either be iterables of key-value
		tuples or implement ``iteritems()`` yielding such an iterator.
		"""

		for mapping in mappings:
			if hasattr(mapping, 'keys'):
				for key in mapping:
					self.__setitem__(key, mapping[key])
			else:
				for key, val in mapping:
					self.__setitem__(key, val)

		for key in kwargs:
			self.__setitem__(key, kwargs[key])


	def _sync_on_terminate(self, sig_num, frame):
		# Wraps sync() so that it can be registered as a SIGTERM handler
		self.sync()
		sys.exit(0)


	def __iter__(self):
		return self._keys.__iter__()

	def iteritems(self):
		"""
		Provide an iterator of key-value tuples in the order in which keys were
		added.
		"""
		for key in self._keys:
			yield key, self._values.__getitem__(key)


	def iterkeys(self):
		"""
		Provide an iterator over keys in the order in which they were added.
		"""
		return self._keys.__iter__()


	def itervalues(self):
		"""
		Provide an iterator over values in the order in which corresponding
		keys were added.
		"""
		for key in self._keys:
			yield self._values.__getitem__(key)


	def items(self):
		"""
		Return a list of key-value tuples in the order in which keys were
		added.
		"""
		return [(key, self._values.__getitem__(key)) for key in self._keys]


	def keys(self):
		"""
		Return a list of keys in the order in which they were added.
		"""
		return list(self._keys)


	def values(self):
		"""
		Return a list of values in the order in which the corresponding keys
		were added.
		"""
		return [self._values.__getitem__(key) for key in self._keys]


	def mark_dirty(self, key):
		"""
		Force ``key`` to be considered out of sync.  The data associated to
		this key will be written to file during the next synchronization.
		"""
		key = self._ensure_unicode(key)
		self._dirty.add(key)


	def dirty(self):
		"""
		Return the set of dirty keys.
		"""
		return set(self._dirty)


	def sync_key(self, key):
		'''
		Force ``key`` to be synchronized to disk immediately.
		'''
		key = self._ensure_unicode(key)
		self.mark_dirty(key)
		self.sync()


	def sync(self):
		"""
		Force synchronization of all dirty values.
		"""
		dirty_files = set()
		for key in self._dirty:
			index = self._index_lookup[key]
			file_num = index / self._file_size
			dirty_files.add(file_num)

		# The write directory should exist, but ensure it.
		self._ensure_path(self._path)

		# Rewrite all the dirty files
		for file_num in dirty_files:

			# Get the dirty file
			path =  self._path_from_int(file_num)
			f = self._open(path, 'w')

			# Go through keys mapped to this file and re-write them
			start = file_num * self._file_size
			stop = start + self._file_size
			for key in self._keys[start:stop]:

				value = self._values[key]
				# Escape tabs in key, and encode using utf8
				serialized_key = self._serialize_key(key)
				serialized_value = self._serialize_value(value)
				f.write('%s\t%s\n' % (serialized_key, serialized_value))

		# No more dirty keys
		self._dirty.clear()


	def hold(self):
		"""
		Suspend the automatic synchronization to disk that normally occurs when
		the number of dirty values reaches ``sync_at``.  (Synchronization will
		still be carried out at termination.)
		"""
		self._hold = True

	
	def unhold(self):
		"""
		Resume automatic synchronization to disk.
		"""
		self._hold = False
		self._maybe_sync()


	def revert(self):
		"""
		Load values from disk into memory, discarding any unsynchronized changes.
		"""

		# read in all data (if any)
		self._read()

		# Keep track of files whose contents don't match values in memory
		self._dirty.clear()


	#def copy(self, path, file_size, gzipped=False):
	#	"""
	#	Synchronize the POD to a new location on disk specified by ``path``.  
	#	Future synchronization will also take place at this new location.  
	#	The old location on disk will be left as-is and will no longer be 
	#	synchronized.  When synchronizing store ``file_size`` number of
	#	values per file, and keep files gzipped if ``gzipped`` is ``True``.
	#	This is not affected by ``hold()``.
	#	"""

	#	self.gzipped = gzipped
	#	self._path = path
	#	self._file_size = file_size

	#	self._set_write_method(gzipped)
	#	self._ensure_path(path)

	#	num_files = int(math.ceil(
	#		len(self._values) / float(self._file_size)
	#	))
	#	self._dirty_files = set(range(num_files))
	#	self.sync()


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
		if self._gzipped:
			return os.path.join(self._path, '%d.json.gz' % i)
		else:
			return os.path.join(self._path, '%d.json' % i)


	def _read(self):
		# Read persisted data from disk.  This is when the POD is initialized.
		self._keys[:] = []
		self._index_lookup.clear()
		self._values.clear()

		for i, fname in enumerate(
			tastypy.ls(self._path, dirs=False, absolute=True
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
					self._open(prev_file_path, 'r').readlines()
				)
				if num_lines_prev_file != self._file_size:
					raise tastypy.PersistentOrderedDictIntegrityError(
						"PersistentOrderedDict: "
						"A file on disk appears to be corrupted, because "
						"it has the wrong number of lines: %s " % prev_file_path
					)

			for entry in self._open(os.path.join(fname)):

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
				self._index_lookup[key] = len(self._keys)-1


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



	def __contains__(self, key):
		key = self._ensure_unicode(key)
		return key in self._index_lookup


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
			self._index_lookup[key] = len(self._keys)-1

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
