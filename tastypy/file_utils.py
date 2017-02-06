from natsort import humansorted
import shutil
import re
import subprocess
import os


def normalize_path(path):
	return os.path.realpath(os.path.expanduser(path))


def file_empty(file_path):
	return os.stat(file_path).st_size == 0


def ensure_removed(path):
	"""
	Ensure that the given path does not exist, by removing it if necessary.
	"""
	if os.path.exists(path):
		shutil.rmtree(path)	


def ensure_exists(path):
	"""
	Ensure that the given path exists, by creating it if it doesn't.  If the
	path exists but is a file, an `OSError` would be raised.
	"""
	if not os.path.exists(path):
		os.makedirs(path)	


def ls(
	path,
	files=True,
	dirs=True,
	match=None,
	exclude=None,
	absolute=False,
	recurse=False,
	list_all=False,
	natural_sort=True,
	iteritems=False
):

	lister = PathLister(
		path=path,
		files=files,
		dirs=dirs,
		match=match,
		exclude=exclude,
		absolute=absolute,
		recurse=recurse,
		list_all=list_all,
		natural_sort=natural_sort,
		iteritems=iteritems
	)
	return lister.generate()


class PathLister(object):

	'''
		Iterator for listing all files in a directory.
		- Lists files found under path, unless <files> is False
		- Can also list directories, if <dirs> is True
		- Only files (and directories) matching <match> 
			will be returned, unless they also match <exclude>.
		- By default, doesn't descend into subdirectories, unless
			<recurse> is True, lists files in subdirs too.
		- If <recurse> is True, only directories matching <match>
			and not matching <exclude> will be followed
		- Paths to files are returned relative to <path>, unless <absolute>
			is true, then absolute paths are returned
		- Files are listed in natural sort ordering (i.e. respecting
			numerical order), but if <natural_sort> is False alphabetical
			order is used instead.
		- Hidden files (starting with '.') are ommitted, but if <list_all>
			is true, then they will be included.  In recursive mode, this
			is necessary in orderd to follow hidden  folders.
	'''

	def __init__(
		self,
		path,
		files=True,
		dirs=True,
		match=None,
		exclude=None,
		absolute=False,
		recurse=False,
		list_all=True,
		natural_sort=True,
		iteritems=False
	):
		self.path = path
		self.files = files
		self.dirs = dirs
		self.match = None if match is None else re.compile(match)
		self.exclude = None if exclude is None else re.compile(exclude)
		self.absolute = absolute
		self.recurse = recurse
		self.list_all = list_all
		self.natural_sort = natural_sort
		self.iteritems=iteritems

		# Validation -- make sure self.path exists
		if not os.path.exists(self.path):
			raise OSError('no such file or directory: %s' % self.path)


	def filter_back_pointers(self, dirs):
		'''
			Exclude '.' and '..' from <dirs>.
		'''
		return filter(
			lambda i: not (i.split('/')[-1]=='.' or i.split('/')[-1]=='..'),
			dirs
		)


	def generate(self):
		'''
		Either return the path generator, or a list of paths, depending on 
		the constructor.
		'''
		self.walker = os.walk(self.path)
		self.next_dir()
		if self.iteritems:
			return self._generate()
		else:
			return [item for item in self._generate()]


	def next_dir(self):
		cur_path, cur_dirs, cur_files = self.walker.next()

		# First reletavize cur_path to current working directory (by default
		# it's reletavized to the path given in the constructor)
		cur_path = os.path.relpath(cur_path, '.')

		# Do we want the files, the directories, both?
		if self.files:
			self.items = cur_files
		else:
			self.items = []
		if self.dirs:
			self.items.extend(cur_dirs)

		# Absolutize the paths if that's what was specified in the constructor
		if self.absolute:
			self.items = [
				os.path.abspath(os.path.join(cur_path, d)) for d in self.items
			]

		# Otherwise reletavize the files to the current working directory
		# But only necessary if cur_path isn't the current working directory
		elif cur_path != '.':
			self.items = [os.path.join(cur_path, f) for f in self.items]

		# Sort the items either "naturally" or alphabetically
		if self.natural_sort:
			self.items = humansorted(self.items, reverse=True)
		else:
			self.items.sort(reverse=True)

		# Filter items against the exclude and match if any
		if self.match is not None:
			self.items = [i for i in self.items if self.match.search(i)]
		if self.exclude is not None:
			self.items = [i for i in self.items if not self.exclude.search(i)]


	def _generate(self):
		'''
			yield the next item, and absolutize the path if necessary.
		'''
		# We'll break out of this loop when stopIteration is raised by 
		# the call to self.get_next()
		while True:
			yield self.get_next()


	def get_next(self):

		while True:

			# Try popping off the next item
			try:
				return self.items.pop()
			except IndexError:
				pass

			# If there's no more items, and if we're in recursive mode, 
			# descend into the next directory
			if self.recurse:
				self.next_dir()
				return self.get_next()

			# And if we're not in recursive mode, then we're done
			else:
				raise StopIteration


	def _ls(self, path, filter_back_pointers=True):

		# Ask OS to list the files and directories in path

		#if self.list_all:
		#	items = check_output(['ls', '-a', path]).split()
		#else:
		#	items = check_output(['ls', path]).split()

		ls = subprocess.Popen(list_command, stdout=subprocess.PIPE)


		# Sort the files and directories
		if self.natural_sort:
			sort_command = ['sort', '-n', '-r']
		else:
			sort_command = ['sort', '-r']
		items = subprocess.check_output(sort_command, stdin=ls.stdout)
		ls.wait()
		items = [os.path.join(path, i) for i in items.split()]

		# Get rid of '.' and '..', if necessary
		if self.list_all and filter_back_pointers:
			items = self.filter_back_pointers(items)

		# Go through the list separate files from directories
		files = []
		dirs = []
		for item in items:

			# Skip if it doesn't match match, or does match exclude
			whitelist_match = (
				True if self.match is None 
				else self.match.search(item) 
			)
			blacklist_match = (
				false if self.exclude is None
				else self.exclude.search(item)
			)
			print blacklist_match
			if not whitelist_match or blacklist_match:
				continue

			# Append files to the list of files
			if os.path.isfile(item):
				files.append(item)

			# Append directories to the list of dirs
			else:
				dirs.append(item)

		return files, dirs

