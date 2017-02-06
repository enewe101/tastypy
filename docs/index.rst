.. tastypy documentation master file, created by
   sphinx-quickstart on tue jan 31 15:18:42 2017.
   you can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tastypy
=======

.. py:module:: tastypy

``tastypy`` provides dict-like datastructures that transparently persist to to
disk.  This is helpful in cases where you need a persisted key-value store but
don't want to make a database.  For example, it could be used to keep track of
the status of URLs in a crawler, or of tasks in a long-running process,
enabling the process to pick up where it left off after a crash or
interruption.

Install
=======
.. code-block:: bash

    pip install tastypy

``PersistentOrderedDict``
=========================

The ``tastypy.POD`` (short alias for ``tastypy.PersistentOrderedDict``) is a
dict-like datastructure that transparently synchronizes to disk.  Supply a path
when creating a ``POD``, and the data will be persisted using files at that
location:

.. code-block:: python

    >>> from tastypy import POD
    >>> my_pod = pod('path/to/my.pod')
    >>> my_pod['foo'] = 'bar'
    >>> exit()

Data stored ``POD``\s is preserved after the program exits:

.. code-block:: python

    >>> from tastypy import POD
    >>> my_pod = pod('path/to/my.pod')
    >>> my_pod['foo']
    bar


JSON -- general, simple, secure
-------------------------------
Data is serialized in JSON format using the builtin ``json`` module for
serialization and deserialization.  JSON is general enough to represent pretty
much any data, and unlike pickles, it is secure, and interoperable across
programs and python versions.  The persistence files are human-readable, and 
easily hacked manually or with other tools.

While there are advantages to using ``json``, there are also some limitations.
Only json-serializable data can be stored in a ``POD``: which includes
string-like, number-like, list-like, and dict-like objects (and arbitrarily
nested combinations).  In a serialization-deserialization cycle, string-likes
will be coerced to ``unicode``\ s, list-likes to ``list``\ s, and dict-likes to
``dict``\ s.  It's actually a great idea to keep your data decoupled from your
programs where possible, so sticking to these very universal data types is
probably an *enabling* constraint.

There is, however, one quirk of ``json`` that can be quite unexpected: 

.. WARNING:: 

    ``json`` converts integer keys of ``dict``\ s to strings
    to comply with the JSON specification:

    .. code-block:: python

        >>> my_pod[1] = {1:1}
        >>> my_pod.sync(); my_pod.revert()  # do a serialize/deserialize cycle
        >>> my_pod[1]
        {'1':1}

    Notice how the key in the stored dict turned from ``1`` into ``'1'``.  
    

Synchronization
---------------

Generally you don't need to think about synchronization---that's the goal
of ``tastypy``.  Still, it's good to understand how it works, and how not to
break it.

Any changes made by keying into the ``POD`` will
be properly synchronized.  However, if you make a reference to a mutable type stored
in the ``POD``, and then mutate it using that reference, there is no way for
the ``POD`` to know about it, and that change will not be persisted.

In other words, don't do this:

.. code-block:: python

    >>> my_pod['key'] = []
    >>> my_list = my_pod['key']
    >>> my_list.append(42)              # BAD! This won't be sync'd!

Instead, do this:

.. code-block:: python

    >>> my_pod['key'] = []
    >>> my_pod['key'].append(42)        # GOOD! This will be sync'd!

.. NOTE::

    If you mutate an object that was accessed by keying into the ``POD``, then
    the ``POD`` knows about the change.  If you mutate an object using another
    reference, the ``POD`` will not persist that change.

``POD``\ s keep track of values that were changed in memory, and synchronize to
disk whenever enough values have changed (by default, 1000), or when the
program terminates.  (The threshold at which to synchronize can be set using the
``sync_at`` argument when creating the ``POD``.)

Can data be lost?
~~~~~~~~~~~~~~~~~
"Dirty" values---values that differ in memory and on disk---can be considered
as having the same status as data that you ``.write()`` to a file object open
for writing.  If the program exits, crashes from an uncaught exception, or
receives a SIGTERM or SIGINT (e.g. from ctrl-C), data will be synchronized.
But, in the exceptional cases that the Python interpreter segfaults or the
program receives a SIGKILL no synchronization is possible, so unsynchronized
data would be lost.

Can I manually control synchronization?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Normally you wouldn't need to, but you can. To synchronize all dirty values
immediately, do ``POD.sync()``.  To synchronize a specific value use
``POD.sync_key(key)``.  To flag a key dirty for the next synchronization, use
``POD.mark_dirty(key)``.  To get the set of dirty keys, do ``POD.dirty()``.
You can suspend automatic synchronization using ``POD.hold()``, and reactivate
it using ``POD.unhold()``.  To drop all un-synchronized changes and revert to the
state stored on disk do ``POD.revert()``.  See the |podref|_.

Opening multiple ``POD``\ s at same location is safe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Conceptually, opening multiple ``POD``\ s to the same location on disk might seem
like opening multiple file handles in write mode to the same location.

For files this isn't safe---when one file object flushes, it will likely 
overwrite data recently written by the other.
But ``POD``\ s open to the same location on disk act like singletons---so they
actually reference the same underlying data, making stale overwrites a
non-problem.  Of course, the situation is completely different if you want
multiple processes to interact with ``POD``\ s at the same location---for that
you should use a |sharedpodintro|_.

.. _podref:

``PersistentOrderedDict`` reference
-----------------------------------

.. py:class:: POD

    Alias for ``tastypy.PersistentOrderedDict``.

.. autoclass:: PersistentOrderedDict
    :member-order: bysource
    :members:

.. _sharedpodintro:

Multiprocessing with ``SharedPOD``\ s
=====================================
To have multiple processes use ``POD``\ s directed at the same location, you
need to use a ``SharedPOD``, which handles synchronization between processes.
Open a single ``SharedPOD`` instance and then distribute it to the children
(e.g. by passing it over a ``Pipe`` or ``Queue``, or as an argument to a
``multiprocessing.Process`` or ``multiprocessing.Pool``).

.. WARNING::

    Do not create multiple ``SharedPOD`` instances pointing to the same
    location on disk.  Make one ``SharedPOD`` (per location on disk) and share
    it with other processes.

The ``SharedPOD`` starts a server process with an underlying
``POD``, and acts as a broker, forwarding method calls to the server and taking
back responses, while safely interleaving each processes' access.
Changes made using a ``SharedPOD`` are immediately visible to all processes.


.. _writetosharedpods:

Writing to shared ``SharedPOD``\ s
----------------------------------
The ``SharedPOD`` has to use a different strategy to ensure that data is
correctly synchronized.  It isn't enough to mark values as dirty: the new values
needs to be forwarded to the underlying server.

This means that you need to explicitly signal when an operation can mutate the
``SharedPOD``.  Any time you do something to a ``SharedPOD`` that can mutate
it, you should perform it on the ``SharedPOD.set`` attribute instead of on the
``ShardPOD`` itself.

So, instead of doing this:

.. code-block:: python

    shared_pod = tastypy.SharedPOD('my.pod')

    shared_pod['foo'] = {'bar':0, 'baz':[]}
    shared_pod['foo']['bar'] += 1
    shared_pod['foo']['baz'].append('fizz')

You should do this:

.. code-block:: python

    shared_pod = tastypy.SharedPOD('my.pod')

    shared_pod.set['foo'] = {'bar':4, 'baz':[]}
    shared_pod.set['foo']['bar'] += 1
    shared_pod.set['foo']['baz'].append('fizz')

The ``SharedPOD``\ |s| ``.set`` attribute uses some tricks to capture
arbitrarily deep "keying" and "indexing", method calls,  arguments, and tell
when it's being operated on by operators like ``+=``, slice assignments like
``shared_pod.set['a'][:] = [4]``, and the like.  It then forwards this
information to be handled and synchronized appropriately.

Just be sure to leave *off* the ``.set`` when you *access* values:

.. code-block:: python

    >>> print shared_pod.set['foo']['baz'][0]
    <tastypy._deep_proxy.DeepProxy at 0x103ed8c90>
    >>> print shared_pod['foo']['baz'][0]
    fizz

``SharedPOD`` multiprocessing example
-------------------------------------

The following example shows how you can use a ``SharedPOD`` in a multiprocessed
program:

.. code-block:: python

    from multiprocessing import Process
    import tastypy

    def worker(pod, proc_num, num_procs):
        for i in pod:
            if i%num_procs == proc_num:
                pod[i] = i**2

    def run_multiproc():
        num_procs = 5 
        init = [(i, None) for i in range(25)]
        pod = tastypy.SharedPOD('my.pod', init=init)
        procs = []
        for i in range(num_procs):
            proc = Process(target=worker, args=(pod, i, num_procs))
            proc.start()
            procs.append(proc)

        for proc in procs:
            proc.join()

        for key, val in pod.iteritems():
            print key, val 

    if __name__ == '__main__':
        run_multiproc()

If you run it, you'll see something like this:

.. code-block:: bash

    $ python shared_pod_example.py
    0 0
    1 1
    2 4
    3 9
    4 16
    5 25
    6 36
    7 49
    8 64
    9 81
    10 100
    11 121
    12 144
    13 169
    14 196
    15 225
    16 256
    17 289
    18 324
    19 361
    20 400
    21 441
    22 484
    23 529
    24 576

.. _sharedpodreference:

SharedPersistentOrderedDict reference
-------------------------------------

.. py:class:: SharedPOD

    Alias for ``tastypy.SharedPersistentOrderedDict``

.. autoclass:: SharedPersistentOrderedDict(path, init={}, gzipped=False, file_size=1000, sync_at=1000)

    .. py:attribute:: set

        Attribute that accepts all mutable operations on the ``SharedPOD``.  
        E.g. instead of this:

        .. code-block:: python

            shared_pod['some']['key'] += 42
            shared_pod['some']['list'].append('forty-two')

        Do this:

        .. code-block:: python

            shared_pod.set['some']['key'] += 42
            shared_pod.set['some']['list'].append('forty-two')

    .. automethod:: close()
    .. automethod:: lock()
    .. automethod:: unlock()

    *The following methods are functionally equivalent to those of* ``POD``:

    .. py:method:: update()
    .. py:method:: mark_dirty()
    .. py:method:: sync_key()
    .. py:method:: hold()

        Note that the underlying ``POD`` continues to track changes from all
        processes while automatic synchronization is suspended.
    .. py:method:: unhold()
    .. py:method:: revert()
    .. py:method:: iteritems()
    .. py:method:: iterkeys()
    .. py:method:: itervalues()
    .. py:method:: items()
    .. py:method:: keys()
    .. py:method:: values()






``ProgressTracker``
===================

The ``tastypy.Tracker`` (short for ``tastypy.ProgressTracker``) is a subclass
of the ``POD`` that helps track the progress of long-running programs that
involve performing many repetitive tasks, so that the program can pick up where
it left off in case of a crash. 

Each value in a tracker represents one task and stores whether that task is
done, and how many times it has been tried, as well as any other data you might
want to associate to it.

Often in a long-running program, you want to attempt any tasks that have
not been done and retry tasks that were not completed successfully, but only up
to some maximum number of attempts.

To motivate the ``ProgressTracker`` and illustrate how it works, let's imagine
that we are crawling a website.  Let's begin with an example that uses a
regular ``POD`` like a queue for the URLs that need to be crawled.  That would
look something like this:

.. code-block:: python

    def crawl(seed_url):

        url_pod = tastypy.POD('urls.pod')
        if seed_url not in url_pod:
            url_pod[seed_url] = {'tries':0, 'done':False}

        for url in url_pod:

            # If we've fetched this url already, skip it
            if url_pod[url]['done']:
                continue

            # If we've tried this url too many times, skip it
            if url_pod[url]['tries'] > 3:
                continue

            # Record that an attempt is being made to crawl this url
            url_pod[url]['tries'] += 1

            # Attempt to crawl the url, move on if we don't succeed
            success, found_links = crawl(url)
            if not success:
                continue

            # Add the new links we found, and mark this url done
            for found_url in found_urls:
                if url not in url_pod:
                    url_pod[url] = {'tries':0, 'done':False}
            url_pod[url]['done'] = True

The ``Tracker`` provides some facilities to support this usecase.  All entries
in a ``Tracker`` are dictionaries that minimally have a ``_done`` flag that
defaults to ``False`` and a ``_tries`` counter that defaults to ``0``, and
various methods support the usage pattern above.  Using a ``Tracker``, the
program would look like this:

.. code-block:: python

    def crawl(seed_url):

        url_tracker = tastypy.POD('urls.tracker', max_tries=3)
        url_tracker.add_if_absent(seed_url)

        for url in url_tracker.try_keys():

            # Attempt to crawl the url, move on if we don't succeed
            success, found_links = crawl(url)
            if not success:
                continue

            # Add the new links we found, and mark this url done
            url_tracker.add_many_if_absent(found_urls)
            url_tracker.mark_done(url)

In the above code block, the ``try_keys()`` iterator is used to iterate over
just the tasks that aren't done and haven't been tried more than ``max_tries``,
while incrementing the tries count for each task yielded.  The
``add_if_absent(key)`` method is also used to initialize a new task with zero
tries (or do nothing if that key already existed).  The ``mark_done(key)``
method is used to mark a task done.  See the Tracker reference for the other
convenience methods for tracking the progress of long-running programs.

Note that you can (and should!) use the ``Tracker`` to store other data related
to tasks---such as task outputs / results.  Just remember that the entries for 
``Tracker``\ s are dictionaries that minimally contain ``_tries``, ``_done``,
and ``_aborted`` keys.  Don't delete or override those or you'll corrupt the
tracker!

.. _progtracker:

``ProgressTracker`` reference
-----------------------------

.. autoclass:: ProgressTracker
    :members: 


Multiprocessing with ``SharedProgressTracker``\ s
=================================================
Just as you can distribute a ``SharedPOD`` to multiple processes, you can
distribute a ``SharedTracker`` (short alias for ``SharedProgressTracker``) to
multiple processes.

The same basic usage applies.  A single ``SharedTracker`` should be made and
distributed to child processes using a ``Queue``, ``Pipe``, or in the arguments
to a ``Process`` or ``Pool``.  All of the ``Trackers`` own methods for updating
the state of a task (such as ``mark_done(key)`` or ``increment_tries(key)``)
are properly synchronized.  If you want to add or mutate your own data stored
on a task, you need to perform mutation operations on the ``Tracker.set``
attribute, not on the tracker itself.  See |writetosharedpods|_ for an
explanation.

``SharedProgressTracker`` reference
-----------------------------------

.. autoclass:: SharedProgressTracker(path, max_tries=0, init={}, gzipped=False, file_size=1000, sync_at=1000)

.. |writetosharedpods| replace:: Writing to ``SharedPOD``\ s
.. |podref| replace:: ``POD`` reference
.. |s| replace:: |rsquo|\ s
.. |em| unicode:: 0x2014 .. em-dash
.. |rsquo| unicode:: 0x2019 .. right single quote
.. |sharedpodintro| replace:: ``SharedPOD``
.. |progtracker| replace:: ``ProgressTracker``
.. |sharedpodreference| replace:: ``SharedPersistentOrderedDict``

