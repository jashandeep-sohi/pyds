User Guide
==========
.. currentmodule:: pyds

.. _parsing:

Parsing
-------
To work with an existing PDS label, first parse it into a :class:`Label` object
using the :func:`parse` function::

 >>> import pyds
 >>> test_parsed_label = pyds.parse(
 ... b"""
 ... PDS_VERSION_ID = PDS3
 ... 
 ... ATTR_BLHA = 2000
 ... NUMBER_OF_DAYS = 2
 ... RATIO_OF_X = 2.0
 ... ID = "lk32j4kajsdk1asdadd8asd8"
 ... 
 ... NAMESPACED:ATTR = 200
 ...
 ... ^POINT_TO_X = 500
 ... ^POINT_TO_Y = "blha.txt"
 ... 
 ... GROUP = INTEGERS
 ... ONE = 0
 ... TWO = 123
 ... THREE = +440
 ... FOUR = -1500000
 ... END_GROUP = INTEGERS
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
 ... GROUP = NUMBERS_WITH_UNITS
 ...  INT = 5 <KM/SEC/SEC>
 ...  REAL = 5.1100 <M/SEC>
 ...  BASED_INTEGER = 2#1001011# <APPLES>
 ... END_GROUP = NUMBERS_WITH_UNITS
 ... 
 ... OBJECT = DATES_AND_TIMES
 ...  GROUP = DATES
 ...   ONE = 1990-07-04
 ...   TWO = 1990-158
 ...   THREE = 2001-001
 ...  END_GROUP = DATES
 ...  
 ...  OBJECT = TIMES
 ...   ONE = 12:00
 ...   TWO = 15:24:12Z
 ...   THREE = 01:10:39.4575+07
 ...  END_OBJECT = TIMES
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
 ... SYMBOL1 = 'ONE-OR-MORE-CHARS EXCEPT THE APOSTROPHE ON ONE LINE'
 ... 
 ... ATTR_IDENTIFIER = ATTR_IDENTIFIER_VALUE
 ... 
 ... A_1D_SEQUENCE = (0.2056, 0.0068, 0.0167, 0.0934, 0.0483, 0.0560)
 ... A_2D_SEQUENCE = ((0, 1008), (1009, 1025), (1026, 1043))
 ... A_SET = {'RED', 'BLUE', 'GREEN', 'HAZEL'}
 ... 
 ... END
 ... """
 ... )
 >>> test_parsed_label
 <pyds.statements.Label object at 0x...>


You can then interact with the :class:`Label` object to read or manipulate
properties of the label. See the discussion :ref:`below<label>` for details.

:func:`parse` must be given a string which **starts** with a valid PDS label as 
it's argument or otherwise it will raise a :exc:`ParsingError`::

 >>> pyds.parse(b"")
 Traceback (most recent call last):
   ...
 pyds.parser.ParsingError: unexpected end
 
 >>> pyds.parse(b"blha blha blha")
 Traceback (most recent call last):
   ...
 pyds.parser.ParsingError: expected equal sign instead of 'blha'

Additional data may **follow** the PDS label in the string.
This is useful when PDS labels are prepended to the data products they 
describe::

 >>> pyds.parse(
 ...  b"""
 ...  PDS_VERSION_ID = PDS3
 ...  TEST = 5
 ...  END
 ...  Blha Blha Blha.
 ...  All of this is ignored. It could be the data product, etc.
 ...  """
 ... )
 <pyds.statements.Label object at 0x...>


.. note::
   
   The :func:`parse` function can only operate on :obj:`bytes` objects.
   Providing a :obj:`str` object will raise an error::

    >>> pyds.parse( # doctest: +IGNORE_EXCEPTION_DETAIL
    ...  """
    ...  PDS_VERSION_ID = PDS3
    ...  TEST = 5
    ...  END
    ...  """
    ... )
    Traceback (most recent call last):
     ...
    TypeError: cannot use a bytes pattern on a string-like object


In the examples above, we have been parsing PDS labels provided explicitly in a
string (i.e. ``b"..."``), however PDS labels are usually stored in files.
We could parse a PDS label stored in a file using the same approach as above::

 >>> file_obj = open("../data/test.img", "r+b")
 >>> file_bytes = file_obj.read()
 >>> pyds.parse(file_bytes)
 <pyds.statements.Label object at 0x...>

However, this is extremely inefficient and results in high memory usage because
the entire file is first read into memory and then parsed. This is especially
true if the file is large.
A more efficient way of parsing a PDS label stored in a file, is to use a 
:obj:`mmap.mmap` (memory mapped file) object::

 >>> import mmap
 >>> file_obj = open("../data/test.img", "r+b")
 >>> mmap_file = mmap.mmap(file_obj.fileno(), 0)
 >>> pyds.parse(mmap_file)
 <pyds.statements.Label object at 0x...>


.. _statements:

Statements
----------
A PDS label is made up of a series of statements, which can be of different
types.
They are represented in this module by instances of an :class:`Attribute`,
a :class:`Group`, or an :class:`Object`.

.. contents:: Contents
   :local:
   :backlinks: top

Attribute
#########

An *attribute assignment statement*, which assigns some value to an attribute,
is represented by an :class:`Attribute` object.
It is instantiated with an identifier and a value::

 >>> test_attr = pyds.Attribute("test_attribute", pyds.Integer(5))
 >>> test_attr
 <pyds.statements.Attribute object at 0x...>

The value must be an instance of one of the value types discussed
:ref:`below<values>`::

 >>> pyds.Attribute("test_attribute", 5)
 Traceback (most recent call last):
 ...
 TypeError: value is not an instance of Value
 
The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pyds.Attribute("12_not_valid", pyds.Integer(5))
 Traceback (most recent call last):
  ...
 ValueError: invalid identifier '12_not_valid'
 >>> pyds.Attribute("THIS_is_VaLiD", pyds.Integer(5))
 <pyds.statements.Attribute object at 0x...>

The identifier can also be *namespaced* by preceding it with another
identifier and a colon::

 >>> pyds.Attribute("namespace_identifier:test_attribute", pyds.Integer(5))
 <pyds.statements.Attribute object at 0x...>

.. note ::

   Although the PDS specification distinguishes between a *pointer statement*
   and an attribute assignment statement, this module does not.
   A pointer statement is also represented with an :class:`Attribute` object by
   preceding the identifier with a caret (``^``)::

    >>> pyds.Attribute("^THIS_POINT_TO_SOMETHING", pyds.Integer(5))
    <pyds.statements.Attribute object at 0x...>
 
To access the identifier and value of an :class:`Attribute` object, use the
:attr:`Attribute.identifier` and :attr:`Attribute.value` attributes
respectively::

 >>> test_attr.identifier
 'TEST_ATTRIBUTE'
 >>> test_attr.value
 <pyds.values.Integer object at 0x...>

To get the PDS serialized string representation of an :class:`Attribute` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_attr))
 TEST_ATTRIBUTE = 5


Group
#####

A *group statement*, which groups other attribute assignment statements,
is represented by a :class:`Group` object.
It is instantiated with an identifier and a :class:`GroupStatements` object::

 >>> test_group = pyds.Group(
 ...  "test_group",
 ...  pyds.GroupStatements(
 ...   pyds.Attribute("nested_attr_1", pyds.Integer(5)),
 ...   pyds.Attribute("nested_attr_2", pyds.Real(10.122))
 ...  )
 ... )
 >>> test_group
 <pyds.statements.Group object at 0x...>
 
A :class:`GroupStatements` object is a container for the nested statements of
a group statement. It behaves just like a :class:`Label` object, except that it
can only contain :class:`Attribute` objects::

 >>> pyds.GroupStatements(pyds.Attribute("test", pyds.Integer(5)))
 <pyds.statements.GroupStatements object at 0x...>
 >>> pyds.GroupStatements(pyds.Group("test", pyds.GroupStatements()))
 Traceback (most recent call last):
  ...
 TypeError: statement is not an instance of Attribute
 >>> pyds.GroupStatements(pyds.Object("test", pyds.ObjectStatements()))
 Traceback (most recent call last):
  ...
 TypeError: statement is not an instance of Attribute

The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pyds.Group(
 ...  "123 this is not valid",
 ...  pyds.GroupStatements(
 ...   pyds.Attribute("nested_attr_1", pyds.Integer(5))
 ...  )
 ... )
 Traceback (most recent call last):
  ...
 ValueError: invalid identifier '123 this is not valid'

To access the identifier and nested statements of a :class:`Group` object, use
the :attr:`Group.identifier` and :attr:`Group.statements` or :attr:`Group.value`
attributes respectively::

 >>> test_group.identifier
 'TEST_GROUP'
 >>> test_group.statements
 <pyds.statements.GroupStatements object at 0x...>
 >>> test_group.statements == test_group.value
 True
 
To get the PDS serialized string representation of a :class:`Group` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_group)) # doctest: +NORMALIZE_WHITESPACE
 GROUP     = TEST_GROUP
  NESTED_ATTR_1 = 5
  NESTED_ATTR_2 = 10.122
 END_GROUP = TEST_GROUP
 

Object
######

An *object statement*, which groups other statements (of all types), is 
represented by an :class:`Object` object.
It is instantiated with an identifier and a :class:`ObjectStatements` object::

 >>> test_object = pyds.Object(
 ...  "test_object",
 ...  pyds.ObjectStatements(
 ...   pyds.Attribute("nested_attr_1", pyds.Integer(5)),
 ...   pyds.Attribute("nested_attr_2", pyds.Real(10.122)),
 ...   pyds.Group(
 ...    "nested_group_1",
 ...    pyds.GroupStatements(
 ...     pyds.Attribute("nested_attr_1", pyds.Integer(122)),
 ...     pyds.Attribute("nested_attr_2", pyds.Integer(22322))
 ...    )
 ...   ),
 ...   pyds.Group(
 ...    "nested_group_2",
 ...    pyds.GroupStatements(
 ...     pyds.Attribute("nested_attr_1", pyds.Real(5.3322)),
 ...     pyds.Attribute("nested_attr_2", pyds.Real(3.14159)),
 ...    )
 ...   ),
 ...   pyds.Object(
 ...    "nested_object",
 ...    pyds.ObjectStatements(
 ...     pyds.Attribute("nested_attr", pyds.Integer(5))
 ...    )
 ...   )
 ...  )
 ... )
 >>> test_object
 <pyds.statements.Object object at 0x...>
 
An :class:`ObjectStatements` object is a container for the nested statements of
an object statement.
It behaves just like a :class:`Label` object, meaning it can contain all three
types of statements, including other object statements.
There is no limit to the depth to which object statements may be nested::

 >>> pyds.ObjectStatements(pyds.Attribute("test", pyds.Integer(5)))
 <pyds.statements.ObjectStatements object at 0x...>
 >>> pyds.ObjectStatements(pyds.Group("test", pyds.GroupStatements()))
 <pyds.statements.ObjectStatements object at 0x...>
 >>> pyds.ObjectStatements(
 ...  pyds.Object(
 ...   "test", 
 ...   pyds.ObjectStatements(
 ...    pyds.Object(
 ...     "test2", 
 ...     pyds.ObjectStatements(
 ...      pyds.Object("test3", pyds.ObjectStatements())
 ...     )
 ...    )
 ...   )
 ...  )
 ... )
 <pyds.statements.ObjectStatements object at 0x...>
 
The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pyds.Object(
 ...  "123 this is not valid",
 ...  pyds.ObjectStatements(
 ...   pyds.Attribute("nested_attr_1", pyds.Integer(5))
 ...  )
 ... )
 Traceback (most recent call last):
  ...
 ValueError: invalid identifier '123 this is not valid'
 
To access the identifier and nested statements of a :class:`Object` object, use
the :attr:`Object.identifier` and :attr:`Object.statements` or 
:attr:`Object.value` attributes respectively::

 >>> test_object.identifier
 'TEST_OBJECT'
 >>> test_object.statements
 <pyds.statements.ObjectStatements object at 0x...>
 >>> test_object.statements == test_object.value
 True

To get the PDS serialized string representation of an :class:`Object` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_object)) # doctest: +NORMALIZE_WHITESPACE
 OBJECT     = TEST_OBJECT
  NESTED_ATTR_1  = 5
  NESTED_ATTR_2  = 10.122
  GROUP          = NESTED_GROUP_1
   NESTED_ATTR_1 = 122
   NESTED_ATTR_2 = 22322
  END_GROUP      = NESTED_GROUP_1
  GROUP          = NESTED_GROUP_2
   NESTED_ATTR_1 = 5.3322
   NESTED_ATTR_2 = 3.14159
  END_GROUP      = NESTED_GROUP_2
  OBJECT         = NESTED_OBJECT
   NESTED_ATTR = 5
  END_OBJECT     = NESTED_OBJECT
 END_OBJECT = TEST_OBJECT


.. _values:

Values
------
An attribute assignment statement (i.e. an :class:`Attribute` object) can
contain various types of values. In this module they are represented by the
following objects.

.. contents:: Contents
   :local:
   :backlinks: top
    

Integer, BasedInteger & Real
############################

A numeric value is represented by an :class:`Integer`, a :class:`BasedInteger`,
or a :class:`Real` object::

 >>> pyds.Integer(1000)
 <pyds.values.Integer object at 0x...>
 >>> pyds.BasedInteger(2, "1111")
 <pyds.values.BasedInteger object at 0x...>
 >>> pyds.Real(10.29932232)
 <pyds.values.Real object at 0x...>
 
A :class:`BasedInteger` object is used to represent an integer specified in a
particular radix/base (i.e. binary, hexadecimal, etc). It is instantiated by
providing the radix as the first argument and the digits as the second
argument::

 >>> pyds.BasedInteger(2, "1111")
 <pyds.values.BasedInteger object at 0x...>
 >>> pyds.BasedInteger(16, "f")
 <pyds.values.BasedInteger object at 0x...>
 >>> pyds.BasedInteger(10, "15")
 <pyds.values.BasedInteger object at 0x...>
 
All three types of numeric values can also have units.
Units are represented by a :class:`Units` object, which is instantiated
with a *units expression* describing the units.
Units expressions are discussed in detail in the PDS documentation,
but basically they must have the form, ``units_factor[[*|/]units_factor]*``,
where *units_factor* is ``units_identifier[**integer]``. It is converted to
an upper case string and set to the :attr:`Units.expression` attribute::

 >>> pyds.Units("km")
 <pyds.values.Units object at 0x...>
 >>> pyds.Units("km**2").expression
 'KM**2'
 >>> pyds.Units("Km**2*sec**-1").expression
 'KM**2*SEC**-1'
 >>> pyds.Units("J/S").expression
 'J/S'

To create a numeric value with units, provide a :class:`Units` object
as the last argument::

 >>> test_int = pyds.Integer(1000, pyds.Units("KM"))
 >>> test_based_int = pyds.BasedInteger(2, "1111", pyds.Units("BYTES"))
 >>> test_real = pyds.Real(10.29932232, pyds.Units("SEC"))
 
This :class:`Units` object can be accessed later using the ``units`` attribute::

 >>> test_int.units.expression
 'KM'
 >>> test_based_int.units.expression
 'BYTES'
 >>> test_real.units.expression
 'SEC'
 
The ``units`` attribute will be :obj:`None` if a numeric value does not have
units::
 
 >>> pyds.Integer(5).units == None
 True
 
The value of a numeric object can be accessed using the ``value`` attribute::

 >>> test_int.value
 1000
 >>> test_based_int.value
 15
 >>> test_real.value
 10.29932232

Attributes :attr:`Integer.value` and :attr:`BasedInteger.value` will always be
:obj:`int` objects, whereas the attribute :attr:`Real.value` will always be a
:obj:`float` object.

The attribute :attr:`BasedInteger.value` gives the base-10 integer
representation of the :class:`BasedInteger` object's value.
To get the base/radix and the digits of a :class:`BasedInteger` object, use
the :attr:`BasedInteger.radix` and :attr:`BasedInteger.digits` attributes
respectively::

 >>> test_based_int.radix
 2
 >>> test_based_int.digits
 '1111'

Numeric objects can also be converted to an :obj:`int` or :obj:`float` object
by calling the built-in :func:`int` or :func:`float` functions on them::

 >>> int(test_int)
 1000
 >>> float(test_int)
 1000.0
 >>> int(test_based_int)
 15
 >>> float(test_based_int)
 15.0
 >>> int(test_real)
 10
 >>> float(test_real)
 10.29932232

To get the PDS serialized string representation of numeric object, call the 
built-in :func:`str` function on it::

 >>> str(test_int)
 '1000 <KM>'
 >>> str(test_based_int)
 '2#1111# <BYTES>'
 >>> str(test_real)
 '10.29932232 <SEC>'


Date
####

A :class:`Date` object can represent a date in two different formats.
The first is the usual *year, month and day of month* format::

 >>> test_date_ymd = pyds.Date(2014, 6, 23)
 >>> test_date_ymd
 <pyds.values.Date object at 0x...>
 
The second is the *year and day of year* format::

 >>> test_date_doy = pyds.Date(2014, None, 174)
 >>> test_date_doy
 <pyds.values.Date object at 0x...>
 
To get the year, month or day of a :class:`Date` object use the
:attr:`Date.year`, :attr:`Date.month`, or :attr:`Date.day` attributes::

 >>> test_date_ymd.year
 2014
 >>> test_date_ymd.month
 6
 >>> test_date_ymd.day
 23
 >>> test_date_doy.day
 174
 
When a :class:`Date` object is in the *year and day of the year* format, then
:attr:`Date.month` will be :obj:`None` and :attr:`Date.day` will refer to the
day of the year instead of the day of the month::

 >>> test_date_doy.month == None
 True

To get the PDS serialized string representation of a :class:`Date` object, call
the  built-in :func:`str` function on it::

 >>> str(test_date_ymd)
 '2014-06-23'
 >>> str(test_date_doy)
 '2014-174'

Time
####

A :class:`Time` object represents a local time, UTC time, or a zoned time::

 >>> test_local_time = pyds.Time(12, 32, 10) # local time
 >>> test_local_time
 <pyds.values.Time object at 0x...>
 >>> test_utc_time = pyds.Time(9, 32, 10.9983, True) # UTC time
 >>> test_utc_time
 <pyds.values.Time object at 0x...>
 >>> test_zoned_time = pyds.Time(20, 19, None, False, -8, 20) # zoned time
 >>> test_zoned_time
 <pyds.values.Time object at 0x...>
 
Providing the seconds is optional, however when provided it can either be an
integer or a float::

 >>> pyds.Time(12, 20, None) # or pyds.Time(12, 20)
 <pyds.values.Time object at 0x...>
 >>> pyds.Time(12, 20, 10)
 <pyds.values.Time object at 0x...>
 >>> pyds.Time(12, 20, 10.2233223)
 <pyds.values.Time object at 0x...>
 
Similarly for a zoned time, providing the minutes of a time zone is optional::

 >>> pyds.Time(6, 9, None, False, -8, None) # or pyds.Time(6, 9, None, False, -8)
 <pyds.values.Time object at 0x...>
 
To get the hours, minutes and seconds of a :class:`Time` object, use the
:attr:`Time.hour`, :attr:`Time.minute` and :attr:`Time.second` attributes::

 >>> test_local_time.hour
 12
 >>> test_local_time.minute
 32
 >>> test_local_time.second
 10.0
 >>> test_zoned_time.second == None
 True
 
To get the hours and minutes of the time zone (if specified), use the
:attr:`Time.zone_hour` and :attr:`Time.zone_minute` attributes::

 >>> test_zoned_time.zone_hour
 -8
 >>> test_zoned_time.zone_minute
 20

To check whether a :class:`Time` object represents a UTC time, test the
:attr:`Time.utc` attribute::

 >>> test_utc_time.utc
 True
 >>> test_local_time.utc
 False
 >>> test_zoned_time.utc
 False
 
When creating a :class:`Time` object, the UTC flag argument takes precedence
over the time zone info::

 >>> t = pyds.Time(12, 20, 9, True, 9, 20)
 >>> t.utc
 True
 >>> t.zone_hour == None
 True
 >>> t.zone_minute == None
 True

To get the PDS serialized string representation of a :class:`Time` object, call
the built-in :func:`str` function on it::

 >>> str(test_local_time)
 '12:32:10'
 >>> str(test_utc_time)
 '09:32:10.9983Z'
 >>> str(test_zoned_time)
 '20:19-08:20'
 
DateTime
########
A :class:`DateTime` object represents a combined date and time::

 >>> test_datetime_ymd_local = pyds.DateTime(2014, 6, 23, 12, 45)
 >>> test_datetime_ymd_local
 <pyds.values.DateTime object at 0x...>
 >>> test_datetime_doy_utc = pyds.DateTime(2014, None, 174, 12, 45, 1, True)
 >>> test_datetime_doy_utc
 <pyds.values.DateTime object at 0x...>
 >>> test_datetime_ymd_zoned = pyds.DateTime(2014, 6, 23, 12, 0, 10.2, False, 8)
 >>> test_datetime_ymd_zoned
 <pyds.values.DateTime object at 0x...>
 
It simply creates a :class:`Date` and :class:`Time` object internally from the
arguments provided to represent the date and the time. They can be accessed
using the :attr:`DateTime.date` and :attr:`DateTime.time` attributes::

 >>> test_datetime_ymd_local.date.month
 6
 >>> test_datetime_ymd_local.time.utc
 False
 >>> test_datetime_doy_utc.time.utc
 True
 >>> test_datetime_doy_utc.date.month == None
 True
 >>> test_datetime_ymd_zoned.time.zone_hour
 8

To get the pyds serialized string representation of a :class:`DateTime` object,
call the built-in :func:`str` function on it::

 >>> str(test_datetime_ymd_local)
 '2014-06-23T12:45'
 >>> str(test_datetime_doy_utc)
 '2014-174T12:45:01Z'
 >>> str(test_datetime_ymd_zoned)
 '2014-06-23T12:00:10.2+08'

Text
####
A :class:`Text` object contains an arbitrary string of characters::

 >>> test_text = pyds.Text(
 ... """Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
 ... tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
 ... veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
 ... commodo consequat."""
 ... )
 >>> test_text
 <pyds.values.Text object at 0x...>
 
It can contain all *ascii* characters, including control 
characters (e.g. ``\n``, ``\t``, etc), except the *double quote* (``"``) 
character::

 >>> pyds.Text(' " ')
 Traceback (most recent call last):
  ...
 ValueError: invalid value ' " '
 
To access the string, use the :attr:`Text.value` attribute::

 >>> print(test_text.value)
 Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
 tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
 veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
 commodo consequat.

To get the PDS serialized string representation of a :class:`Text` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_text))
 "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod
 tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim
 veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea
 commodo consequat."

Symbol
######
A :class:`Symbol` object contains a string of characters used to represent
a symbolic value::

 >>> test_symbol = pyds.Symbol("BLHA-BLHA#BLHA BLHA")
 >>> test_symbol
 <pyds.values.Symbol object at 0x...>
 
It can contain all **printable** *ascii* characters except the single quote
(``'``) character. That means it also cannot contain control characters 
(e.g. ``\n``, ``\t``, etc)::

 >>> pyds.Symbol("This is boooring\n But it must be done...")
 Traceback (most recent call last):
  ...
 ValueError: invalid value 'This is boooring\n But it must be done...'

The string is upper cased and stored as such internally.
It is accessible using the :attr:`Symbol.value` attribute::

 >>> pyds.Symbol("this should be upper cased").value
 'THIS SHOULD BE UPPER CASED'
 >>> test_symbol.value
 'BLHA-BLHA#BLHA BLHA'
 
To get the PDS serialized string representation of a :class:`Symbol` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_symbol))
 'BLHA-BLHA#BLHA BLHA'

Identifier
##########
An identifier is usually used as the name of an attribute (i.e. in an attribute 
assignment statement), a group or an object.
It can also be used as a value of an attribute assignment statement using an
:class:`Identifier` object::

 >>> test_identifier = pyds.Identifier("USA_NASA_PDS_1_0007")
 >>> test_identifier
 <pyds.values.Identifier object at 0x...>
 
Identifiers are composed of letters, digits, and underscores. 
Underscores are used to separate words in an identifier.
The first character of an identifier must be a letter.
The last character may not be an underscore::

 >>> pyds.Identifier("VOYAGER")
 <pyds.values.Identifier object at 0x...>
 >>> pyds.Identifier("VOYAGER_2")
 <pyds.values.Identifier object at 0x...>
 >>> pyds.Identifier("1_VOYAGER")
 Traceback (most recent call last):
  ...
 ValueError: invalid value '1_VOYAGER'
 >>> pyds.Identifier("_VOYAGER")
 Traceback (most recent call last):
  ...
 ValueError: invalid value '_VOYAGER'
 
The string is upper cased and stored as such internally.
It is accessible using the :attr:`Identifier.value` attribute::

 >>> pyds.Identifier("voyager").value
 'VOYAGER'
 >>> test_identifier.value
 'USA_NASA_PDS_1_0007'
 
To get the PDS serialized string representation of an :class:`Identifier`
object, call the built-in :func:`str` function on it::

 >>> print(str(test_identifier))
 USA_NASA_PDS_1_0007

Set
###
A :class:`Set` object represents a set of values::

 >>> test_set = pyds.Set(pyds.Integer(5), pyds.Symbol("MARS"))
 >>> test_set
 <pyds.values.Set object at 0x...>
 
It behaves just like the built-in :obj:`set` object, supporting all the methods
and operators it supports, except that it can only contain :class:`Integer` 
and :class:`Symbol` objects::

 >>> test_set.add(pyds.Real(5.0))
 Traceback (most recent call last):
  ...
 TypeError: value is not an instance of Symbol or Integer
 >>> test_set.add(pyds.Integer(5000))
 >>> test_set.add(pyds.Integer(5000))
 >>> len(test_set)
 3
 >>> test_set.add(pyds.Symbol("Blue"))
 >>> test_set.add(pyds.Integer(299))
 >>> test_set.discard(pyds.Integer(299))
 >>> len(test_set)
 4
 
An empty :class:`Set` object is also allowed::
 
 >>> pyds.Set()
 <pyds.values.Set object at 0x...>
 
To get the PDS serialized string representation of a :class:`Set` object, call
the built-in :func:`str` function on it::

 >>> print(str(pyds.Set()))
 {}
 >>> print(str(test_set)) # doctest: +SKIP
 {'BLUE', 5000, 5, 'MARS'}
 

Sequence1D
##########
A :class:`Sequence1D` object represents a one dimensional sequence of values::

 >>> test_sequence_1d = pyds.Sequence1D(
 ...  pyds.Integer(5),
 ...  pyds.Real(10), 
 ...  pyds.Text("Blha Blha"),
 ...  pyds.Date(2012, 12, 9),
 ...  pyds.Time(12, 32, 16)
 ... )
 >>> test_sequence_1d
 <pyds.values.Sequence1D object at 0x...>
 
It can contain any of the value objects discussed above (e.g. :class:`Integer`,
:class:`Date`, :class:`Text`, etc.), except for a :class:`Set` object::

 >>> pyds.Sequence1D(pyds.Set(pyds.Integer(5)))
 Traceback (most recent call last):
  ...
 TypeError: value is not an instance of Scalar
 
Other than that, it behaves just like the built-in :obj:`list` object,
supporting all the methods and operators it supports::

 >>> test_sequence_1d[0]
 <pyds.values.Integer object at 0x...>
 >>> str(test_sequence_1d[-1])
 '12:32:16'
 >>> test_sequence_1d.append(pyds.BasedInteger(2, "111"))
 >>> len(test_sequence_1d)
 6
 >>> pyds.Integer(5) in test_sequence_1d
 True
 
To get the PDS serialized string representation of a :class:`Sequence1D` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_sequence_1d))
 (5, 10.0, "Blha Blha", 2012-12-09, 12:32:16, 2#111#)
 
Although a :class:`Sequence1D` object may become empty while manipulating it,
it should not be empty when serializing it to a PDS formated string::

 >>> len(pyds.Sequence1D())
 0
 >>> str(pyds.Sequence1D())
 Traceback (most recent call last):
  ...
 RuntimeError: sequence does not contain at least 1 value

Sequence2D
##########
A :class:`Sequence2D` object represents a two dimensional sequence of values::
 
 >>> test_sequence_2d =  pyds.Sequence2D(
 ...  pyds.Sequence1D(pyds.Integer(1), pyds.Integer(2), pyds.Integer(3)),
 ...  pyds.Sequence1D(pyds.Integer(4), pyds.Integer(5), pyds.Integer(6)),
 ...  pyds.Sequence1D(pyds.Integer(7), pyds.Integer(8), pyds.Integer(9))
 ... )
 >>> test_sequence_2d
 <pyds.values.Sequence2D object at 0x...>

It does so by containing a sequence of :class:`Sequence1D` objects.
Other than that, it behaves just like a :class:`Sequence1D` object.

To get the PDS serialized string representation of a :class:`Sequence2D` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_sequence_2d))
 ((1, 2, 3), (4, 5, 6), (7, 8, 9))

.. _label:

Label
-----
A :class:`Label` object is analogous to a PDS label.
It's a container for a sequence of :ref:`statement objects <statements>`, which
represent the statements of a PDS label.
As discussed :ref:`above <parsing>`, use the :func:`parse` function to parse
a :class:`Label` object from a PDS label string, or instantiate one directly
to create a new PDS label::

 >>> test_parsed_label # see above
 <pyds.statements.Label object at 0x...>
 >>> pyds.Label(
 ...  pyds.Attribute("PDS_VERSION_ID", pyds.Identifier("PDS3")),
 ...  pyds.Attribute("NUMBER_OF_DAYS", pyds.Integer(500)),
 ...  pyds.Group("ROVER_IDS", pyds.GroupStatements(
 ...   pyds.Attribute("MER1", pyds.Identifier("D24KJHJ2K3H1JH22HHKSDD")),
 ...   pyds.Attribute("MER2", pyds.Identifier("DLK3J658978XLK213KJH87")),
 ...  ))
 ... )
 <pyds.statements.Label object at 0x...>

It implements a list like interface for manipulating and querying the statements
it contains.
To add statements, use the :meth:`Label.insert` and :meth:`Label.append`
methods::

 >>> len(test_parsed_label)
 21
 >>> test_parsed_label.insert(1, pyds.Attribute("inserted_attr", pyds.Integer(5)))
 >>> len(test_parsed_label)
 22
 >>> test_parsed_label.append(pyds.Attribute("appended_attr", pyds.Real(3.14)))
 >>> len(test_parsed_label)
 23
 
To retrieve statements, use the :meth:`Label.get` method::

 >>> test_parsed_label.get(1)
 <pyds.statements.Attribute object at 0x...>
 >>> print(str(test_parsed_label.get(1)))
 INSERTED_ATTR = 5
 >>> print(str(test_parsed_label.get(-1)))
 APPENDED_ATTR = 3.14
 
To remove statements, use the :meth:`Label.pop` method::
 
 >>> len(test_parsed_label)
 23
 >>> test_parsed_label.pop(-1)
 <pyds.statements.Attribute object at 0x...>
 >>> len(test_parsed_label)
 22
 
Since each statement in a PDS label has a unique identifier, a statement's
value can be retreived using it's identifier::

 >>> test_parsed_label["inserted_attr"]
 <pyds.values.Integer object at 0x...>
 >>> test_parsed_label["integers"]
 <pyds.statements.GroupStatements object at 0x...>
 >>> test_parsed_label["dates_and_times"]
 <pyds.statements.ObjectStatements object at 0x...>
 
Although identifiers are stored internally as upper cased string, they are
case-insensitive::
 
 >>> test_parsed_label["inserted_attr"] == test_parsed_label["InSeRtEd_AtTr"]
 True

The type of value returned depends on the type of the statement that the 
identifier refers to.
If it's an :class:`Attribute` assignment statement, then one of the value
objects discussed :ref:`above <values>` is returned.
If it's a :class:`Group` statement, then a :class:`GroupStatements` object is
returned.
And if it's a :class:`Object` statement, then an :class:`ObjectStatements` 
object is returned.

.. note::
   :class:`GroupStatements` and :class:`ObjectStatements` objects also behave
   like :class:`Label` objects. This makes it simple to retrieve nested
   values::

    >>> test_parsed_label["dates_and_times"]["dates"]["one"]
    <pyds.values.Date object at 0x...>
    >>> test_parsed_label["dates_and_times"]["times"]["one"]
    <pyds.values.Time object at 0x...>
 

A statement can also be added using a similar approach::

 >>> len(test_parsed_label)
 22
 >>> test_parsed_label["monkey_age"] = pyds.Integer(5)
 >>> test_parsed_label["monkey_group"] = pyds.GroupStatements()
 >>> test_parsed_label["monkey_object"] = pyds.ObjectStatements()
 >>> len(test_parsed_label)
 25

If a statement with the provided identifier does not exist, then a new
statement is created using the provided identifier and value and then it's
appended to the sequence. If, however, a statement does exist with the provided
identifier, then it's removed and the new statement takes it's place in the 
sequence::

 >>> test_parsed_label["monkey_age"] == test_parsed_label.get(22).value
 True
 >>> test_parsed_label["monkey_age"]
 <pyds.values.Integer object at 0x...>
 >>> test_parsed_label["monkey_age"] = pyds.Real(5.62)
 >>> test_parsed_label["monkey_age"] == test_parsed_label.get(22).value
 True
 >>> test_parsed_label["monkey_age"]
 <pyds.values.Real object at 0x...>

A statement can also be removed using it's identifier::

 >>> del test_parsed_label["dates_and_times"]["times"]["one"]
 >>> del test_parsed_label["monkey_age"]
 >>> del test_parsed_label["monkey_group"]
 >>> del test_parsed_label["monkey_object"]
 >>> "one" in test_parsed_label["dates_and_times"]["times"]
 False
 >>> "monkey_age" in test_parsed_label
 False
 >>> "monkey_group" in test_parsed_label
 False
 >>> "monkey_object" in test_parsed_label
 False
 

Serializing
-----------
You can serialize a :class:`Label` object into a string by calling the built-in 
:func:`str` function on it::

 >>> print(str(test_parsed_label)) # doctest: +SKIP
 PDS_VERSION_ID     = PDS3
 INSERTED_ATTR      = 5
 ATTR_BLHA          = 2000
 NUMBER_OF_DAYS     = 2
 RATIO_OF_X         = 2.0
 ID                 = "lk32j4kajsdk1asdadd8asd8"
 NAMESPACED:ATTR    = 200
 ^POINT_TO_X        = 500
 ^POINT_TO_Y        = "blha.txt"
 GROUP              = INTEGERS
  ONE   = 0
  TWO   = 123
  THREE = 440
  FOUR  = -1500000
 END_GROUP          = INTEGERS
 GROUP              = BASED_INTEGERS
  ONE   = 2#1001011#
  TWO   = 8#113#
  THREE = 10#75#
  FOUR  = 16#+4B#
  FIVE  = 16#-4B#
 END_GROUP          = BASED_INTEGERS
 GROUP              = REAL_NUMBERS
  ONE   = 0.0
  TWO   = 123.0
  THREE = 1234.56
  FOUR  = -0.9981
  FIVE  = -0.001
  SIX   = 314590.0
 END_GROUP          = REAL_NUMBERS
 GROUP              = NUMBERS_WITH_UNITS
  INT           = 5 <KM/SEC/SEC>
  REAL          = 5.11 <M/SEC>
  BASED_INTEGER = 2#1001011# <APPLES>
 END_GROUP          = NUMBERS_WITH_UNITS
 OBJECT             = DATES_AND_TIMES
  GROUP      = DATES
   ONE   = 1990-07-04
   TWO   = 1990-158
   THREE = 2001-01
  END_GROUP  = DATES
  OBJECT     = TIMES
   TWO        = 15:24:12Z
   THREE      = 01:10:39.4575+07
  END_OBJECT = TIMES
  GROUP      = DATE_TIMES
   ONE   = 1990-07-04T12:00
   TWO   = 1990-158T15:24:12Z
   THREE = 2001-01T01:10:39.457591+07
  END_GROUP  = DATE_TIMES
 END_OBJECT         = DATES_AND_TIMES
 TEXT1              = "blha blha BLHA BLHA                blha
          blha blha blha"
 TEXT2              = "blha blha blha. Any character but a quotation mark."
 TEXT3              = ""
 SYMBOL1            = 'ONE-OR-MORE-CHARS EXCEPT THE APOSTROPHE ON ONE LINE'
 ATTR_IDENTIFIER    = ATTR_IDENTIFIER_VALUE
 A_1D_SEQUENCE      = (0.2056, 0.0068, 0.0167, 0.0934, 0.0483, 0.056)
 A_2D_SEQUENCE      = ((0, 1008), (1009, 1025), (1026, 1043))
 A_SET              = {'RED', 'BLUE', 'HAZEL', 'GREEN'}
 END  

You can also call the built-in :func:`bytes` function on it to get an ascii byte
string instead of a Unicode string::

 >>> bytes(test_parsed_label) == str(test_parsed_label).encode("ascii")
 True

The serialized string is a valid PDS label that other readers can parse::
 
 >>> bytes(pyds.parse(bytes(test_parsed_label))) == bytes(test_parsed_label) # doctest: +SKIP
 True

.. vim: tabstop=1 expandtab
