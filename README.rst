.. tastypy documentation master file, created by
   sphinx-quickstart on Tue Jan 31 15:18:42 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tastypy
=======

.. py:module:: tastypy

``tastypy`` let's you easily interact with dict-like objects that are
"traslucently" persisted to disk.  It's designed to be used in cases where you
need database-like functionality but don't want to actually create a database.
A common use-case is in long-running programs, where you want to keep track of
progress so that you can pick up where you left off when you stop the program 
or it crashes.

Install
=======
.. code-block:: bash

    pip install tastypy

``PersistentOrderedDict``
=========================

The ``tastypy.POD`` (which is the short spelling for
``tastypy.PersistentOrderedDict``) is a dict-like datastructure that
transparently synchronizes to disk.  Supply a path when creating a ``POD``,
and the data will be peristed using files at that location:

.. code-block:: bash

    >>> from tastypy import POD
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo'] = 'bar'
    >>> exit()

Data stored ``POD``\s is preserved after the program exits:

.. code-block:: python

    >>> from tastypy import POD
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo']
    bar


JSON only
---------
JSON is used as the serializaton for data in ``POD``\s, so only JSON-serializable
data can be stored.  JSON is quite general, and represents the most common data 
types naturally, but there are some limitations.  The choice to use JSON
reflects the goal of keeping the design simple, having a human-readable format
for the persistence files, and avoiding security issues (which would arise if
using ``pickle``).

As a consequence, data stored in ``POD``\s must be JSON-serializable.  This
means using integers, strings, as well as integers and strings in arbitrarily
nested lists and dictionaries.  The ``POD``\ |s| keys, and the keys of
dictionaries in values of a ``POD``, will be converted to strings.  All strings
are converted to unicode by serialization.  Tuples can be used, but will be
serialized as lists.

Some of these restrictions could be relaxed by writing a for-purpose
serializer, but that would limit interoperability and simplicity, expecially
for people familiar with Python's ``json`` builtin.

To illustrate some of the gotcha's

.. code-block:: python

    >>> my_pod['integer-key'] = {1:'bar'}
    >>> my_pod['tuple'] = ('baz', 42)
    >>> exit()

Notice that the key ``1`` is converted to a string (though ``42`` remains as a
number), and the tuple is converted to a list.  That's just how ``json`` works.

.. code-block:: python

    >>> my_pod['foo']
    {u'1': u'bar'}
    >>> my_pod['tuple']
    [u'baz', 42]

Synchronization
===============

The ``POD`` was designed so that in most cases, synchronization between disk
and memory is transparent.  The ``POD`` keeps track of which keys may have gone 
out of sync with the disk, and periodically synchronizes
(`customize synchronization`_).  A ``POD`` will always synchronize if it is
destroyed or if the program exits or crashes, as long as the Python interpreter
doesn't segfault, which is fairly rare.

Any time you access keys, whether during assignment or some other manipulation,
the ``POD`` considers that key to be *dirty*.  Once 1000 keys are dirty, the
``POD`` will synchronize.  It's possible to circumvent synchronization if you
create another reference to the contents of a key, and then interact with it
via that reference.  But as long as you don't do that, your data will be kept
in sync.

So, the following will be properly synchronized:

.. code-block:: python

    >>> my_pod['key'] = {}
    >>> my_pod['key']['subkey1'] = 1 # __setitem__ called on dict, but only
    >>> my_pod['key']['subkey2'] = []
    >>> my_pod['key']['subkey2'].append(1)

However, the following may not synchronize correctly:

.. code-block:: python

    >>> value = {}
    >>> my_pod['key'] = value   # This is ok
    >>> value['subkey1'].append('foo')  # not seen, due to use of non-POD ref
    >>> value['subkey2'] = 'baz'    # also not seen.

A good rule of thumb is that a ``POD`` is not aware of lines of code in which
it's name doesn't appear.



.. py:class:: POD

    Alias for PersistentOrderedDict

.. autoclass:: PersistentOrderedDict
    :member-order: bysource
    :members:



``ProgressTracker``
===================

The ``tastypy.Tracker`` (short for ``tastypy.ProgressTracker``) is a subclass
of the ``POD`` that helps track the progress of long-running programs that
involve performing many repetative tasks, so that the program can pick up where
it left off in case of a crash. 

Each value in a tracker represents one task and stores whether that task is
done, and how many times it has been tried, as well as any other data you might
want to associate to it.

Typically for this kind of lon-running program, you want to attempt any tasks
that have not been done and retry tasks that were not completed successfully, but
only up to some maximum number of attempts.

For illustrative purposes, the next example shows how the tracker helps with
this, but we'll see a more concise way to do it in a moment.

.. code-block:: python

    def do_work(work_queue):
        
        tracker = tastypy.Tracker('path/to/my.tracker')

        for task in work_queue:

            # If the task has be done, skip it
            if tracker.check(task.name):
                continue

            # Add the task if it is not already in the tracker
            if task.name not in tracker:
                tracker.add(task.name)

            # Skip this task if we've tried it too many times
            if tracker.tries(task.name) > MAX_TRIES:
                continue

            # Now attempt the task
            result = do_work(task)

            # If it succeeded, mark the task done, and record results
            if result.success:
                tracker.mark_done(task.name)
                tracker[task.name]['result'] = result


We can factor out some of the repetitive logic using other functions on the
tracker.  First, we can let the tracker know how many times we care to try a
task before giving up.  And second, we can make use of the function
``try_it(key)``.
This packs several steps in the logic we saw in the last example together:

    - It checks if the task exists in the tracker, if not, it adds it
    - It checks if the task is done, if yes, it returns ``False``
    - It checks if the task has already been tried the maximum number of times,
      and if so, it also returns ``False``
    - Otherwise it returns true, and it increments the counter for the number
      of times the task has been tried

The following function will process each task in a queue, keep track of
attempts, and skip tasks that have been done or which have been attempted too
many times, and record results from each task

.. code-block:: python

    def do_work(work_queue):
        
        tracker = tastypy.Tracker('path/to/my.tracker', max_tries=3)

        for task in work_queue:
            
            # Skip tasks that are done or tried too many times
            if not tracker.try_it(task.name):
                continue

            # Do the work
            do_work(task)

            # Mark the task done and record results
            tracker.mark_done(task.name)
            tracker[task.name]['result'] = result
                

This tends to be the most common usecase, although the tracker is versatile,
and is just a ``POD`` with extra methods.  See the full listing of methods
below. The value stored for each task is a ``dict`` with two special keys used
to keep track of the status: ``_tries`` and ``_done``.  You can attach any
other values, but of course you'll want to avoid overwriting or deleting these 
keys.


.. autoclass:: _ProgressTracker
    :members: 

.. _customize synchronization:

Customize synchronization
-------------------------

In general, you should stick to 


by assigning somethign to one of their keys.  For example, doing ``my_pod['foo']
= 'baz'`` triggers ``my_pod`` to sync to disk.

This is accomplished within the ``__setitem__`` method of ``POD``, so any
assignment to a key will trigger synchronization.

However, if you assign a mutable object to a ``POD`` there is no way for it to
know if you mutate *that* object.  For example:

.. code-block:: python

    >>> my_pod['mutable'] = [1,2,3]	# synchronization happens
    >>> my_pod['mutable'].append(4)	# no synchronization!

To explicitly ask for a key to be synchronized, simply call 
``my_pod.update(key)``.

Suspending synchronization
==========================

If you are making many changes to a ``POD``, it is often best to suspend
synchronization, make all of the changes, then synchronize afterward.

To temporarily turn off automatic synchronization, call ``POD.hold()``.
For a on-time synchronization of all not-yet-sync'd changes to be syncronized, 
call ``POD.sync()``.  To reactivate automatic synchronization (and synchronize
any outstanding changes) call ``POD.unhold()``.

Note, ``POD`` and its related always synchronize at exit, e.g. if the program 
crashes or if you issue a keyboard interrupt, so you don't need to worry about 
hitting Ctrl-C.

This is similar to how buffered data in an open file is handled--only a very bad 
crash that prevents the program from performing cleanup operations at exit
would cause lost data.


.. |s| replace:: |rsquo|\ s
.. |rsquo| unicode:: 0x2019 .. copyright sign

