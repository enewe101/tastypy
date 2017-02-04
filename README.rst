<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">


<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    
    <title>tastypy &#8212; tastypy 0.0.0 documentation</title>
    
    <link rel="stylesheet" href="_static/alabaster.css" type="text/css" />
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
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  </head>
  <body role="document">
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          <div class="body" role="main">
            
  <div class="section" id="module-tastypy">
<span id="tastypy"></span><h1>tastypy<a class="headerlink" href="#module-tastypy" title="Permalink to this headline">¶</a></h1>
<p><a href="#id2"><span class="problematic" id="id3">|copy|</span></a> <code class="docutils literal"><span class="pre">tastypy</span></code> let&#8217;s you easily interact with dict-like objects that are
&#8220;traslucently&#8221; persisted to disk.  It&#8217;s designed to be used in cases where you
need database-like functionality but don&#8217;t want to actually create a database.
A common use-case is in long-running programs, where you want to keep track of
progress so that you can pick up where you left off when you stop the program
or it crashes.</p>
</div>
<div class="section" id="install">
<h1>Install<a class="headerlink" href="#install" title="Permalink to this headline">¶</a></h1>
<div class="highlight-bash"><div class="highlight"><pre><span></span>pip install tastypy
</pre></div>
</div>
</div>
<div class="section" id="persistentordereddict">
<h1><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code><a class="headerlink" href="#persistentordereddict" title="Permalink to this headline">¶</a></h1>
<p>The <code class="docutils literal"><span class="pre">tastypy.POD</span></code> (which is the short spelling for
<code class="docutils literal"><span class="pre">tastypy.PersistentOrderedDict</span></code>) is a dict-like datastructure that
transparently synchronizes to disk.  Supply a path when creating a <code class="docutils literal"><span class="pre">POD</span></code>,
and the data will be peristed using files at that location:</p>
<div class="highlight-bash"><div class="highlight"><pre><span></span>&gt;&gt;&gt; from tastypy import POD
&gt;&gt;&gt; <span class="nv">my_pod</span> <span class="o">=</span> POD<span class="o">(</span><span class="s1">&#39;path/to/my.pod&#39;</span><span class="o">)</span>
&gt;&gt;&gt; my_pod<span class="o">[</span><span class="s1">&#39;foo&#39;</span><span class="o">]</span> <span class="o">=</span> <span class="s1">&#39;bar&#39;</span>
&gt;&gt;&gt; exit<span class="o">()</span>
</pre></div>
</div>
<p>Data stored <code class="docutils literal"><span class="pre">POD</span></code>s is preserved after the program exits:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="kn">from</span> <span class="nn">tastypy</span> <span class="kn">import</span> <span class="n">POD</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span> <span class="o">=</span> <span class="n">POD</span><span class="p">(</span><span class="s1">&#39;path/to/my.pod&#39;</span><span class="p">)</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span>
<span class="go">bar</span>
</pre></div>
</div>
<div class="section" id="json-only">
<h2>JSON only<a class="headerlink" href="#json-only" title="Permalink to this headline">¶</a></h2>
<p>JSON is used as the serializaton for data in <code class="docutils literal"><span class="pre">POD</span></code>s, so only JSON-serializable
data can be stored.  JSON is quite general, and represents the most common data
types naturally, but there are some limitations.  The choice to use JSON
reflects the goal of keeping the design simple, having a human-readable format
for the persistence files, and avoiding security issues (which would arise if
using <code class="docutils literal"><span class="pre">pickle</span></code>).</p>
<p>As a consequence, data stored in <code class="docutils literal"><span class="pre">POD</span></code>s must be JSON-serializable.  This
means using integers, strings, as well as integers and strings in arbitrarily
nested lists and dictionaries.  The <code class="docutils literal"><span class="pre">POD</span></code>’s keys, and the keys of
dictionaries in values of a <code class="docutils literal"><span class="pre">POD</span></code>, will be converted to strings.  All strings
are converted to unicode by serialization.  Tuples can be used, but will be
serialized as lists.</p>
<p>Some of these restrictions could be relaxed by writing a for-purpose
serializer, but that would limit interoperability and simplicity, expecially
for people familiar with Python&#8217;s <code class="docutils literal"><span class="pre">json</span></code> builtin.</p>
<p>To illustrate some of the gotcha&#8217;s</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;integer-key&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">{</span><span class="mi">1</span><span class="p">:</span><span class="s1">&#39;bar&#39;</span><span class="p">}</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;tuple&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">(</span><span class="s1">&#39;baz&#39;</span><span class="p">,</span> <span class="mi">42</span><span class="p">)</span>
<span class="gp">&gt;&gt;&gt; </span><span class="nb">exit</span><span class="p">()</span>
</pre></div>
</div>
<p>Notice that the key <code class="docutils literal"><span class="pre">1</span></code> is converted to a string (though <code class="docutils literal"><span class="pre">42</span></code> remains as a
number), and the tuple is converted to a list.  That&#8217;s just how <code class="docutils literal"><span class="pre">json</span></code> works.</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;foo&#39;</span><span class="p">]</span>
<span class="go">{u&#39;1&#39;: u&#39;bar&#39;}</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;tuple&#39;</span><span class="p">]</span>
<span class="go">[u&#39;baz&#39;, 42]</span>
</pre></div>
</div>
</div>
</div>
<div class="section" id="synchronization">
<h1>Synchronization<a class="headerlink" href="#synchronization" title="Permalink to this headline">¶</a></h1>
<p>The <code class="docutils literal"><span class="pre">POD</span></code> was designed so that in most cases, synchronization between disk
and memory is transparent.  The <code class="docutils literal"><span class="pre">POD</span></code> keeps track of which keys may have gone
out of sync with the disk, and periodically synchronizes
(<a class="reference internal" href="#customize-synchronization">customize synchronization</a>).  A <code class="docutils literal"><span class="pre">POD</span></code> will always synchronize if it is
destroyed or if the program exits or crashes, as long as the Python interpreter
doesn&#8217;t segfault, which is fairly rare.</p>
<p>Any time you access keys, whether during assignment or some other manipulation,
the <code class="docutils literal"><span class="pre">POD</span></code> considers that key to be <em>dirty</em>.  Once 1000 keys are dirty, the
<code class="docutils literal"><span class="pre">POD</span></code> will synchronize.  It&#8217;s possible to circumvent synchronization if you
create another reference to the contents of a key, and then interact with it
via that reference.  But as long as you don&#8217;t do that, your data will be kept
in sync.</p>
<p>So, the following will be properly synchronized:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">{}</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">][</span><span class="s1">&#39;subkey1&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="mi">1</span> <span class="c1"># __setitem__ called on dict, but only</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">][</span><span class="s1">&#39;subkey2&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">[]</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">][</span><span class="s1">&#39;subkey2&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="mi">1</span><span class="p">)</span>
</pre></div>
</div>
<p>However, the following may not synchronize correctly:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">value</span> <span class="o">=</span> <span class="p">{}</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;key&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="n">value</span>   <span class="c1"># This is ok</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">value</span><span class="p">[</span><span class="s1">&#39;subkey1&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="s1">&#39;foo&#39;</span><span class="p">)</span>  <span class="c1"># not seen, due to use of non-POD ref</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">value</span><span class="p">[</span><span class="s1">&#39;subkey2&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="s1">&#39;baz&#39;</span>    <span class="c1"># also not seen.</span>
</pre></div>
</div>
<p>A good rule of thumb is that a <code class="docutils literal"><span class="pre">POD</span></code> is not aware of lines of code in which
it&#8217;s name doesn&#8217;t appear.</p>
<dl class="class">
<dt id="tastypy.POD">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">POD</code><a class="headerlink" href="#tastypy.POD" title="Permalink to this definition">¶</a></dt>
<dd><p>Alias for PersistentOrderedDict</p>
</dd></dl>

<dl class="class">
<dt id="tastypy.PersistentOrderedDict">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">PersistentOrderedDict</code><span class="sig-paren">(</span><em>path</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict" title="Permalink to this definition">¶</a></dt>
<dd><p>A key-value mapping container that synchronizes transparently to disk at
the location given by <code class="docutils literal"><span class="pre">path</span></code>.  Data will persist after program
interruption and can be accessed by creating a new instance directed at the
same path.  The JSON-formatted persistence files are gzipped if <code class="docutils literal"><span class="pre">gzipped</span></code> 
is <code class="docutils literal"><span class="pre">True</span></code>.  Each files stores a number of values given by
<code class="docutils literal"><span class="pre">file_size</span></code>.  Smaller values give faster synchronization but create 
more files.  Synchronization automatically occurs when the number of
values that are out of sync with those stored on disk reaches <code class="docutils literal"><span class="pre">sync_at</span></code>
or if the program terminates.</p>
<dl class="method">
<dt id="tastypy.PersistentOrderedDict.keys">
<code class="descname">keys</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.keys" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of the keys, matching the order in which they were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.values">
<code class="descname">values</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.values" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of the <code class="docutils literal"><span class="pre">POD</span></code>&#8216;s values.  The order of values is
guaranteed to match the order of <code class="docutils literal"><span class="pre">self.keys()</span></code></p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.items">
<code class="descname">items</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.items" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a list of key-value pairs, matching the order in which keys were 
added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.iteritems">
<code class="descname">iteritems</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.iteritems" title="Permalink to this definition">¶</a></dt>
<dd><p>Return an iterator that yields key-value pairs, matching the order
in which keys were added.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.mark_dirty">
<code class="descname">mark_dirty</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.mark_dirty" title="Permalink to this definition">¶</a></dt>
<dd><p>Force <code class="docutils literal"><span class="pre">key</span></code> to be considered out of sync.  The data associated to
this key will be re-written to file during the next synchronization.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.update">
<code class="descname">update</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.update" title="Permalink to this definition">¶</a></dt>
<dd><p>Force <code class="docutils literal"><span class="pre">key</span></code> to be synchronized to disk immediately.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.sync">
<code class="descname">sync</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.sync" title="Permalink to this definition">¶</a></dt>
<dd><p>Force synchronization of all &#8220;dirty&#8221; values (which have changed from
the values stored on disk).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.hold">
<code class="descname">hold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.hold" title="Permalink to this definition">¶</a></dt>
<dd><p>Suspend automatic synchronization to disk.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.unhold">
<code class="descname">unhold</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.unhold" title="Permalink to this definition">¶</a></dt>
<dd><p>Resume automatic synchronization to disk.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.revert">
<code class="descname">revert</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.revert" title="Permalink to this definition">¶</a></dt>
<dd><p>Load values from disk into memory, discarding any unsynchronized changes.
Forget any files have been marked &#8220;dirty&#8221;.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy.PersistentOrderedDict.copy">
<code class="descname">copy</code><span class="sig-paren">(</span><em>path</em>, <em>file_size</em>, <em>gzipped=False</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy.PersistentOrderedDict.copy" title="Permalink to this definition">¶</a></dt>
<dd><p>Synchronize the POD to a new location on disk specified by <code class="docutils literal"><span class="pre">path</span></code>.  
Future synchronization will also take place at this new location.  
The old location on disk will be left as-is and will no longer be 
synchronized.  When synchronizing store <code class="docutils literal"><span class="pre">file_size</span></code> number of
values per file, and keep files gzipped if <code class="docutils literal"><span class="pre">gzipped</span></code> is <code class="docutils literal"><span class="pre">True</span></code>.
This is not affected by <code class="docutils literal"><span class="pre">hold()</span></code>.</p>
</dd></dl>

</dd></dl>

</div>
<div class="section" id="progresstracker">
<h1><code class="docutils literal"><span class="pre">ProgressTracker</span></code><a class="headerlink" href="#progresstracker" title="Permalink to this headline">¶</a></h1>
<p>The <code class="docutils literal"><span class="pre">tastypy.Tracker</span></code> (short for <code class="docutils literal"><span class="pre">tastypy.ProgressTracker</span></code>) is a subclass
of the <code class="docutils literal"><span class="pre">POD</span></code> that helps track the progress of long-running programs that
involve performing many repetative tasks, so that the program can pick up where
it left off in case of a crash.</p>
<p>Each value in a tracker represents one task and stores whether that task is
done, and how many times it has been tried, as well as any other data you might
want to associate to it.</p>
<p>Typically for this kind of lon-running program, you want to attempt any tasks
that have not been done and retry tasks that were not completed successfully, but
only up to some maximum number of attempts.</p>
<p>For illustrative purposes, the next example shows how the tracker helps with
this, but we&#8217;ll see a more concise way to do it in a moment.</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">do_work</span><span class="p">(</span><span class="n">work_queue</span><span class="p">):</span>

    <span class="n">tracker</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">Tracker</span><span class="p">(</span><span class="s1">&#39;path/to/my.tracker&#39;</span><span class="p">)</span>

    <span class="k">for</span> <span class="n">task</span> <span class="ow">in</span> <span class="n">work_queue</span><span class="p">:</span>

        <span class="c1"># If the task has be done, skip it</span>
        <span class="k">if</span> <span class="n">tracker</span><span class="o">.</span><span class="n">check</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">):</span>
            <span class="k">continue</span>

        <span class="c1"># Add the task if it is not already in the tracker</span>
        <span class="k">if</span> <span class="n">task</span><span class="o">.</span><span class="n">name</span> <span class="ow">not</span> <span class="ow">in</span> <span class="n">tracker</span><span class="p">:</span>
            <span class="n">tracker</span><span class="o">.</span><span class="n">add</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">)</span>

        <span class="c1"># Skip this task if we&#39;ve tried it too many times</span>
        <span class="k">if</span> <span class="n">tracker</span><span class="o">.</span><span class="n">tries</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">)</span> <span class="o">&gt;</span> <span class="n">MAX_TRIES</span><span class="p">:</span>
            <span class="k">continue</span>

        <span class="c1"># Now attempt the task</span>
        <span class="n">result</span> <span class="o">=</span> <span class="n">do_work</span><span class="p">(</span><span class="n">task</span><span class="p">)</span>

        <span class="c1"># If it succeeded, mark the task done, and record results</span>
        <span class="k">if</span> <span class="n">result</span><span class="o">.</span><span class="n">success</span><span class="p">:</span>
            <span class="n">tracker</span><span class="o">.</span><span class="n">mark_done</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">)</span>
            <span class="n">tracker</span><span class="p">[</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">][</span><span class="s1">&#39;result&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="n">result</span>
</pre></div>
</div>
<p>We can factor out some of the repetitive logic using other functions on the
tracker.  First, we can let the tracker know how many times we care to try a
task before giving up.  And second, we can make use of the function
<code class="docutils literal"><span class="pre">try_it(key)</span></code>.
This packs several steps in the logic we saw in the last example together:</p>
<blockquote>
<div><ul class="simple">
<li>It checks if the task exists in the tracker, if not, it adds it</li>
<li>It checks if the task is done, if yes, it returns <code class="docutils literal"><span class="pre">False</span></code></li>
<li>It checks if the task has already been tried the maximum number of times,
and if so, it also returns <code class="docutils literal"><span class="pre">False</span></code></li>
<li>Otherwise it returns true, and it increments the counter for the number
of times the task has been tried</li>
</ul>
</div></blockquote>
<p>The following function will process each task in a queue, keep track of
attempts, and skip tasks that have been done or which have been attempted too
many times, and record results from each task</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">do_work</span><span class="p">(</span><span class="n">work_queue</span><span class="p">):</span>

    <span class="n">tracker</span> <span class="o">=</span> <span class="n">tastypy</span><span class="o">.</span><span class="n">Tracker</span><span class="p">(</span><span class="s1">&#39;path/to/my.tracker&#39;</span><span class="p">,</span> <span class="n">max_tries</span><span class="o">=</span><span class="mi">3</span><span class="p">)</span>

    <span class="k">for</span> <span class="n">task</span> <span class="ow">in</span> <span class="n">work_queue</span><span class="p">:</span>

        <span class="c1"># Skip tasks that are done or tried too many times</span>
        <span class="k">if</span> <span class="ow">not</span> <span class="n">tracker</span><span class="o">.</span><span class="n">try_it</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">):</span>
            <span class="k">continue</span>

        <span class="c1"># Do the work</span>
        <span class="n">do_work</span><span class="p">(</span><span class="n">task</span><span class="p">)</span>

        <span class="c1"># Mark the task done and record results</span>
        <span class="n">tracker</span><span class="o">.</span><span class="n">mark_done</span><span class="p">(</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">)</span>
        <span class="n">tracker</span><span class="p">[</span><span class="n">task</span><span class="o">.</span><span class="n">name</span><span class="p">][</span><span class="s1">&#39;result&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="n">result</span>
</pre></div>
</div>
<p>This tends to be the most common usecase, although the tracker is versatile,
and is just a <code class="docutils literal"><span class="pre">POD</span></code> with extra methods.  See the full listing of methods
below. The value stored for each task is a <code class="docutils literal"><span class="pre">dict</span></code> with two special keys used
to keep track of the status: <code class="docutils literal"><span class="pre">_tries</span></code> and <code class="docutils literal"><span class="pre">_done</span></code>.  You can attach any
other values, but of course you&#8217;ll want to avoid overwriting or deleting these
keys.</p>
<dl class="class">
<dt id="tastypy._ProgressTracker">
<em class="property">class </em><code class="descclassname">tastypy.</code><code class="descname">_ProgressTracker</code><span class="sig-paren">(</span><em>path</em>, <em>gzipped=False</em>, <em>file_size=1000</em>, <em>sync_at=1000</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker" title="Permalink to this definition">¶</a></dt>
<dd><p>ProgressTracker(path)</p>
<p>A specialized subclass of POD whose values are all dictionaries
representing the status of tasks or items to be &#8220;done&#8221;, with convenience
functions for keeping track of the number of times items have been tried.
Synchronizing disk using files stored under <code class="docutils literal"><span class="pre">path</span></code>.  If <code class="docutils literal"><span class="pre">gzipped</span></code> is
<code class="docutils literal"><span class="pre">True</span></code>, then gzip the persistence files.  <code class="docutils literal"><span class="pre">lines_per_file</span></code> determines
how many of the <code class="docutils literal"><span class="pre">Tracker</span></code>’s values are stored in a single before creating
a new one.</p>
<dl class="method">
<dt id="tastypy._ProgressTracker.add">
<code class="descname">add</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.add" title="Permalink to this definition">¶</a></dt>
<dd><p>Add a key to the tracker, initialized as not done, with zero tries.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.add_if_absent">
<code class="descname">add_if_absent</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.add_if_absent" title="Permalink to this definition">¶</a></dt>
<dd><p>Same as add, but don&#8217;t raise an error if the key exists, just do nothing.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.check">
<code class="descname">check</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.check" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns <code class="docutils literal"><span class="pre">True</span></code> if <code class="docutils literal"><span class="pre">key</span></code> is done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.check_or_add">
<code class="descname">check_or_add</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.check_or_add" title="Permalink to this definition">¶</a></dt>
<dd><p>checks if there is an entry for key already marked as done
(returns True if so).  If no entry exists for key, it makes one
and provides it with a defualt value of _done:False and _tries:0</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.decrement_tries">
<code class="descname">decrement_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.decrement_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Decrement the tries counter for <code class="docutils literal"><span class="pre">key</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.fraction_done">
<code class="descname">fraction_done</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.fraction_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the fraction (between 0 and 1) of entries that are done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.fraction_tried">
<code class="descname">fraction_tried</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.fraction_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the fraction (between 0 and 1) of entries that have been tried
at least once.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.increment_tries">
<code class="descname">increment_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.increment_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Increment the tries counter for <code class="docutils literal"><span class="pre">key</span></code>.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.mark_done">
<code class="descname">mark_done</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.mark_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> as done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.mark_not_done">
<code class="descname">mark_not_done</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.mark_not_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Mark the <code class="docutils literal"><span class="pre">key</span></code> as not done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.num_done">
<code class="descname">num_done</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.num_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the number of entries that are done.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.num_tried">
<code class="descname">num_tried</code><span class="sig-paren">(</span><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.num_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Returns the number of entries that have been tried at least once.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.percent">
<code class="descname">percent</code><span class="sig-paren">(</span><em>fraction</em>, <em>decimals</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.percent" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage, corresponding to the
fraction given.  E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of 
decimals in the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.percent_done">
<code class="descname">percent_done</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.percent_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries done,
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in the
percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.percent_not_done">
<code class="descname">percent_not_done</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.percent_not_done" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries <em>not</em> done,
E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in the
percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.percent_not_tried">
<code class="descname">percent_not_tried</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.percent_not_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries tried at least
once, E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.percent_tried">
<code class="descname">percent_tried</code><span class="sig-paren">(</span><em>decimals=2</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.percent_tried" title="Permalink to this definition">¶</a></dt>
<dd><p>Return a string representing the percentage of entries tried at least
once, E.g.: <code class="docutils literal"><span class="pre">'34.70</span> <span class="pre">%'</span></code>.  Includes <code class="docutils literal"><span class="pre">decimal</span></code> number of decimals in
the percentage representation (default 2).</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.reset_tries">
<code class="descname">reset_tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.reset_tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Reset the tries counter for <code class="docutils literal"><span class="pre">key</span></code> to zero.</p>
</dd></dl>

<dl class="method">
<dt id="tastypy._ProgressTracker.tries">
<code class="descname">tries</code><span class="sig-paren">(</span><em>key</em><span class="sig-paren">)</span><a class="headerlink" href="#tastypy._ProgressTracker.tries" title="Permalink to this definition">¶</a></dt>
<dd><p>Retrieve the number of times <code class="docutils literal"><span class="pre">key</span></code> has been tried.</p>
</dd></dl>

</dd></dl>

<div class="section" id="customize-synchronization">
<span id="id1"></span><h2>Customize synchronization<a class="headerlink" href="#customize-synchronization" title="Permalink to this headline">¶</a></h2>
<p>In general, you should stick to</p>
<p>by assigning somethign to one of their keys.  For example, doing <code class="docutils literal"><span class="pre">my_pod['foo']</span>
<span class="pre">=</span> <span class="pre">'baz'</span></code> triggers <code class="docutils literal"><span class="pre">my_pod</span></code> to sync to disk.</p>
<p>This is accomplished within the <code class="docutils literal"><span class="pre">__setitem__</span></code> method of <code class="docutils literal"><span class="pre">POD</span></code>, so any
assignment to a key will trigger synchronization.</p>
<p>However, if you assign a mutable object to a <code class="docutils literal"><span class="pre">POD</span></code> there is no way for it to
know if you mutate <em>that</em> object.  For example:</p>
<div class="highlight-python"><div class="highlight"><pre><span></span><span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;mutable&#39;</span><span class="p">]</span> <span class="o">=</span> <span class="p">[</span><span class="mi">1</span><span class="p">,</span><span class="mi">2</span><span class="p">,</span><span class="mi">3</span><span class="p">]</span>     <span class="c1"># synchronization happens</span>
<span class="gp">&gt;&gt;&gt; </span><span class="n">my_pod</span><span class="p">[</span><span class="s1">&#39;mutable&#39;</span><span class="p">]</span><span class="o">.</span><span class="n">append</span><span class="p">(</span><span class="mi">4</span><span class="p">)</span>     <span class="c1"># no synchronization!</span>
</pre></div>
</div>
<p>To explicitly ask for a key to be synchronized, simply call
<code class="docutils literal"><span class="pre">my_pod.update(key)</span></code>.</p>
</div>
</div>
<div class="section" id="suspending-synchronization">
<h1>Suspending synchronization<a class="headerlink" href="#suspending-synchronization" title="Permalink to this headline">¶</a></h1>
<p>If you are making many changes to a <code class="docutils literal"><span class="pre">POD</span></code>, it is often best to suspend
synchronization, make all of the changes, then synchronize afterward.</p>
<p>To temporarily turn off automatic synchronization, call <code class="docutils literal"><span class="pre">POD.hold()</span></code>.
For a on-time synchronization of all not-yet-sync&#8217;d changes to be syncronized,
call <code class="docutils literal"><span class="pre">POD.sync()</span></code>.  To reactivate automatic synchronization (and synchronize
any outstanding changes) call <code class="docutils literal"><span class="pre">POD.unhold()</span></code>.</p>
<p>Note, <code class="docutils literal"><span class="pre">POD</span></code> and its related always synchronize at exit, e.g. if the program
crashes or if you issue a keyboard interrupt, so you don&#8217;t need to worry about
hitting Ctrl-C.</p>
<p>This is similar to how buffered data in an open file is handled&#8211;only a very bad
crash that prevents the program from performing cleanup operations at exit
would cause lost data.</p>
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
<li><a class="reference internal" href="#persistentordereddict"><code class="docutils literal"><span class="pre">PersistentOrderedDict</span></code></a><ul>
<li><a class="reference internal" href="#json-only">JSON only</a></li>
</ul>
</li>
<li><a class="reference internal" href="#synchronization">Synchronization</a></li>
<li><a class="reference internal" href="#progresstracker"><code class="docutils literal"><span class="pre">ProgressTracker</span></code></a><ul>
<li><a class="reference internal" href="#customize-synchronization">Customize synchronization</a></li>
</ul>
</li>
<li><a class="reference internal" href="#suspending-synchronization">Suspending synchronization</a></li>
</ul>
<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="#">Documentation overview</a><ul>
  </ul></li>
</ul>
</div>
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
    <div class="footer">
      &copy;2017, Edward Newell.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 1.4.6</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.9</a>
      
      |
      <a href="_sources/index.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>