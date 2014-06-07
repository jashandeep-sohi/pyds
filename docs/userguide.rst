User Guide
==========
This guide covers the basics to get you started with :mod:`pds`. It does not
go into detail about the PDS labeling system. Read the `PDS documentation`_ for
that. Also, see :doc:`reference`.

.. _PDS documentation: http://pds.jpl.nasa.gov/tools/standards-reference.shtml

Reading
-------
To parse a PDS label attached to a file:
    
>>> import pds
>>> file_object = open("./data/test.img", "r+b")
>>> file_content = file_object.read()
>>> pds.parse(file_content)
<pds.Label object at 0x...>


Rather than reading the entire contents of the file into a variable and then
parsing it, you could use a :class:`mmap.mmap` object. This is especially
useful if the file is large:
  
>>> import mmap
>>> file_mmap = mmap.mmap(file_object.fileno(), 0)
>>> pds.parse(file_mmap)
<pds.Label object at 0x...>


The :obj:`bytes` representation of a :class:`Label` object is a valid PDS
string which when parsed leads to an identical :class:`Label` object:
  
>>> label = pds.parse(file_mmap)
>>> bytes(label) == bytes(pds.parse(bytes(label)))
True



Manipulating
------------


Writing
-------

.. vim: tabstop=1 expandtab
