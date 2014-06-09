User Guide
==========
.. currentmodule:: pds

This guide covers the basics to get you started with :mod:`pds`. It does not
go into detail about PDS labels. See the `PDS documentation`_ for that.

.. _PDS documentation: http://pds.jpl.nasa.gov/tools/standards-reference.shtml

Reading
-------
To read an existing PDS label, use the :func:`parse` function::

 >>> import pds
 >>> pds.parse(
 ...  b"""
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  """
 ... )
 <pds.Label object at 0x...>


:func:`parse` takes a PDS label as an argument and parses it into a
:class:`Label` object. :class:`Label` can then be used to access and manipulate
the properties of the label.

:func:`parse` must be given a valid PDS label, otherwise it will raise a
:exc:`ParsingError`::

 >>> pds.parse(b"")
 Traceback (most recent call last):
   ...
 pds.ParsingError: unexpected end
 
 >>> pds.parse(b"blha blha blha")
 Traceback (most recent call last):
   ...
 pds.ParsingError: expected equal sign instead of 'blha'


Notice, how we have been providing a :obj:`bytes` string (i.e. ``b"..."``) to 
the :func:`parse` function. This is because :func:`parse` cannot operate on a
:obj:`str` string (PDS labels may only contain *ascii* characters)::

 >>> pds.parse(
 ...  """
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  """
 ... )
 Traceback (most recent call last):
   ...
 TypeError: can't use a bytes pattern on a string-like object


In the examples above, we have been parsing PDS labels provided explicitly in a
string (i.e. ``b"..."``). However, PDS labels are usually stored in files.
We can parse a PDS label in a file using the same approach as above::

 >>> file_obj = open("../data/test.img", "r+b")
 >>> file_bytes = file_obj.read()
 >>> pds.parse(file_bytes)
 <pds.Label object at 0x...>


However, this is extremely inefficient and results in high memory usage because
the entire file is first read into memory and then parsed. This is especially
true if the file is large. A more efficient way of parsing a PDS label in a
file, is to use a :obj:`mmap.mmap` (memory mapped file) object::

 >>> import mmap
 >>> file_obj = open("../data/test.img", "r+b")
 >>> mmap_file = mmap.mmap(file_obj.fileno(), 0)
 >>> pds.parse(mmap_file)
 <pds.Label object at 0x...>



Manipulating
------------


Writing
-------



.. vim: tabstop=1 expandtab
