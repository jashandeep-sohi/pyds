User Guide
==========
.. currentmodule:: pds

This guide covers the basics to get you started with :mod:`pds`. It does not
go into detail about PDS labels. See the `PDS documentation`_ for that.

.. _PDS documentation: http://pds.jpl.nasa.gov/tools/standards-reference.shtml

Reading
-------
In order to work with an existing PDS label, we must first parse it into a
:class:`Label` object. This is done using the function :func:`parse`.
For example::

 >>> import pds
 >>> label_bytes = b"""
 ... PDS_VERSION_ID = PDS3
 ... TEST = 5
 ... END
 ... """
 >>> pds.parse(label_bytes)
 <pds.Label object at 0x...>



Manipulating
------------


Writing
-------



.. vim: tabstop=1 expandtab
