'''
The persistent ordered dict is a data struture that can be interacted with
like a python dict, and which is easy to keep synced with an on-disk copy

This allows you to easily persist data between non-concurrent runs of a
program.  It's useful for keeping track of progress in long jobs.
'''

import math
import atexit
import json
import os
import re
import copy
from file_utils import ls
import gzip


LINES_PER_FILE = 1000


# Define Exceptions for the PersistentOrderedDict class and its subclasses
class PersistentOrderedDictException(Exception):
	pass
class DuplicateKeyException(PersistentOrderedDictException):
	pass
class PersistentOrderedDictIntegrityException(PersistentOrderedDictException):
	pass


class PersistentOrderedDict(object):

	ESCAPE_TAB_PATTERN = re.compile('\t')
	UNESCAPE_TAB_PATTERN = re.compile(r'(?P<prefix>^|[^\\])\\t')
	ESCAPE_SLASH_PATTERN = re.compile(r'\\')
	UNESCAPE_SLASH_PATTERN = re.compile(r'\\\\')

	def __init__(
		self, 
		path,
		gzipped=False,
		lines_per_file=LINES_PER_FILE,
		verbose=False
	):
	"""
    Create (or re-establish) a ``PersistentOrderedDict``, synchronizing to disk
    using files stored under ``path``.  If ``gzipped`` is ``True``, then gzip
    the persistence files.  ``lines_per_file`` determines how many of the
    ``POD``'s values are stored in a single before creating a new one.  A large
    number reduces the total number of files crated, whereas a smaller number
    makes for faster synchronization because a smaller amount of data needs to
    be written to update a single change.
	"""

		self.path = path
		self.lines_per_file = lines_per_file
		self.gzipped = gzipped
		self.verbose = verbose

		self.set_write_method(gzipped)
		self.ensure_path(path)

		# read in all data (if any)
		self.read()

		# Hold is off by default -> updates are immediately written to file
		self._hold = False

		# Keep track of files whose contents don't match values in memory
		self.dirty_files = set()

		# Always be sure to synchronize before the script exits
		atexit.register(self.unhold)


	def set_write_method(self, gzipped):

		if gzipped:
			self.open = gzip.open
		else:
			self.open = open


	def ensure_path(self, path):

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

		self.gzipped = gzipped
		self.path = path
		self.lines_per_file = lines_per_file

		self.set_write_method(gzipped)
		self.ensure_path(path)

		num_files = int(math.ceil(
			len(self.data) / float(self.lines_per_file)
		))
		self.dirty_files = set(range(num_files))
		self.sync()


	def hold(self):
		'''
		temporarily prevent writing updates to file
		'''
		self._hold = True

	
	def unhold(self):
		'''
		Resume writing updates to file, synchronize any dirty files.
		'''
		self._hold = False
		self.sync()


	def keys(self):
		return copy.copy(self.key_order)


	def values(self):
		return copy.copy([self.data[k] for k in self.key_order])


	def path_from_int(self, i):
		if self.gzipped:
			return os.path.join(self.path, '%d.json.gz' % i)
		else:
			return os.path.join(self.path, '%d.json' % i)


	def read(self):

		self.key_order = []
		self.index_lookup = {}
		self.data = {}

		i=0
		for fname in ls(self.path, dirs=False):

			if self.verbose:
				print fname

			# ensure that files are in expected order,
			# that none are missing, and that no lines are missing.
			if fname != self.path_from_int(i):
				raise PersistentOrderedDictIntegrityException(
					'Expected %s but found %s.' 
					% (self.path_from_int(i), fname)
				)

			if i > 0:
				prev_file_path = self.path_from_int(i-1)
				num_lines_prev_file = len(
					self.open(prev_file_path, 'r').readlines()
				)
				if num_lines_prev_file != self.lines_per_file:
					raise PersistentOrderedDictIntegrityException(
						"PersistentOrderedDict: "
						"A file on disk appears to be corrupted, because "
						"it's missing lines: %s " % prev_file_path
					)

			i += 1

			for entry in self.open(os.path.join(fname)):

				# skip blank lines (there's always one at end of file)
				if entry=='':
					continue

				key, json_record = entry.split('\t', 1)
				key = self.UNESCAPE_TAB_PATTERN.sub('\g<prefix>\t', key)
				key = self.UNESCAPE_SLASH_PATTERN.sub(r'\\', key)
				key = key.decode('utf8')
				
				# remove the newline of the end of json_record, and read it
				record = json.loads(json_record[:-1])
				self.data[key] = record
				self.key_order.append(key)
				self.index_lookup[key] = len(self.key_order)-1


	def mark_dirty(self, key):

		key = self.ensure_unicode(key)
		index = self.index_lookup[key]
		file_num = index / self.lines_per_file
		self.dirty_files.add(file_num)


	def sync(self):

		#graceful = GracefulDeath()

		# No synchronization happens when hold is on.  This reduces I/O
		# when many values need to be updated
		if self._hold:
			return

		for file_num in self.dirty_files:

			# Get the dirty file
			try:
				path =  self.path_from_int(file_num)
			except TypeError:
				print file_num
				raise
			f = self.open(path, 'w')

			# Go through keys mapped to this file and re-write them
			start = file_num * self.lines_per_file
			stop = start + self.lines_per_file
			for key in self.key_order[start:stop]:

				record = self.data[key]
				# Escape tabs in key, and encode using utf8
				key = self.escape_key(key)
				f.write('%s\t%s\n' % (key, json.dumps(record)))

		# No more dirty files
		self.dirty_files = set()


	def escape_key(self, key):
		key = key.encode('utf8')
		key = self.ESCAPE_SLASH_PATTERN.sub(r'\\\\', key)
		key = self.ESCAPE_TAB_PATTERN.sub(r'\\t', key)
		return key


	def __iter__(self):
		self.pointer = 0
		return self


	def next(self):
		try:
			key = self.key_order[self.pointer]
		except IndexError:
			raise StopIteration

		val = self.data[key]
		self.pointer += 1

		return key, val


	def __contains__(self, key):
		key = self.ensure_unicode(key)
		return key in self.index_lookup


	def __len__(self):
		return len(self.key_order)


	def __getitem__(self, key):
		key = self.ensure_unicode(key)
		return self.data[key]


	def ensure_unicode(self, key):

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
		This can be called to ensure that a specific key will be 
		synchronized.  It's helpful if a mutable object is stored at that 
		key, since it could be changed without triggering __setitem__;
		this provides a way to notify PersistentOrderedDict that the value 
		at that key has changed.
		'''
		key = self.ensure_unicode(key)
		self.mark_dirty(key)
		self.sync()


	def set_item(self, key, val):

		key = self.ensure_unicode(key)
		val = copy.deepcopy(val)

		# if there isn't already an entry, we need to allocate a new slot
		if key not in self.data:
			self.key_order.append(key)
			self.index_lookup[key] = len(self.key_order)-1

		# update the value held at <key>
		self.data[key] = val
		self.mark_dirty(key)
		self.sync()


	def __setitem__(self, key, val):

		key = self.ensure_unicode(key)
		val = copy.deepcopy(val)

		# if there isn't already an entry, we need to allocate a new slot
		if key not in self.data:
			self.key_order.append(key)
			self.index_lookup[key] = len(self.key_order)-1

		# update the value held at <key>
		self.data[key] = val
		self.mark_dirty(key)
		self.sync()


	def set(self, key, subkey, value):
		key = self.ensure_unicode(key)
		self[key][subkey] = value
		self.update(key)


	def add(self, key):
		key = self.ensure_unicode(key)
		if key in self:
			raise DuplicateKeyException(
				'PersistentOrderedDict: key "%s" already exists.' % key)
		else:
			self[key] = True


	def add_if_absent(self, key):
		'''
		Same as add, but don't raise an error if the key exists, just do 
		nothing in that case.
		'''
		try:
			self.add(key)
		except DuplicateKeyException:
			pass


	def convert_to_tracker(self):

		# Rewrite every value to satisfy the form of a progress tracker
		self.hold()
		for key, spec in self:

			# Ensure the value at key is a dict, and add special keys
			if not isinstance(spec, dict):
				self[key] = {'val':spec, '_done':False, '_tries':0}
			else:
				self[key].update({'_done':False, '_tries':0})

			# Mark the key as updated
			self.update(key)

		self.unhold()

