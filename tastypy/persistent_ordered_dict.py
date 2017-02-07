"""
The persistent ordered dict is a data struture that can be interacted with
like a python dict, and which is easy to keep synced with an on-disk copy

This allows you to easily persist data between non-concurrent runs of a
program.  It's useful for keeping track of progress in long jobs.
"""

# TODO keys should be converted to a special internal type that knows if it's
# unicode escaped.  Or, in otherwords, we should be checking if keys are
# unicode in getitem and setitem.

import tastypy
import atexit
import os
import copy
import gzip
import signal
import sys


DEFAULT_FILE_SIZE = 1000
DEFAULT_SYNC_AT = 1000

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

	``PersistentOrderedDict``\ s opened to the same file path share underlying
	memory so that they don't stale over-write one another's data.  Setting
	``clone`` to true gives the instance it's own memory space.
	"""

	_SHARED_POD_STATE = {}

	def __init__(
		self, 
		path,
		init={},
		gzipped=False,
		file_size=DEFAULT_FILE_SIZE,
		sync_at=DEFAULT_SYNC_AT,
		clone=True
	):
		# In addition to initializing some of the attributes fo the POD, we'll
		# also identify many of them with class attributes, which produces
		# singleton-like behavior, and protects against stale overwrites if
		# multiple PODs are created that point at the same location on disk
		path = tastypy.normalize_path(path)
		self._ensure_path(path)
		self._init_sharable_attrs(path, gzipped, file_size, clone)

		# Bind the file opening algorithm to self's namespace
		self._open = gzip.open if gzipped else open

		# Different clones can have different sync_at and _hold values.
		self.sync_at = sync_at
		self._hold = False

		# Mix in any data specified to the init keyword argument
		self.update(init)

		self.set = tastypy._DeepProxy(
			#self._set_deep,
			self._call_deep
		)


	def _call_deep(self, key_tuple, method_name, *args, **kwargs):

		target = _deep_getitem(self, key_tuple)
		target_ancester = _deep_getitem(self, key_tuple[:-1])
		try:
			return_val = getattr(target, method_name)(*args, **kwargs)
		except AttributeError:
			if method_name.startswith('__i'):
				method_name = '__' + method_name[3:]
				return_val = getattr(target, method_name)(*args, **kwargs)
			else:
				raise
			
		if len(key_tuple):
			self.mark_dirty(key_tuple[0])
			self._maybe_sync()

		return return_val


	# We access the shared state through a method so that subclasses can use
	# different shared state to isolate themselves.
	def _get_shared_state(self):
		return self._SHARED_POD_STATE


	def _shared_attrs(self, path, gzipped, file_size):
		return {
			'_path': path,
			'_values': {},
			'_keys': [],
			'_index_lookup': {},
			'_dirty': set(),
			'_open': open,
			'_gzipped': gzipped,
			'_file_size': file_size
		}


	def _init_sharable_attrs(self, path, gzipped, file_size, clonable):
		# Instances that point to the same location are made to be "clones" of
		# eachother, by pointing certain "sharable attributes" at the same memory
		# location (using class variables).  This prevents them from
		# stale-overwriting one anothers data, because they share the same
		# data.  Howver if clonable is False, then we don't put the sharable
		# attributes on class variables, keeping them isolated.

		# Dose a clone already exist?
		clone_already_exists = path in self._get_shared_state()

		# If we're cloning a pre-existing clone, retrieve shared attrs, and 
		# check for consistency in file handling with the existing clone
		if clonable and clone_already_exists:

			for key in self._get_shared_state()[path]:
				setattr(self, key, self._get_shared_state()[path][key])

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

		# If clonable, but no clone existed, initialize sharable attrs
		elif clonable and not clone_already_exists:

			if clonable:

				# Create the shared space for PODs to this disk location
				self._get_shared_state()[path] = self._shared_attrs(
					path,gzipped,file_size)

				# Identify with the shared space
				for key in self._get_shared_state()[path]:
					setattr(self, key, self._get_shared_state()[path][key])

		# If not clonable, initialize sharable attrs, but keep them isolate.
		else:
			for key, val in self._shared_attrs(path,gzipped,file_size).items():
				setattr(self, key, val)

		# If we didn't clone an existing clone (maybe because there wasn't one)
		# do a fresh read from file and register to sync at process exit
		if not clone_already_exists:

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

			# Get the keys that belong in this file
			start = file_num * self._file_size
			stop = start + self._file_size
			relevant_keys = self._keys[start:stop]

			# Serialize the data and write the file
			serializer = tastypy.JSONSerializer.dump_items(
				(k, self._values[k]) for k in relevant_keys
			)
			for line in serializer:
				f.write(line)

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
		# Clear core data
		self._keys[:] = []
		self._index_lookup.clear()
		self._values.clear()
		self._dirty.clear()

		# read in all data (if any)
		self._read()


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

		# Read each file found in path that matches the naming format
		naming_format = '\d+\.json.gz' if self._gzipped else '\d+\.json'
		file_iterator = tastypy.ls(
			self._path, dirs=False, absolute=True, match=naming_format)
		for i, file_path in enumerate(file_iterator):

			# Detect gaps in numbering of file names (indicates missing file)
			if file_path != self._path_from_int(i):
				raise tastypy.PersistentOrderedDictIntegrityError(
					'Expected %s but found %s.  File missing?' 
					% (self._path_from_int(i), file_path)
				)

			# Check if the previous file (if any) had the right number of lines
			if i > 0 and prev_num_entries != self._file_size: 
				raise tastypy.PersistentOrderedDictIntegrityError(
					"The file %s appears to be corrupted, because it has "
					"%d lines (instead of %d)." 
					% (prev_file_path, prev_num_entries, self._file_size)
				)

			# Read all the data from this file.  Record number of entries, to 
			# be verified if this isn't the last file.
			prev_file_path = file_path
			prev_num_entries = 0
			try:
				deserialized = tastypy.JSONSerializer.read_items(
					self._open(file_path))
				for key, value in deserialized:
					prev_num_entries += 1

					# Allow subclasses to intercept and re-interpret lines
					key, value = self._read_intercept(key, value)

					# Register the data
					self._values[key] = value
					self._keys.append(key)
					self._index_lookup[key] = len(self._keys)-1

			# Contextualize parsing errors (can be due to bad JSON format)
			except ValueError as error:
				raise tastypy.PersistentOrderedDictIntegrityError(
					'PersistentOrderedDict: The file %s disk appears to be '
					'corrupted:\n%s' 
					% (self._path_from_int(i), str(error))
				)

	def _read_intercept(self, key, val):
		return key, val


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
