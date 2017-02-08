'''
The SharedProgressTracker is a sharable proxy to a progress_tracker that runs
in a separate spawned process.  The proxy can be treated just like a progress
tracker and can be accessed from different processes without any need to worry
about synchronization.
'''

# TODO: need to have mark_dirty send that key's value using the "set" command
#	or something, and test it.
# TODO: add the dirty command and other commands recently added to the POD
# TODO: add the init constructor argument

from functools import wraps
from contextlib import contextmanager
import sys
import multiprocessing
import tastypy
from tblib import pickling_support
pickling_support.install()


ITERITEMS_CHUNK_SIZE = 1000
ITERKEYS_CHUNK_SIZE = 1000

def _requires_lock(lock):
	def decorator(f):
		@wraps(f)
		def f_with_lock(*args, **kwargs):
			with lock:
				return_val = f(*args, **kwargs)
				return return_val

		return f_with_lock
	return decorator


def _requires_tracker_open(f):
	@wraps(f)
	def f_that_requires_tracker_open(self, *args, **kwargs):
		if not self.tracker_open:
			raise tastypy.CalledClosedTrackerError
		return f(self, *args, **kwargs)

	return f_that_requires_tracker_open


def serve_datastructure(datastructure_builder, pipe):
	"""
	Starts a server that creates a datastructure by running
	``datastructure_builder`` without arguments, and executes commands on the
	datastructure that are received over ``pipe`` from clients that act as
	proxies for the datastructure.
	"""

	datastructure = datastructure_builder()

	# Continually listen for remote requests to execute functions on the 
	# progress tracker.  Satisfy those requests, sending the results of the
	# function calls back to the caller, via the SharedProgressTracker, which
	# acts as a proxy.
	is_open = True
	while is_open:

		# Continually listen for requests
		message = pipe.recv()

		# Handle signal to shut down the progress tracker server
		if message == SharedProgressTracker.CLOSE:
			is_open = False
			datastructure.sync()
			pipe.send('closed')

		# Handle remote function calls on the progress tracker
		else:

			# Handle requests for iteration here
			attr = message[0]
			if attr == 'iter':

				# Determine what range of iteration has been requested.
				include_values, start, end = message[1:]
				keys = datastructure._keys[start:end]

				# We need to let the caller know if there are more items
				# to iterate
				has_more = True
				if len(datastructure) <= end:
					has_more = False

				# Will we return just the keys, or keys and values?
				if include_values:
					vals = [datastructure._values[k] for k in keys]
					return_data = zip(keys, vals)
				else: 
					return_data = keys

				# Return the iteration fragment
				pipe.send((return_data, has_more))

			# Handle all non-iteration requests here
			else:
				args, kwargs = message[1], message[2]
				try:
					return_val = getattr(datastructure, attr)(*args, **kwargs)
				except Exception as error:
					pipe.send((None, error))
				else:
					pipe.send((return_val, None))



class SharedPersistentOrderedDict(object):
	"""
	A multiprocessing-safe proxy for ``tasatypy.POD``.  Data will be
	syncronized to disk in files under ``path``.  The ``SharedPOD`` supports the
	same iteration methods as ``POD``; multiple processes can iterate
	concurrently without blocking eachother.  All iteration methods return keys
	and or values in the order in which keys were added.
	"""

	CLOSE = 0
	LOCK = multiprocessing.RLock()
	PASS_THROUGHS = {
		'update', '_call_deep', 'hold', 'unhold', 'revert', 
		'mark_dirty', 'sync', 'sync_key'
	}
	SERVER_DATASTRUCTURE = tastypy.PersistentOrderedDict

	def __init__(
			self, 
			path,
			init={},
			gzipped=False,
			file_size=tastypy.DEFAULT_FILE_SIZE,
			sync_at=tastypy.DEFAULT_SYNC_AT,
			clone=True
		):

		# Underlying datastructures supporting a shared proxy can't be clones.
		clone=False

		self.client_pipe, server_pipe = multiprocessing.Pipe()

		# Define a function that builds the underlying datastructure
		def build_datastructure():
			return self.SERVER_DATASTRUCTURE(
				path=path, init=init, gzipped=gzipped, 
				file_size=file_size, sync_at=sync_at, clone=clone
			)

		# Create / start the server, passing it the datastructure-building 
		# function
		server_tracker = multiprocessing.Process(
			target=serve_datastructure,
			args=(build_datastructure, server_pipe)
		)
		server_tracker.daemon = True	# Shut down server if main process exits
		server_tracker.start()

		# The POD is open for business
		self.tracker_open = True

		self.set = tastypy._DeepProxy(self._call_deep)

	@_requires_lock(LOCK)
	def close(self):
		"""
		Ask the the underlying ``POD`` server to terminate (it will synchronize
		to disk first).  Normally you don't need to use this because the server
		process will sync and shutdown automatically when its parent process
		terminates.
		"""
		self.client_pipe.send(self.CLOSE)
		# Wait for confirmation that the close signal was received and that the
		# data structure did it's final synchronization
		self.client_pipe.recv()


	@_requires_tracker_open
	def lock(self):
		"""
		Only allow the caller to read / write to the ``SharedPOD``.  
		All other processes are blocked until ``unlock`` is called.
		"""
		self.LOCK.acquire()


	@contextmanager
	@_requires_tracker_open
	def locked(self):
		"""
		Context manager under which only the calling process can interact with
		the ``SharedPOD``, all other processes being blocked until the context
		is closed.  Using this context manager is preferable to calling
		``lock()`` followed by ``unlock()`` because the lock will be released
		even if an exception is thrown or a return statement reached.  

		Usage:

		.. code-block:: python

			with pod.locked():
				pod.set['some-key'] += 1

		See `Avoiding raciness`_ to see when you need to use this.
		"""
		self.lock()
		try:
			yield
		finally:
			self.unlock()


	@_requires_tracker_open
	def unlock(self):
		"""
		Allow other processes to read / write.
		"""
		self.LOCK.release()


	def __getattr__(self, attr):
		#This hook let's us forward lots of different method calls without
		#having to write a separate definition that does forwarding for each of
		#them.  Whenever an "unknown" method is called, __getattr__ gets called,
		#and if the method is in the list of methods that we want to forward, we
		#will simply capture the method name and arguments, and forward it to
		#the POD server to be executed on its POD, and wait for the return value
		#to be sent back.

		#To capture the arguments on a method that should be forwarded, we
		#define a lambda to stand as that method, which simply calls a method
		#forwarding handler with the method name and captured arguments.

		#This strategy works for ordinary methods but not magic methods like
		#__setitem__ and __len__; so for each of those we need to write a
		#definition that does forwarding.

		#Calling a methods that isn't found in in the list of methods to be 
		#forwarded will cause AttributeError to be raised as usual.
		if attr in self.PASS_THROUGHS:
			return lambda *a, **kw: self._passthrough(attr, *a, **kw)
		raise AttributeError(attr)


	@_requires_tracker_open
	@_requires_lock(LOCK)
	def _passthrough(self, method_name, *args, **kwargs):
		# This method is used to forward method calls on the SharedPOD to the
		# server, where those methods get called on the actual POD.  The return
		# value is sent back from the server, along with any errors that were
		# raised, so that they can be returned / raised here.
		self.client_pipe.send((method_name, args, kwargs))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val


	@_requires_tracker_open
	def _iter(self, include_values):
		"""
		Provide an iterable of key, value tuples.  The items are retrieved
		in chunks from the ``POD`` server, to prevent the calling process from
		hogging access to the ``SharedPOD`` during iteration.  Multiple
		processes can iterate concurrently.
		"""
		# This helper manages requests to the progress tracker for iteration
		# over its values.  This isn't handled just with method forwarding like
		# for other methods.  That's because, for performace reasons, it's
		# better to fetch chunks of data, releasing the lock between fetches,
		# so that one process doesn't tie up the server when iterating over the
		# dataset.  That means multiple processes can iterate concurrently,
		# which is useful because sometimes that's exactly what workers need to
		# do.  The extra chunking / lock management logic is handled here, in
		# cooperation with the server.

		has_more = True
		start, end = 0, ITERITEMS_CHUNK_SIZE

		# Request chunks from the server, then yield items from them locally
		while has_more:

			# Get a chunk
			self.LOCK.acquire()
			self.client_pipe.send(('iter', include_values, start, end))
			items, has_more = self.client_pipe.recv()
			self.LOCK.release()

			# Yield items from the chunk
			for item in items:
				yield item

			# Advance chunk pointer
			start += ITERITEMS_CHUNK_SIZE
			end += ITERITEMS_CHUNK_SIZE

	def iteritems(self):
		"""
		Provide an iterator of key-value tuples in the order in which keys were
		added.
		"""
		for item in self._iter(True):
			yield item

	def iterkeys(self):
		"""
		Provide an iterator over keys in the order in which they were added.
		"""
		for key, val in self._iter(False):
			yield key

	def itervalues(self):
		"""
		Provide an iterator over values in the order in which corresponding
		keys were added.
		"""
		for key, val in self._iter(True):
			yield val

	def __iter__(self):
		for key in self._iter(False):
			yield key

	def items(self):
		"""
		Return a list of key-value tuples in the order in which keys were
		added.
		"""
		return [item for item in self._iter(True)]

	def keys(self):
		"""
		Return a list of keys in the order in which they were added.
		"""
		return [key for key in self._iter(False)]

	def values(self):
		"""
		Return a list of values in the order in which the corresponding keys
		were added.
		"""
		return [val for key, val in self._iter(True)]

	# Magic methods need to be manually forwarded because __getattr__ does not
	# get called for magic methods.
	def __setitem__(self, *args, **kwargs):
		return self._passthrough('__setitem__', *args, **kwargs)
	def __getitem__(self, *args, **kwargs):
		return self._passthrough('__getitem__', *args, **kwargs)
	def __contains__(self, *args, **kwargs):
		return self._passthrough('__contains__', *args, **kwargs)
	def __len__(self, *args, **kwargs):
		return self._passthrough('__len__', *args, **kwargs)



class SharedProgressTracker(SharedPersistentOrderedDict):
	"""
	A multiprocessing-safe progress tracker that can be shared by many
	processes.  Like a ``SharedPOD``, but meant for tracking tasks---each value
	is a dict representing whether the corresponding task has been done and how
	many times it has been tried.
	
	Data is syncronized to disk in files under ``path``.  Specify the maximum
	number of times a task should be tried using ``max_tries``, which
	influences which tasks are tried under certain iteration modes.  If
	``max_tries`` is ``0`` no limit is applied.

	Provide initial data to initialize (or update) the mapping using the
	``init`` parameter.  The argument should be an iterable of key-value tuples
	or should implement ``iteritems()`` yielding such an iterable.  This is
	equivalent to calling ``update(init_arg)`` after creating the
	``SharedTracker``.	

	The JSON-formatted persistence files are gzipped if ``gzipped`` is
	``True``.    Each file stores a number of values given by ``file_size``.
	Smaller values give faster synchronization but create more files.  Data is
	automatically synchronized to disk when the number of "dirty" values
	reaches ``sync_at``, or if the program terminates.

	Supports all methods of |progtracker|_ and |sharedpodreference|_.
	"""
	CLOSE = 0
	LOCK = multiprocessing.RLock()
	PASS_THROUGHS = SharedPersistentOrderedDict.PASS_THROUGHS | {
		
		'increment_tries', 'decrement_tries', 'reset_tries', 'tries', 

		'done', 'mark_done', 'mark_not_done', 

		'add', 	'check_or_add', 'add_if_absent', 'add_many', 
			'add_many_if_absent',

		'abort', 'unabort', 'aborted',

		'num_tried', 'fraction_tried','percent_tried', 'percent_not_tried',
		'num_done', 'fraction_done', 'percent_done', 'percent_not_done', 
		'num_aborted', 'fraction_aborted', 'percent_aborted', 
			'percent_not_aborted', 
		'percent', 
	}
	SERVER_DATASTRUCTURE = tastypy.ProgressTracker

	def __init__(
		self, 
		path,
		max_tries=0,
		init={},
		gzipped=False,
		file_size=tastypy.DEFAULT_FILE_SIZE,
		sync_at=tastypy.DEFAULT_SYNC_AT,
		clone=False
	):

		# Underlying datastructures supporting a shared proxy can't be clones.
		clone=False

		# Delegate to SharedPOD to start up the server.  The datastructure sent
		# to the server is overridden by SERVER_DATASTRUCTURE above.
		super(SharedProgressTracker, self).__init__(
			path, init, gzipped, file_size, sync_at, clone
		)

		# Remember max_tries locally
		self.max_tries = max_tries


	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def todo_items(self, allow_aborted=False):
		"""
		Provide an iterator of key-value tuples for keys not yet marked done and 
		with fewer than max_tries.
		"""
		for key, val in self._iter(True):
			worth_trying = (
				not val['_done']
				and (self.max_tries < 1 or val['_tries'] < self.max_tries)
				and (allow_aborted or not val['_aborted'])
			)
			if worth_trying:
				yield key, val

	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def todo_keys(self, allow_aborted=False):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.
		"""
		for key, val in self.todo_items(allow_aborted):
			yield key, val

	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def todo_values(self, allow_aborted=False):
		"""
		Provide an iterator over values corresponding to keys not yet marked 
		done and with fewer than max_tries.
		"""
		for key, val in self.todo_items(allow_aborted):
			yield val

	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def try_items(self, allow_aborted=False):
		"""
		Provide an iterator over key-value tuples for keys not yet marked done
		and with fewer tries than max_tries. Increment the number of tries for
		each item yielded.
		"""
		for key, val in self.todo_items(allow_aborted):
			self.increment_tries(key)
			yield key, val


	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def try_keys(self, allow_aborted=False):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.  Increment the number of tries for each key yielded.
		"""
		for key, val in self.try_items(allow_aborted):
			yield key


	# TODO: it would be good to find a way to properly delegate the filtering
	# of done keys to the server, since that transmits less data between
	# processes and means less code duplication.
	def try_values(self, allow_aborted=False):
		"""
		Provide an iterator over keys not yet marked done and with fewer tries
		than max_tries.  Increment the number of tries for each value yielded.
		"""
		for key, val in self.try_items(allow_aborted):
			yield val


# Give shorter aliases
SharedPOD = SharedPersistentOrderedDict
SharedTracker = SharedProgressTracker
