from unittest import main, TestCase

import gzip
import sys
import os
import time
import random
import shutil
import tastypy
import multiprocessing

# TODO: test gates.
# TODO: test that max_tries=0 has the expected effects
# TODO: test that allow_aborted has the expected effects
# TODO: test SharedTracker special iterations
# TODO: test ProgressTracker aborted()
# TODO: There was a bug with PODs and Trackers in which they would be borg'd to
# 	eachother causing bad initializatin (missing attrubutes like _num_done in
# 	Tracker).  This was seen from interactions *between tests* but there should
# 	be a specific test for that
# asynchronous.  Add test
# TODO: is clone being respected in tracker?
# TODO: test that key access can trigger sync'ing and that it the accessed key
# remains dirty afterward
# TODO: test that int and tuple-typed keys work

TEST_PATH = 'test-data'
DEFAULT_TRACKER_ITEM = dict(tastypy.DEFAULT_PROGRESS_TRACKER_MAPPING)

def remove_if_exists(path):
	if os.path.exists(path):
		shutil.rmtree(path)

def read_test_files(gzipped=False):
	entries = {}
	_open = gzip.open if gzipped else open
	for path in tastypy.ls(TEST_PATH):
		try:
			f = _open(path)
			entries.update(tastypy.JSONSerializer.read_items(f))
		except IOError:
			raise
			pass
	return entries


class TestPOD(TestCase):

	def basic_test(self, gzipped):
		"""
		Create a POD, check that it's files are written in the specified with
		the correct number of lines per file, and that data persists through a
		deletion
		"""

		# Test that data is stored correctly, and persisted after the POD
		# object is deleted in this namespace
		remove_if_exists(TEST_PATH)
		my_pod = tastypy.POD(TEST_PATH, gzipped=gzipped, clone=False)
		my_pod['a'] = 1
		my_pod['b'] = '2'
		my_pod['c'] = {'key':[1,'2']}
		for i in range(tastypy.DEFAULT_FILE_SIZE):
			my_pod[str(i)] = i

		# Open a POD to same location, and check tha all data is there
		target_fname = '0.json.gz' if gzipped else '0.json'
		entries = read_test_files(gzipped)

		self.assertEqual(entries['a'], 1)
		self.assertEqual(entries['b'], '2')
		self.assertEqual(entries['c'], {'key': [1, '2']})
		self.assertEqual(len(entries), tastypy.DEFAULT_FILE_SIZE)

	def test_basic(self):
		"""
		Run the basic test first for plain .json files, then for gzipped.
		"""
		self.basic_test(False)
		self.basic_test(True)


	def test_integrity_check(self):
		"""
		Create corrupted POD persistence files and ensure that POD raises the
		appropriate exception.
		"""

		# Make a POD
		remove_if_exists(TEST_PATH)
		my_pod = tastypy.POD(TEST_PATH)
		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_FILE_SIZE):
			my_pod[str(i)] = 'yo'
		my_pod.sync()

		# Add an extra validly formatted value on the end of the file.
		open(my_pod._path_from_int(0), 'a').write('"extra-key"\t"extra-val"\n')

		# Check that an integrity error gets raised (due to too many entries)
		with self.assertRaises(tastypy.PersistentOrderedDictIntegrityError):
			my_pod.revert()

		# Remove old POD's files and make a new POD
		remove_if_exists(TEST_PATH)
		my_pod = tastypy.POD(TEST_PATH)
		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_FILE_SIZE):
			my_pod[str(i)] = i
		my_pod.sync()

		# Mangle one of the lines in the middle of the file
		stored_data_str = open(my_pod._path_from_int(0)).read().split('\n')
		stored_data_str[500] = 'bad format'
		open(my_pod._path_from_int(0), 'w').write('\n'.join(stored_data_str))

		# Check that an integrity error gets raised
		with self.assertRaises(tastypy.PersistentOrderedDictIntegrityError):
			my_pod.revert()


	def test_auto_sync(self):
		"""
		Test that synchronization can be suspended and reactivated, that
		synchronization can be forced manually, and that specific items can be
		marked for synchronization.
		"""

		# Clear previous data files if any
		remove_if_exists(TEST_PATH)

		# Make a new POD, and add one value
		my_pod = tastypy.POD(TEST_PATH, clone=False)
		my_pod['a'] = 1

		# That value isn't synced to disk yet
		entries = read_test_files()
		with self.assertRaises(KeyError):
			entries['a']

		# Data is synced when the buffer reaches a certain size
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod[str(i)] = i
		entries = read_test_files()
		self.assertEqual(entries['a'], 1)


	def test_hold(self):

		# Clear previous data files if any
		remove_if_exists(TEST_PATH)

		# Make a new POD, and add one value
		my_pod = tastypy.POD(TEST_PATH, clone=False)
		my_pod['a'] = 1

		# When a hold is applied, data isn't sync'd even if we add many values
		my_pod.hold()
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod[str(i)] = i
		entries = read_test_files()
		with self.assertRaises(KeyError):
			entries['a']

		# Manually calling sync() does synchronize out-of-sync data
		my_pod.sync()
		entries = read_test_files()
		self.assertTrue(entries['a'], 1)

		# But automatic synchronization is still disabled
		my_pod['b'] = 2
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod[str(i)] = i
		entries = read_test_files()
		with self.assertRaises(KeyError):
			entries['b']

		# Calling unhold() synchronizes out-of-sync data if it's beyond the
		# sync_at threshold
		my_pod.unhold()
		entries = read_test_files()
		self.assertEqual(entries['b'], 2)

		# And it also re-enables automatic synchronization
		my_pod['c'] = 3
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod[str(i)] = i
		entries = read_test_files()
		self.assertEqual(entries['c'], 3)


	def test_iteration(self):
		"""
		Test that iteration, keys, values, items, and iteritems work as
		expected.
		"""
		num_lines = 20

		# Clear previous data files if any
		remove_if_exists(TEST_PATH)

		# Test various iteration functions
		my_pod = tastypy.POD(TEST_PATH, clone=False)
		my_pod.hold()
		for i in range(num_lines):
			my_pod[str(i)] = i
		my_pod.sync()

		# A POD can be treated as an iterable, it yields its keys
		accumulate_keys = []
		for key in my_pod:
			accumulate_keys.append(key)
		self.assertEqual(accumulate_keys, [str(i) for i in range(num_lines)])

		# A list of key-value pairs be obtained using ``.items()``
		self.assertEqual(my_pod.items(), [(str(i), i) for i in range(num_lines)])

		# An iterator of key-value pairs can be obtained using ``.iteritems()``
		accumulate_items = []
		for key, val in my_pod.iteritems():
			accumulate_items.append((key, val))
		self.assertEqual(accumulate_items, [(str(i), i) for i in
			range(num_lines)])

		# A list of keys can be obtained using ``.keys()``
		self.assertEqual(my_pod.keys(), [str(i) for i in range(num_lines)])

		# Mutating the returned keys has no effect on the POD
		my_pod.keys().extend(['adding', 'fake', 'keys'])
		self.assertFalse(
			any(['adding' in my_pod, 'fake' in my_pod, 'keys' in my_pod]))
		self.assertEqual(len(my_pod), num_lines)
		self.assertEqual(my_pod.keys()[-1], str(num_lines-1))

		# A list of values can be obtained using ``.values()``
		self.assertEqual(my_pod.values(), range(num_lines))

		# Mutating the list of values doesn't affect the POD
		my_pod.values().extend([1,2,3])
		self.assertEqual(my_pod.values(), range(num_lines))
		self.assertEqual(my_pod.values()[-1], num_lines-1)



	def test_in(self):
		"""
		Test that PODs their length and what keys are "in" them.
		"""
		# Clear previous data files if any
		remove_if_exists(TEST_PATH)

		# Test that my_pod knows what keys it has
		my_pod = tastypy.POD(TEST_PATH, clone=False)
		my_pod['a'] = 1
		self.assertTrue('a' in my_pod)
		self.assertFalse('b' in my_pod)



class TestTracker(TestCase):

	def test_add(self):
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.Tracker(TEST_PATH, clone=False)

		# Check that addition insets the expected value
		my_tracker.add('a')
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_tracker.add(str(i))
		self.assertEqual(my_tracker['a'], DEFAULT_TRACKER_ITEM)

		# Verify persistence
		entries = read_test_files()
		self.assertEqual(entries['a'], DEFAULT_TRACKER_ITEM)

		# Verify that DuplicateKeyError is raised if we try adding the same
		# key twice
		with self.assertRaises(tastypy.DuplicateKeyError):
			my_tracker.add('a')

		# DuplicateKeyError is not raise for ``add_if_absent()``
		my_tracker.add_if_absent('a')

		# Test the check function (should return false)
		self.assertFalse(my_tracker.done('a'))

		# Mark done, now check should return True
		my_tracker.mark_done('a')
		self.assertTrue(my_tracker.done('a'))

		# Mark not done, now check returns False again
		my_tracker.mark_not_done('a')
		self.assertFalse(my_tracker.done('a'))

		# Test check or add.  On a key that exists but is not done, it should
		# return False and have no effect on the entry
		self.assertTrue(my_tracker.should_do_add('a'))
		self.assertEqual(my_tracker['a'], DEFAULT_TRACKER_ITEM)

		# Test check or add.  On a key that exists and is done, it should
		# return True and have no effect on the entry
		my_tracker.mark_done('a')
		self.assertFalse(my_tracker.should_do_add('a'))
		self.assertEqual(
			my_tracker['a'], 
			{'_tries':0, '_aborted':False, '_done':True}
		)

		# Test check or add.  On a key that doesn't exist, it will return True
		# and add the key
		self.assertTrue(my_tracker.should_do_add('b'))
		self.assertEqual(my_tracker['b'], DEFAULT_TRACKER_ITEM)

		# Test incrementing tries
		self.assertEqual(my_tracker.tries('a'), 0)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker.tries('a'), 1)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker.tries('a'), 2)
		my_tracker.decrement_tries('a')
		self.assertEqual(my_tracker.tries('a'), 1)
		my_tracker.reset_tries('a')
		self.assertEqual(my_tracker.tries('a'), 0)

		# Test setting a sub-key
		my_tracker['a']['b'] = 'c'
		self.assertEqual(
			my_tracker['a'], 
			{'b':'c', '_tries':0, '_done':True, '_aborted':False}
		)

		# Test that a sub-key will be synchronized
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_tracker.reset_tries(str(i))
		entries = read_test_files()
		self.assertEqual(
			entries['a'],
			{'b':'c', '_tries':0, '_done':True, '_aborted':False}
		)


	def test_update(self):
		# Test tries status
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.Tracker(TEST_PATH, clone=False)

		my_tracker.add('a')
		my_tracker['a']['foo'] = 1
		my_tracker.update(
			{
				'a': {'foo': 2, 'bar': [3], 'beep': 'x'},
				'b': {'_tries':1, 'fizz': 'baz'}
			}, 
			(('a', {'beep':'xx', 'boo':42}),),
			c={'bam':[89]}
		)

		my_tracker.sync()
		entries = read_test_files()
		self.assertEqual(
			entries['a'],
			{
				'_tries':0, '_aborted':False, '_done':False, 
				'foo':2, 'bar':[3], 'beep':'xx', 'boo':42
			}
		)
		self.assertEqual(
			entries['b'],
			{'_tries':1, '_aborted':False, '_done':False, 'fizz':'baz'}
		)
		self.assertEqual(
			entries['c'], 
			{'_tries':0, '_aborted':False, '_done':False, 'bam':[89]}
		)


	def test_done_tried(self):

		# Test tries status
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.Tracker(TEST_PATH, clone=False)
		my_tracker.add('a')
		my_tracker.add('b')

		# Test tries status
		self.assertEqual(my_tracker.num_tried(), 0)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker.num_tried(), 1)
		my_tracker.add_if_absent('b')
		my_tracker.increment_tries('b')
		self.assertEqual(my_tracker.num_tried(), 2)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker.num_tried(), 2)
		my_tracker.sync()

		self.assertEqual(my_tracker.num_tried(), 2)
		self.assertEqual(my_tracker.fraction_tried(), 1.0)
		self.assertEqual(my_tracker.percent_tried(), '100.00 %')
		my_tracker.reset_tries('b')
		self.assertEqual(my_tracker.fraction_tried(), 0.5)
		self.assertEqual(my_tracker.percent_tried(), '50.00 %')

		# Test progress status
		self.assertEqual(my_tracker.num_done(), 0)
		self.assertEqual(my_tracker.fraction_done(), 0.0)
		self.assertEqual(my_tracker.percent_done(), '0.00 %')
		my_tracker.mark_done('a')
		self.assertEqual(my_tracker.num_done(), 1)
		self.assertEqual(my_tracker.fraction_done(), 0.5)
		self.assertEqual(my_tracker.percent_done(), '50.00 %')
		my_tracker.mark_done('b')
		self.assertEqual(my_tracker.num_done(), 2)
		self.assertEqual(my_tracker.fraction_done(), 1.0)
		self.assertEqual(my_tracker.percent_done(), '100.00 %')



class TestSharedPOD(TestCase):

	# TODO: test that in-memory values are still shared between processes when
	# hold is active, but that all processes except caller are blocked when
	# lock is called.
	def test_basic_functions(self):

		remove_if_exists(TEST_PATH)

		# Shared PODs should sync when they close
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)
		my_pod.set['a'] = 1
		my_pod.close()
		entries = read_test_files()
		self.assertEqual(entries['a'], 1)

		# SharedPODs don't sync automatically when hold is called
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)
		my_pod.hold()
		my_pod.set['b'] = 2
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod.set[i] = i
		entries = read_test_files()
		self.assertFalse('b' in entries)

		# The SharedPOD sycs when unhold is called (it has more than sync_at
		# dirty values)
		my_pod.unhold()
		entries = read_test_files()
		self.assertEqual(entries['b'], 2)

		# And automatic synchronization has resumed
		my_pod.set['c'] = 3
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_pod.set[i] = i
		entries = read_test_files()
		self.assertEqual(entries['c'], 3)


	def test_deep_assignment(self):

		remove_if_exists(TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)
		my_pod['a'] = {'int': 1, 'list':[], 'dict':{'a':1}}
		my_pod.sync()

		# First just check that the value is there
		entries = read_test_files()
		self.assertEqual(
			entries['a'], {'int': 1, 'list':[], 'dict':{'a':1}}
		)

		# Try different updates
		my_pod.set['a']['list'].append(2)
		my_pod.set['a']['dict']['b'] = 4
		my_pod.set['a']['int'] += 1
		my_pod.sync()
		expected = {'int': 2, 'list':[2], 'dict':{'a':1, 'b':4}}
		entries = read_test_files()
		self.assertEqual(entries['a'], expected)

		# Try different updates
		del my_pod.set['a']['int']
		my_pod.set['a']['list'].append(5)
		my_pod.set['a']['dict'].update({'c':6})
		my_pod.sync()
		expected ={'list':[2,5], 'dict':{'a':1, 'b':4, 'c':6}}
		entries = read_test_files()
		self.assertEqual(entries['a'], expected)


	def test_concurrent_write(self):
		remove_if_exists(TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)
		my_pod.set['a'] = 0

		p1 = multiprocessing.Process(
				target=self.concurrent_write, args=(my_pod,'A'))
		p2 = multiprocessing.Process(
				target=self.concurrent_write, args=(my_pod,'B'))

		p1.start()
		p2.start()

		p1.join()
		p2.join()

		self.assertEqual(my_pod['a'], 400)


	def test_iteration(self):

		remove_if_exists(TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)

		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_FILE_SIZE):
			my_pod[str(i)] = i
		my_pod.unhold()

		expected_values = range(2 * tastypy.DEFAULT_FILE_SIZE)
		expected_keys = [str(i) for i in expected_values]
		expected_items = zip(expected_keys, expected_values)
		self.assertEqual(my_pod.values(), expected_values)
		self.assertEqual(my_pod.keys(), expected_keys)
		self.assertEqual(my_pod.items(), expected_items)

		accumulate_items = []
		for item in my_pod.iteritems():
			accumulate_items.append(item)
		self.assertEqual(accumulate_items, expected_items)

		accumulate_keys = []
		for key in my_pod:
			accumulate_keys.append(key)
		self.assertEqual(accumulate_keys, expected_keys)

		my_pod.close()


	def test_hold(self):

		remove_if_exists(TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(TEST_PATH)

		# Spawn two processes that each request a hold on the same POD and
		# insert some data.  The first process will get the hold first, and be
		# able to insert all of its data before the second process.  Therefore we
		# should never see the insertions by the processes interleaved.
		p1 = multiprocessing.Process(
			target=self.do_test_hold, args=(my_pod,'A'))
		p2 = multiprocessing.Process(
			target=self.do_test_hold, args=(my_pod,'B'))

		start_time = time.time()
		p1.start()
		p2.start()

		p1.join()
		p2.join()

		p1_insertion_times = []
		p2_insertion_times = []

		
		p1_times = [my_pod['A:'+str(i)] - start_time for i in range(10)]
		p2_times = [my_pod['B:'+str(i)] - start_time for i in range(10)] 
		p1_max_time = max(p1_times)
		p1_min_time = min(p1_times)
		p2_min_time = min(p2_times)
		p2_max_time = max(p2_times)

		done_sequentially = (
			p1_max_time <= p2_min_time or p2_max_time <= p1_min_time
		)
		self.assertTrue(done_sequentially)

		my_pod.close()

	
	def concurrent_write(self, my_pod, name):
		for i in range(200):
			with my_pod.locked():
				my_pod.set['a'] += 1


	def do_test_hold(self, my_pod, name):
		with my_pod.locked():
			for i in range(10):
				time.sleep(random.random()/100.)
				my_pod['%s:%d' % (name, i)] = time.time()


class TestSharedTracker(TestCase):

	def test_basic_function(self):
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(TEST_PATH)

		# Demonstrate basic persistence
		my_tracker.add('a')
		my_tracker.close()
		entries = read_test_files()
		self.assertTrue(entries['a'], {'_tries':0, '_done':False})

		# Demonstrate hold()
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(TEST_PATH)
		my_tracker.hold()
		my_tracker.add('a')
		for i in range(tastypy.DEFAULT_SYNC_AT):
			my_tracker.add(i)

		entries = read_test_files()
		self.assertFalse('a' in entries)

		# Unhold causes unsync'd values to be sync'd
		my_tracker.unhold()
		entries = read_test_files()
		self.assertEqual(entries['a'], DEFAULT_TRACKER_ITEM) 

		# Demonstrate increment_tries()
		my_tracker.increment_tries('a')
		my_tracker.sync()
		entries = read_test_files()
		self.assertEqual(entries['a']['_tries'], 1) 

		# Demonstrate decrement_tries()
		my_tracker.decrement_tries('a')
		my_tracker.sync()
		entries = read_test_files()
		self.assertEqual(entries['a']['_tries'], 0) 

		# Demontstrate mark_done() and check()
		my_tracker.mark_done('a')
		my_tracker.sync()
		entries = read_test_files()
		self.assertTrue(entries['a']['_done'])

		# Demonstrate mark_not_done() and check()
		my_tracker.mark_not_done('a')
		my_tracker.sync()
		entries = read_test_files()
		self.assertFalse(entries['a']['_done'])


	def test_fraction(self):

		# Demonstrate num_done and num_tried, and related functions
		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(TEST_PATH)

		my_tracker.add('a')
		my_tracker.mark_done('a')
		my_tracker.add('b')
		my_tracker.mark_done('b')
		my_tracker.increment_tries('b')
		my_tracker.add('c')
		my_tracker.sync()

		self.assertEqual(my_tracker.num_done(), 2)
		self.assertEqual(my_tracker.fraction_done(), 2/3.)
		self.assertEqual(my_tracker.percent_done(), '%.2f %%' % (200/3.))

		self.assertEqual(my_tracker.num_tried(), 1)
		self.assertEqual(my_tracker.fraction_tried(), 1/3.)
		self.assertEqual(my_tracker.percent_tried(), '%.2f %%' % (100/3.))



	def test_iteration(self):

		remove_if_exists(TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(TEST_PATH)

		my_tracker.hold()
		for i in range(20):
			my_tracker.add(str(i))
		my_tracker.unhold()

		expected_keys = [str(i) for i in range(20)]
		expected_values = [DEFAULT_TRACKER_ITEM for i in expected_keys]
		expected_items = zip(expected_keys, expected_values)
		self.assertEqual(my_tracker.values(), expected_values)
		self.assertEqual(my_tracker.keys(), expected_keys)
		self.assertEqual(my_tracker.items(), expected_items)

		accumulate_items = []
		for item in my_tracker.iteritems():
			accumulate_items.append(item)
		self.assertEqual(accumulate_items, expected_items)

		accumulate_keys = []
		for key in my_tracker:
			accumulate_keys.append(key)
		self.assertEqual(accumulate_keys, expected_keys)

		my_tracker.close()


	def test_special_iteration(self):
		remove_if_exists(TEST_PATH)
		tracker = tastypy.SharedProgressTracker(TEST_PATH, max_tries=2)

		tracker.add_many(['a','b','c','d'])

		# A will not be yielded because it's aborted
		tracker.abort('a')

		# 'b' will be yielded because it has only one try (max_tries=2)
		tracker.increment_tries('b')

		# 'c' will not be yielded because it has two tries
		tracker.increment_tries('c')
		tracker.increment_tries('c')

		# 'd' will not be yielded because it is marked done
		tracker.mark_done('d')

		items = []
		for item in tracker.todo_items():
			items.append(item)
		self.assertEqual(items, [
			('b', {'_tries':1, '_done':False, '_aborted':False})
		])


		


	def test_concurrent_write(self):
		remove_if_exists(TEST_PATH)
		tracker = tastypy.SharedProgressTracker(TEST_PATH)
		tracker.add('yo')

		p1 = multiprocessing.Process(
				target=self.concurrent_write, args=(tracker,'A'))
		p2 = multiprocessing.Process(
				target=self.concurrent_write, args=(tracker,'B'))

		p1.start()
		p2.start()

		p1.join()
		p2.join()

		self.assertEqual(tracker.tries('yo'), 400)
		tracker.close()


	def test_hold(self):
		remove_if_exists(TEST_PATH)
		tracker = tastypy.SharedProgressTracker(TEST_PATH)

		# Spawn two processes that each request a hold on the same tracker and
		# insert some data.  The first process will get the hold first, and be
		# able to insert all of its data before the second process.  Therefore we
		# should never see the insertions by the processes interleaved.
		p1 = multiprocessing.Process(
			target=self.do_test_hold, args=(tracker,'A'))
		p2 = multiprocessing.Process(
			target=self.do_test_hold, args=(tracker,'B'))

		start_time = time.time()
		p1.start()
		p2.start()

		p1.join()
		p2.join()

		p1_insertion_times = []
		p2_insertion_times = []
		
		p1_times = [tracker['A:'+str(i)]['time'] - start_time for i in range(10)]
		p2_times = [tracker['B:'+str(i)]['time'] - start_time for i in range(10)]
		p1_max_time = max(p1_times)
		p1_min_time = min(p1_times)
		p2_min_time = min(p2_times)
		p2_max_time = max(p2_times)

		done_sequentially = (
			p1_max_time <= p2_min_time or p2_max_time <= p1_min_time
		)
		self.assertTrue(done_sequentially)

		tracker.close()

	
	def concurrent_write(self, tracker, name):
		for i in range(200):
			tracker.increment_tries('yo')


	def do_test_hold(self, tracker, name):
		with tracker.locked():
			for i in range(10):
				time.sleep(random.random() / 100.0)
				key = '%s:%d' % (name, i)
				tracker.add(key)
				tracker.set[key]['time'] = time.time()


if __name__ == '__main__':
	main()

