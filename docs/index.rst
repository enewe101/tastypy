.. tastypy documentation master file, created by
   sphinx-quickstart on tue jan 31 15:18:42 2017.
   you can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tastypy
=======

.. py:module:: tastypy

This documentation is best viewed on 
`readthedocs <http://python-tastypy.readthedocs.io/en/latest/>`_.

``tastypy`` provides a dict-like datastructure that transparently persists to
disk, making the data available after a program crashes or exits.  The
datastructure's iterators yield keys and values in the order in which keys were
first added.

This is helpful whenever you want a persistent key-value store, but don't want
to create a database.  For example, you can store partial results from a
long-running program, and allow the program to pick up where it left off after
a crash or interruption.

Included:

 - |POD|_ (alias for |PersistentOrderedDict|_): a persistent dict-like mapping.
 - |Tracker|_: a subclass of |POD|_ specifically for tracking the state of
   repetitive tasks in a long running program (for example, use it as a queue
   for URLs in a crawler).

Multiprocessing-safe versions are also included:

 -  |SharedPOD|_ (alias for |SharedPersistentOrderedDict|_)
 - |SharedTracker|_

.. NOTE::

    Please report any bugs and request features by opening an issue at the
    project's `github page <https://github.com/enewe101/tastypy>`_. 

Install
=======
.. code-block:: bash

    pip install tastypy

.. _PersistentOrderedDict:
.. _POD:

``PersistentOrderedDict``
=========================

The ``tastypy.POD`` (short alias for ``tastypy.PersistentOrderedDict``) is a
dict-like datastructure that transparently synchronizes to disk.  Supply a path
when creating a ``POD``, and the data will be persisted using files at that
location:

.. code-block:: python

    >>> from tastypy import POD
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo'] = 'bar'
    >>> exit()

Previously-stored data can then be accessed after the original program
terminates:

.. code-block:: python

    >>> from tastypy import POD
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo']
    'bar'

``POD``\ s are meant to feel like ``dict``\ s in most respects.  They support
the same iteration mechanisms, a similar implementation of ``update()``, and
their ``len`` corresponds to their number of entries.

JSON -- general, simple, secure
-------------------------------
Data is serialized in JSON format using the builtin ``json`` module for
serialization and deserialization.  JSON is general enough to represent pretty
much any data, and unlike pickles, it is secure, application-independant, and
interoperable across programs and python versions.  The persistence files are
human-readable, and easily hacked manually or with other tools.

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

    ``json.encode()`` converts integer keys of ``dict``\ s to ``unicode``\ s
    to comply with the JSON specification.  This quirk is inherited by 
    ``tastypy``:

    .. code-block:: python

        >>> my_pod[1] = {1:1}
        >>> my_pod.sync(); my_pod.revert()  # do a serialize/deserialize cycle
        >>> my_pod[1]
        {'1':1}

    Notice how the key in the stored ``dict`` turned from ``1`` into ``'1'``.  
    

Synchronization
---------------

Generally you don't need to think about synchronization---that's the goal
of ``tastypy``.  Still, it's good to understand how it works, and how not to
break it.

Any changes made by keying into the ``POD`` will
be properly synchronized.  However, if you make a reference to a mutable type stored
in the ``POD``, and then mutate it using *that* reference, there is no way for
the ``POD`` to know about it, and that change will not be persisted.

So, for example:

.. code-block:: python

    >>> my_pod['key'] = []
    >>> my_list = my_pod['key']
    >>> my_list.append(42)              # BAD! This won't be sync'd!
    >>> my_pod['key'].append(42)        # GOOD! This will be sync'd!

``POD``\ s keep track of values that were changed in memory, and synchronize to
disk whenever enough values have changed (by default, 1000), or when the
program terminates.  (The synchronization threshold can be set using the
``sync_at`` argument when creating the ``POD``.)

Can data be lost?
~~~~~~~~~~~~~~~~~
"Dirty" values---values that differ in memory and on disk---can be considered
as having the same status as data that you ``.write()`` to a file object open
for writing.  If the program exits, crashes from an uncaught exception, or
receives a SIGTERM or SIGINT (e.g. from ctrl-C), data *will* be synchronized.
But, in the exceptional cases that the Python interpreter segfaults or the
program receives a SIGKILL, no synchronization is possible, so unsynchronized
data would be lost.

Can I manually control synchronization?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Normally you won't need to, but you can. To do a one-time synchronization of
all dirty values immediately, do :py:meth:`POD.sync()
<PersistentOrderedDict.sync()>`.  To synchronize a specific value use
:py:meth:`POD.sync_key(key) <PersistentOrderedDict.sync_key()>`.  To flag a
key dirty for the next synchronization, use :py:meth:`POD.mark_dirty(key)
<PersistentOrderedDict.mark_dirty()>`.  To get the set of dirty keys, do
:py:meth:`POD.dirty() <PersistentOrderedDict.dirty()>`.  You can suspend
automatic synchronization using :py:meth:`POD.hold()
<PersistentOrderedDict.hold()>`, and reactivate it using :py:meth:`POD.unhold()
<PersistentOrderedDict.unhold()>`.  To drop all un-synchronized changes and
revert to the state stored on disk do :py:meth:`POD.revert()
<PersistentOrderedDict.revert()>`.  See the |podref|_.

Opening multiple ``POD``\ s at same location is safe
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Conceptually, opening multiple ``POD``\ s to the same location on disk might seem
like opening multiple file handles in write mode to the same location.

For files this isn't safe---when one file object flushes, it will likely 
overwrite data recently written by another.
But ``POD``\ s open to the same location on disk act like singletons---so they
actually reference the same underlying data, making stale overwrites a
non-problem.  Of course, the situation is completely different if you want
multiple processes to interact with ``POD``\ s at the same location---for that
you should use a |sharedpodintro|_.

(It's possible to open a ``POD`` with isolated memory by passing
``clone=False`` when creating it---but you shouldn't need to do that.)

.. _podref:

``PersistentOrderedDict`` reference
-----------------------------------

.. py:class:: POD

    Alias for ``tastypy.PersistentOrderedDict``.

.. autoclass:: PersistentOrderedDict
    :member-order: bysource
    :members:

.. _sharedpodintro:
.. _SharedPersistentOrderedDict:
.. _SharedPOD:

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
need to be forwarded to the underlying server.

This means that you need to explicitly signal when an operation can mutate the
``SharedPOD``.  Any time you do something to a ``SharedPOD`` that can mutate
it, you should perform it on the ``SharedPOD.set`` attribute instead of on the
``ShardPOD`` itself.

So, instead of doing this:

.. code-block:: python

    shared_pod = tastypy.SharedPOD('my.pod')

    shared_pod['foo'] = {'bar':0, 'baz':[]}         # BAD! Won't sync.
    shared_pod.set['foo'] = {'bar':4, 'baz':[]}     # Good!

    shared_pod['foo']['bar'] += 1                   # BAD! Won't sync.
    shared_pod.set['foo']['bar'] += 1               # Good!

    shared_pod['foo']['baz'].append('fizz')         # BAD! Won't sync.
    shared_pod.set['foo']['baz'].append('fizz')     # Good!

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

Avoiding raciness
-----------------
The ``SharedPOD`` eliminates any raciness problems related to it's internal
synchronization to disk, and it ensures that each process holding the same
``SharedPOD`` always sees the most up-to-date values, whether sync'd to disk or
not.

However, that doesn't prevent you from introducing your own raciness in how you 
use ``SharedPOD``\ s (or any other shared datastructure for that matter).

Issues generally arise when you read some shared value, and take an action
based on that value, while other processes might modify it.  Usually a safe
policy is to have different processes read/write to non-overlapping subsets of
the ``SharedPOD``\ |s| keys.

But if you can't or don't want to set up your program that way, then use a
locked context to avoid raciness.  To demonstrate that, we'll use the
prototypical example that can introduce a race condition: incrementing a value.
Suppose that we have a worker function, that will be executed by a bunch of
different workers, that looks like this:

.. code-block:: python

    def work(pod):
        pod.set['some-key'] += 1

That may look fine, but the ``+=`` operator really corresponds to first
computing the sum ``old_val + 1`` and *then* assigning it back to the variable.
As process A is doing the ``+=``, process B could come along and update the
varable, doing its update after A computed the sum but before A assigns it
back.  So, B's update would be lost.  To temporarily prevent other processes
from modifying the ``SharedPOD``, use the :py:meth:`SharedPOD.locked()
<SharedPersistentOrderedDict.locked()>` context manager, like so:

.. code-block:: python

    def work(shared_pod):
        with shared_pod.locked():
            shared_pod.set['some-key'] += 1

So, when exactly do you need to do that?  First off, any of ``SharedPOD``\ |s|
own methods, or methods defined *on* its values can be treated as *atomic*,
because internally a lock will be acuired before calling the method, and
released afterward.

So you don't need a locked context for something like
``pod.set['some-list'].append('item')``, or 
``del pod.set['some-dict']['some-key']``.
Contrary to the above you also don't need a locked context when using the
``+=`` operator on values that *are mutable objects that
implement* ``__iadd__`` and perform the operation *inplace*.  For example, 
you don't need a lock for augmented assignment to a list, e.g. 
``pod.set['I-store-a-list'] += [1]``.

You need a locked context if:

 - You read a value from a ``SharedPOD``
 - You take action based on that value
 - It would be bad if that value changed before finishing that action
 - Other processes can modify that value


``SharedPOD`` multiprocessing example
-------------------------------------

The following example shows how you can use a ``SharedPOD`` in a multiprocessed
program.  In this example, each worker reads / writes to it's own subset of the
``SharedPOD`` so locking isn't necessary:

.. code-block:: python

    from multiprocessing import Process
    import tastypy

    def work(pod, proc_num, num_procs):
        for i in pod:
            if i%num_procs == proc_num:
                pod.set[i] = i**2

    def run_multiproc():
        num_procs = 5 
        init = [(i, None) for i in range(25)]
        pod = tastypy.SharedPOD('my.pod', init=init)
        procs = []
        for i in range(num_procs):
            proc = Process(target=work, args=(pod, i, num_procs))
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

    Alias for :py:class:`SharedPersistentOrderedDict`.

.. autoclass:: SharedPersistentOrderedDict(path, init={}, gzipped=False, file_size=1000, sync_at=1000)

        .. py:attribute:: set

            Attribute that accepts all mutable operations on the ``SharedPOD``.  
            E.g.:

            .. code-block:: python

                shared_pod['some']['key'] += 42                     # BAD!, won't sync
                shared_pod.set['some']['key'] += 42                 # Good!

                shared_pod['some']['list'].append('forty-two')      # BAD!, won't sync
                shared_pod.set['some']['list'].append('forty-two')  # Good!

        .. automethod:: close()
        .. automethod:: locked()
        .. automethod:: lock()
        .. automethod:: unlock()

    *The following methods are functionally equivalent to those of* ``POD``:

        .. py:method:: update()
        .. py:method:: mark_dirty()
        .. py:method:: sync()
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




.. _ProgressTracker:
.. _Tracker:

``ProgressTracker``
===================

The ``tastypy.Tracker`` (short for ``tastypy.ProgressTracker``) is a subclass
of |POD|_ that helps track the progress of long-running programs that
involve performing many repetitive tasks, so that the program can pick up where
it left off in case of a crash. 

Each value in a tracker represents one task and stores whether that task is
done, aborted, and how many times it has been tried, along with other data you
might want to associate to it.

Often in a long-running program, you want to attempt any tasks that have
not been done successfully, but only attempt tasks some maximum number of times.

To motivate the ``ProgressTracker`` and illustrate how it works, let's imagine
that we are crawling a website.  We'll begin by implementing that using a
regular |POD|_ to keep track of the URLs that need to be crawled.  Then we'll
see how the ``Tracker`` can support that usecase.  First using a |POD|_:

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
            success, found_urls = crawl(url)
            if not success:
                continue

            # Add the new urls we found, and mark this url done
            for found_url in found_urls:
                if url not in url_pod:
                    url_pod[url] = {'tries':0, 'done':False}
            url_pod[url]['done'] = True

As you can see, we use the |POD|_ to keep track of URLs as they are discovered,
along with which ones have been fetched already, and how many times each one
has been tried.  Any time this program is started up, it will only attempt to
crawl URLs that haven't yet been crawled successfully, while ignoring any that
have already been tried at least 3 times.

The ``Tracker`` provides some facilities to support this usecase.  All entries
in a ``Tracker`` are dictionaries that minimally have a ``_done`` flag that
defaults to ``False``, an ``_aborted`` flag that also defaults to ``False``, and
a ``_tries`` counter that defaults to ``0``.  ``Tracker``\ s have various
methods to help keep track of tasks, and let you iterate over only tasks that
aren't done, aborted, or tried too many times.  Using a ``Tracker``, the program
would look like this:

.. code-block:: python

    def crawl(seed_url):

        url_tracker = tastypy.POD('urls.tracker', max_tries=3)
        url_tracker.add_if_absent(seed_url)

        for url in url_tracker.try_keys():

            # Attempt to crawl the url, move on if we don't succeed
            success, found_urls = crawl(url)
            if not success:
                continue

            # Add the new urls we found, and mark this url done
            url_tracker.add_many_if_absent(found_urls)
            url_tracker.mark_done(url)

In the above code block, the ``try_keys()`` iterator is used to iterate over
just the tasks that aren't done, aborted, or already tried ``max_tries`` times,
while incrementing the ``_tries`` on each task that gets yielded.  The
``add_if_absent(key)`` method is used to initialize a new task with zero tries,
but only if that task isn't already in the Tracker.  The ``mark_done(key)``
method is used to mark a task done.  See the Tracker reference for the other
convenience methods for tracking the progress of long-running programs.

Note that you can (and should!) use the ``Tracker`` to store other data related
to tasks---such as task outputs / results.  Just remember that the entry for
each task is a ``dict`` that minimally contain ``_tries``, ``_done``,
and ``_aborted`` keys, so don't overwrite these with values that don't make 
sense!

.. _progtracker:

``ProgressTracker`` reference
-----------------------------

.. autoclass:: ProgressTracker

    ``ProgressTracker`` supports all of the methods provided by 
    :py:class:`POD <PersistentOrderedDict>`\ s, with one small
    difference to the update function, and adds many methods for managing
    tasks.

        .. automethod:: update

    ``ProgressTracker`` adds the following methods to those provided by 
    :py:class:`POD <PersistentOrderedDict>`:

    *Add tasks*

        .. automethod:: add
        .. automethod:: add_if_absent
        .. automethod:: add_many
        .. automethod:: add_many_if_absent

    *Change the status of tasks*

        .. automethod:: mark_done
        .. automethod:: mark_not_done
        .. automethod:: increment_tries
        .. automethod:: decrement_tries
        .. automethod:: reset_tries
        .. automethod:: abort
        .. automethod:: unabort

    *Check the status of tasks*

        .. automethod:: done
        .. automethod:: tries
        .. automethod:: aborted

    .. _gates:

    *Gates to decide if a task should be done*

        .. automethod:: should_do
        .. automethod:: should_do_add
        .. automethod:: should_try
        .. automethod:: should_try_add

    .. _iterators:

    *Iterate over tasks to be done*

        .. automethod:: todo_items
        .. automethod:: todo_keys
        .. automethod:: todo_values
        .. automethod:: try_items
        .. automethod:: try_keys
        .. automethod:: try_values

    *Check the status of all tasks*
        
        .. automethod:: num_done
        .. automethod:: fraction_done
        .. automethod:: percent_done
        .. automethod:: percent_not_done

        .. automethod:: num_tried
        .. automethod:: fraction_tried
        .. automethod:: percent_tried
        .. automethod:: percent_not_tried

        .. automethod:: num_aborted
        .. automethod:: fraction_aborted
        .. automethod:: percent_aborted
        .. automethod:: percent_not_aborted





.. _SharedProgressTracker:
.. _SharedTracker:

Multiprocessing with ``SharedProgressTracker``\ s
=================================================
Just as you can distribute a ``SharedPOD`` to multiple processes, you can
distribute a ``SharedTracker`` (short alias for ``SharedProgressTracker``) to
multiple processes.

The same basic usage applies.  A single ``SharedTracker`` should be made and
distributed to child processes using a ``Queue``, ``Pipe``, or in the arguments
to a ``Process`` or ``Pool``.  All of the ``Tracker``\ |s| own methods for 
updating
the state of a task (such as ``mark_done(key)`` or ``increment_tries(key)``)
are guaranteed to synchronized properly to disk.  
If you want to add or mutate your own data stored on a task, then as for
|POD|_\ s, perform mutation operations on the ``Tracker.set`` attribute, not on
the ``Tracker`` itself.  See |writetosharedpods|_ for an explanation.

``SharedProgressTracker`` reference
-----------------------------------

.. py:class:: SharedTracker

    Alias for :py:class:`SharedProgressTracker`.

.. autoclass:: SharedProgressTracker(path, max_tries=0, init={}, gzipped=False, file_size=1000, sync_at=1000)

.. |writetosharedpods| replace:: Writing to ``SharedPOD``\ s
.. |podref| replace:: ``POD`` reference
.. |pod_ref| replace:: ``POD``
.. |s| replace:: |rsquo|\ s
.. |em| unicode:: 0x2014 .. em-dash
.. |rsquo| unicode:: 0x2019 .. right single quote
.. |sharedpodintro| replace:: ``SharedPOD``
.. |progtracker| replace:: ``ProgressTracker``
.. |sharedpodreference| replace:: ``SharedPersistentOrderedDict``
.. |PersistentOrderedDict| replace:: ``PersistentOrderedDict``
.. |SharedPersistentOrderedDict| replace:: ``SharedPersistentOrderedDict``
.. |POD| replace:: ``POD``
.. |SharedPOD| replace:: ``SharedPOD``
.. |ProgressTracker| replace:: ``ProgressTracker``
.. |Tracker| replace:: ``Tracker``
.. |SharedProgressTracker| replace:: ``SharedProgressTracker``
.. |SharedTracker| replace:: ``SharedTracker``
