'''
The SharedProgressTracker is a sharable proxy to a progress_tracker that runs
in a separate spawned process.  The proxy can be treated just like a progress
tracker and can be accessed from different processes without any need to worry
about synchronization.
'''

import multiprocessing
from .progress_tracker import ProgressTracker

def requires_lock(lock):
	def decorator(f):
		def f_with_lock(*args, **kwargs):
			lock.acquire()
			return_val = f(*args, **kwargs)
			lock.release()
			return return_val

		return f_with_lock
	return decorator


def requires_tracker_open(f):
	def f_that_requires_tracker_open(self, *args, **kwargs):
		if not self.tracker_open:
			raise CalledClosedTrackerException
		return f(self, *args, **kwargs)

	return f_that_requires_tracker_open



class CalledClosedTrackerException(Exception):
	pass



class SharedProgressTracker(object):
	pass

	CLOSE = 0
	LOCK = multiprocessing.RLock()

	def __init__(self, path):

		self.client_pipe, server_pipe = multiprocessing.Pipe()
		self.lock = multiprocessing.Lock()

		# create a real progress_tracker and a listen loop around it
		client_tracker = multiprocessing.Process(
			target=progress_tracker_serve,
			args=(path, server_pipe)
		)
		client_tracker.start()

		self.tracker_open = True

	@requires_lock(LOCK)
	def close(self):
		self.client_pipe.send(self.CLOSE)

	@requires_tracker_open
	def hold(self):
		self.LOCK.acquire()
		self.client_pipe.send(('hold',))
		return self.client_pipe.recv()

	@requires_tracker_open
	def unhold(self):
		self.client_pipe.send(('unhold',))
		return_val = self.client_pipe.recv()
		self.LOCK.release()
		return return_val

	@requires_tracker_open
	@requires_lock(LOCK)
	def read(self):
		self.client_pipe.send(('read',))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def mark_dirty(self, key):
		self.client_pipe.send(('mark_dirty', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def sync(self):
		self.client_pipe.send(('sync',))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def __contains__(self, key):
		self.client_pipe.send(('__contains__', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def __len__(self):
		self.client_pipe.send(('__len__',))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def __getitem__(self, key):
		self.client_pipe.send(('__getitem__', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def update(self, key):
		self.client_pipe.send(('update', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def __setitem__(self, key, val):
		self.client_pipe.send(('__setitem__', key, val))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def check_or_add(self, key):
		self.client_pipe.send(('check_or_add', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def set(self, key, subkey, val):
		self.client_pipe.send(('set', key, subkey, val))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def check(self, key):
		self.client_pipe.send(('check', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def add(self, key):
		self.client_pipe.send(('add', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def increment_tries(self, key):
		self.client_pipe.send(('increment_tries', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def reset_tries(self, key):
		self.client_pipe.send(('reset_tries', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def mark_done(self, key):
		self.client_pipe.send(('mark_done', key))
		return self.client_pipe.recv()

	@requires_tracker_open
	@requires_lock(LOCK)
	def mark_not_done(self, key):
		self.client_pipe.send(('mark_not_done', key))
		return self.client_pipe.recv()


	
def progress_tracker_serve(path, pipe):
	progress_tracker = ProgressTracker(path)
	is_open = True
	while is_open:
		message = pipe.recv()
		if message == SharedProgressTracker.CLOSE:
			is_open = False
		else:
			attr, args = message[0], message[1:]
			pipe.send(getattr(progress_tracker, attr)(*args))

		

