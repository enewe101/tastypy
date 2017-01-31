'''
The progress tracker is a specialized persistent ordered dict that offers a few
extra methods for the common usecase of keeping track of progress in
long-running processes and resuming the work where it was left off after a
crash or suspension.
'''

from .persistent_ordered_dict import PersistentOrderedDict

class ProgressTracker(PersistentOrderedDict):

	def check_or_add(self, key):
		'''
		checks if there is an entry for key already marked as done
		(returns True if so).  If no entry exists for key, it makes one
		and provides it with a defualt value of _done:False and _tries:0
		'''
		key = self.ensure_unicode(key)
		if key in self:
			if self[key]['_done']:
				return True
			else:
				return False
		else:
			self[key] = {'_done':False, '_tries':0}
			return False


	def check(self, key):
		key = self.ensure_unicode(key)
		if key in self:
			if self[key]['_done']:
				return True
			else:
				return False
		else:
			return False


	def add(self, key):
		key = self.ensure_unicode(key)
		if key in self:
			raise DuplicateKeyException(
				'ProgressTracker: key "%s" already exists.' % key)
		else:
			self[key] = {'_done':False, '_tries':0}


	def increment_tries(self, key):
		key = self.ensure_unicode(key)
		self[key]['_tries'] += 1
		self.update(key)


	def reset_tries(self, key):
		key = self.ensure_unicode(key)
		self[key]['_tries'] = 0
		self.update(key)


	def mark_done(self, key):
		key = self.ensure_unicode(key)
		self[key]['_done'] = True
		self.update(key)


	def mark_not_done(self, key):
		key = self.ensure_unicode(key)
		self[key]['_done'] = False
		self.update(key)


