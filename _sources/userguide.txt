User Guide
==========
.. currentmodule:: pds

This guide covers the basics to get you started with :mod:`pds`. It does not
go into detail about PDS labels. See the `PDS documentation`_ for that.

.. _PDS documentation: http://pds.jpl.nasa.gov/tools/standards-reference.shtml

Reading
-------
In order to work with an existing PDS label, we must first parse it into a
:class:`Label` object. This is done using the :func:`parse` function::

 >>> import pds
 >>> pds.parse(
 ...  b"""
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  """
 ... )
 <pds.Label object at 0x...>

:func:`parse` must be given a valid PDS label, otherwise it raises a
:exc:`ParsingError`::

 >>> pds.parse(b"")
 Traceback (most recent call last):
   ...
 pds.ParsingError: unexpected end
 
 >>> pds.parse(b"blha blha blha")
 Traceback (most recent call last):
   ...
 pds.ParsingError: expected equal sign instead of 'blha'

Notice, how we have been providing a :obj:`bytes` string (i.e ``b"..."``) to the
:func:`parse` function. This is because :func:`parse` cannot operate on
:obj:`str` strings, as PDS labels may only contain *ascii* characters::

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


 



Manipulating
------------


Writing
-------



.. vim: tabstop=1 expandtab
