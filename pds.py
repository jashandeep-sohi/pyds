# pds - A Python module to read & write Planetary Data System (PDS) labels.
# v0.1.0 
# Copyright (C) 2014 Jashandeep Sohi
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

from weakref import WeakValueDictionary as _WeakValueDict, proxy as _weak_proxy
from re import compile as _re_compile
from collections.abc import MutableSet as _MutableSet
from collections.abc import MutableSequence as _MutableSequence
from datetime import date as _date, time as _time, datetime as _datetime
import abc

################
# Constants
################

# PDS labels are written in ODL (object description language) w/ additional
# constraints.
# -References: 
#   http://pds.jpl.nasa.gov/documents/sr/Chapter12.pdf (ODL)
#   http://pds.jpl.nasa.gov/documents/sr/Chapter05.pdf (PDS Labels) 
#
# Only ascii chars are allowed (i.e. no utf).
# Lexical tokens **may** be seperated by ascii whitespace.
#
# The following tuple of tuples defines all lexial tokens of ODL. It's used to
# build a single regexp, which can be used to match tokens in a byte string.
#
# The order in which the tokens are specified matters because tokens do not
# **have** to be delimted by whitespace. At least that's the understanding from
# the docs.
#
# Each lexical token is defined by a tuple of the form:
# (token_name, token_re, token_re_group_names)
# 
# - token_name is the a string specifing the token name/type,
# - token_re is a regexp string. Wirte this regexp assuming re.X & re.S flags
#   are set. A token_re may contain catching groups (i.e. (..)) but not named
#   catching groups (i.e. (?P<name>...)). Any catching groups should be named
#   in token_re_group_names.
# - token_re_group_names is a tuple of group names for any catching groups in
#   token_re. The order should match. Don't use token_name.
#   If there are no groups in token_re specify an empty tuple.

ODL_LEX_TOK_SPEC = (
  (
    "date_time",
    r"""
    ([0-9]+)[-]([0-9]+)(?:[-]([0-9]+))?
    T
    ([0-9]+)[:]([0-9]+)
    (?:
      [:]
      (
        [0-9]+(?:[.][0-9]*)?
        |
        [.][0-9]+
      )
    )?
    (?:
      (Z)
      |
      ([+-][0-9]+)(?:[:][0-9]+)?
    )?
    """,
    (
      "year", "doy_month", "day", "hour", "min",
      "sec", "zulu", "zone_hour", "zone_min"
    )
  ),
  (
    "time",
    r"""
    ([0-9]+)[:]([0-9]+)
    (?:
      [:]
      (
        [0-9]+(?:[.][0-9]*)?
        |
        [.][0-9]+
      )
    )?
    (?:
      (Z)
      |
      ([+-][0-9]+)(?:[:][0-9]+)?
    )?
    """,
    ("hour", "min", "sec", "zulu", "zone_hour", "zone_min")
  ),
  (
    "date",
    "([0-9]+)[-]([0-9]+)(?:[-]([0-9]+))?",
    ("year", "doy_month", "day")
  ),
  (
    "based_integer",
    "([0-9]+)[#]([+-]?[0-9a-zA-Z]+)[#]",
    ("radix", "digits")
  ),
  (
    "real",
    r"""
    [+-]?
    (?:
      [0-9]+(?:[.][0-9]*)?[eE][+-]?[0-9]+
      |
      [0-9]+[.][0-9]*
      |
      [.][0-9]+
    )
    """,
    ()
  ),
  (
    "integer",
    "[+-]?[0-9]+",
    (),
  ),
  (
    "text",
    '"([^"]*)"',
    ("string")
  ),
  (
    "symbol",
    r"'([^'\x00-\x1f\x7f]+)'",
    ("string",)
  ),
  (
    "identifier",
    "[a-zA-Z](?:[_]?[0-9a-zA-Z])*",
    ()
  ),
  (
    "comment",
    r"/\*([^\r\n\f\v]*)\*/.*?[\r\n\f\v]+",
    ("string",)
  ),
  (
    "newline",
    r"(?:\r\n|\r|\n)",
    ()
  ),
  (
    "special_char",
    "(\*\*|[:=,*/^<>(){}])",
    ()
  ) 
)

ODL_LEX_TOK_RE = _re_compile(
  r"""(?xs)
  [ \t\v\f]*
  (?:
    {}
  )
  [ \t\v\f]*
  """.format(
    "|".join("(?P<{}>{})".format(n,r) for n,r,g in ODL_LEX_TOK_SPEC)
  ).encode()
)

# This dict maps each token's groups to the corresponding group index in
# ODL_LEX_TOK_RE. This is used later when creating Token objects.
ODL_LEX_TOK_GROUPS_INDEX = {
  token_name: {
    group_name: ODL_LEX_TOK_RE.groupindex[token_name]+i
  for i, group_name in enumerate([token_name] + list(token_groups))
  }
for token_name, token_re, token_groups in ODL_LEX_TOK_SPEC
}


################
# Classes
################

class _DoubleLinkNode(object):

  __slots__ = ("prev", "next", "value", "__weakref__")
  
  def __init__(self, value = None):
    self.value = value

class _DoubleLinkedNodes(object):
  
  def __init__(self):
    self.root_hard = _DoubleLinkNode()
    self.root = _weak_proxy(self.root_hard)
    self.root.next = self.root
    self.root.prev = self.root
    self.length = 0

  def insert_node(self, node, index): 
    node_after = self.get_node(index)
    node_before = node_after.prev
    
    node.next = node_after
    node.prev = node_before
    
    node_before.next = node
    node_after.prev = _weak_proxy(node)
    
    self.length += 1
    return node
  
  def get_node(self, index):
    if index > len(self)/2:
      node = self.root
      for _ in range(len(self)-index):
        node = node.prev
    else:
      node = self.root.next
      for _ in range(index):
        node = node.next
    return node
  
  def remove_node(self, node):
    node_before, node_after = node.prev, node.next
    
    node_before.next = node_after
    node_after.prev = node_before
    
    self.length -= 1
    return node
  
  def __len__(self):
    return self.length 
  
class Statements(object):
  
  @property
  def max_identifier_width(self):
    return max(
      10,
      max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
    )
  
  def __init__(self):
    self._nodes = _DoubleLinkedNodes()
    self._dict = _WeakValueDict()
  
  @classmethod
  def from_iterable(cls, iterable):
    instance = cls()
    for statement in iterable:
      instance.append(statement)
    return instance
               
  def _insert(self, statement, index):
    index = max(0, len(self) + index) if index < 0 else min(len(self), index)
    new_node = self._nodes.insert_node(_DoubleLinkNode(statement), index)
    self._dict[statement.identifier] = new_node
  
  def _append(self, statement):
    self._insert(statement, len(self))
  
  def insert(self, statement, index):
    try:
      self._dict[statement.identifier]
    except KeyError:
      self._insert(statement, index)
    except AttributeError:
      raise TypeError("expected a Statement object")
    else:
      raise ValueError(
        "statement with identifier '{}' already exists".format(
          statement.identifier
        )
      )
    
  def append(self, statement):
    self.insert(statement, len(self))
  
  def get(self, index):
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      return self._nodes.get_node(index).value
       
  def pop(self, index):
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      node = self._nodes.get_node(index)
      return self._nodes.remove_node(node).value
  
  def __setitem__(self, key, value):    
    try:
      stmt = Attribute(key, value)
    except TypeError:
      if isinstance(value, GroupStatements):
        stmt = Group(key, value)
      elif isinstance(value, ObjectStatements):
        stmt = Object(key, value)
      else:
        raise TypeError("invalid value type")
    try:
      old_node = self._dict[stmt.identifier]
    except KeyError:
      self._append(stmt)
    else:
      old_node.value = stmt
  
  def __getitem__(self, key):
    return self._dict[key.upper()].value.value
    
  def __delitem__(self, key):
    node = self._nodes.remove_node(self._dict[key.upper()])
    del node
  
  def __contains__(self, key):
    try:
      self[key]
    except KeyError:
      return False
    else:
      return True
    
  def __iter__(self):
    current_node = self._nodes.root.next
    while current_node is not self._nodes.root:
      yield current_node.value
      current_node = current_node.next
  
  def __reversed__(self):
    current_node = self._nodes.root.prev
    while current_node is not self._nodes.root:
      yield current_node.value
      current_node = current_node.prev
    
  def __len__(self):
    return len(self._nodes)
  
  def __str__(self):
    width = str(self.max_identifier_width)
    return "\r\n".join(
      stmt._format("", width) for stmt in iter(self)
    )
      
  def __bytes__(self):
    return str(self).encode("ascii")

class Label(Statements):
  
  def __str__(self):
    return "{}\r\nEND ".format(super().__str__())
       
class GroupStatements(Statements):
  
  @Statements.max_identifier_width.getter
  def max_identifier_width(self):
    return max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
  
  def _insert(self, statement, index):
    if isinstance(statement, (Group, Object)):
      raise TypeError(
        "cannot have Group or Object statements in Group statements"
      )
    super()._insert(statement, index)
    
class ObjectStatements(Statements):
  pass

class Statement(object):
  
  VALID_IDENT_RE = _re_compile(r"""(?xi)
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
  """)
  
  @property
  def identifier(self):
    return self._identifier
  
  @identifier.setter
  def identifier(self, value):
    if not self.VALID_IDENT_RE.fullmatch(value):
      raise ValueError("invalid identifier '{}'".format(value))
    self._identifier = value.upper()
    
  @property
  def value(self):
    return self._value
    
  @value.setter
  def value(self, value):
    self._value = value
  
  def __init__(self, *args, **kwargs):
    raise NotImplementedError("base class may not be instantiated")
        
  def __str__(self):
    return self._format("", "")  

class Attribute(Statement):
  
  VALID_IDENT_RE = _re_compile("""(?xi)
    (?:
      (?:
        (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
        (?:[a-z](?:_?[a-z0-9])*)
      )
      :
      |
      \^
    )?
    (?:
      (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
      (?:[a-z](?:_?[a-z0-9])*)
    )
  """)
  
  @Statement.value.setter
  def value(self, value):
    if isinstance(value, str):
      self._value = value
    else:
      raise TypeError()
  
  def __init__(self, identifier, value):
    self.identifier = identifier
    self.value = value
      
  def _format(self, indent, width):
    return "{}{} = {}".format(
      indent,
      format(self.identifier, width),
      self.value
    )
          
class Group(Statement):
    
  @Statement.value.setter
  def value(self, value):
    if isinstance(value, GroupStatements):
      self._value = value
    else:
      self._value = GroupStatements.from_iterable(value)
    
  def __init__(self, identifier, group_statements):      
    self.identifier = identifier
    self.value = group_statements
    self.statements = self.value
    
  def _format(self, indent, width):
    sub_width = str(self.statements.max_identifier_width)
    sub_indent = indent + " "
    return "\r\n{}{} = {}\r\n{}\r\n{}{} = {}\r\n".format(
      indent,
      format("GROUP", width),
      self.identifier,
      "\r\n".join(
        stmt._format(sub_indent, sub_width) for stmt in iter(self.statements)
      ),
      indent,
      format("END_GROUP", width),
      self.identifier
    )
     
class Object(Statement):
  
  @Statement.value.setter
  def value(self, value):
    if isinstance(value, ObjectStatements):
      self._value = value
    else:
      self._value = ObjectStatements.from_iterable(value)
  
  def __init__(self, identifier, object_statements):
    self.identifier = identifier
    self.value = object_statements
    self.statements = self.value
    
  def _format(self, indent, width):
    sub_width = str(self.statements.max_identifier_width)
    sub_indent = indent + " "
    return "\r\n{}{} = {}\r\n{}\r\n{}{} = {}\r\n".format(
      indent,
      format("OBJECT", width),
      self.identifier,
      "\r\n".join(
        stmt._format(sub_indent, sub_width) for stmt in iter(self.statements)
      ),
      indent,
      format("END_OBJECT", width),
      self.identifier
    )
  
class Value(object, metaclass=abc.ABCMeta):
  @abc.abstractmethod
  def __init__(self, *args, **kwargs):
    pass

class Scalar(Value):
  pass
    
class Units(object):
  VALID_RE = _re_compile(r"""(?xi)
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
    if validate and not self.VALID_RE.fullmatch(expression):
      raise ValueError("invalid units expression {!r}".format(expression))
    
    self.expression = expression.upper()
  
  def __str__(self):
    return "<{}>".format(self.expression)

class Numeric(Scalar):
  
  @abc.abstractmethod
  def __init__(self, value, units):
    self.value = value
    if not units or isinstance(units, Units):
      self.units = units
    else:
      self.units = Units(units)
    
  def __int__(self):
    return int(self.value)
    
  def __float__(self):
    return float(self.value)
    
  def __str__(self):
    return "{}{}".format(
      self.value,
      " {}".format(self.units) if self.units else ""
    )
    
class Integer(Numeric):
  
  def __init__(self, value, units = ""):
    super().__init__(int(value), units)
    
class BasedInteger(Numeric):
    
  def __init__(self, radix, digits, units = ""):
    if radix < 2 or radix > 12:
      raise ValueError("radix must be between 2 and 12")
      
    super().__init__(int(digits, radix), units)
    self.radix = radix
    self.digits = digits
    
  def __str__(self):
    return "{}#{}#{}".format(
      self.radix,
      self.digits,
      " {}".format(self.units) if self.units else ""
    )

class Real(Numeric):

  def __init__(self, value, units = ""):
    super().__init__(float(value), units)
    

class Text(Scalar):
  VALID_RE = _re_compile(r'[\x00-\x21\x23-\x7f]*')
    
  def __init__(self, value, validate = True):
    if validate and not self.VALID_RE.fullmatch(value):
      raise ValueError("invalid text value {!r}".format(value))
      
    self.value = value
    
  def __str__(self):
    return '"{}"'.format(self.value)
    

class Symbol(Scalar):
  VALID_RE = _re_compile(r'[\x20-\x26\x28-\x7e]+')
  
  def __init__(self, value, validate = True):
    if validate and not self.VALID_RE.fullmatch(value):
      raise ValueError("invalid symbol value {!r}".format(value))
    
    self.value = value.upper()
    
  def __str__(self):
    return "'{}'".format(self.value)


class Identifier(Scalar):
  VALID_RE = _re_compile("""(?xi)
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
  """)
  
  def __init__(self, value, validate = True):
    if validate and not self.VALID_RE.fullmatch(value):
      raise ValueError("invalid identifier value {!r}".format(value))
    
    self.value = value.upper()
    
  def __str__(self):
    return "{}".format(self.value)


class Time(Scalar):
  
  @classmethod
  def local(cls, hour, minute, second = None):
    return cls(hour, minute, second, False)
    
  @classmethod
  def utc(cls, hour, minute, second = None):
    return cls(hour, minute, second, True)
    
  @classmethod
  def zoned(cls, hour, minute, second = None, zone_hour = 0, zone_min = None):
    return cls(hour, minute, second, False, zone_hour, zone_min)
  
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
      raise ValueError("hour must be between 0 and 23")
    
    if minute < 0 or minute > 59:
      raise ValueError("minute must be between 0 and 59")
      
    if second is not None:
      second = float(second)
      if second < 0 or second > 59:
        raise ValueError("second must be between 0 and 59")
    
    if zone_hour is not None:
      zone_hour = int(zone_hour)
      if zone_hour < -12 or zone_hour > 12:
        raise ValueError("zone hour must be between -12 and 12")
      
      if zone_minute is not None:
        zone_minute = int(zone_minute)
        if zone_minute < 0 or zone_minute > 59:
          raise ValueError("zone minute must be between 0 and 59")
    
    self.hour = hour
    self.minute = hour
    self.second = second
    self.utc = utc
    self.zone_hour = zone_hour
    self.zone_minute = zone_minute

  def __str__(self):
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
  
  MONTH_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

  @classmethod
  def doy(cls, year, day):
    return cls(year, None, day)
  
  def __init__(self, year, month, day):
    year = int(year)
    leap_year = year % 4 and (year % 100 != 0 or year % 400 == 0)
    
    if month is None:  
      max_day = 365 + leap_year
    else:
      month = int(month)
      if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
      max_day = self.MONTH_DAYS[month] + (month == 3 and leap_year)
      
    if day < 1 or day > max_day:
      raise ValueError("day must be between 1 and {}".format(max_day))
    
    self.year = year
    self.month = month
    self.day = day
    
  def __str__(self):
    return "{}-{}".format(
      self.year,
      "{:02d}".format(self.day) if self.month is None
        else "{:02d}-{:02d}".format(self.month, self.day)
    )
     
class DateTime(Scalar):
  
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
  
  def __str__(self):
    return "{}T{}".format(
      self.date,
      self.time
    )



################
# Functions
################

def _generate_tokens(byte_str):
  line_no = 1
  line_pos = -1
  for match in ODL_LEX_TOK_RE.finditer(byte_str):
    name = match.lastgroup
    if name == "newline":
      line_no += 1
      line_pos = match.end("newline") - 1
      continue
    yield {
      "name": name,
      "groups": {
        group_name: match.group(group_index)
      for group_name, group_index in ODL_LEX_TOK_GROUPS_INDEX[name].items()
      },
      "line": line_no,
      "column": match.start(name) - line_pos
    }


def parse(byte_string):
  tokens = _generate_tokens(byte_string)
      
  
  
# vim: tabstop=2 expandtab
