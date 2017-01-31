.. tastypy documentation master file, created by
   sphinx-quickstart on Tue Jan 31 15:18:42 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tastypy
=======

Contents:

.. toctree::
   :maxdepth: 2


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

The main datastructure you get with tastypy is a persistent dict-like object
uncreatively called a ``PersistentOrderedDict``.  That's a lot to type, so it's
aliased to ``tastypy.POD``.

Just like a dict, you can key into a ``POD``, and iterate over it.  To make a new
POD, pass in a path to where the data should be persisted on disk.

.. code-block:: python

    >>> from tastypy import POD
    >>>
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo'] = 'bar'
    >>> my_pod['foo']
    'bar'
    >>>
    >>> for key in my_pod:
    ...     print(key + ' ' + my_pod[key])
    ...
    foo bar

The major difference, of course, is that the ``POD``'s data is persisted:

.. code-block:: python

    >>> del my_pod
    >>> my_pod = POD('path/to/my.pod')
    >>> my_pod['foo']
    'bar'

Note that currently keys must be ``str``'s or ``unicode``'s (sorry, no
``int``'s or other hashables!), and internally they are stored as ``unicode``'s.
This is a consequence of the file format used for persistence.  I plan to
remove this restriction eventually.

Synchronization
===============

Normally ``POD`` instances synchronize to disk any time they are directly mutated
by assigning somethign to one of their keys.  For example, doing ``my\_pod['foo']
= 'baz'`` triggers ``my\_pod`` to sync to disk.

This is accomplished within the ``__setitem__`` method of ``POD``, so any
assignment to a key will trigger synchronization.

However, if you assign a mutable object to a ``POD`` there is no way for it to
know if you mutate that object.  For example:

.. code-block:: python

    >>> my_pod['mutable'] = [1,2,3]	# synchronization happens
    >>> my_pod['mutable'].append(4)	# no synchronization!

To explicitly ask for a key to be synchronized, simply call 
``my\_pod.update(key)``.

Suspending synchronization
==========================

If you are making many changes to a ``POD``, it is often best to suspend
synchronization, make all of the changes, and then synchronize at the end.
This can be accomplished using ``POD.hold()`` and ``POD.unhold()``.  Calling
``POD.hold()`` suspends synchronization so that any changes are reflected in
memory only.  Calling ``POD.unhold()`` synchronizes all as-yet unsynchronized
changes, and reactivates synchronization.  If you want to synchronize to the 
current state but not lift the hold, you can call ``POD.sync()``.

Note, ``POD``'s always synchronize at exit, e.g. if the program crashes or if you
issue a keyboard interrupt, so you don't need to worry about hitting Ctrl-C.
Only a very bad crash preventing the program from performing cleanup operations
at exit would cause lost data, similar to the behavior of buffered data in a
file open for writing.

In the future, the default behavior of ``POD``'s will be to buffer a certain
amount of changed data to decrease the frequency of disk writes, meaning that it
won't generally be necessary to be aware of the synchronization process.

.. autoclass:: POD
    :members:


