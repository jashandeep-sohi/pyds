User Guide
==========
.. currentmodule:: pds

This guide covers the basics to get you started with :mod:`pds`. It does not
go into detail about PDS labels. See the `PDS documentation`_ for that.

.. _PDS documentation: http://pds.jpl.nasa.gov/tools/standards-reference.shtml

Parsing
-------
To work with an existing PDS label, use the :func:`parse` function to parse it
into a :class:`Label` object::

 >>> import pds
 >>> pds.parse(
 ...  b"""
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  """
 ... )
 <pds.Label object at 0x...>

This :class:`Label` object can then be used to interface with the label.
See the discussion below.

:func:`parse` must be given a string which **starts** with a valid PDS label as 
it's argument or otherwise it will raise a :exc:`ParsingError`::

 >>> pds.parse(b"")
 Traceback (most recent call last):
   ...
 pds.ParsingError: unexpected end
 
 >>> pds.parse(b"blha blha blha")
 Traceback (most recent call last):
   ...
 pds.ParsingError: expected equal sign instead of 'blha'

Additional data may **follow** the PDS label in the string.
This is useful when PDS labels are prepended to the data products they 
describe::

 >>> pds.parse(
 ...  b"""
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  Blha Blha Blha.
 ...  All of this is ignored. It could be the data product, etc.
 ...  """
 ... )
 <pds.Label object at 0x...>


.. note::
   
   We have been providing a :obj:`bytes` string (i.e. ``b"..."``) to 
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
string (i.e. ``b"..."``), however PDS labels are usually stored in files.
We could parse a PDS label stored in a file using the same approach as above::

 >>> file_obj = open("../data/test.img", "r+b")
 >>> file_bytes = file_obj.read()
 >>> pds.parse(file_bytes)
 <pds.Label object at 0x...>


However, this is extremely inefficient and results in high memory usage because
the entire file is first read into memory and then parsed. This is especially
true if the file is large.

A more efficient way of parsing a PDS label stored in a file, is to use a 
:obj:`mmap.mmap` (memory mapped file) object::

 >>> import mmap
 >>> file_obj = open("../data/test.img", "r+b")
 >>> mmap_file = mmap.mmap(file_obj.fileno(), 0)
 >>> pds.parse(mmap_file)
 <pds.Label object at 0x...>



>>> test_label = pds.parse(
... b"""
... PDS_VERSION_ID = PDS3
... 
... INTEGER_1 = 0
... INTEGER_2 = 123
... INTEGER_3 = +440
... INTEGER_4 = -1500000
... 
... GROUP = BASED_INTEGERS
...  ONE = 2#1001011#
...  TWO = 8#113#
...  THREE = 10#75#
...  FOUR = 16#+4B#
...  FIVE = 16#-4B#
... END_GROUP = BASED_INTEGERS
... 
... GROUP = REAL_NUMBERS
...  ONE = 0.0
...  TWO = 123.
...  THREE = +1234.56
...  FOUR = -.9981
...  FIVE = -1.E-3
...  SIX = 31459e1
... END_GROUP = REAL_NUMBERS
... 
... OBJECT = DATES_AND_TIMES
...  GROUP = DATES
...   ONE = 1990-07-04
...   TWO = 1990-158
...   THREE = 2001-001
...  END_GROUP = DATES
...  
...  GROUP = TIMES
...   ONE = 12:00
...   TWO = 15:24:12Z
...   THREE = 01:10:39.4575+07
...  END_GROUP = TIMES
...  
...  GROUP = DATE_TIMES
...   ONE = 1990-07-04T12:00
...   TWO = 1990-158T15:24:12Z
...   THREE = 2001-001T01:10:39.457591+7
...  END_GROUP = DATE_TIMES
... END_OBJECT = DATES_AND_TIMES
... 
... TEXT1 = "blha blha BLHA BLHA                blha
...          blha blha blha"
... 
... TEXT2 = "blha blha blha. Any character but a quotation mark."
... 
... TEXT3 = ""
... 
... SYMBOL1 = 'ONE-OR-MORE-CHARS'
... 
... GROUP = NUMBERS_WITH_UNITS
...  INT = 5 <KM/SEC/SEC>
...  REAL = 5.1100 <M/SEC>
...  BASED_INTGER = 2#1001011# <APPLES>
... END_GROUP = NUMBERS_WITH_UNITS
... 
... ATTR_IDENTIFIER = ATTR_IDENTIFIER_VALUE
... 
... A_1D_SEQUENCE = (0.2056, 0.0068, 0.0167, 0.0934, 0.0483, 0.0560)
... A_2D_SEQUENCE = ((0, 1008), (1009, 1025), (1026, 1043))
... A_SET = { 'RED', 'BLUE', 'GREEN', 'HAZEL' }
... 
... END
... """
... )


.. vim: tabstop=1 expandtab
