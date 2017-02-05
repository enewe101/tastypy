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

import sys
import multiprocessing
import tastypy
from tblib import pickling_support
pickling_support.install()


print 'DEBUG -- RESET CHUNK SIZES!'
ITERITEMS_CHUNK_SIZE = 100
ITERKEYS_CHUNK_SIZE = 100

def _requires_lock(lock):
	def decorator(f):
		def f_with_lock(*args, **kwargs):
			lock.acquire()
			try:
				return_val = f(*args, **kwargs)
			except Exception as e:
				lock.release()
				raise
			lock.release()
			return return_val

		return f_with_lock
	return decorator


def _requires_tracker_open(f):
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

		# Handle remote function calls on the progress tracker
		else:

			# Handle requests for iteration here
			attr, args = message[0], message[1:]
			if attr == 'iter':

				# Determine what range of iteration has been requested.
				keys_only, start, end = args
				keys = datastructure._keys[start:end]

				# We need to let the caller know if there are more items
				# to iterate
				has_more = True
				if len(datastructure) <= end:
					has_more = False

				# Will we return just the keys, or keys and values?
				if keys_only:
					return_data = keys
				else: 
					vals = [datastructure._values[k] for k in keys]
					return_data = zip(keys, vals)

				# Return the iteration fragment
				pipe.send((return_data, has_more))

			# Handle all non-iteration requests here
			else:
				try:
					return_val = getattr(datastructure, attr)(*args)
				except Exception as error:
					pipe.send((None, error))
				else:
					pipe.send((return_val, None))



class SharedPersistentOrderedDict(object):
	"""
	A multiprocessing-safe progress tracker that can be shared by many
	processes.  Data will be syncronized to disk in files under ``path``.  
	Avoids the problem of concurrent disk access that would arise if an
	ordinary ProgressTracker were shared by multiple processes.
	Note POD's ``copy`` and ``convert_to_tracker`` methods are not supported.
	"""

	CLOSE = 0
	LOCK = multiprocessing.RLock()

	def __init__(self, path):

		self.client_pipe, server_pipe = multiprocessing.Pipe()
		# create a real progress_tracker and a listen loop around it
		server_tracker = multiprocessing.Process(
			target=serve_datastructure,
			args=(lambda: tastypy.PersistentOrderedDict(path), server_pipe)
		)
		server_tracker.daemon = True	# Shut down server if main process exits
		server_tracker.start()
		# The POD is open for business
		self.tracker_open = True


	@_requires_lock(LOCK)
	def close(self):
		self.client_pipe.send(self.CLOSE)


	@_requires_tracker_open
	def lock(self):
		"""
		Only allow read / write from the calling process.  All other processes
		are blocked until ``unlock`` is called.
		"""
		self.LOCK.acquire()


	@_requires_tracker_open
	def unlock(self):
		"""
		Allow read / write other processes.
		"""
		self.LOCK.release()


	@_requires_tracker_open
	def holdlock(self):
		"""
		Suspend automatic synchronization, so that changes are only reflected in
		memory.  Prevent reading and writing by other processes.
		"""
		self.LOCK.acquire()
		self.client_pipe.send(('hold',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val


	@_requires_tracker_open
	def unholdlock(self):
		"""
		Resume automatic synchronization, and synchronize any changes made in 
		memory that have not yet been sync'd to disk, and allow other processes 
		to read / write
		"""
		self.client_pipe.send(('unhold',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		self.LOCK.release()
		return return_val

	
	@_requires_tracker_open
	@_requires_lock(LOCK)
	def hold(self):
		"""
		Suspend automatic synchronization (for all processes), so changes are
		only held in memory.  Changes made by one process are still visible to
		other processes.
		"""
		self.client_pipe.send(('hold',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def unhold(self):
		"""
		Resume automatic synchronization (for all processes), so changes are
		only held in memory.  Changes made by one process are still visible to
		other processes.
		"""
		self.client_pipe.send(('unhold',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def revert(self):
		"""Proxy for ``POD.revert()``."""
		self.client_pipe.send(('revert',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def maybe_sync(self):
		"""Proxy for ``POD.maybe_sync()``."""
		self.client_pipe.send(('maybe_sync',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def mark_dirty(self, key):
		"""Proxy for ``POD.mark_dirty()``."""
		self.client_pipe.send(('mark_dirty', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def sync(self):
		"""Proxy for ``POD.sync()``."""
		self.client_pipe.send(('sync',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def __contains__(self, key):
		# Proxy for ``POD.__contains__()``.
		self.client_pipe.send(('__contains__', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def __len__(self):
		# Proxy for ``POD.__len__()``.
		self.client_pipe.send(('__len__',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	def iteritems(self):
		"""Proxy for ``POD.iteritems()``."""
		# This helper manages requests to the progress tracker for iteration
		# over its values.  It is a compromize between two extremes: 1)
		# requesting each iterations' item separately (acquiring the lock each
		# time) and 2) requesting the full iterable in one request, which means
		# potentially pushing a lot of data through the pipe at once and
		# holding onto the lock for a long time.  Instead, the items for
		# iteration are requested in chunks, and are yielded individually from
		# the locally stored chunk.

		has_more = True
		start, end = 0, ITERITEMS_CHUNK_SIZE

		# Request chunks from the server, then yield items from them locally
		while has_more:

			# Get a chunk
			self.LOCK.acquire()
			self.client_pipe.send(('iter', False, start, end))
			items, has_more = self.client_pipe.recv()
			self.LOCK.release()

			# Yield items from the chunk
			for item in items:
				yield item

			# Advance chunk pointer
			start += ITERITEMS_CHUNK_SIZE
			end += ITERITEMS_CHUNK_SIZE

	
	@_requires_tracker_open
	def __iter__(self):
		# Proxy for ``POD.__iter__()``.
		#
		# This helper manages requests to the progress tracker for iteration
		# over its values.  It is a compromize between two extremes: 1)
		# requesting each iterations' item separately (acquiring the lock each
		# time) and 2) requesting the full iterable in one request, which means
		# potentially pushing a lot of data through the pipe at once and
		# holding onto the lock for a long time.  Instead, the items for
		# iteration are requested in chunks, and are yielded individually from
		# the locally stored chunk.

		has_more = True
		start, end = 0, ITERKEYS_CHUNK_SIZE

		# Request chunks from the server, then yield items from them locally
		while has_more:

			# Get a chunk
			self.LOCK.acquire()
			self.client_pipe.send(('iter', True, start, end))
			items, has_more = self.client_pipe.recv()
			self.LOCK.release()

			# Yield items from the chunk
			for item in items:
				yield item

			# Advance chunk pointer
			start += ITERKEYS_CHUNK_SIZE
			end += ITERKEYS_CHUNK_SIZE

	def items(self):
		"""Proxy for ``POD.items()``."""
		return [item for item in self.iteritems()]

	def keys(self):
		"""Proxy for ``POD.keys()``."""
		return [key for key in self]

	def values(self):
		"""Proxy for ``POD.values()``."""
		return [val for key, val in self.iteritems()]


	@_requires_tracker_open
	@_requires_lock(LOCK)
	def __getitem__(self, key):
		# Proxy for ``POD.__getitem__()``.
		self.client_pipe.send(('__getitem__', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def update(self, key):
		"""Proxy for ``POD.update()``."""
		self.client_pipe.send(('update', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def __setitem__(self, key, val):
		# Proxy for ``POD.__setitem__()``.
		self.client_pipe.send(('__setitem__', key, val))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def set(self, key_tuple, val):
		"""Proxy for ``POD.set()``."""
		self.client_pipe.send(('set', key_tuple, val))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val


SharedPOD = SharedPersistentOrderedDict


class SharedProgressTracker(SharedPersistentOrderedDict):
	"""
	A multiprocessing-safe progress tracker that can be shared by many
	processes.  Data will be syncronized to disk in files under ``path``.  
	Avoids the problem of concurrent disk access that would arise if an
	ordinary ProgressTracker were shared by multiple processes.
	"""

	CLOSE = 0
	LOCK = multiprocessing.RLock()

	def __init__(self, path):
		self.client_pipe, server_pipe = multiprocessing.Pipe()
		# create a real progress_tracker and a listen loop around it
		server_tracker = multiprocessing.Process(
			target=serve_datastructure,
			args=(lambda: tastypy.ProgressTracker(path), server_pipe)
		)
		server_tracker.daemon = True	# shut down server if main process exits
		server_tracker.start()
		# The tracker is ready for business
		self.tracker_open = True

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def check_or_add(self, key):
		"""Proxy for ``Tracker.check_or_add()``."""
		self.client_pipe.send(('check_or_add', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def check(self, key):
		"""Proxy for ``Tracker.check()``."""
		self.client_pipe.send(('check', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def add(self, key):
		"""Proxy for ``Tracker.add()``."""
		self.client_pipe.send(('add', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def increment_tries(self, key):
		"""Proxy for ``Tracker.increment_tries()``."""
		self.client_pipe.send(('increment_tries', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def decrement_tries(self, key):
		"""Proxy for ``Tracker.decrement_tries()``."""
		self.client_pipe.send(('decrement_tries', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def reset_tries(self, key):
		"""Proxy for ``Tracker.reset_tries()``."""
		self.client_pipe.send(('reset_tries', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def tries(self, key):
		"""Proxy for ``Tracker.tries()``."""
		self.client_pipe.send(('tries', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val


	@_requires_tracker_open
	@_requires_lock(LOCK)
	def mark_done(self, key):
		"""Proxy for ``Tracker.mark_done()``."""
		self.client_pipe.send(('mark_done', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def mark_not_done(self, key):
		"""Proxy for ``Tracker.mark_not_done()``."""
		self.client_pipe.send(('mark_not_done', key))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def add_if_absent(self, key):
		"""Proxy for ``Tracker.add_if_absent()``."""
		self.client_pipe.send(('add_if_absent', key))
		return self.client_pipe.recv()
		
	@_requires_tracker_open
	@_requires_lock(LOCK)
	def num_done(self):
		self.client_pipe.send(('num_done',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def num_tried(self):
		"""Proxy for ``Tracker.num_tried()``."""
		self.client_pipe.send(('num_tried',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def fraction_done(self):
		"""Proxy for ``Tracker.fraction_done()``."""
		self.client_pipe.send(('fraction_done',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def fraction_tried(self):
		"""Proxy for ``Tracker.fraction_tried()``."""
		self.client_pipe.send(('fraction_tried',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def percent_not_done(self, decimals=2):
		"""Proxy for ``Tracker.percent_not_done()``."""
		self.client_pipe.send(('percent_not_done',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def percent_done(self, decimals=2):
		"""Proxy for ``Tracker.percent_done()``."""
		self.client_pipe.send(('percent_done',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def percent_not_tried(self, decimals=2):
		"""Proxy for ``Tracker.percent_not_tried()``."""
		self.client_pipe.send(('percent_not_tried',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def percent_tried(self, decimals=2):
		"""Proxy for ``Tracker.percent_tried()``."""
		self.client_pipe.send(('percent_tried',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val

	@_requires_tracker_open
	@_requires_lock(LOCK)
	def percent(self, fraction, decimals):
		"""Proxy for ``Tracker.percent()``."""
		self.client_pipe.send(('percent',))
		return_val, error = self.client_pipe.recv()
		if error is not None:
			raise error
		return return_val


SharedTracker = SharedProgressTracker
