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
 >>> label = b"""
 ... PDS_VERSION_ID = PDS3
 ... TEST = 5
 ... END
 ... """
 >>> pds.parse(label)
 <pds.Label object at 0x...>

:func:`parse` must be given a valid PDS label, otherwise it raises an 
:exc:`ParsingError`::

 >>> pds.parse(b"")
 Traceback (most recent call last):
   ...
 pds.ParsingError: unexpected end


Manipulating
------------


Writing
-------



.. vim: tabstop=1 expandtab
