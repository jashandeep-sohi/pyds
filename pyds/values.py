# vim: filetype=python3 tabstop=2 expandtab

# pyds
# Copyright (C) 2015 Jashandeep Sohi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import abc

from re import compile as re_compile
from collections.abc import MutableSet, MutableSequence

__all__ = (
  "Value",
  "Scalar",
  "Units",
  "Numeric",
  "Integer",
  "BasedInteger",
  "Real",
  "Text",
  "Symbol",
  "Identifier",
  "Time",
  "Date",
  "DateTime",
  "Set",
  "Sequence1D",
  "Sequence2D",
)

class Value(object, metaclass = abc.ABCMeta):
  """
  Base class for PDS value types.
  
  .. note::
      This is an abstract base class and therefore cannot be instantiated
      directly.
  
  .. seealso::
      :class:`Scalar`, :class:`Set`, :class:`Sequence1D`, :class:`Sequence2D`
  """
  
  @abc.abstractmethod
  def __init__(self, *args, **kwargs):
    pass

class Scalar(Value):
  """
  Base class for PDS scalar value types.
  
  .. note::
      This is an abstract base class and therefore cannot be instantiated
      directly.
      
  .. seealso::
      :class:`Numeric`, :class:`Date`, :class:`Time`, :class:`DateTime`,
      :class:`Text`, :class:`Symbol`, :class:`Identifier`
  """
  
  pass
    
class Units(object):
  """
  Represents a PDS units expression.
  
  Parameters
    - `expression` (:obj:`str`)
    
      An expression specifying the units.
      
    - `validate` (:obj:`True` or :obj:`False`)
      
      Whether `expression` should be checked to see if it's a valid units
      expression. 
  
  Raises
    - :exc:`ValueError`
      
      If `validate` is :obj:`True` and `expression` is not valid.
  
  Attributes
    .. attribute:: expression
      
        Units expression.
        A :obj:`str` instance.
        Read-only.
  """
  
  _VALID_RE = re_compile(r"""(?xi)
    (?:
    (?:
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
    )
    (?:\*\*[+-]?[0-9]+)?
    )
    (?:
      [*/]
      (?:
      (?:
      (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
      (?:[a-z](?:_?[a-z0-9])*)
      )
      (?:\*\*[+-]?[0-9]+)?
      )
    )*
  """)
    
  def __init__(self, expression, validate = True):
    if validate and not self._VALID_RE.fullmatch(expression):
      raise ValueError("invalid expression {!r}".format(expression))
    
    self.expression = expression.upper()
  
  def __eq__(self, other):
    if isinstance(other, Units):
      return self.expression == other.expression
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Units):
      return self.expresion != other.expression
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash(self.expression)
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "<{}>".format(self.expression)

class Numeric(Scalar):
  """
  Base class for PDS numeric value types.
  
  .. note::  
      This is an abstract base class and therefore cannot be instantiated
      directly.
  
  .. seealso::
      :class:`Integer`, :class:`BasedInteger`, :class:`Real`
  """
  
  @abc.abstractmethod
  def __init__(self, value, units = None):
    self.value = value
    
    if units is not None:
      if not isinstance(units, Units):
        raise TypeError("units is not an instance of Units")
    self.units = units
   
  def __int__(self):
    """
    Return :attr:`value` as an :obj:`int`.
    """
    return int(self.value)
    
  def __float__(self):
    """
    Return :attr:`value` as a :obj:`float`.
    """
    return float(self.value)
    
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}{}".format(
      self.value,
      " {}".format(self.units) if self.units else ""
    )
    
class Integer(Numeric):
  """
  Represents a PDS integer value.
  
  Parameters
    - `value` (:obj:`int`)
      
      Value of the integer.
    
    - `units` (:obj:`None` or :class:`Units`)
    
      The units associated with the integer.
    
  Raises
    - :exc:`TypeError`
    
      If `units` is not :obj:`None` **and** `units` is not an instance of 
      :class:`Units`.
    
  Attributes
    .. attribute:: value
        
        Value of the integer.
        Instance of :obj:`int`.
        Read-only.
        
    .. attribute:: units
    
        Units associated with the integer.
        :obj:`None` or a :class:`Units` instance.
        Read-only.
  """
  
  def __eq__(self, other):
    if isinstance(other, Integer):
      return self.value == other.value and self.units == other.units
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Integer):
      return self.value != other.value or self.units != other.units
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash((self.value, self.units))
  
  def __init__(self, value, units = None):
    super().__init__(int(value), units)
    
class BasedInteger(Numeric):
  """
  Represents a PDS based integer value.
  
  Parameters
    - `radix` (:obj:`int`)
        
      Base of the integer.
        
    - `digits` (:obj:`str`)
    
      The digits of the integer in base `radix`.
      
    - `units` (:obj:`None` or :class:`Units`)
      
      The units associated with the integer.
  
  Raises
    - :exc:`ValueError`
    
      If `radix` is not between 2 and 16.
      
    - :exc:`TypeError`
      
      If `units` is not :obj:`None` **and** `units` is not an instance of 
      :class:`Units`.

  Attributes
    .. attribute:: radix
    
        Base of the integer.
        A :obj:`int` instance.
        Read-only.
        
    .. attribute:: digits
    
        Digits of the integer.
        A :obj:`str` instance.
        Read-only.
        
    .. attribute:: value
        
        Value of the integer in base 10.
        A :obj:`int` instnace.
        Read-only.
        
    .. attribute:: units
        
        Units associated with the integer.
        A :obj:`str` instance.
        Read-only.
  """
    
  def __init__(self, radix, digits, units = None):
    radix = int(radix)
    if radix < 2 or radix > 16:
      raise ValueError("radix is not between 2 and 16")
    
    super().__init__(int(digits, radix), units)
    self.radix = radix
    self.digits = digits.upper()
  
  def __eq__(self, other):
    if isinstance(other, BasedInteger):
      return self.radix == other.radix and self.digits == other.digits and \
        self.units == other.units
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, BasedInteger):
      return self.radix != other.radix or self.digits != other.digits or \
        self.units != other.units
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash((self.radix, self.digits, self.units))  
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}#{}#{}".format(
      self.radix,
      self.digits,
      " {}".format(self.units) if self.units else ""
    )

class Real(Numeric):
  """
  Represents a PDS real value.
  
  Parameters
    - `value` (:obj:`float`)
        
      Value of the real number.
      
    - `units` (:obj:`none` or :class:`Units`)
    
      Units associated with the real number.
  
  Raises
    - :exc:`TypeError`
    
      If `units` is not :obj:`None` **and** `units` is not an instance of 
      :class:`Units`.
  
  Attributes
    .. attribute:: value
        
        Value of the real number.
        A :obj:`float` instance.
        Read-only.
        
    .. attribute:: units
    
        Units associated with the real number.
        A :obj:`str`: instance.
        Read-only.
  """
  
  def __init__(self, value, units = None):
    super().__init__(float(value), units)
  
  def __eq__(self, other):
    if isinstance(other, Real):
      return self.value == other.value and self.units == other.units
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Real):
      return self.value != other.value or self.units != other.units
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash((self.value, self.units))  

class Text(Scalar):
  """
  Represents a PDS text value.
  
  Parameters
    - `value` (:obj:`str`)
        
      The text value.
        
    - `validate` (:obj:`True` or :obj:`False`)
    
      Whether `value` should be checked to see if it's a valid text value.  
    
  Raises
    - :exc:`ValueError`
    
      If `validate` is :obj:`True` and `value` is not a valid PDS text value.
    
  Attributes
    .. attribute:: value
    
        The text value.
        :obj:`str` instance.
        Read-only.
  """
  
  _VALID_RE = re_compile(r'[\x00-\x21\x23-\x7f]*')
    
  def __init__(self, value, validate = True):
    if validate and not self._VALID_RE.fullmatch(value):
      raise ValueError("invalid value {!r}".format(value))
      
    self.value = value
  
  def __eq__(self, other):
    if isinstance(other, Text):
      return self.value == other.value
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Text):
      return self.value != other.value
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash(self.value)  
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return '"{}"'.format(self.value)
    

class Symbol(Scalar):
  """
  Represents a PDS symbol value.
  
  Parameters
    - `value` (:obj:`str`)
      
      The symbol value.
      
    - `validate` (:obj:`bool`)
    
      Whether `value` should be checked to see if it's a valid symbol value.
  
  Raises
    - :exc:`ValueError`
    
      If `value` is not a valid PDS symbol.
  
  Attributes
    .. attribute:: value
    
        The symbol value.
        :obj:`str`: instance.
        Read-only.
  """
  
  _VALID_RE = re_compile(r'[\x20-\x26\x28-\x7e]+')
  
  def __init__(self, value, validate = True):
    if validate and not self._VALID_RE.fullmatch(value):
      raise ValueError("invalid value {!r}".format(value))
    
    self.value = value.upper()
  
  def __eq__(self, other):
    if isinstance(other, Symbol):
      return self.value == other.value
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Symbol):
      return self.value != other.value
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash(self.value)  
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "'{}'".format(self.value)


class Identifier(Scalar):
  """
  Represents a PDS identifier value.
  
  Parameters
    - `value` (:obj:`str`)
    
      Identifier value.
      
    - `validate` (:obj:`True` or :obj:`False`)
    
      Whether `value` should be checked to see if it's a valid identifier value.
    
  Raises
    - :exc:`ValueError`
    
      If `value` is not a valid PDS identifier.
    
  Attributes
    .. attribute:: value
  """
  
  _VALID_RE = re_compile("""(?xi)
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
  """)
  
  def __init__(self, value, validate = True):
    if validate and not self._VALID_RE.fullmatch(value):
      raise ValueError("invalid value {!r}".format(value))
    
    self.value = value.upper()
  
  def __eq__(self, other):
    if isinstance(other, Identifier):
      return self.value == other.value
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Identifier):
      return self.value != other.value
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash(self.value)  
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}".format(self.value)


class Time(Scalar):
  """
  Represents a PDS time value.
  
  Parameters
    - `hour` (:obj:`int`)
    
    - `minute` (:obj:`int`)
    
    - `second` (:obj:`None` or :obj:`float`)
    
    - `utc` (:obj:`True` or :obj:`False`)
      
      Whether the time is in UTC or not.
      
    - `zone_hour` (:obj:`None` or :obj:`int`)
    
      If `utc` is :obj:`True` and `zone_hour` is not :obj:`None`, `zone_hour`
      is stored, but when :class:`Time` is serialized, it's serialized ignoring
      `zone_hour`.
      
    - `zone_minute` (:obj:`None` or :obj:`int`)
    
  Raises
    - :exc:`ValueError`
    
      - If `hour` is not between 0 and 23.
      - If `minute` is not between 0 and 59.
      - If `second` is not :obj:`None` **and** not between 0 and 59.
      - If `zone_hour` is not :obj:`None` **and** not between -12 and 12.
      - If `zone_hour` is not :obj:`None` **and** `zone_minute` is not between 0
        and 59.
  
  Attributes
    .. attribute:: hour
        
        :obj:`int`. Read-only.
        
    .. attribute:: minute
    
        :obj:`int`. Read-only.
        
    .. attribute:: second
    
        :obj:`float`. Read-only.
        
    .. attribute:: utc
        
        Whether :class:`Time` is in UTC.
        :obj:`True` or :obj:`False`. Read-only.
        
    .. attribute:: zone_hour
    
        :obj:`None` or :obj:`int`. Read-only.
        
    .. attribute:: zone_minute
        
        :obj:`None` or :obj:`int`. Read-only.
  """
    
  def __init__(self,
    hour,
    minute, 
    second = None,
    utc = False,
    zone_hour = None,
    zone_minute = None
  ):
    hour = int(hour)
    minute = int(minute)
    
    if hour < 0 or hour > 23:
      raise ValueError("hour is not between 0 and 23")
    
    if minute < 0 or minute > 59:
      raise ValueError("minute is not between 0 and 59")
      
    if second is not None:
      second = float(second)
      if second < 0 or second > 59:
        raise ValueError("second is not between 0 and 59")
    
    if not utc:
      if zone_hour is not None:
        zone_hour = int(zone_hour)
        if zone_hour < -12 or zone_hour > 12:
          raise ValueError("zone hour is not between -12 and 12")
        
        if zone_minute is not None:
          zone_minute = int(zone_minute)
          if zone_minute < 0 or zone_minute > 59:
            raise ValueError("zone minute is not between 0 and 59")
    else:
      zone_hour = None
      zone_minute = None
    
    self.hour = hour
    self.minute = minute
    self.second = second
    self.utc = bool(utc)
    self.zone_hour = zone_hour
    self.zone_minute = zone_minute

  def __eq__(self, other):
    if isinstance(other, Time):
      return self.hour == other.hour and self.minute == other.minute and \
        self.second == other.second and self.utc == other.utc and \
        self.zone_hour == other.zone_hour and \
        self.zone_minute == other.zone_minute
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Time):
      return self.hour != other.hour or self.minute != other.minute or \
        self.second != other.second or self.utc != other.utc or \
        self.zone_hour != other.zone_hour or \
        self.zone_minute != other.zone_minute
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash((
      self.hour,
      self.minute,
      self.second,
      self.utc,
      self.zone_hour,
      self.zone_minute
    ))
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    h_m_s = "{:02d}:{:02d}{}".format(
      self.hour,
      self.minute,
      ":{:015.12f}".format(self.second).rstrip("0").rstrip(".") 
        if self.second is not None else ""
    )
    if self.utc:
      return "{}Z".format(h_m_s)
    elif self.zone_hour is not None:
      return "{}{}".format(
        h_m_s,
        "{:+03d}{}".format(
          self.zone_hour,
          ":{:02d}".format(self.zone_minute)
            if self.zone_minute is not None else ""
        )
      )
    else:
      return h_m_s
    
class Date(Scalar):
  """
  Represents a PDS date value.
  
  Parameters
    - `year` (:obj:`int`)
    
    - `month` (:obj:`None` or :obj:`int`)
      
      If :obj:`None`, then `day` is interperated as the day of the year instead
      of as the day of the month, and :class:`Date` serialized in 'day-of-year'
      format.
    
    - `day` (:obj:`int`)
    
      The day of the month if `month` is not :obj:`None`. Otherwise it's the
      day of the year.
    
  Raises
    - :exc:`ValueError`
    
      - If `month` is not :obj:`None` **and** not between 1 and 12.
      - If `month` is not :obj:`None` **and** `day` is not between 1 and the 
        number of days in the month `month`.
      - If `month` is :obj:`None` **and** `day` is not between 1 and the number
        of days in the year `year` (365 or 366 depending on if it's a leap 
        year).
  
  Attributes
    .. attribute:: year
        
        :obj:`int`. Read-only.
        
    .. attribute:: month
        
        :obj:`None` or :obj:`int`. Read-only.
        
    .. attribute:: day
        
        Day of year if :attr:`month` is :obj:`None`. Otherwise, day of the month
        of month :attr:`month`. :obj:`int`. Read-only.
  """
  
  MONTH_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  
  def __init__(self, year, month, day):
    year = int(year)
    day = int(day)
    leap_year = year % 4 and (year % 100 != 0 or year % 400 == 0)
    
    if month is None:  
      max_day = 365 + leap_year
    else:
      month = int(month)
      if month < 1 or month > 12:
        raise ValueError("month is not between 1 and 12")
      max_day = self.MONTH_DAYS[month] + (month == 3 and leap_year)
      
    if day < 1 or day > max_day:
      raise ValueError("day is not between 1 and {}".format(max_day))
    
    self.year = year
    self.month = month
    self.day = day
  
  def __eq__(self, other):
    if isinstance(other, Date):
      return self.year == other.year and self.month == other.month and \
        self.day == other.day
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, Date):
      return self.year != other.year or self.month != other.month or \
        self.day != other.day
    else:
      return NotImplemented
  
  def __hash__(self):
    return hash((
      self.year,
      self.month,
      self.day
    ))  
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}-{}".format(
      self.year,
      "{:02d}".format(self.day) if self.month is None
        else "{:02d}-{:02d}".format(self.month, self.day)
    )
     
class DateTime(Scalar):
  """
  Represents a PDS date-time value.
  
  Parameters
    - `year` (:obj:`int`)
    - `month` (:obj:`None` or :obj:`int`)
      
      If :obj:`None`, then `day` is interperated as the day of the year instead
      of as the day of the month, and :class:`Date` serialized in 'day-of-year'
      format.
      
    - `day` (:obj:`int`)
    
      The day of the month if `month` is not :obj:`None`. Otherwise it's the
      day of the year.
      
    - `hour` (:obj:`int`)
    - `minute` (:obj:`int`)
    - `second` (:obj:`None` or :obj:`float`)
    - `utc` (:obj:`True` or :obj:`False`)
      
      Whether the time is in UTC or not.
      
    - `zone_hour` (:obj:`None` or :obj:`int`)
    
      If `utc` is :obj:`True` and `zone_hour` is not :obj:`None`, `zone_hour`
      is stored, but when :class:`Time` is serialized, it's serialized ignoring
      `zone_hour`.
      
    - `zone_minute` (:obj:`None` or :obj:`int`)    
    
  Raises
    :exc:`ValueError`
    
    - If `month` is not :obj:`None` **and** not between 1 and 12.
    - If `month` is not :obj:`None` **and** `day` is not between 1 and the 
      number of days in the month `month`.
    - If `month` is :obj:`None` **and** `day` is not between 1 and the number of
      days in the year `year` (365 or 366 depending on if it's a leap year).
    - If `hour` is not between 0 and 23.
    - If `minute` is not between 0 and 59.
    - If `second` is not :obj:`None` **and** not between 0 and 59.
    - If `zone_hour` is not :obj:`None` **and** not between -12 and 12.
    - If `zone_hour` is not :obj:`None` **and** `zone_minute` is not between 0
      and 59.
  
  Attributes
    .. attribute:: date
    
        Instance of :class:`Date`. Read-only.
        
    .. attribute:: time
    
        Instance of :class:`Time`. Read-only.
  """
    
  def __init__(
    self,
    year, 
    month, 
    day, 
    hour, 
    minute, 
    second = None,
    utc = False,
    zone_hour = None,
    zone_minute = None
  ):
    self.date = Date(year, month, day)
    self.time = Time(hour, minute, second, utc, zone_hour, zone_minute)
  
  def __eq__(self, other):
    if isinstance(other, DateTime):
      return self.date == other.date and self.time == other.time
    else:
      return NotImplemented
  
  def __ne__(self, other):
    if isinstance(other, DateTime):
      return self.date != other.date or self.time != other.time
    else: 
      return NotImplemented
  
  def __hash__(self):
    return hash((self.date, self.time))
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}T{}".format(
      self.date,
      self.time
    )

class Set(Value, MutableSet):
  """
  Represents a PDS set value.
  
  """
  
  def __init__(self, *values):
    self._set = set()
    for value in values:
      self.add(value)
    
  def __contains__(self, value):
    """
    Test if set contains `value`.
    Return :obj:`True` if it exits and :obj:`False` otherwise.
    """
    return value in self._set
    
  def __iter__(self):
    """
    Return an :obj:`iterator` that iterates over the values in the set.
    
    Called by :func:`iter`.
    """
    return iter(self._set)
    
  def __len__(self):
    """
    Return the number of values in the set.
    
    Called by :func:`len`.
    """
    return len(self._set)
    
  def add(self, value):
    """
    Add `value` to the set.
    
    Parameters
      - `value` (:class:`Symbol` or :class:`Integer`)
    
    Raises
      - :exc:`TypeError`
        
        If value is not an instance of :class:`Symbol` or :class:`Integer`.
    """
    if isinstance(value, (Symbol, Integer)):
      self._set.add(value)
    else:
      raise TypeError("value is not an instance of Symbol or Integer")
  
  def discard(self, value):
    """
    Remove `value` from the set.
    """
    self._set.discard(value)
    
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{{{}}}".format(
      ", ".join(str(value) for value in self)
    )

class Sequence1D(Value, MutableSequence):
  """
  Represents a 1D PDS sequence value.
  
  """
  
  def __init__(self, *values):
    self._list = list()
    for v in values:
      self.append(v)
    
  def __getitem__(self, index):
    """
    Return value at index `index`.
    """
    return self._list[index]
    
  def __setitem__(self, index, value):
    """
    .. note::
        See :meth:`insert`.
    """
    self.insert(index, value)
    
  def __delitem__(self, index):
    """
    Remove the value at index `index`.
    """
    del self._list[index]
  
  def __len__(self):
    """
    Return the number of values in the sequence.
    """
    return len(self._list)
    
  def __iter__(self):
    """
    Return an :obj:`iterator` that iterates over the values in the sequence.
    """
    return iter(self._list)
    
  def insert(self, index, value):
    """
    Insert value `value` at index `index`.
    
    `value` must be an instance of :class:`Scalar`, otherwise raise
    :exc:`TypeError`.
    """
    if isinstance(value, Scalar):
      self._list.insert(index, value)
    else:
      raise TypeError("value is not an instance of Scalar")
      
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    
    Raises
      - :exc:`RuntimeError`
        
        If the sequence does not contain at least 1 value.
    """
    if len(self) < 1:
      raise RuntimeError("sequence does not contain at least 1 value")
      
    return "({})".format(
      ", ".join(str(value) for value in self)
    )

class Sequence2D(Sequence1D):
  """
  Represents a 2D PDS sequence value.
  """
  
  def insert(self, index, value):
    """
    Insert value `value` at index `index`.
    
    `value` must be an instance of :class:`Sequence1D`, otherwise raise
    :exc:`TypeError`.
    """
    if isinstance(value, Sequence1D):
      self._list.insert(index, value)
    else:
      raise TypeError("value is not an instance of Sequence1D")
