from unittest import main, TestCase

import os
import time
import random
import shutil
import tastypy
import multiprocessing

def remove_if_exists(path):
	if os.path.exists(path):
		shutil.rmtree(path)


class TestPOD(TestCase):

	TEST_PATH = 'test.pod'

	def tearDown(self):
		remove_if_exists(self.TEST_PATH)

	def test_basic(self):
		"""
		Create a POD, check that it's files are written in the specified with
		the correct number of lines per file, and that data persists through a
		deletion
		"""

		# Test that data is stored correctly, and persisted after the POD
		# object is deleted in this namespace
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.POD(self.TEST_PATH)
		my_pod.hold()
		my_pod['a'] = 1
		my_pod['b'] = '2'
		my_pod['c'] = {'key':[1,'2']}
		for i in range(tastypy.DEFAULT_LINES_PER_FILE):
			my_pod[str(i)] = i
		my_pod.sync()

		# Delete the POD.  Its data should persist though!
		del my_pod

		# Open a POD to same location, and check tha all data is there
		my_pod = tastypy.POD(self.TEST_PATH)
		self.assertEqual(my_pod['a'], 1)
		self.assertEqual(my_pod['b'], '2')
		self.assertEqual(my_pod['c'], {'key': [1, '2']})
		vals = [my_pod[str(i)] for i in range(tastypy.DEFAULT_LINES_PER_FILE)]
		self.assertEqual(vals, range(tastypy.DEFAULT_LINES_PER_FILE))

		shutil.rmtree(self.TEST_PATH)


	def test_integrity_check(self):
		"""
		Create corrupted POD persistence files and ensure that POD raises the
		appropriate exception.
		"""

		# Make a POD
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.POD(self.TEST_PATH)
		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_LINES_PER_FILE):
			my_pod[str(i)] = 'yo'
		my_pod.sync()

		# Add an extra validly formatted value on the end of the file.
		# (This should cause an error in a moment because the number of values 
		# per file is strictly limited so that the correct files are overrwitten 
		# during syncing).
		open(my_pod._path_from_int(0), 'a').write('extra-key\t"extra-val"\n')

		# Check that an integrity error gets raised.
		with self.assertRaises(tastypy.PersistentOrderedDictIntegrityError):
			my_pod = tastypy.POD(self.TEST_PATH)

		# Remove old POD's files and make a new POD
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.POD(self.TEST_PATH)
		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_LINES_PER_FILE):
			my_pod[str(i)] = i
		my_pod.sync()

		# Mangle one of the lines in the middle of the file
		stored_data_str = open(my_pod._path_from_int(0)).read().split('\n')
		stored_data_str[500] = 'bad format'
		open(my_pod._path_from_int(0), 'w').write('\n'.join(stored_data_str))

		# Check that an integrity error gets raised
		with self.assertRaises(tastypy.PersistentOrderedDictIntegrityError):
			my_pod = tastypy.POD(self.TEST_PATH)


	def test_synchronization_control(self):
		"""
		Test that synchronization can be suspended and reactivated, that
		synchronization can be forced manually, and that specific items can be
		marked for synchronization.
		"""

		# Clear previous data files if any
		remove_if_exists(self.TEST_PATH)

		# By default, data is sync'd immediately
		my_pod = tastypy.POD(self.TEST_PATH)
		my_pod['a'] = 1

		del my_pod
		my_pod = tastypy.POD(self.TEST_PATH)
		self.assertEqual(my_pod['a'], 1)

		# When a hold is applied, data is no longer sync'd
		my_pod.hold()
		my_pod['b'] = 2
		
		# Accessing my_pod['b'] will raise a key error
		my_other_pod = tastypy.POD(self.TEST_PATH)
		with self.assertRaises(KeyError):
			my_other_pod['b']

		# Calling sync() does synchronize out-of-sync data
		my_pod.sync()
		my_other_pod = tastypy.POD(self.TEST_PATH)
		self.assertTrue(my_other_pod['b'], 2)

		# But automatic synchronization is still disabled
		my_pod['c'] = 3
		my_other_pod = tastypy.POD(self.TEST_PATH)
		with self.assertRaises(KeyError):
			my_other_pod['c']

		# Calling unhold() also synchronizes out-of-sync data
		my_pod.unhold()
		my_other_pod = tastypy.POD(self.TEST_PATH)
		self.assertEqual(my_other_pod['c'], 3)

		# And it also re-enables automatic synchronization
		my_pod['d'] = 4
		my_other_pod = tastypy.POD(self.TEST_PATH)
		self.assertEqual(my_other_pod['d'], 4)


	def test_iteration(self):
		"""
		Test that iteration, keys, values, items, and iteritems work as
		expected.
		"""
		num_lines = 20

		# Clear previous data files if any
		remove_if_exists(self.TEST_PATH)

		# Test various iteration functions
		my_pod = tastypy.POD(self.TEST_PATH)
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
		remove_if_exists(self.TEST_PATH)

		# Test that my_pod knows what keys it has
		my_pod = tastypy.POD(self.TEST_PATH)
		my_pod['a'] = 1
		self.assertTrue('a' in my_pod)
		self.assertFalse('b' in my_pod)




class TestTracker(TestCase):

	TEST_PATH = 'test.tracker'

	def tearDown(self):
		remove_if_exists(self.TEST_PATH)

	def test_add(self):
		remove_if_exists(self.TEST_PATH)
		my_tracker = tastypy.Tracker(self.TEST_PATH)

		# Check that addition insets the expected value
		my_tracker.add('a')
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':False})

		# Verify persistence
		del my_tracker
		my_tracker = tastypy.Tracker(self.TEST_PATH)
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':False})

		# Verify that DuplicateKeyError is raised if we try adding the same
		# key twice
		with self.assertRaises(tastypy.DuplicateKeyError):
			my_tracker.add('a')

		# DuplicateKeyError is not raise for ``add_if_absent()``
		my_tracker.add_if_absent('a')

		# Test check (should return false)
		self.assertFalse(my_tracker.check('a'))

		# Mark done, now check should return True
		my_tracker.mark_done('a')
		self.assertTrue(my_tracker.check('a'))

		# Mark not done, now check returns False again
		my_tracker.mark_not_done('a')
		self.assertFalse(my_tracker.check('a'))

		# Test check or add.  On a key that exists but is not done, it should
		# return False but have no effect on the entry
		self.assertFalse(my_tracker.check_or_add('a'))
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':False})

		# Test check or add.  On a key that exists but is not done, it should
		# return False but have no effect on the entry
		my_tracker.mark_done('a')
		self.assertTrue(my_tracker.check_or_add('a'))
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':True})

		# Test check or add.  On a key that doesn't exist, it will return False
		# and add the key
		self.assertFalse(my_tracker.check_or_add('b'))
		self.assertEqual(my_tracker['b'], {'_tries':0, '_done':False})

		# Test incrementing tries
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':True})
		self.assertEqual(my_tracker.tries('a'), 0)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker['a'], {'_tries':1, '_done':True})
		self.assertEqual(my_tracker.tries('a'), 1)
		my_tracker.increment_tries('a')
		self.assertEqual(my_tracker['a'], {'_tries':2, '_done':True})
		self.assertEqual(my_tracker.tries('a'), 2)
		my_tracker.decrement_tries('a')
		self.assertEqual(my_tracker['a'], {'_tries':1, '_done':True})
		self.assertEqual(my_tracker.tries('a'), 1)
		my_tracker.reset_tries('a')
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':True})
		self.assertEqual(my_tracker.tries('a'), 0)

		# Test setting other values
		my_tracker.set('a', 'b', 'c')
		self.assertEqual(my_tracker['a'], {'b':'c', '_tries':0, '_done':True})

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
		new_tracker = tastypy.Tracker(self.TEST_PATH)
		self.assertEqual(new_tracker.num_tried(), 2)
		self.assertEqual(new_tracker.fraction_tried(), 1.0)
		self.assertEqual(new_tracker.percent_tried(), '100.00 %')
		new_tracker.reset_tries('b')
		self.assertEqual(new_tracker.fraction_tried(), 0.5)
		self.assertEqual(new_tracker.percent_tried(), '50.00 %')

		# Test progress status
		self.assertEqual(new_tracker.num_done(), 1)
		self.assertEqual(new_tracker.fraction_done(), 0.5)
		self.assertEqual(new_tracker.percent_done(), '50.00 %')
		new_tracker.mark_done('b')
		self.assertEqual(new_tracker.num_done(), 2)
		self.assertEqual(new_tracker.fraction_done(), 1.0)
		self.assertEqual(new_tracker.percent_done(), '100.00 %')



class TestSharedPOD(TestCase):

	TEST_PATH = 'test.pod'

	def tearDown(self):
		remove_if_exists(self.TEST_PATH)

	# TODO: test that in-memory values are still shared between processes when
	# hold is active, but that all processes except caller are blocked when
	# lock is called.

	def test_basic_functions(self):
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		my_pod['a'] = 1
		my_pod.close()

		my_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertEqual(my_pod['a'], 1)
		self.assertTrue('a' in my_pod)
		self.assertFalse('b' in my_pod)

		my_pod.hold()
		my_pod['c'] = {'key':1}
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertTrue('c' in my_pod)
		self.assertFalse('c' in other_pod)
		self.assertRaises(KeyError, lambda: other_pod['c'])
		with self.assertRaises(KeyError):
			other_pod['c']
		my_pod.unhold()

		other_pod.close()
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertTrue('c' in other_pod)
		self.assertEqual(other_pod['c'], {'key':1})

		my_pod.hold()
		my_pod['d'] = 1
		my_pod.maybe_sync()
		other_pod.close()
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertFalse('d' in other_pod)
		my_pod.sync()
		other_pod.close()
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertTrue('d' in other_pod)

		my_pod.hold()
		my_pod.set('c', 'key', 2)
		other_pod.close()
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertEqual(other_pod['c']['key'], 1)
		my_pod.sync()
		other_pod.close()
		other_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)
		self.assertEqual(other_pod['c']['key'], 2)
		my_pod.unhold()

		my_pod.close()
		other_pod.close()


	def test_concurrent_write(self):
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)

		p1 = multiprocessing.Process(
				target=self.concurrent_write, args=(my_pod,'A'))
		p2 = multiprocessing.Process(
				target=self.concurrent_write, args=(my_pod,'B'))

		p1.start()
		p2.start()

		p1.join()
		p2.join()

		self.assertEqual(my_pod['yo'], 400)
		my_pod.close()


	def test_iteration(self):

		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)

		my_pod.hold()
		for i in range(2 * tastypy.DEFAULT_LINES_PER_FILE):
			my_pod[str(i)] = i
		my_pod.unhold()

		expected_values = range(2 * tastypy.DEFAULT_LINES_PER_FILE)
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
		remove_if_exists(self.TEST_PATH)
		my_pod = tastypy.SharedPersistentOrderedDict(self.TEST_PATH)

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
			my_pod.lock()
			if 'yo' in my_pod:
				my_pod['yo'] += 1
			else:
				my_pod['yo'] = 1
			my_pod.unlock()


	def do_test_hold(self, my_pod, name):
		my_pod.holdlock()
		for i in range(10):
			time.sleep(random.random()/100.)
			my_pod['%s:%d' % (name, i)] = time.time()
		my_pod.unholdlock()


class TestSharedTracker(TestCase):

	TEST_PATH = 'test.tracker'


	def tearDown(self):
		remove_if_exists(self.TEST_PATH)


	def test_basic_function(self):
		remove_if_exists(self.TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		my_tracker.add('a')
		my_tracker.close()

		my_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertTrue('a' in my_tracker)
		self.assertEqual(my_tracker['a'], {'_tries':0, '_done':False})
		self.assertFalse('b' in my_tracker)

		my_tracker.hold()
		my_tracker.set('a', 'key', 1)
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertTrue('a' in my_tracker)
		self.assertTrue('a' in other_tracker)
		self.assertRaises(KeyError, lambda: other_tracker['a']['key'])

		my_tracker.unhold()
		other_tracker.close()
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertTrue('a' in other_tracker)
		self.assertEqual(other_tracker['a']['key'], 1)

		other_tracker.close()
		my_tracker.increment_tries('a')
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertEqual(other_tracker.tries('a'), 1)

		other_tracker.close()
		my_tracker.decrement_tries('a')
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertEqual(other_tracker.tries('a'), 0)

		other_tracker.close()
		my_tracker.mark_done('a')
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertTrue(other_tracker.check('a'))

		other_tracker.close()
		my_tracker.mark_not_done('a')
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
		self.assertFalse(other_tracker.check('a'))

		other_tracker.close()
		my_tracker.add('b')
		my_tracker.mark_done('b')
		my_tracker.increment_tries('b')
		my_tracker.add('c')
		my_tracker.increment_tries('c')
		other_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)

		self.assertEqual(other_tracker.num_done(), 1)
		self.assertEqual(other_tracker.fraction_done(), 1/3.)
		self.assertEqual(other_tracker.percent_done(), '%.2f %%' % (100/3.))

		self.assertEqual(other_tracker.num_tried(), 2)
		self.assertEqual(other_tracker.fraction_tried(), 2/3.)
		self.assertEqual(other_tracker.percent_tried(), '%.2f %%' % (200/3.))



	def test_iteration(self):

		remove_if_exists(self.TEST_PATH)
		my_tracker = tastypy.SharedProgressTracker(self.TEST_PATH)

		my_tracker.hold()
		for i in range(20):
			my_tracker.add(str(i))
		my_tracker.unhold()

		expected_keys = [str(i) for i in range(20)]
		expected_values = [{'_tries':0, '_done':False} for i in expected_keys]
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


	def test_concurrent_write(self):
		remove_if_exists(self.TEST_PATH)
		tracker = tastypy.SharedProgressTracker(self.TEST_PATH)
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
		remove_if_exists(self.TEST_PATH)
		tracker = tastypy.SharedProgressTracker(self.TEST_PATH)

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
		tracker.holdlock()
		for i in range(10):
			time.sleep(random.random() / 100.0)
			key = '%s:%d' % (name, i)
			tracker.add(key)
			tracker.set(key, 'time', time.time())
		tracker.unholdlock()


if __name__ == '__main__':
	main()
