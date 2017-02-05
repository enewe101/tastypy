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

.. code-block:: python

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


JSON -- general, simple, secure
-------------------------------
JSON was selected as the serialization format, and the builtin ``json`` is the
serializer.  JSON is general enough to represent pretty much any data, and
unlike pickles, it is secure and interoperable between programs and python
versions.  It has the added very handy advantage that the persistence files are
human-readable, and are easily hacked manually or with unix tools or other
programs.

While there are advantages to using ``json`` (great advantages), we also
inheret some limitations.  Naturally, only JSON serializable data can
be stored in a ``POD`` -- that means string-like, number-like, list-like, and
dict-like objects (and arbitrarily nested combinations).

And we inherit the fact that ``json`` can slightly alter data in a cycle of
serialization/deserialization:

    - string-like's become ``unicode``\ s (e.g. ``'a'`` becomes ``u'a'``)
    - list-like's become ``list``\ s (e.g. ``(1,2)`` becomes ``[1,2]``)
    - dict-like's become ``dict``\ s (e.g. ``Counter({'a':2})`` becomes ``{u'a':
      2}``)

It's actually a great idea to keep your data as application independant as
possible, so one might view this as an *enabling* constraint.

But there is one quirk of ``json`` that can be quite unexpected: 

.. WARNING:: 

    ``json`` converts integer keys of ``dict``\ s to strings
    to comply with the JSON specification:

    .. code-block:: python

        >>> my_pod[1] = {1:1}
        >>> my_pod.sync(); my_pod.revert()  # do a serialize/deserialize cycle
        >>> my_pod[1]
        {'1':1}

    Notice how the key in the stored dict turned from ``1`` into ``'1'``.  
    
With all its advantages, this tradeoff in using ``json`` seems well worth it.


Synchronization
---------------

Generally you don't need to think about synchronization---that's the goal
of ``tastypy``.  But it's good to understand the assumptions and limitations of
the synchronization strategy so that you don't accidentally circumvent it.

Under normal circumstances, the only thing you need to avoid is making changes
to a datastructure's contents using a deep reference:

.. code-block:: python

    >>> my_pod['key'] = {}                      # Good
    >>> my_pod['key']['subkey1'] = 1            # Good
    >>> my_pod['key']['subkey2'] = []           # Good
    >>> my_pod['key']['subkey2'].append(1)      # Good
    >>> #
    >>> deep_reference = my_pod['key']          # Getting ready to do bad stuff
    >>> deep_reference['subkey1'] = 2           # Bad!
    >>> deep_reference['subkey2'].append(2)     # Bad!


.. NOTE::

    Generally, any change effected by accessing / setting a key on the
    datastructure will be properly synchronizeded.  The datastructures mark
    keys as dirty using the ``__getitem__`` and ``__setitem__`` methods.

Synchronizing each time a value is written or accessed wouldn't be very
performant.  So instead, datastructures keep track of which elements are
"dirty", and synchronize them when the number of dirty elements reaches 1000
(set this using the ``sync_at`` keyword argument to the constructor).

Dirty values can be considered as having the same status as buffered data in a
file object open for writing---if the program exits, crashes from an uncaught
exception, or receives a SIGTERM or SIGINT (e.g. from ctrl-C), data will be
synchronized.  However, in exceptional circumstances, such as the Python
interpreter segfaulting or a SIGKILL signal, synchronization is impossible.  

If for some reason you need to manually controll synchronization, you can. To
synchronize all dirty values immediately, do ``POD.sync()``.  To synchronize a
specific value use ``POD.update(key)``.  To flag a key dirty for the next
synchronization, use ``POD.mark_dirty(key)``.  To get the set of dirty keys, do
``POD.dirty()``.  You can suspend automatic synchronization using ``POD.hold()``,
and reactivate it using ``POD.unhold()``.  To drop all un-sync'd changes and
revert to the state stored on disk do ``POD.revert()``.

Multiprocessing
---------------
Obviously opening multiple ``POD``\ s directed at the same location on disk is
a bad idea.  Concurrent writes would likely result in stale data overriting, or
corrupted files.  

In a single-processing situation, you are actually protected
from this because ``POD``\ s opened to the same normalized path on disk are
actually singletons (technically Borgs).  This makes stale updates a
non-issue in single-processed applications.

In a multiprocessing context use a ``tastypy.SharedPOD``, which 
handles inter-process synchronization concerns for you in the background.  
Create the ``SharedPOD`` in the main process, and share it with child
processes.

.. WARNING::

    Do not create multiple ``SharedPOD`` instances within child processes.
    Create a single ``SharedPOD`` instance in a main process and share it with
    the children.

The ``SharedPOD`` is actually a proxy to a ``POD`` running in a background
server process.  Processes can concurrently call any of the usual ``POD`` 
methods on the ``SharedPOD``, and they will be interleaved safely.
Alterations to values made by one process will be immediately visible to all 
others, even if the underlying ``POD`` has not yet synchronized to disk.

For the most part, you can interact with a ``SharedPOD`` just like a ``POD``,
but one of the strategies for synchronizing can't be reliably done via proxy,
which means that you need to be a bit more careful with how you mutate data.
Only updates that make direct assignments to one of the ``SharedPOD``\ s keys
can be properly synchronized.  The following are examples of good and bad
approaches to changing values:

.. code-block:: python

    import tastypy
    shared_pod = tastypy.SharedPOD('my.pod')

    shared_pod['a'] = {'key': 42}               # Direct assignment to a key is always synchronized
    
    shared_pod['a']['key'] = 17                 # Assignment to a "subkey" is not!
    shared_pod.mark_dirty('a')                  # Now it's synchronized.
    
    shared_pod.set(('a', 'key'), {})            # Assign to a subkey and synchronize in one step
    shared_pod.set(('a', 'key', 'deeper'), 77)  # Go as deep as you want

    shared_pod['a'].update({'other_key': 13})   # modifications to mutable types don't get synchronized
    shared_pod.mark_dirty('a')                  # OK, synchronized!

The following example shows how you can use a ``SharedPOD`` in a multiprocessed
program:

.. code-block:: python

    from multiprocessing import Process
    import tastypy

    def worker(pod, proc_num, num_procs):
        for i, key in enumerate(pod):
            if i%num_procs == proc_num:
                pod.set((key,'result'), pod[key]**2)

    def run_multiproc():
        num_procs = 5
        pod = tastypy.SharedPOD('my.pod', init={str(i):i for i in range(1000)})
        procs = []
        for i in range(num_procs):
            proc = Process(target=worker, args=(pod, i, num_procs)
            proc.start()
            procs.append(proc)

        for proc in procs:
            proc.join()

    if __name__ == '__main__':
        run_multiproc()




``PersistentOrderedDict`` reference
-----------------------------------

.. py:class:: POD

    Alias for ``POD.PersistentOrderedDict``.

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
.. |em| unicode:: 0x2014 .. em-dash
.. |rsquo| unicode:: 0x2019 .. right single quote

