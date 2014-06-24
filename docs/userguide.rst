User Guide
==========
.. currentmodule:: pds

.. _parsing:

Parsing
-------
To work with an existing PDS label, first parse it into a :class:`Label` object
using the :func:`parse` function::

 >>> import pds
 >>> test_label = pds.parse(
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
 >>> test_label
 <pds.Label object at 0x...>


You can then interact with the :class:`Label` object to read or manipulate
properties of the label. See the discussion :ref:`below<label>` for details.

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
   
   The :func:`parse` function can only operate on :obj:`bytes` objects.
   Providing a :obj:`str` object will raise an error::

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


Statements
----------
A PDS label is made up of a series of statements, which can be of different
types.
They are represented in this module by instances of an :class:`Attribute`,
a :class:`Group`, or an :class:`Object`.

.. rubric:: Attribute

An *attribute assignment statement*, which assigns some value to an attribute,
is represented by an :class:`Attribute` object.
It is instantiated with an identifier and a value::

 >>> test_attr = pds.Attribute("test_attribute", pds.Integer(5))
 >>> test_attr
 <pds.Attribute object at 0x...>

The value must be an instance of one of the value types discussed
:ref:`below<values>`::

 >>> pds.Attribute("test_attribute", 5)
 Traceback (most recent call last):
 ...
 TypeError: value is not an instance of Value
 
The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pds.Attribute("12_not_valid", pds.Integer(5))
 Traceback (most recent call last):
  ...
 ValueError: invalid identifier '12_not_valid'
 >>> pds.Attribute("THIS_is_VaLiD", pds.Integer(5))
 <pds.Attribute object at 0x...>

The identifier can also be *namespaced* by preceding it with another
identifier and a colon::

 >>> pds.Attribute("namespace_identifier:test_attribute", pds.Integer(5))
 <pds.Attribute object at 0x...>

.. note ::

   Although the PDS specification distinguishes between a *pointer statement*
   and an attribute assignment statement, this module does not.
   A pointer statement is also represented with an :class:`Attribute` object by
   preceding the identifier with a caret (``^``)::

    >>> pds.Attribute("^THIS_POINT_TO_SOMETHING", pds.Integer(5))
    <pds.Attribute object at 0x...>
 
To access the identifier and value of an :class:`Attribute` object, use the
:attr:`Attribute.identifier` and :attr:`Attribute.value` attributes
respectively::

 >>> test_attr.identifier
 'TEST_ATTRIBUTE'
 >>> test_attr.value
 <pds.Integer object at 0x...>

To get the PDS serialized string representation of an :class:`Attribute` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_attr))
 TEST_ATTRIBUTE = 5


.. rubric:: Group

A *group statement*, which groups other attribute assignment statements,
is represented by a :class:`Group` object.
It is instantiated with an identifier and a :class:`GroupStatements` object::

 >>> test_group = pds.Group(
 ...  "test_group",
 ...  pds.GroupStatements(
 ...   pds.Attribute("nested_attr_1", pds.Integer(5)),
 ...   pds.Attribute("nested_attr_2", pds.Real(10.122))
 ...  )
 ... )
 >>> test_group
 <pds.Group object at 0x...>
 
A :class:`GroupStatements` object is a container for the nested statements of
a group statement. It behaves just like a :class:`Label` object, except that it
can only contain :class:`Attribute` objects::

 >>> pds.GroupStatements(pds.Attribute("test", pds.Integer(5)))
 <pds.GroupStatements object at 0x...>
 >>> pds.GroupStatements(pds.Group("test", pds.GroupStatements()))
 Traceback (most recent call last):
  ...
 TypeError: statement is not an instance of Attribute
 >>> pds.GroupStatements(pds.Object("test", pds.ObjectStatements()))
 Traceback (most recent call last):
  ...
 TypeError: statement is not an instance of Attribute

The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pds.Group(
 ...  "123 this is not valid",
 ...  pds.GroupStatements(
 ...   pds.Attribute("nested_attr_1", pds.Integer(5))
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
 <pds.GroupStatements object at 0x...>
 >>> test_group.statements == test_group.value
 True
 
To get the PDS serialized string representation of a :class:`Group` object,
call the built-in :func:`str` function on it::

 >>> print(str(test_group)) # doctest: +NORMALIZE_WHITESPACE
 GROUP     = TEST_GROUP
  NESTED_ATTR_1 = 5
  NESTED_ATTR_2 = 10.122
 END_GROUP = TEST_GROUP
 

.. rubric:: Object

An *object statement*, which groups other statements (of all types), is 
represented by an :class:`Object` object.
It is instantiated with an identifier and a :class:`ObjectStatements` object::

 >>> test_object = pds.Object(
 ...  "test_object",
 ...  pds.ObjectStatements(
 ...   pds.Attribute("nested_attr_1", pds.Integer(5)),
 ...   pds.Attribute("nested_attr_2", pds.Real(10.122)),
 ...   pds.Group(
 ...    "nested_group_1",
 ...    pds.GroupStatements(
 ...     pds.Attribute("nested_attr_1", pds.Integer(122)),
 ...     pds.Attribute("nested_attr_2", pds.Integer(22322))
 ...    )
 ...   ),
 ...   pds.Group(
 ...    "nested_group_2",
 ...    pds.GroupStatements(
 ...     pds.Attribute("nested_attr_1", pds.Real(5.3322)),
 ...     pds.Attribute("nested_attr_2", pds.Real(3.14159)),
 ...    )
 ...   ),
 ...   pds.Object(
 ...    "nested_object",
 ...    pds.ObjectStatements(
 ...     pds.Attribute("nested_attr", pds.Integer(5))
 ...    )
 ...   )
 ...  )
 ... )
 >>> test_object
 <pds.Object object at 0x...>
 
An :class:`ObjectStatements` object is a container for the nested statements of
an object statement.
It behaves just like a :class:`Label` object, meaning it can contain all three
types of statements, including other object statements.
There is no limit to the depth to which object statements may be nested::

 >>> pds.ObjectStatements(pds.Attribute("test", pds.Integer(5)))
 <pds.ObjectStatements object at 0x...>
 >>> pds.ObjectStatements(pds.Group("test", pds.GroupStatements()))
 <pds.ObjectStatements object at 0x...>
 >>> pds.ObjectStatements(
 ...  pds.Object(
 ...   "test", 
 ...   pds.ObjectStatements(
 ...    pds.Object(
 ...     "test2", 
 ...     pds.ObjectStatements(
 ...      pds.Object("test3", pds.ObjectStatements())
 ...     )
 ...    )
 ...   )
 ...  )
 ... )
 <pds.ObjectStatements object at 0x...>
 
The identifier must be a valid PDS identifier
(i.e. ``letter[letter|digit|_letter|_digit]*``).
It is converted to an upper case string and stored as such internally::

 >>> pds.Object(
 ...  "123 this is not valid",
 ...  pds.ObjectStatements(
 ...   pds.Attribute("nested_attr_1", pds.Integer(5))
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
 <pds.ObjectStatements object at 0x...>
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
contain the following types of values.

.. rubric:: Numeric

A numeric value is represented by an :class:`Integer`, a :class:`BasedInteger`,
or a :class:`Real` object::

 >>> pds.Integer(1000)
 <pds.Integer object at 0x...>
 >>> pds.BasedInteger(2, "1111")
 <pds.BasedInteger object at 0x...>
 >>> pds.Real(10.29932232)
 <pds.Real object at 0x...>
 
A :class:`BasedInteger` object is used to represent an integer specified in a
particular radix/base (i.e. binary, hexadecimal, etc). It is instantiated by
providing the radix as the first argument and the digits as the second
argument::

 >>> pds.BasedInteger(2, "1111")
 <pds.BasedInteger object at 0x...>
 >>> pds.BasedInteger(16, "f")
 <pds.BasedInteger object at 0x...>
 >>> pds.BasedInteger(10, "15")
 <pds.BasedInteger object at 0x...>
 
All three types of numeric values can also have units.
Units are represented by a :class:`Units` object, which is instantiated
with a *units expression* describing the units.
Units expressions are discussed in detail in the PDS documentation,
but basically they must have the form, ``units_factor[[*|/]units_factor]*``,
where *units_factor* is ``units_identifier[**integer]``. It is converted to
an upper case string and set to the :attr:`Units.expression` attribute::

 >>> pds.Units("km")
 <pds.Units object at 0x...>
 >>> pds.Units("km**2").expression
 'KM**2'
 >>> pds.Units("Km**2*sec**-1").expression
 'KM**2*SEC**-1'
 >>> pds.Units("J/S").expression
 'J/S'

To create a numeric value with units, provide a :class:`Units` object
as the last argument::

 >>> test_int = pds.Integer(1000, pds.Units("KM"))
 >>> test_based_int = pds.BasedInteger(2, "1111", pds.Units("BYTES"))
 >>> test_real = pds.Real(10.29932232, pds.Units("SEC"))
 
This :class:`Units` object can be accessed later using the ``units`` attribute::

 >>> test_int.units.expression
 'KM'
 >>> test_based_int.units.expression
 'BYTES'
 >>> test_real.units.expression
 'SEC'
 
The ``units`` attribute will be :obj:`None` if a numeric value does not have
units::
 
 >>> pds.Integer(5).units == None
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

:attr:`BasedInteger.value` is the base-10 integer representation of the
:class:`BasedInteger` object's value.
The base/radix and the digits of a :class:`BasedInteger` object can be accessed
using the attributes :attr:`BasedInteger.radix` and :attr:`BasedInteger.digits`
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

.. rubric:: Temporal

.. rubric:: Text

.. rubric:: Symbol

.. rubric:: Identifier

.. rubric:: Set

.. rubric:: Sequence


.. _label:

Label
-----
A :class:`Label` object is analogous to a PDS label.
You can either instantiate one directly, if you want to create a new PDS label
or, as discussed :ref:`above <parsing>`, use the :func:`parse` function to
create one from an existing PDS label.

A :class:`Label` is a container for a sequence of statements.

:class:`Label` implements a list like interface for manipulating the statements
it contains.
For example, you can add statements to it using :meth:`Label.insert`
and :meth:`Label.append`::
 
 >>> test_stmt_1 = pds.Attribute("test1", pds.Integer(5))
 >>> test_stmt_2 = pds.Attribute("test2", pds.Real(10))
 >>> test_label.insert(0, test_stmt_1)
 >>> test_label.append(test_stmt_2)

Or retrieve statements from it using :meth:`Label.get`::

 >>> test_label.get(0) == test_stmt_1
 True
 >>> test_label.get(-1) == test_stmt_2
 True
 
And remove statements from it using :meth:`Label.pop`::
 
 >>> test_label.pop(0) == test_stmt_1
 True
 >>> test_label.get(0) == test_stmt_1
 False
 >>> test_label.pop(-1) == test_stmt_2
 True
 >>> test_label.get(-1) == test_stmt_2
 False


Serializing
-----------

.. vim: tabstop=1 expandtab
