Introduction
============
PDS labels are used by the `Planetary Data System`_ and other NASA data systems
to describe the contents and format of data products. This module is capable of
handling version 3 PDS labels as documented in the 
`PDS Standards Reference v3.8`_. PDS labels are written in
`Object Description Language`_ (ODL). ODL is a relatively simple attribute
assignment based language, with support for integers, real numbers, sequences,
text and other various types.

This module is capable of parsing PDS label strings into Python objects which
can then be used to read and manipulate different properties of the label.
The reverse is also possible: it can serialize Python objects into a valid PDS
string.

.. _Planetary Data System: http://pds.jpl.nasa.gov/

.. _Object Description Language:
   https://pds.jpl.nasa.gov/documents/sr/Chapter12.pdf
   
.. _PDS Standards Reference v3.8: 
   http://pds.jpl.nasa.gov/documents/sr/StdRef_20090227_v3.8.pdf

.. vim: tabstop=1 expandtab
