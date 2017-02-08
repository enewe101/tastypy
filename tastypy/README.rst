<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">


<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    
    <title>tastypy &#8212; tastypy 0.0.0 documentation</title>
    
    <link rel="stylesheet" href="_static/classic.css" type="text/css" />
    <link rel="stylesheet" href="_static/pygments.css" type="text/css" />
    
    <script type="text/javascript">
      var DOCUMENTATION_OPTIONS = {
        URL_ROOT:    './',
        VERSION:     '0.0.0',
        COLLAPSE_INDEX: false,
        FILE_SUFFIX: '.html',
        HAS_SOURCE:  true
      };
    </script>
    <script type="text/javascript" src="_static/jquery.js"></script>
    <script type="text/javascript" src="_static/underscore.js"></script>
    <script type="text/javascript" src="_static/doctools.js"></script>
    <link rel="top" title="tastypy 0.0.0 documentation" href="#" /> 
  </head>
  <body role="document">
    <div class="related" role="navigation" aria-label="related navigation">
      <h3>Navigation</h3>
      <ul>
        <li class="right" style="margin-right: 10px">
          <a href="genindex.html" title="General Index"
             accesskey="I">index</a></li>
        <li class="right" >
          <a href="py-modindex.html" title="Python Module Index"
             >modules</a> |</li>
        <li class="nav-item nav-item-0"><a href="#">tastypy 0.0.0 documentation</a> &#187;</li> 
      </ul>
    </div>  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          <div class="body" role="main">
            
  <div class="section" id="module-tastypy">
<span id="tastypy"></span><h1>tastypy<a class="headerlink" href="#module-tastypy" title="Permalink to this headline">¶</a></h1>
<p><code class="docutils literal"><span class="pre">tastypy</span></code> provides dict-like datastructures that transparently persist to to
disk, along with multiprocessing-safe versions.  This is helpful in cases where you need a persisted key-value store but
don&#8217;t want to make a database.  For example, it could be used to keep track of
the status of URLs in a crawler, or of tasks in a long-running process,
enabling the process to pick up where it left off after a crash or
interruption.</p>
<p>Included:</p>
<blockquote>
<div><ul class="simple">
<li><a class="reference internal" href="#persistentordereddict"><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code></a> (<a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a> for short): a transparently persistent
dict-like mapping</li>
<li><a class="reference internal" href="#sharedpersistentordereddict"><code class="docutils literal"><span class="pre">SharedPersistentOrderedDict</span></code></a> (<a class="reference internal" href="#sharedpod"><code class="docutils literal"><span class="pre">SharedPOD</span></code></a> for short): a
multiprocessing-safe version of <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a></li>
<li><a class="reference internal" href="#progresstracker"><code class="docutils literal"><span class="pre">ProgressTracker</span></code></a> (<a class="reference internal" href="#tracker"><code class="docutils literal"><span class="pre">Tracker</span></code></a> for short): a subclass of <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a> that helps
keep track of long-running processes with repetitive tasks</li>
<li><a class="reference internal" href="#sharedprogresstracker"><code class="docutils literal"><span class="pre">SharedProgressTracker</span></code></a> (<a class="reference internal" href="#sharedtracker"><code class="docutils literal"><span class="pre">SharedTracker</span></code></a> for short): a
multiprocessing-safe version of <a class="reference internal" href="#tracker"><code class="docutils literal"><span class="pre">Tracker</span></code></a></li>
</ul>
</div></blockquote>
<div class="admonition note">
<p class="first admonition-title">Note</p>
<p class="last">Please report any bugs request features by opening an issue at the
prject&#8217;s <a class="reference external" href="https://github.com/enewe101/tastypy">github page</a>.</p>
</div>
</div>
<div class="section" id="install">
<h1>Install<a class="headerlink" href="#install" title="Permalink to this headline">¶</a></h1>
<div class="highlight-bash"><div class="highlight"><pre><span></span>pip install tastypy
</pre></div>
</div>
</div>
<div class="section" id="pod">
<span id="persistentordereddict"></span><span id="id1"></span><h1><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code><a class="headerlink" href="#pod" title="Permalink to this headline">¶</a></h1>
<p>The <code class="docutils literal"><span class="pre">tastypy.POD</span></code> (short alias for <code class="docutils literal"><span class="pre">tastypy.PersistentOrderedDict</span></code>) is a
dict-like datastructure that transparently synchronizes to disk.  Supply a path
when creating a <code class="docutils literal"><span class="pre">POD</span></code>, and the data will be persisted using files at that
location:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="kn">from</span> <span class="nn">tastypy</span> <span class="kn">import</span> <span class="n">POD</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span> <span class="o">=</span> <span class="n">POD</span><span class="p">(</span><span class="s1">&#39;path/to/my.pod&#39;</span><span class="p">)</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="s1">&#39;bar&#39;</span>
<span class="gp">&gt;&gt;&gt; </span><span class="nb">exit</span><span class="p">()</span>
</pre></div>
</div>
<p>Data stored in <code class="docutils literal"><span class="pre">POD</span></code>s is preserved after the program exits:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="kn">from</span> <span class="nn">tastypy</span> <span class="kn">import</span> <span class="n">POD</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span> <span class="o">=</span> <span class="n">POD</span><span class="p">(</span><span class="s1">&#39;path/to/my.pod&#39;</span><span class="p">)</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span>
<span class="go">bar</span>
</pre></div>
</div>
<p><code class="docutils literal"><span class="pre">POD</span></code>s are meant to feel like <code class="docutils literal"><span class="pre">dict</span></code>s in most respects.  They support
the same iteration mechanisms, a similar implementation of <code class="docutils literal"><span class="pre">update()</span></code>, and
their <code class="docutils literal"><span class="pre">len</span></code> corresponds to their number of entries.</p>
<div class="section" id="json-general-simple-secure">
<h2>JSON &#8211; general, simple, secure<a class="headerlink" href="#json-general-simple-secure" title="Permalink to this headline">¶</a></h2>
<p>Data is serialized in JSON format using the builtin <code class="docutils literal"><span class="pre">json</span></code> module for
serialization and deserialization.  JSON is general enough to represent pretty
much any data, and unlike pickles, it is secure, application-independant, and
interoperable across programs and python versions.  The persistence files are
human-readable, and easily hacked manually or with other tools.</p>
<p>While there are advantages to using <code class="docutils literal"><span class="pre">json</span></code>, there are also some limitations.
Only json-serializable data can be stored in a <code class="docutils literal"><span class="pre">POD</span></code>: which includes
string-like, number-like, list-like, and dict-like objects (and arbitrarily
nested combinations).  In a serialization-deserialization cycle, string-likes
will be coerced to <code class="docutils literal"><span class="pre">unicode</span></code>s, list-likes to <code class="docutils literal"><span class="pre">list</span></code>s, and dict-likes to
<code class="docutils literal"><span class="pre">dict</span></code>s.  It&#8217;s actually a great idea to keep your data decoupled from your
programs where possible, so sticking to these very universal data types is
probably an <em>enabling</em> constraint.</p>
<p>There is, however, one quirk of <code class="docutils literal"><span class="pre">json</span></code> that can be quite unexpected:</p>
<div class="admonition warning">
<p class="first admonition-title">Warning</p>
<p><code class="docutils literal"><span class="pre">json.encode()</span></code> converts integer keys of <code class="docutils literal"><span class="pre">dict</span></code>s to <code class="docutils literal"><span class="pre">unicode</span></code>s
to comply with the JSON specification.  This quirk is inherited by
<code class="docutils literal"><span class="pre">tastypy</span></code>:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="mi">1</span><span class="p">:</span><span class="mi">1</span><span class="p">}</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="o">.</span><span class="n">sync</span><span class="p">();</span> <span class="n">my_pod</span><span class="o">.</span><span class="n">revert</span><span class="p">()</span>  <span class="c1"># do a serialize/deserialize cycle</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="mi">1</span><span class="p">]</span>
<span class="go">{&#39;1&#39;:1}</span>
</pre></div>
</div>
<p class="last">Notice how the key in the stored <code class="docutils literal"><span class="pre">dict</span></code> turned from <code class="docutils literal"><span class="pre">1</span></code> into <code class="docutils literal"><span class="pre">'1'</span></code>.</p>
</div>
</div>
<div class="section" id="synchronization">
<h2>Synchronization<a class="headerlink" href="#synchronization" title="Permalink to this headline">¶</a></h2>
<p>Generally you don&#8217;t need to think about synchronization&#8212;that&#8217;s the goal
of <code class="docutils literal"><span class="pre">tastypy</span></code>.  Still, it&#8217;s good to understand how it works, and how not to
break it.</p>
<p>Any changes made by keying into the <code class="docutils literal"><span class="pre">POD</span></code> will
be properly synchronized.  However, if you make a reference to a mutable type stored
in the <code class="docutils literal"><span class="pre">POD</span></code>, and then mutate it using <em>that</em> reference, there is no way for
the <code class="docutils literal"><span class="pre">POD</span></code> to know about it, and that change will not be persisted.</p>
<p>In other words, don&#8217;t do this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">[]</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_list</span> <span class="o">=</span> <span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_list</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="mi">42</span><span class="p">)</span>              <span class="c1"># BAD! This won&#39;t be sync&#39;d!</span>
</pre></div>
</div>
<p>Instead, do this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">[]</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="mi">42</span><span class="p">)</span>        <span class="c1"># GOOD! This will be sync&#39;d!</span>
</pre></div>
</div>
<div class="admonition note">
<p class="first admonition-title">Note</p>
<p class="last">If you mutate an object that was accessed by keying into the <code class="docutils literal"><span class="pre">POD</span></code>, then
the <code class="docutils literal"><span class="pre">POD</span></code> knows about the change.  If you mutate an object using another
reference, the <code class="docutils literal"><span class="pre">POD</span></code> will not persist that change.</p>
</div>
<p><code class="docutils literal"><span class="pre">POD</span></code>s keep track of values that were changed in memory, and synchronize to
disk whenever enough values have changed (by default, 1000), or when the
program terminates.  (The synchronization threshold can be set using the
<code class="docutils literal"><span class="pre">sync_at</span></code> argument when creating the <code class="docutils literal"><span class="pre">POD</span></code>.)</p>
<div class="section" id="can-data-be-lost">
<h3>Can data be lost?<a class="headerlink" href="#can-data-be-lost" title="Permalink to this headline">¶</a></h3>
<p>&#8220;Dirty&#8221; values&#8212;values that differ in memory and on disk&#8212;can be considered
as having the same status as data that you <code class="docutils literal"><span class="pre">.write()</span></code> to a file object open
for writing.  If the program exits, crashes from an uncaught exception, or
receives a SIGTERM or SIGINT (e.g. from ctrl-C), data <em>will</em> be synchronized.
But, in the exceptional cases that the Python interpreter segfaults or the
program receives a SIGKILL, no synchronization is possible, so unsynchronized
data would be lost.</p>
</div>
<div class="section" id="can-i-manually-control-synchronization">
<h3>Can I manually control synchronization?<a class="headerlink" href="#can-i-manually-control-synchronization" title="Permalink to this headline">¶</a></h3>
<p>Normally you won&#8217;t need to, but you can. To do a one-time synchronization of
all dirty values immediately, do <a class="reference internal" href="#tastypy.PersistentOrderedDict.sync" title="tastypy.PersistentOrderedDict.sync"><code class="xref py py-meth docutils literal"><span class="pre">POD.sync()</span></code></a>.  To synchronize a specific value use
<a class="reference internal" href="#tastypy.PersistentOrderedDict.sync_key" title="tastypy.PersistentOrderedDict.sync_key"><code class="xref py py-meth docutils literal"><span class="pre">POD.sync_key(key)</span></code></a>.  To flag a
key dirty for the next synchronization, use <a class="reference internal" href="#tastypy.PersistentOrderedDict.mark_dirty" title="tastypy.PersistentOrderedDict.mark_dirty"><code class="xref py py-meth docutils literal"><span class="pre">POD.mark_dirty(key)</span></code></a>.  To get the set of dirty keys, do
<a class="reference internal" href="#tastypy.PersistentOrderedDict.dirty" title="tastypy.PersistentOrderedDict.dirty"><code class="xref py py-meth docutils literal"><span class="pre">POD.dirty()</span></code></a>.  You can suspend
automatic synchronization using <a class="reference internal" href="#tastypy.PersistentOrderedDict.hold" title="tastypy.PersistentOrderedDict.hold"><code class="xref py py-meth docutils literal"><span class="pre">POD.hold()</span></code></a>, and reactivate it using <a class="reference internal" href="#tastypy.PersistentOrderedDict.unhold" title="tastypy.PersistentOrderedDict.unhold"><code class="xref py py-meth docutils literal"><span class="pre">POD.unhold()</span></code></a>.  To drop all un-synchronized changes and
revert to the state stored on disk do <a class="reference internal" href="#tastypy.PersistentOrderedDict.revert" title="tastypy.PersistentOrderedDict.revert"><code class="xref py py-meth docutils literal"><span class="pre">POD.revert()</span></code></a>.  See the <a class="reference internal" href="#podref"><code class="docutils literal"><span class="pre">POD</span></code> reference</a>.</p>
</div>
<div class="section" id="opening-multiple-pods-at-same-location-is-safe">
<h3>Opening multiple <code class="docutils literal"><span class="pre">POD</span></code>s at same location is safe<a class="headerlink" href="#opening-multiple-pods-at-same-location-is-safe" title="Permalink to this headline">¶</a></h3>
<p>Conceptually, opening multiple <code class="docutils literal"><span class="pre">POD</span></code>s to the same location on disk might seem
like opening multiple file handles in write mode to the same location.</p>
<p>For files this isn&#8217;t safe&#8212;when one file object flushes, it will likely
overwrite data recently written by another.
But <code class="docutils literal"><span class="pre">POD</span></code>s open to the same location on disk act like singletons&#8212;so they
actually reference the same underlying data, making stale overwrites a
non-problem.  Of course, the situation is completely different if you want
multiple processes to interact with <code class="docutils literal"><span class="pre">POD</span></code>s at the same location&#8212;for that
you should use a <a class="reference internal" href="#sharedpodintro"><code class="docutils literal"><span class="pre">SharedPOD</span></code></a>.</p>
<p>(It&#8217;s possible to open a <code class="docutils literal"><span class="pre">POD</span></code> with isolated memory by passing
<code class="docutils literal"><span class="pre">clone=False</span></code> when creating it&#8212;but you shouldn&#8217;t need to do that.)</p>
</div>
</div>
<div class="section" id="persistentordereddict-reference">
<span id="podref"></span><h2><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code> reference<a class="headerlink" href="#persistentordereddict-reference" title="Permalink to this headline">¶</a></h2>
<dl class="class">
<dt id="tastypy.POD">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">POD</code><a class="headerlink" href="#tastypy.POD" title="Permalink to this definition">¶</a></dt>
<dd><p>Alias for <code class="docutils literal"><span class="pre">tastypy.PersistentOrderedDict</span></code>.</p>
</dd></dl>

<dl class="class">
<dt id="tastypy.PersistentOrderedDict">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">PersistentOrderedDict</code><span class="sig-paren">(</span><em>path</em>, <em>init={}</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em>, <em>clone=True</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict" title="Permalink to this definition">¶</a></dt>
<dd><p>A key-value mapping that synchronizes transparently to disk at the location
given by <code class="docutils literal"><span class="pre">path</span></code>.  When treated as an iterable, it yields keys in the
order in which they were originally added. Data will persist after program
interruption and can be accessed by creating a new instance directed at the
same path.</p>
<p>Provide initial data to initialize (or update) the mapping using the
<code class="docutils literal"><span class="pre">init</span></code> parameter.  The argument should be an iterable of key-value tuples
or should implement <code class="docutils literal"><span class="pre">iteritems()</span></code> yielding such an iterable.  This is
equivalent to calling <code class="docutils literal"><span class="pre">update(init_arg)</span></code> after creating the <code class="docutils literal"><span class="pre">POD</span></code>.</p>
<p>The JSON-formatted persistence files are gzipped if <code class="docutils literal"><span class="pre">gzipped</span></code> is
<code class="docutils literal"><span class="pre">True</span></code>.    Each file stores a number of values given by <code class="docutils literal"><span class="pre">file_size</span></code>.
Smaller values give faster synchronization but create more files.  Data is
automatically synchronized to disk when the number of &#8220;dirty&#8221; values
reaches <code class="docutils literal"><span class="pre">sync_at</span></code>, or if the program terminates.</p>
<p><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code>s opened to the same file path share underlying
memory so that they don&#8217;t stale over-write one another&#8217;s data.  Setting
<code class="docutils literal"><span class="pre">clone</span></code> to true gives the instance it&#8217;s own memory space.</p>
<dl class="method">
<dt id="tastypy.PersistentOrderedDict.update">
<code class="descname">update</code><span class="sig-paren">(</span><em>*mappings</em>, <em>**kwargs</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.update" title="Permalink to this definition">¶</a></dt>
<dd><p>Update self to reflect key-value mappings, and reflect key-value pairs
provided as keyword arguments.  Arguments closer to the right take 
precedence.  Mapping objects must either be iterables of key-value
tuples or implement <code class="docutils literal"><span class="pre">iteritems()</span></code> yielding such an iterator.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.iteritems">
<code class="descname">iteritems</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.iteritems" title="Permalink to this definition">¶</a></dt>
<dd><p>Provide an iterator of key-value tuples in the order in which keys were
added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.iterkeys">
<code class="descname">iterkeys</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.iterkeys" title="Permalink to this definition">¶</a></dt>
<dd><p>Provide an iterator over keys in the order in which they were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.itervalues">
<code class="descname">itervalues</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.itervalues" title="Permalink to this definition">¶</a></dt>
<dd><p>Provide an iterator over values in the order in which corresponding
keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.items">
<code class="descname">items</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.items" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of key-value tuples in the order in which keys were
added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.keys">
<code class="descname">keys</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.keys" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of keys in the order in which they were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.values">
<code class="descname">values</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.values" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of values in the order in which the corresponding keys
were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.mark_dirty">
<code class="descname">mark_dirty</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.mark_dirty" title="Permalink to this definition">¶</a></dt>
<dd><p>Force <code class="docutils literal"><span class="pre">key</span></code> to be considered out of sync.  The data associated to
this key will be written to file during the next synchronization.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.dirty">
<code class="descname">dirty</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.dirty" title="Permalink to this definition">¶</a></dt>
<dd><p>Return the set of dirty keys.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.sync_key">
<code class="descname">sync_key</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.sync_key" title="Permalink to this definition">¶</a></dt>
<dd><p>Force <code class="docutils literal"><span class="pre">key</span></code> to be synchronized to disk immediately.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.sync">
<code class="descname">sync</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.sync" title="Permalink to this definition">¶</a></dt>
<dd><p>Force synchronization of all dirty values.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.hold">
<code class="descname">hold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.hold" title="Permalink to this definition">¶</a></dt>
<dd><p>Suspend the automatic synchronization to disk that normally occurs when
the number of dirty values reaches <code class="docutils literal"><span class="pre">sync_at</span></code>.  (Synchronization will
still be carried out at termination.)</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.unhold">
<code class="descname">unhold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.unhold" title="Permalink to this definition">¶</a></dt>
<dd><p>Resume automatic synchronization to disk.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.revert">
<code class="descname">revert</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.revert" title="Permalink to this definition">¶</a></dt>
<dd><p>Load values from disk into memory, discarding any unsynchronized changes.</p>
</dd></dl>

</dd></dl>

</div>
</div>
<div class="section" id="multiprocessing-with-sharedpods">
<span id="sharedpod"></span><span id="sharedpersistentordereddict"></span><span id="sharedpodintro"></span><h1>Multiprocessing with <code class="docutils literal"><span class="pre">SharedPOD</span></code>s<a class="headerlink" href="#multiprocessing-with-sharedpods" title="Permalink to this headline">¶</a></h1>
<p>To have multiple processes use <code class="docutils literal"><span class="pre">POD</span></code>s directed at the same location, you
need to use a <code class="docutils literal"><span class="pre">SharedPOD</span></code>, which handles synchronization between processes.
Open a single <code class="docutils literal"><span class="pre">SharedPOD</span></code> instance and then distribute it to the children
(e.g. by passing it over a <code class="docutils literal"><span class="pre">Pipe</span></code> or <code class="docutils literal"><span class="pre">Queue</span></code>, or as an argument to a
<code class="docutils literal"><span class="pre">multiprocessing.Process</span></code> or <code class="docutils literal"><span class="pre">multiprocessing.Pool</span></code>).</p>
<div class="admonition warning">
<p class="first admonition-title">Warning</p>
<p class="last">Do not create multiple <code class="docutils literal"><span class="pre">SharedPOD</span></code> instances pointing to the same
location on disk.  Make one <code class="docutils literal"><span class="pre">SharedPOD</span></code> (per location on disk) and share
it with other processes.</p>
</div>
<p>The <code class="docutils literal"><span class="pre">SharedPOD</span></code> starts a server process with an underlying
<code class="docutils literal"><span class="pre">POD</span></code>, and acts as a broker, forwarding method calls to the server and taking
back responses, while safely interleaving each processes&#8217; access.
Changes made using a <code class="docutils literal"><span class="pre">SharedPOD</span></code> are immediately visible to all processes.</p>
<div class="section" id="writing-to-shared-sharedpods">
<span id="writetosharedpods"></span><h2>Writing to shared <code class="docutils literal"><span class="pre">SharedPOD</span></code>s<a class="headerlink" href="#writing-to-shared-sharedpods" title="Permalink to this headline">¶</a></h2>
<p>The <code class="docutils literal"><span class="pre">SharedPOD</span></code> has to use a different strategy to ensure that data is
correctly synchronized.  It isn&#8217;t enough to mark values as dirty: the new values
needs to be forwarded to the underlying server.</p>
<p>This means that you need to explicitly signal when an operation can mutate the
<code class="docutils literal"><span class="pre">SharedPOD</span></code>.  Any time you do something to a <code class="docutils literal"><span class="pre">SharedPOD</span></code> that can mutate
it, you should perform it on the <code class="docutils literal"><span class="pre">SharedPOD.set</span></code> attribute instead of on the
<code class="docutils literal"><span class="pre">ShardPOD</span></code> itself.</p>
<p>So, instead of doing this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="n">shared_pod</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">SharedPOD</span><span class="p">(</span><span class="s1">&#39;my.pod&#39;</span><span class="p">)</span>

<span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="s1">&#39;bar&#39;</span><span class="p">:</span><span class="mi">0</span><span class="p">,</span> <span class="s1">&#39;baz&#39;</span><span class="p">:[]}</span>
<span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;bar&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
<span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;baz&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="s1">&#39;fizz&#39;</span><span class="p">)</span>
</pre></div>
</div>
<p>You should do this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="n">shared_pod</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">SharedPOD</span><span class="p">(</span><span class="s1">&#39;my.pod&#39;</span><span class="p">)</span>

<span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="s1">&#39;bar&#39;</span><span class="p">:</span><span class="mi">4</span><span class="p">,</span> <span class="s1">&#39;baz&#39;</span><span class="p">:[]}</span>
<span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;bar&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
<span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;baz&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="s1">&#39;fizz&#39;</span><span class="p">)</span>
</pre></div>
</div>
<p>The <code class="docutils literal"><span class="pre">SharedPOD</span></code>’s <code class="docutils literal"><span class="pre">.set</span></code> attribute uses some tricks to capture
arbitrarily deep &#8220;keying&#8221; and &#8220;indexing&#8221;, method calls,  arguments, and tell
when it&#8217;s being operated on by operators like <code class="docutils literal"><span class="pre">+=</span></code>, slice assignments like
<code class="docutils literal"><span class="pre">shared_pod.set['a'][:]</span> <span class="pre">=</span> <span class="pre">[4]</span></code>, and the like.  It then forwards this
information to be handled and synchronized appropriately.</p>
<p>Just be sure to leave <em>off</em> the <code class="docutils literal"><span class="pre">.set</span></code> when you <em>access</em> values:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="k">print</span> <span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;baz&#39;</span><span class="p">][</span><span class="mi">0</span><span class="p">]</span>
<span class="go">&lt;tastypy._deep_proxy.DeepProxy at 0x103ed8c90&gt;</span>
<span class="gp">&gt;&gt;&gt; </span><span class="k">print</span> <span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">][</span><span class="s1">&#39;baz&#39;</span><span class="p">][</span><span class="mi">0</span><span class="p">]</span>
<span class="go">fizz</span>
</pre></div>
</div>
</div>
<div class="section" id="avoiding-raciness">
<h2>Avoiding raciness<a class="headerlink" href="#avoiding-raciness" title="Permalink to this headline">¶</a></h2>
<p>The <code class="docutils literal"><span class="pre">SharedPOD</span></code> eliminates any raciness problems related to it&#8217;s internal
synchronization to disk, and it ensures that each process holding the same
<code class="docutils literal"><span class="pre">SharedPOD</span></code> always sees the most up-to-date values, whether sync&#8217;d to disk or
not.</p>
<p>However, that doesn&#8217;t prevent you from introducing your own raciness in how you
use <code class="docutils literal"><span class="pre">SharedPOD</span></code>s (or any other shared datastructure for that matter).</p>
<p>Issues generally arise when you read some shared value, and take an action
based on that value, while other processes might modify it.  Usually a safe
policy is to have different processes read/write to non-overlapping subsets of
the <code class="docutils literal"><span class="pre">SharedPOD</span></code>’s keys.</p>
<p>But if you can&#8217;t or don&#8217;t want to set up your program that way, then use a
locked context to avoid raciness.  To demonstrate that, we&#8217;ll use the
prototypical example that can introduce a race condition: incrementing a value.
Suppose that we have a worker function, that will be executed by a bunch of
different workers, that looks like this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">work</span><span class="p">(</span><span class="n">pod</span><span class="p">):</span>
    <span class="n">pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;some-key&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
</pre></div>
</div>
<p>That may look fine, but the <code class="docutils literal"><span class="pre">+=</span></code> operator really corresponds to first
computing the sum <code class="docutils literal"><span class="pre">old_val</span> <span class="pre">+</span> <span class="pre">1</span></code> and <em>then</em> assigning it back to the variable.
As process A is doing the <code class="docutils literal"><span class="pre">+=</span></code>, process B could come along and update the
varable, doing its update after A computed the sum but before A assigns it
back.  So, B&#8217;s update would be lost.  To temporarily prevent other processes
from modifying the <code class="docutils literal"><span class="pre">SharedPOD</span></code>, use the <a class="reference internal" href="#tastypy.SharedPersistentOrderedDict.locked" title="tastypy.SharedPersistentOrderedDict.locked"><code class="xref py py-meth docutils literal"><span class="pre">SharedPOD.locked()</span></code></a> context manager, like so:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">work</span><span class="p">(</span><span class="n">shared_pod</span><span class="p">):</span>
    <span class="k">with</span> <span class="n">shared_pod</span><span class="o">.</span><span class="n">locked</span><span class="p">():</span>
        <span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;some-key&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
</pre></div>
</div>
<p>So, when exactly do you need to do that?  First off, any of <code class="docutils literal"><span class="pre">SharedPOD</span></code>’s
own methods, or methods defined <em>on</em> its values can be treated as <em>atomic</em>,
because internally a lock will be acuired before calling the method, and
released afterward.</p>
<p>So you don&#8217;t need a locked context for something like
<code class="docutils literal"><span class="pre">pod.set['some-list'].append('item')</span></code>, or
<code class="docutils literal"><span class="pre">del</span> <span class="pre">pod.set['some-dict']['some-key']</span></code>.
Contrary to the above you also don&#8217;t need a locked context when using the
<code class="docutils literal"><span class="pre">+=</span></code> operator on values that <em>are mutable objects that
implement</em> <code class="docutils literal"><span class="pre">__iadd__</span></code> and perform the operation <em>inplace</em>.  For example,
you don&#8217;t need a lock for augmented assignment to a list, e.g.
<code class="docutils literal"><span class="pre">pod.set['I-store-a-list']</span> <span class="pre">+=</span> <span class="pre">[1]</span></code>.</p>
<p>You need a locked context if:</p>
<blockquote>
<div><ul class="simple">
<li>You read a value from a <code class="docutils literal"><span class="pre">SharedPOD</span></code></li>
<li>You take action based on that value</li>
<li>It would be bad if that value changed before finishing that action</li>
<li>Other processes can modify that value</li>
</ul>
</div></blockquote>
</div>
<div class="section" id="sharedpod-multiprocessing-example">
<h2><code class="docutils literal"><span class="pre">SharedPOD</span></code> multiprocessing example<a class="headerlink" href="#sharedpod-multiprocessing-example" title="Permalink to this headline">¶</a></h2>
<p>The following example shows how you can use a <code class="docutils literal"><span class="pre">SharedPOD</span></code> in a multiprocessed
program.  In this example, each worker reads / writes to it&#8217;s own subset of the
<code class="docutils literal"><span class="pre">SharedPOD</span></code> so locking isn&#8217;t necessary:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="kn">from</span> <span class="nn">multiprocessing</span> <span class="kn">import</span> <span class="n">Process</span>
<span class="kn">import</span> <span class="nn">tastypy</span>

<span class="k">def</span> <span class="nf">work</span><span class="p">(</span><span class="n">pod</span><span class="p">,</span> <span class="n">proc_num</span><span class="p">,</span> <span class="n">num_procs</span><span class="p">):</span>
    <span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="n">pod</span><span class="p">:</span>
        <span class="k">if</span> <span class="n">i</span><span class="o">%</span><span class="n">num_procs</span> <span class="o">==</span> <span class="n">proc_num</span><span class="p">:</span>
            <span class="n">pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="n">i</span><span class="p">]</span> <span class="o">=</span> <span class="n">i</span><span class="o">**</span><span class="mi">2</span>

<span class="k">def</span> <span class="nf">run_multiproc</span><span class="p">():</span>
    <span class="n">num_procs</span> <span class="o">=</span> <span class="mi">5</span>
    <span class="n">init</span> <span class="o">=</span> <span class="p">[(</span><span class="n">i</span><span class="p">,</span> <span class="bp">None</span><span class="p">)</span> <span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">range</span><span class="p">(</span><span class="mi">25</span><span class="p">)]</span>
    <span class="n">pod</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">SharedPOD</span><span class="p">(</span><span class="s1">&#39;my.pod&#39;</span><span class="p">,</span> <span class="n">init</span><span class="o">=</span><span class="n">init</span><span class="p">)</span>
    <span class="n">procs</span> <span class="o">=</span> <span class="p">[]</span>
    <span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">range</span><span class="p">(</span><span class="n">num_procs</span><span class="p">):</span>
        <span class="n">proc</span> <span class="o">=</span> <span class="n">Process</span><span class="p">(</span><span class="n">target</span><span class="o">=</span><span class="n">work</span><span class="p">,</span> <span class="n">args</span><span class="o">=</span><span class="p">(</span><span class="n">pod</span><span class="p">,</span> <span class="n">i</span><span class="p">,</span> <span class="n">num_procs</span><span class="p">))</span>
        <span class="n">proc</span><span class="o">.</span><span class="n">start</span><span class="p">()</span>
        <span class="n">procs</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="n">proc</span><span class="p">)</span>

    <span class="k">for</span> <span class="n">proc</span> <span class="ow">in</span> <span class="n">procs</span><span class="p">:</span>
        <span class="n">proc</span><span class="o">.</span><span class="n">join</span><span class="p">()</span>

    <span class="k">for</span> <span class="n">key</span><span class="p">,</span> <span class="n">val</span> <span class="ow">in</span> <span class="n">pod</span><span class="o">.</span><span class="n">iteritems</span><span class="p">():</span>
        <span class="k">print</span> <span class="n">key</span><span class="p">,</span> <span class="n">val</span>

<span class="k">if</span> <span class="n">__name__</span> <span class="o">==</span> <span class="s1">&#39;__main__&#39;</span><span class="p">:</span>
    <span class="n">run_multiproc</span><span class="p">()</span>
</pre></div>
</div>
<p>If you run it, you&#8217;ll see something like this:</p>
<div class="highlight-bash"><div class="highlight"><pre><span></span>$ python shared_pod_example.py
<span class="m">0</span> 0
<span class="m">1</span> 1
<span class="m">2</span> 4
<span class="m">3</span> 9
<span class="m">4</span> 16
<span class="m">5</span> 25
<span class="m">6</span> 36
<span class="m">7</span> 49
<span class="m">8</span> 64
<span class="m">9</span> 81
<span class="m">10</span> 100
<span class="m">11</span> 121
<span class="m">12</span> 144
<span class="m">13</span> 169
<span class="m">14</span> 196
<span class="m">15</span> 225
<span class="m">16</span> 256
<span class="m">17</span> 289
<span class="m">18</span> 324
<span class="m">19</span> 361
<span class="m">20</span> 400
<span class="m">21</span> 441
<span class="m">22</span> 484
<span class="m">23</span> 529
<span class="m">24</span> 576
</pre></div>
</div>
</div>
<div class="section" id="sharedpersistentordereddict-reference">
<span id="sharedpodreference"></span><h2>SharedPersistentOrderedDict reference<a class="headerlink" href="#sharedpersistentordereddict-reference" title="Permalink to this headline">¶</a></h2>
<dl class="class">
<dt id="tastypy.SharedPOD">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">SharedPOD</code><a class="headerlink" href="#tastypy.SharedPOD" title="Permalink to this definition">¶</a></dt>
<dd><p>Alias for <a class="reference internal" href="#tastypy.SharedPersistentOrderedDict" title="tastypy.SharedPersistentOrderedDict"><code class="xref py py-class docutils literal"><span class="pre">SharedPersistentOrderedDict</span></code></a>.</p>
</dd></dl>

<dl class="class">
<dt id="tastypy.SharedPersistentOrderedDict">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">SharedPersistentOrderedDict</code><span class="sig-paren">(</span><em>path</em>, <em>init={}</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict" title="Permalink to this definition">¶</a></dt>
<dd><p>A multiprocessing-safe proxy for <code class="docutils literal"><span class="pre">tasatypy.POD</span></code>.  Data will be
syncronized to disk in files under <code class="docutils literal"><span class="pre">path</span></code>.  The <code class="docutils literal"><span class="pre">SharedPOD</span></code> supports the
same iteration methods as <code class="docutils literal"><span class="pre">POD</span></code>; multiple processes can iterate
concurrently without blocking eachother.  All iteration methods return keys
and or values in the order in which keys were added.</p>
<blockquote>
<div><dl class="attribute">
<dt id="tastypy.SharedPersistentOrderedDict.set">
<code class="descname">set</code><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.set" title="Permalink to this definition">¶</a></dt>
<dd><p>Attribute that accepts all mutable operations on the <code class="docutils literal"><span class="pre">SharedPOD</span></code>.
E.g. instead of this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;some&#39;</span><span class="p">][</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">42</span>
<span class="n">shared_pod</span><span class="p">[</span><span class="s1">&#39;some&#39;</span><span class="p">][</span><span class="s1">&#39;list&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="s1">&#39;forty-two&#39;</span><span class="p">)</span>
</pre></div>
</div>
<p>Do this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;some&#39;</span><span class="p">][</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">42</span>
<span class="n">shared_pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;some&#39;</span><span class="p">][</span><span class="s1">&#39;list&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="s1">&#39;forty-two&#39;</span><span class="p">)</span>
</pre></div>
</div>
</dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.close">
<code class="descname">close</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.close" title="Permalink to this definition">¶</a></dt>
<dd><p>Ask the the underlying <code class="docutils literal"><span class="pre">POD</span></code> server to terminate (it will synchronize
to disk first).  Normally you don&#8217;t need to use this because the server
process will sync and shutdown automatically when its parent process
terminates.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.locked">
<code class="descname">locked</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.locked" title="Permalink to this definition">¶</a></dt>
<dd><p>Context manager under which only the calling process can interact with
the <code class="docutils literal"><span class="pre">SharedPOD</span></code>, all other processes being blocked until the context
is closed.  Using this context manager is preferable to calling
<code class="docutils literal"><span class="pre">lock()</span></code> followed by <code class="docutils literal"><span class="pre">unlock()</span></code> because the lock will be released
even if an exception is thrown or a return statement reached.</p>
<p>Usage:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">with</span> <span class="n">pod</span><span class="o">.</span><span class="n">locked</span><span class="p">():</span>
        <span class="n">pod</span><span class="o">.</span><span class="n">set</span><span class="p">[</span><span class="s1">&#39;some-key&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>
</pre></div>
</div>
<p>See <a class="reference internal" href="#avoiding-raciness">Avoiding raciness</a> to see when you need to use this.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.lock">
<code class="descname">lock</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.lock" title="Permalink to this definition">¶</a></dt>
<dd><p>Only allow the caller to read / write to the <code class="docutils literal"><span class="pre">SharedPOD</span></code>.  
All other processes are blocked until <code class="docutils literal"><span class="pre">unlock</span></code> is called.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.unlock">
<code class="descname">unlock</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.unlock" title="Permalink to this definition">¶</a></dt>
<dd><p>Allow other processes to read / write.</p>
</dd></dl>

</div></blockquote>
<p><em>The following methods are functionally equivalent to those of</em> <code class="docutils literal"><span class="pre">POD</span></code>:</p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.update">
<code class="descname">update</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.update" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.mark_dirty">
<code class="descname">mark_dirty</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.mark_dirty" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.sync">
<code class="descname">sync</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.sync" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.sync_key">
<code class="descname">sync_key</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.sync_key" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.hold">
<code class="descname">hold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.hold" title="Permalink to this definition">¶</a></dt>
<dd><p>Note that the underlying <code class="docutils literal"><span class="pre">POD</span></code> continues to track changes from all
processes while automatic synchronization is suspended.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.unhold">
<code class="descname">unhold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.unhold" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.revert">
<code class="descname">revert</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.revert" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.iteritems">
<code class="descname">iteritems</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.iteritems" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.iterkeys">
<code class="descname">iterkeys</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.iterkeys" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.itervalues">
<code class="descname">itervalues</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.itervalues" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.items">
<code class="descname">items</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.items" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.keys">
<code class="descname">keys</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.keys" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

<dl class="method">
<dt id="tastypy.SharedPersistentOrderedDict.values">
<code class="descname">values</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedPersistentOrderedDict.values" title="Permalink to this definition">¶</a></dt>
<dd></dd></dl>

</div></blockquote>
</dd></dl>

</div>
</div>
<div class="section" id="tracker">
<span id="progresstracker"></span><span id="id2"></span><h1><code class="docutils literal"><span class="pre">ProgressTracker</span></code><a class="headerlink" href="#tracker" title="Permalink to this headline">¶</a></h1>
<p>The <code class="docutils literal"><span class="pre">tastypy.Tracker</span></code> (short for <code class="docutils literal"><span class="pre">tastypy.ProgressTracker</span></code>) is a subclass
of <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a> that helps track the progress of long-running programs that
involve performing many repetitive tasks, so that the program can pick up where
it left off in case of a crash.</p>
<p>Each value in a tracker represents one task and stores whether that task is
done, aborted, and how many times it has been tried, along with other data you
might want to associate to it.</p>
<p>Often in a long-running program, you want to attempt any tasks that have
not been done successfully, but only attempt tasks some maximum number of times.</p>
<p>To motivate the <code class="docutils literal"><span class="pre">ProgressTracker</span></code> and illustrate how it works, let&#8217;s imagine
that we are crawling a website.  We&#8217;ll begin by implementing that using a
regular <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a> to keep track of the URLs that need to be crawled.  Then we&#8217;ll
see how the <code class="docutils literal"><span class="pre">Tracker</span></code> can support that usecase.  First using a <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a>:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">crawl</span><span class="p">(</span><span class="n">seed_url</span><span class="p">):</span>

    <span class="n">url_pod</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">POD</span><span class="p">(</span><span class="s1">&#39;urls.pod&#39;</span><span class="p">)</span>
    <span class="k">if</span> <span class="n">seed_url</span> <span class="ow">not</span> <span class="ow">in</span> <span class="n">url_pod</span><span class="p">:</span>
        <span class="n">url_pod</span><span class="p">[</span><span class="n">seed_url</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="s1">&#39;tries&#39;</span><span class="p">:</span><span class="mi">0</span><span class="p">,</span> <span class="s1">&#39;done&#39;</span><span class="p">:</span><span class="bp">False</span><span class="p">}</span>

    <span class="k">for</span> <span class="n">url</span> <span class="ow">in</span> <span class="n">url_pod</span><span class="p">:</span>

        <span class="c1"># If we&#39;ve fetched this url already, skip it</span>
        <span class="k">if</span> <span class="n">url_pod</span><span class="p">[</span><span class="n">url</span><span class="p">][</span><span class="s1">&#39;done&#39;</span><span class="p">]:</span>
            <span class="k">continue</span>

        <span class="c1"># If we&#39;ve tried this url too many times, skip it</span>
        <span class="k">if</span> <span class="n">url_pod</span><span class="p">[</span><span class="n">url</span><span class="p">][</span><span class="s1">&#39;tries&#39;</span><span class="p">]</span> <span class="o">&gt;</span> <span class="mi">3</span><span class="p">:</span>
            <span class="k">continue</span>

        <span class="c1"># Record that an attempt is being made to crawl this url</span>
        <span class="n">url_pod</span><span class="p">[</span><span class="n">url</span><span class="p">][</span><span class="s1">&#39;tries&#39;</span><span class="p">]</span> <span class="o">+=</span> <span class="mi">1</span>

        <span class="c1"># Attempt to crawl the url, move on if we don&#39;t succeed</span>
        <span class="n">success</span><span class="p">,</span> <span class="n">found_links</span> <span class="o">=</span> <span class="n">crawl</span><span class="p">(</span><span class="n">url</span><span class="p">)</span>
        <span class="k">if</span> <span class="ow">not</span> <span class="n">success</span><span class="p">:</span>
            <span class="k">continue</span>

        <span class="c1"># Add the new links we found, and mark this url done</span>
        <span class="k">for</span> <span class="n">found_url</span> <span class="ow">in</span> <span class="n">found_urls</span><span class="p">:</span>
            <span class="k">if</span> <span class="n">url</span> <span class="ow">not</span> <span class="ow">in</span> <span class="n">url_pod</span><span class="p">:</span>
                <span class="n">url_pod</span><span class="p">[</span><span class="n">url</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="s1">&#39;tries&#39;</span><span class="p">:</span><span class="mi">0</span><span class="p">,</span> <span class="s1">&#39;done&#39;</span><span class="p">:</span><span class="bp">False</span><span class="p">}</span>
        <span class="n">url_pod</span><span class="p">[</span><span class="n">url</span><span class="p">][</span><span class="s1">&#39;done&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="bp">True</span>
</pre></div>
</div>
<p>As you can see, we use the <a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a> to keep track of URLs as they are discovered,
along with which ones have been fetched already, and how many times each one
has been tried.  Any time this program is started up, it will only attempt to
crawl URLs that haven&#8217;t yet been crawled successfully, while ignoring any that
have already been tried at least 3 times.</p>
<p>The <code class="docutils literal"><span class="pre">Tracker</span></code> provides some facilities to support this usecase.  All entries
in a <code class="docutils literal"><span class="pre">Tracker</span></code> are dictionaries that minimally have a <code class="docutils literal"><span class="pre">_done</span></code> flag that
defaults to <code class="docutils literal"><span class="pre">False</span></code>, a <code class="docutils literal"><span class="pre">_aborted</span></code> flag that also defaults to <code class="docutils literal"><span class="pre">False</span></code>, and
a <code class="docutils literal"><span class="pre">_tries</span></code> counter that defaults to <code class="docutils literal"><span class="pre">0</span></code>.  <code class="docutils literal"><span class="pre">Tracker</span></code>s have various
methods to help keep track of tasks, and let you iterate over only tasks that
aren&#8217;t done, aborted, or tried too many times.  Using a <code class="docutils literal"><span class="pre">Tracker</span></code>, the program
would look like this:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">crawl</span><span class="p">(</span><span class="n">seed_url</span><span class="p">):</span>

    <span class="n">url_tracker</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">POD</span><span class="p">(</span><span class="s1">&#39;urls.tracker&#39;</span><span class="p">,</span> <span class="n">max_tries</span><span class="o">=</span><span class="mi">3</span><span class="p">)</span>
    <span class="n">url_tracker</span><span class="o">.</span><span class="n">add_if_absent</span><span class="p">(</span><span class="n">seed_url</span><span class="p">)</span>

    <span class="k">for</span> <span class="n">url</span> <span class="ow">in</span> <span class="n">url_tracker</span><span class="o">.</span><span class="n">try_keys</span><span class="p">():</span>

        <span class="c1"># Attempt to crawl the url, move on if we don&#39;t succeed</span>
        <span class="n">success</span><span class="p">,</span> <span class="n">found_links</span> <span class="o">=</span> <span class="n">crawl</span><span class="p">(</span><span class="n">url</span><span class="p">)</span>
        <span class="k">if</span> <span class="ow">not</span> <span class="n">success</span><span class="p">:</span>
            <span class="k">continue</span>

        <span class="c1"># Add the new links we found, and mark this url done</span>
        <span class="n">url_tracker</span><span class="o">.</span><span class="n">add_many_if_absent</span><span class="p">(</span><span class="n">found_urls</span><span class="p">)</span>
        <span class="n">url_tracker</span><span class="o">.</span><span class="n">mark_done</span><span class="p">(</span><span class="n">url</span><span class="p">)</span>
</pre></div>
</div>
<p>In the above code block, the <code class="docutils literal"><span class="pre">try_keys()</span></code> iterator is used to iterate over
just the tasks that aren&#8217;t done, aborted, or already tried <code class="docutils literal"><span class="pre">max_tries</span></code> times,
while incrementing the <code class="docutils literal"><span class="pre">_tries</span></code> on each task that gets yielded.  The
<code class="docutils literal"><span class="pre">add_if_absent(key)</span></code> method is used to initialize a new task with zero tries,
but only if that task isn&#8217;t already in the Tracker.  The <code class="docutils literal"><span class="pre">mark_done(key)</span></code>
method is used to mark a task done.  See the Tracker reference for the other
convenience methods for tracking the progress of long-running programs.</p>
<p>Note that you can (and should!) use the <code class="docutils literal"><span class="pre">Tracker</span></code> to store other data related
to tasks&#8212;such as task outputs / results.  Just remember that the entry for
each task is a <code class="docutils literal"><span class="pre">dict</span></code> that minimally contain <code class="docutils literal"><span class="pre">_tries</span></code>, <code class="docutils literal"><span class="pre">_done</span></code>,
and <code class="docutils literal"><span class="pre">_aborted</span></code> keys, so don&#8217;t overwrite these with values that don&#8217;t make
sense!</p>
<div class="section" id="progresstracker-reference">
<span id="progtracker"></span><h2><code class="docutils literal"><span class="pre">ProgressTracker</span></code> reference<a class="headerlink" href="#progresstracker-reference" title="Permalink to this headline">¶</a></h2>
<dl class="class">
<dt id="tastypy.ProgressTracker">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">ProgressTracker</code><span class="sig-paren">(</span><em>path</em>, <em>max_tries=0</em>, <em>init={}</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em>, <em>clone=True</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker" title="Permalink to this definition">¶</a></dt>
<dd><p>A specialized subclass of <code class="docutils literal"><span class="pre">POD</span></code> for tracking tasks, whose values are
dicts representing whether the task has been done or aborted, and how many 
times it has been tried.</p>
<p>Transprantly aynchronizes to disk using files stored under <code class="docutils literal"><span class="pre">path</span></code>.  
Specify the maximum number of times a task should be tried using 
<code class="docutils literal"><span class="pre">max_tries</span></code>, which influences the behaviour of <a class="reference internal" href="#gates">gates</a> and <a class="reference internal" href="#iterators">iterators</a>.
If <code class="docutils literal"><span class="pre">max_tries</span></code> is <code class="docutils literal"><span class="pre">0</span></code> no limit is applied.</p>
<p>Optionally provide data to initialize (or update) the mapping using the
<code class="docutils literal"><span class="pre">init</span></code> parameter.  The argument should be an iterable of key-value tuples
or should implement <code class="docutils literal"><span class="pre">iteritems()</span></code> yielding such an iterable.  This is
equivalent to calling <code class="docutils literal"><span class="pre">update(init_arg)</span></code> after creating the <code class="docutils literal"><span class="pre">POD</span></code>.</p>
<p>The JSON-formatted persistence files are gzipped if <code class="docutils literal"><span class="pre">gzipped</span></code> is
<code class="docutils literal"><span class="pre">True</span></code>.    Each file stores a number of values given by <code class="docutils literal"><span class="pre">file_size</span></code>.
Smaller values give faster synchronization but create more files.  Data is
automatically synchronized to disk when the number of &#8220;dirty&#8221; values
reaches <code class="docutils literal"><span class="pre">sync_at</span></code>, or if the program terminates.</p>
<p><code class="docutils literal"><span class="pre">ProgressTracker</span></code> supports all of the methods provided by
<a class="reference internal" href="#tastypy.PersistentOrderedDict" title="tastypy.PersistentOrderedDict"><code class="xref py py-class docutils literal"><span class="pre">POD</span></code></a>s, with one small
difference to the update function, and adds many methods for managing
tasks.</p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.update">
<code class="descname">update</code><span class="sig-paren">(</span><em>*mappings</em>, <em>**kwargs</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.update" title="Permalink to this definition">¶</a></dt>
<dd><p>Similar to <a class="reference internal" href="#tastypy.PersistentOrderedDict.update" title="tastypy.PersistentOrderedDict.update"><code class="xref py py-func docutils literal"><span class="pre">POD.update</span></code></a>, the
mappings and keyword arguments should provide key-value pairs, but the
values should be <code class="docutils literal"><span class="pre">dict</span></code>s.  The provided values are used to
<code class="docutils literal"><span class="pre">dict.update()</span></code> the existing values.  If the key didn&#8217;t exist,
<a class="reference internal" href="#tastypy.ProgressTracker.add" title="tastypy.ProgressTracker.add"><code class="xref py py-meth docutils literal"><span class="pre">add(key)</span></code></a> is called before attempting to mixin the
supplied value.  Therefore it is never necessary to provide special
keys (<code class="docutils literal"><span class="pre">'_done'</span></code>, <code class="docutils literal"><span class="pre">'_tries'</span></code>, <code class="docutils literal"><span class="pre">'_aborted'</span></code>) in update dictionaries
unless you actually want to mutate those values.</p>
</dd></dl>

</div></blockquote>
<p><code class="docutils literal"><span class="pre">ProgressTracker</span></code> adds the following methods to those provided by
<a class="reference internal" href="#tastypy.PersistentOrderedDict" title="tastypy.PersistentOrderedDict"><code class="xref py py-class docutils literal"><span class="pre">POD</span></code></a>:</p>
<p><em>Add tasks</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.add">
<code class="descname">add</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.add" title="Permalink to this definition">¶</a></dt>
<dd><p>Add a key to the tracker, initialized as not done, not aborted, and
with zero tries.  Attempting to add an already-existing key will raise
<code class="docutils literal"><span class="pre">tastypy.DuplicateKeyError</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.add_if_absent">
<code class="descname">add_if_absent</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.add_if_absent" title="Permalink to this definition">¶</a></dt>
<dd><p>Same as <a class="reference internal" href="#tastypy.ProgressTracker.add" title="tastypy.ProgressTracker.add"><code class="xref py py-meth docutils literal"><span class="pre">add()</span></code></a>, but don&#8217;t raise an error if the key exists,
just do nothing.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.add_many">
<code class="descname">add_many</code><span class="sig-paren">(</span><em>keys_iterable</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.add_many" title="Permalink to this definition">¶</a></dt>
<dd><p>Add each key yielded by keys iterator, initialized as not done, 
with zero tries.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.add_many_if_absent">
<code class="descname">add_many_if_absent</code><span class="sig-paren">(</span><em>keys_iterable</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.add_many_if_absent" title="Permalink to this definition">¶</a></dt>
<dd><p>Same as <a class="reference internal" href="#tastypy.ProgressTracker.add_many" title="tastypy.ProgressTracker.add_many"><code class="xref py py-meth docutils literal"><span class="pre">add_many()</span></code></a>, but silently skip keys that are already in
the tracker.</p>
</dd></dl>

</div></blockquote>
<p><em>Change the status of tasks</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.mark_done">
<code class="descname">mark_done</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.mark_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> as done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.mark_not_done">
<code class="descname">mark_not_done</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.mark_not_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> as not done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.increment_tries">
<code class="descname">increment_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.increment_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Increment the tries counter for <code class="docutils literal"><span class="pre">key</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.decrement_tries">
<code class="descname">decrement_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.decrement_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Decrement the tries counter for <code class="docutils literal"><span class="pre">key</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.reset_tries">
<code class="descname">reset_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.reset_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Reset the tries counter for <code class="docutils literal"><span class="pre">key</span></code> to zero.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.abort">
<code class="descname">abort</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.abort" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> aborted.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.unabort">
<code class="descname">unabort</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.unabort" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> not aborted.</p>
</dd></dl>

</div></blockquote>
<p><em>Check the status of tasks</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.done">
<code class="descname">done</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.done" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns <code class="docutils literal"><span class="pre">True</span></code> if <code class="docutils literal"><span class="pre">key</span></code> is done.  Does not raise <code class="docutils literal"><span class="pre">KeyError</span></code> if
key does not exist, just returns <code class="docutils literal"><span class="pre">False</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.tries">
<code class="descname">tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Retrieve the number of times <code class="docutils literal"><span class="pre">key</span></code> has been tried.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.aborted">
<code class="descname">aborted</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.aborted" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns <code class="docutils literal"><span class="pre">True</span></code> if <code class="docutils literal"><span class="pre">key</span></code> was aborted.</p>
</dd></dl>

</div></blockquote>
<p id="gates"><em>Gates to decide if a task should be done</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.should_do">
<code class="descname">should_do</code><span class="sig-paren">(</span><em>key</em>, <em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.should_do" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns <code class="docutils literal"><span class="pre">True</span></code> if <code class="docutils literal"><span class="pre">key</span></code> is not done, not aborted, and not tried
more than <code class="docutils literal"><span class="pre">max_tries</span></code> times.  If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then
return <code class="docutils literal"><span class="pre">True</span></code> for keys that would otherwise return <code class="docutils literal"><span class="pre">False</span></code> only
because they are aborted.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.should_do_add">
<code class="descname">should_do_add</code><span class="sig-paren">(</span><em>key</em>, <em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.should_do_add" title="Permalink to this definition">¶</a></dt>
<dd><p>Similar to <a class="reference internal" href="#tastypy.ProgressTracker.should_do" title="tastypy.ProgressTracker.should_do"><code class="xref py py-meth docutils literal"><span class="pre">should_do()</span></code></a>, but if the key doesn&#8217;t exist, it will
be added and <code class="docutils literal"><span class="pre">True</span></code> will be returned.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.should_try">
<code class="descname">should_try</code><span class="sig-paren">(</span><em>key</em>, <em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.should_try" title="Permalink to this definition">¶</a></dt>
<dd><p>Similar to <a class="reference internal" href="#tastypy.ProgressTracker.should_do" title="tastypy.ProgressTracker.should_do"><code class="xref py py-meth docutils literal"><span class="pre">should_do()</span></code></a>, but increments the number of tries on
keys for which <code class="docutils literal"><span class="pre">True</span></code> will be returned.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.should_try_add">
<code class="descname">should_try_add</code><span class="sig-paren">(</span><em>key</em>, <em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.should_try_add" title="Permalink to this definition">¶</a></dt>
<dd><p>Similar to <a class="reference internal" href="#tastypy.ProgressTracker.should_try" title="tastypy.ProgressTracker.should_try"><code class="xref py py-meth docutils literal"><span class="pre">should_try()</span></code></a>, but if the key doesn&#8217;t exist, it will
be added and <code class="docutils literal"><span class="pre">True</span></code> will be returned.</p>
</dd></dl>

</div></blockquote>
<p id="iterators"><em>Iterate over tasks to be done</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.todo_items">
<code class="descname">todo_items</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.todo_items" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator of key-value tuples for keys that are not done, not
aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.  
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted items that meet the
other criteria.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.todo_keys">
<code class="descname">todo_keys</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.todo_keys" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator over keys that are not done, not
aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.  
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted keys that meet the
other criteria.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.todo_values">
<code class="descname">todo_values</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.todo_values" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator over values corresponding to keys that are not
done, not aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted values that meet the
other criteria.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.try_items">
<code class="descname">try_items</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.try_items" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator of key-value tuples for keys that are not
done, not aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted items that meet the
other criteria.
Increment the number of tries for each key yielded.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.try_keys">
<code class="descname">try_keys</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.try_keys" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator over keys that are not
done, not aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted keys that meet the
other criteria.
Increment the number of tries for each key yielded.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.try_values">
<code class="descname">try_values</code><span class="sig-paren">(</span><em>allow_aborted=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.try_values" title="Permalink to this definition">¶</a></dt>
<dd><p>Provides an iterator over values corresponding to keys that are not
done, not aborted, and have been tried fewer than <code class="docutils literal"><span class="pre">max_tries</span></code> times.
If <code class="docutils literal"><span class="pre">allow_aborted</span></code> is <code class="docutils literal"><span class="pre">True</span></code>, then yield aborted values that meet the
other criteria.
Increment the number of tries for the key corresponding to each value
yeilded.
Iteration order matches the order in which keys were added.</p>
</dd></dl>

</div></blockquote>
<p><em>Check the status of all tasks</em></p>
<blockquote>
<div><dl class="method">
<dt id="tastypy.ProgressTracker.num_done">
<code class="descname">num_done</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.num_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the number of entries that are done.  
Recall that <code class="docutils literal"><span class="pre">len(tracker)</span></code> returns the total number of entries.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.fraction_done">
<code class="descname">fraction_done</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.fraction_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the fraction (between 0 and 1) of entries that are done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_done">
<code class="descname">percent_done</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries done,
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in the
percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_not_done">
<code class="descname">percent_not_done</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_not_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries <em>not</em> done,
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in the
percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.num_tried">
<code class="descname">num_tried</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.num_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the number of entries that have been tried at least once.
Recall that <code class="docutils literal"><span class="pre">len(tracker)</span></code> returns the total number of entries.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.fraction_tried">
<code class="descname">fraction_tried</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.fraction_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the fraction (between 0 and 1) of entries that have been tried
at least once.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_tried">
<code class="descname">percent_tried</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries tried at least
once, E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_not_tried">
<code class="descname">percent_not_tried</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_not_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries tried at least
once, E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.num_aborted">
<code class="descname">num_aborted</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.num_aborted" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the number of entries that have been aborted.
Recall that <code class="docutils literal"><span class="pre">len(tracker)</span></code> returns the total number of entries.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.fraction_aborted">
<code class="descname">fraction_aborted</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.fraction_aborted" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the fraction (between 0 and 1) of entries that have been
aborted.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_aborted">
<code class="descname">percent_aborted</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_aborted" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries aborted, 
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.ProgressTracker.percent_not_aborted">
<code class="descname">percent_not_aborted</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.ProgressTracker.percent_not_aborted" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries aborted, 
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

</div></blockquote>
</dd></dl>

</div>
</div>
<div class="section" id="multiprocessing-with-sharedprogresstrackers">
<span id="sharedtracker"></span><span id="sharedprogresstracker"></span><h1>Multiprocessing with <code class="docutils literal"><span class="pre">SharedProgressTracker</span></code>s<a class="headerlink" href="#multiprocessing-with-sharedprogresstrackers" title="Permalink to this headline">¶</a></h1>
<p>Just as you can distribute a <code class="docutils literal"><span class="pre">SharedPOD</span></code> to multiple processes, you can
distribute a <code class="docutils literal"><span class="pre">SharedTracker</span></code> (short alias for <code class="docutils literal"><span class="pre">SharedProgressTracker</span></code>) to
multiple processes.</p>
<p>The same basic usage applies.  A single <code class="docutils literal"><span class="pre">SharedTracker</span></code> should be made and
distributed to child processes using a <code class="docutils literal"><span class="pre">Queue</span></code>, <code class="docutils literal"><span class="pre">Pipe</span></code>, or in the arguments
to a <code class="docutils literal"><span class="pre">Process</span></code> or <code class="docutils literal"><span class="pre">Pool</span></code>.  All of the <code class="docutils literal"><span class="pre">Tracker</span></code>’s own methods for
updating
the state of a task (such as <code class="docutils literal"><span class="pre">mark_done(key)</span></code> or <code class="docutils literal"><span class="pre">increment_tries(key)</span></code>)
are guaranteed to synchronized properly to disk.
If you want to add or mutate your own data stored on a task, then as for
<a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">POD</span></code></a>s, perform mutation operations on the <code class="docutils literal"><span class="pre">Tracker.set</span></code> attribute, not on
the <code class="docutils literal"><span class="pre">Tracker</span></code> itself.  See <a class="reference internal" href="#writetosharedpods">Writing to <code class="docutils literal"><span class="pre">SharedPOD</span></code>s</a> for an explanation.</p>
<div class="section" id="sharedprogresstracker-reference">
<h2><code class="docutils literal"><span class="pre">SharedProgressTracker</span></code> reference<a class="headerlink" href="#sharedprogresstracker-reference" title="Permalink to this headline">¶</a></h2>
<dl class="class">
<dt id="tastypy.SharedTracker">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">SharedTracker</code><a class="headerlink" href="#tastypy.SharedTracker" title="Permalink to this definition">¶</a></dt>
<dd><p>Alias for <a class="reference internal" href="#tastypy.SharedProgressTracker" title="tastypy.SharedProgressTracker"><code class="xref py py-class docutils literal"><span class="pre">SharedProgressTracker</span></code></a>.</p>
</dd></dl>

<dl class="class">
<dt id="tastypy.SharedProgressTracker">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">SharedProgressTracker</code><span class="sig-paren">(</span><em>path</em>, <em>max_tries=0</em>, <em>init={}</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.SharedProgressTracker" title="Permalink to this definition">¶</a></dt>
<dd><p>A multiprocessing-safe progress tracker that can be shared by many
processes.  Like a <code class="docutils literal"><span class="pre">SharedPOD</span></code>, but meant for tracking tasks&#8212;each value
is a dict representing whether the corresponding task has been done and how
many times it has been tried.</p>
<p>Data is syncronized to disk in files under <code class="docutils literal"><span class="pre">path</span></code>.  Specify the maximum
number of times a task should be tried using <code class="docutils literal"><span class="pre">max_tries</span></code>, which
influences which tasks are tried under certain iteration modes.  If
<code class="docutils literal"><span class="pre">max_tries</span></code> is <code class="docutils literal"><span class="pre">0</span></code> no limit is applied.</p>
<p>Provide initial data to initialize (or update) the mapping using the
<code class="docutils literal"><span class="pre">init</span></code> parameter.  The argument should be an iterable of key-value tuples
or should implement <code class="docutils literal"><span class="pre">iteritems()</span></code> yielding such an iterable.  This is
equivalent to calling <code class="docutils literal"><span class="pre">update(init_arg)</span></code> after creating the
<code class="docutils literal"><span class="pre">SharedTracker</span></code>.</p>
<p>The JSON-formatted persistence files are gzipped if <code class="docutils literal"><span class="pre">gzipped</span></code> is
<code class="docutils literal"><span class="pre">True</span></code>.    Each file stores a number of values given by <code class="docutils literal"><span class="pre">file_size</span></code>.
Smaller values give faster synchronization but create more files.  Data is
automatically synchronized to disk when the number of &#8220;dirty&#8221; values
reaches <code class="docutils literal"><span class="pre">sync_at</span></code>, or if the program terminates.</p>
<p>Supports all methods of <a class="reference internal" href="#progtracker"><code class="docutils literal"><span class="pre">ProgressTracker</span></code></a> and <a class="reference internal" href="#sharedpodreference"><code class="docutils literal"><span class="pre">SharedPersistentOrderedDict</span></code></a>.</p>
</dd></dl>

</div>
</div>


          </div>
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
  <h3><a href="#">Table Of Contents</a></h3>
  <ul>
<li><a class="reference internal" href="#">tastypy</a></li>
<li><a class="reference internal" href="#install">Install</a></li>
<li><a class="reference internal" href="#pod"><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code></a><ul>
<li><a class="reference internal" href="#json-general-simple-secure">JSON &#8211; general, simple, secure</a></li>
<li><a class="reference internal" href="#synchronization">Synchronization</a><ul>
<li><a class="reference internal" href="#can-data-be-lost">Can data be lost?</a></li>
<li><a class="reference internal" href="#can-i-manually-control-synchronization">Can I manually control synchronization?</a></li>
<li><a class="reference internal" href="#opening-multiple-pods-at-same-location-is-safe">Opening multiple <code class="docutils literal"><span class="pre">POD</span></code>s at same location is safe</a></li>
</ul>
</li>
<li><a class="reference internal" href="#persistentordereddict-reference"><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code> reference</a></li>
</ul>
</li>
<li><a class="reference internal" href="#multiprocessing-with-sharedpods">Multiprocessing with <code class="docutils literal"><span class="pre">SharedPOD</span></code>s</a><ul>
<li><a class="reference internal" href="#writing-to-shared-sharedpods">Writing to shared <code class="docutils literal"><span class="pre">SharedPOD</span></code>s</a></li>
<li><a class="reference internal" href="#avoiding-raciness">Avoiding raciness</a></li>
<li><a class="reference internal" href="#sharedpod-multiprocessing-example"><code class="docutils literal"><span class="pre">SharedPOD</span></code> multiprocessing example</a></li>
<li><a class="reference internal" href="#sharedpersistentordereddict-reference">SharedPersistentOrderedDict reference</a></li>
</ul>
</li>
<li><a class="reference internal" href="#tracker"><code class="docutils literal"><span class="pre">ProgressTracker</span></code></a><ul>
<li><a class="reference internal" href="#progresstracker-reference"><code class="docutils literal"><span class="pre">ProgressTracker</span></code> reference</a></li>
</ul>
</li>
<li><a class="reference internal" href="#multiprocessing-with-sharedprogresstrackers">Multiprocessing with <code class="docutils literal"><span class="pre">SharedProgressTracker</span></code>s</a><ul>
<li><a class="reference internal" href="#sharedprogresstracker-reference"><code class="docutils literal"><span class="pre">SharedProgressTracker</span></code> reference</a></li>
</ul>
</li>
</ul>

  <div role="note" aria-label="source link">
    <h3>This Page</h3>
    <ul class="this-page-menu">
      <li><a href="_sources/index.txt"
            rel="nofollow">Show Source</a></li>
    </ul>
   </div>
<div id="searchbox" style="display: none" role="search">
  <h3>Quick search</h3>
    <form class="search" action="search.html" method="get">
      <div><input type="text" name="q" /></div>
      <div><input type="submit" value="Go" /></div>
      <input type="hidden" name="check_keywords" value="yes" />
      <input type="hidden" name="area" value="default" />
    </form>
</div>
<script type="text/javascript">$('#searchbox').show(0);</script>
        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="related" role="navigation" aria-label="related navigation">
      <h3>Navigation</h3>
      <ul>
        <li class="right" style="margin-right: 10px">
          <a href="genindex.html" title="General Index"
             >index</a></li>
        <li class="right" >
          <a href="py-modindex.html" title="Python Module Index"
             >modules</a> |</li>
        <li class="nav-item nav-item-0"><a href="#">tastypy 0.0.0 documentation</a> &#187;</li> 
      </ul>
    </div>
    <div class="footer" role="contentinfo">
        &#169; Copyright 2017, Edward Newell.
      Created using <a href="http://sphinx-doc.org/">Sphinx</a> 1.4.6.
    </div>
  </body>
</html>