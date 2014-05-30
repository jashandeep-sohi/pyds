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
    "comment",
    r"/\*([^\r\n\f\v]*)\*/.*?[\r\n\f\v]+",
    ("string",)
  ),
  (
    "date_time",
    r"""
    ([0-9]+)(?:[-]([0-9]+))?[-]([0-9]+)
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
      "year", "month", "day", "hour", "minute",
      "second", "utc", "zone_hour", "zone_minute"
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
    ("hour", "minute", "second", "utc", "zone_hour", "zone_minute")
  ),
  (
    "date",
    "([0-9]+)(?:[-]([0-9]+))?[-]([0-9]+)",
    ("year", "month", "day")
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
    ("string",)
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
    "equal",
    "=",
    ()
  ),
  (
    "comma",
    ",",
    ()
  ),
  (
    "two_asterisk",
    "\*\*",
    ()
  ),
  (
    "asterisk",
    "\*",
    ()
  ),
  (
    "slant",
    "/",
    ()
  ),
  (
    "circumflex",
    "\^",
    ()
  ),
  (
    "open_bracket",
    "<",
    ()
  ),
  (
    "close_bracket",
    ">",
    ()
  ),
  (
    "open_paren",
    "[(]",
    ()
  ),
  (
    "close_paren",
    "[)]",
    ()
  ),
  (
    "open_brace",
    "{",
    ()
  ),
  (
    "close_brace",
    "}",
    ()
  ),
  (
    "colon",
    ":",
    ()
  )
)

ODL_LEX_TOK_RE = _re_compile(
  r"""(?xi)
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
  
class Statements(object, metaclass = abc.ABCMeta):
  
  @property
  def max_identifier_width(self):
    return max(
      10,
      max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
    )
  
  @abc.abstractmethod
  def __init__(self, *statements):
    self._nodes = _DoubleLinkedNodes()
    self._dict = _WeakValueDict()
    
    for statement in statements:
      self.append(statement)
               
  def _insert(self, index, statement):
    index = max(0, len(self) + index) if index < 0 else min(len(self), index)
    new_node = self._nodes.insert_node(_DoubleLinkNode(statement), index)
    self._dict[statement.identifier] = new_node
  
  def _append(self, statement):
    self._insert(len(self), statement)
  
  def insert(self, index, statement):
    if not isinstance(statement, Statement):
      raise TypeError("statement is not an instance of Statement")
    
    if statement.identifier in self:
      raise ValueError(
        "statement with identifier {!r} already exists".format(
          statement.identifier
        )
      )
    self._insert(index, statement)
    
  def append(self, statement):
    self.insert(len(self), statement)
  
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
      try:
        stmt = Group(key, value)
      except TypeError:
        try:
          stmt = Object(key, value)
        except TypeError:
          raise TypeError()
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
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
  
  def __str__(self):
    return "{}\r\nEND ".format(super().__str__())
       
class GroupStatements(Statements):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)  
  
  @Statements.max_identifier_width.getter
  def max_identifier_width(self):
    return max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
  
  def _insert(self, index, statement):
    if isinstance(statement, (Group, Object)):
      raise TypeError(
        "statement is an instance of Object or Group"
      )
    super()._insert(index, statement)
    
class ObjectStatements(Statements):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

class Statement(object, metaclass = abc.ABCMeta):
  
  VALID_IDENT_RE = _re_compile(r"""(?xi)
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
  """)
    
  @abc.abstractmethod
  def __init__(self, identifier, value, validate_identifier = True):    
    if validate_identifier and not self.VALID_IDENT_RE.fullmatch(identifier):
      raise ValueError("invalid identifier {!r}".format(identifier))
    
    self.identifier = identifier.upper()
    self.value = value
          
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
    
  def __init__(self, identifier, value, validate_identifier = True):
    if not isinstance(value, Value):
      raise TypeError("value is not an instance of Value")
    super().__init__(identifier, value, validate_identifier)
      
  def _format(self, indent, width):
    return "{}{} = {}".format(
      indent,
      format(self.identifier, width),
      self.value
    )
          
class Group(Statement):
        
  def __init__(self, identifier, group_statements, validate_identifier = True):
    if not isinstance(group_statements, GroupStatements):
      raise TypeError("group_statements is not an instance of GroupStatements")
      
    self.statements = group_statements
    super().__init__(identifier, self.statements, validate_identifier)
    
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
  
  def __init__(self, identifier, object_statements, validate_identifier = True):
    if not isinstance(object_statements, ObjectStatements):
      raise TypeError(
        "object_statements is not an instance of ObjectStatements"
      )
      
    self.statements = object_statements
    super().__init__(identifier, self.statements, validate_identifier)
    
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
  
class Value(object, metaclass = abc.ABCMeta):
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
      raise ValueError("invalid expression {!r}".format(expression))
    
    self.expression = expression
  
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
    radix = int(radix)
    if radix < 2 or radix > 12:
      raise ValueError("radix is not between 2 and 12")
    
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
      raise ValueError("invalid value {!r}".format(value))
      
    self.value = value
    
  def __str__(self):
    return '"{}"'.format(self.value)
    

class Symbol(Scalar):
  VALID_RE = _re_compile(r'[\x20-\x26\x28-\x7e]+')
  
  def __init__(self, value, validate = True):
    if validate and not self.VALID_RE.fullmatch(value):
      raise ValueError("invalid value {!r}".format(value))
    
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
      raise ValueError("invalid value {!r}".format(value))
    
    self.value = value.upper()
    
  def __str__(self):
    return "{}".format(self.value)


class Time(Scalar):
    
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
    
    if zone_hour is not None:
      zone_hour = int(zone_hour)
      if zone_hour < -12 or zone_hour > 12:
        raise ValueError("zone hour is not between -12 and 12")
      
      if zone_minute is not None:
        zone_minute = int(zone_minute)
        if zone_minute < 0 or zone_minute > 59:
          raise ValueError("zone minute is not between 0 and 59")
    
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

class Set(Value, _MutableSet):

  def __init__(self, *values):
    self._set = set()
    for value in values:
      self.add(value)
    
  def __contains__(self, value):
    return value in self._set
    
  def __iter__(self):
    return iter(self._set)
    
  def __len__(self):
    return len(self._set)
    
  def add(self, value):
    if isinstance(value, (Symbol, Integer)):
      self._set.add(value)
    else:
      raise TypeError("value is not an instance of Symbol or Integer")
  
  def discard(self, value):
    self._set.discard(value)
    
  def __str__(self):
    return "{{{}}}".format(
      ", ".join(str(value) for value in self)
    )

class Sequence1D(Value, _MutableSequence):
  
  def __init__(self, value, *values):
    self._list = list()
    self.append(value)
    for v in values:
      self.append(v)
    
  def __getitem__(self, index):
    return self._list[index]
    
  def __setitem__(self, index, value):
    self.insert(index, value)
    
  def __delitem__(self, index):
    del self._list[index]
  
  def __len__(self):
    return len(self._list)
    
  def __iter__(self):
    return iter(self._list)
    
  def insert(self, index, value):
    if isinstance(value, Scalar):
      self._list.insert(index, value)
    else:
      raise TypeError("value is not an instance of Scalar")
      
  def __str__(self):
    if len(self) < 1:
      raise RuntimeError("sequence does not contain at least 1 value")
      
    return "({})".format(
      ", ".join(str(value) for value in self)
    )

class Sequence2D(Sequence1D):

  def insert(self, index, value):
    if isinstance(value, Sequence1D):
      self._list.insert(index, value)
    else:
      raise TypeError("value is not an instance of Sequence1D")
      

class _Token(dict):
  
  __slots__ = ("name",)  
  
  def __init__(self, name, *args, **kwargs):
    self.name = name
    super().__init__(*args, **kwargs)
    
  def __repr__(self):
    return repr(self[self.name].decode("utf-8"))
    

class ParsingError(Exception):
  pass
  
  
################
# Functions
################

def _generate_tokens(byte_str):
  reserved_identifiers = {
    b"end": "end",
    b"group": "begin_group",
    b"begin_group": "begin_group",
    b"end_group": "end_group",
    b"object": "begin_object",
    b"begin_object": "begin_object", 
    b"end_object": "end_object"
  }
  for match in ODL_LEX_TOK_RE.finditer(byte_str):
    name = match.lastgroup
    val = match.group(name).lower()
    if "identifier" == name and val in reserved_identifiers:
      token_name = reserved_identifiers[val]
      token = _Token(token_name, ((token_name, match.group(name)),))
    elif "comment" == name:
      continue
    else:
      token = _Token(
        name,
        (
          (group_name, match.group(group_index))
          for group_name, group_index in ODL_LEX_TOK_GROUPS_INDEX[name].items()
        )
      )
    sent_token = yield token
    if sent_token is not None:
      yield None
      yield sent_token

def _parse_units(tokens):
  tok1 = next(tokens)
  if "open_bracket" in tok1:
    tok2 = next(tokens)
    units = b""
    while "close_bracket" not in tok2:
      units += tok2[tok2.name]
      tok2 = next(tokens)
    units = Units(units.decode("utf-8"))
  else:
    tokens.send(tok1)
    units = ""
  return units

def _parse_value(tok1, tokens):
  if "open_paren" in tok1:
    tok2 = next(tokens)
    if "open_paren" in tok2:
      def gen_values():
        yield _parse_value(tok2, tokens)
        tok3 = next(tokens)
        while "close_paren" not in tok3:
          if "comma" not in tok3:
            raise ParsingError(
              "expected comma instead of {!r}".format(tok3)
            )
          yield _parse_value(next(tokens), tokens)
          tok3 = next(tokens)
      return Sequence2D(*gen_values())
    else:
      def gen_values():
        yield _parse_value(tok2, tokens)
        tok3 = next(tokens)
        while "close_paren" not in tok3:
          if "comma" not in tok3:
            raise ParsingError(
              "expected comma instead of {!r}".format(tok3)
            )
          yield _parse_value(next(tokens), tokens)
          tok3 = next(tokens)
      return Sequence1D(*gen_values())
  elif "open_brace" in tok1:
    def gen_values():
      tok2 = next(tokens)
      if "close_brace" not in tok2:
        yield _parse_value(tok2, tokens)        
        tok2 = next(tokens)
        while "close_brace" not in tok2:
          if "comma" not in tok2:
            raise ParsingError(
              "expected comma instead of {!r}".format(tok2)
            )
          yield _parse_value(next(tokens), tokens)
          tok2 = next(tokens)
    return Set(*gen_values())
  elif "identifier" in tok1:
    return Identifier(tok1["identifier"].decode("utf-8"), False)
  elif "symbol" in tok1:
    return Symbol(tok1["string"].decode("utf-8"), False)
  elif "text" in tok1:
    return Text(tok1["string"].decode("utf-8"), False)
  elif "date" in tok1:
    return Date(tok1["year"], tok1["month"], tok1["day"])
  elif "time" in tok1:
    return Time(
      tok1["hour"],
      tok1["minute"],
      tok1["second"],
      bool(tok1["utc"]),
      tok1["zone_hour"],
      tok1["zone_minute"]
    )
  elif "date_time" in tok1:
    return DateTime(
      tok1["year"],
      tok1["month"],
      tok1["day"],
      tok1["hour"],
      tok1["minute"],
      tok1["second"],
      bool(tok1["utc"]),
      tok1["zone_hour"],
      tok1["zone_minute"]
    )
  elif "integer" in tok1:
    units = _parse_units(tokens)
    return Integer(tok1["integer"], units) 
  elif "based_integer" in tok1:
    units = _parse_units(tokens)
    return BasedInteger(tok1["radix"], tok1["digits"].decode("utf-8"), units)
  elif "real" in tok1:
    units = _parse_units(tokens)
    return Real(tok1["real"], units)
  else:
    raise ParsingError("unexpected {!r}".format(tok1))

def _parse_stmt(tok1, tokens):
  if "identifier" in tok1:
    tok2 = next(tokens)
    if "colon" in tok2:
      tok3 = next(tokens)
      if "identifier" not in tok3:
        raise ParsingError(
          "expected namespace identifier instead of {!r}".format(tok3)
        )
      identifier = tok1["identifier"] + b":" + tok3["identifier"]  
      tok2 = next(tokens)
    else:
      identifier = tok1["identifier"]
    
    if not "equal" in tok2:
      raise ParsingError(
        "expected equal sign instead of {!r}".format(tok2)
      )
    value = _parse_value(next(tokens), tokens)
    return Attribute(identifier.decode("utf-8"), value, False)  
  elif "circumflex" in tok1:
    tok2 = next(tokens)
    if "identifier" not in tok2:
      raise ParsingError(
        "expected identifier instead of {!r}".format(tok2)
      )
    tok3 = next(tokens)
    if "equal" not in tok3:
      raise ParsingError(
        "expected equal sign instead of {!r}".format(tok3)
      )
    identifier = b"^" + tok2["identifier"]
    value = _parse_value(next(tokens), tokens)
    return Attribute(identifier.decode("utf-8"), value, False)
  elif "begin_object" in tok1:
    tok2 = next(tokens)
    if "equal" not in tok2:
      raise ParsingError(
        "expected equal sign instead of {!r}".format(tok2)
      )
    tok3 = next(tokens)
    if "identifier" not in tok3:
      raise ParsingError(
        "expected object identifier instead of {!r}".format(tok3)
      )
    identifier = tok3["identifier"]
    object_statements = ObjectStatements()
    tok4 = next(tokens)
    while "end_object" not in tok4:
      object_statements.append(_parse_stmt(tok4, tokens))
      tok4 = next(tokens)
    tok5 = next(tokens)
    if "equal" in tok5:
      tok6 = next(tokens)
      if "identifier" not in tok6:
        raise ParsingError(
          "expected object identifier instead of {!r}".format(tok6)
        )
      if tok6["identifier"] != identifier:
        raise ParsingError(
          "object identifier {!r} does not match end object \
           identifier {!r}".format(tok3, tok6)
        )
    else:
      tokens.send(tok5)
    return Object(identifier.decode("utf-8"), object_statements, False)
  elif "begin_group" in tok1:
    tok2 = next(tokens)
    if "equal" not in tok2:
      raise ParsingError(
        "expected equal sign instead of {!r}".format(tok2)
      )
    tok3 = next(tokens)
    if "identifier" not in tok3:
      raise ParsingError(
        "expected group identifier instead of {!r}".format(tok3)
      )
    identifier = tok3["identifier"]
    group_statements = GroupStatements()
    tok4 = next(tokens)
    while "end_group" not in tok4:
      group_statements.append(_parse_stmt(tok4, tokens))
      tok4 = next(tokens)
    tok5 = next(tokens)
    if "equal" in tok5:
      tok6 = next(tokens)
      if "identifier" not in tok6:
        raise ParsingError(
          "expected group identifier instead of {!r}".format(tok6)
        )
      if tok6["identifier"] != identifier:
        raise ParsingError(
          "group identifier {!r} does not match end group \
           identifier {!r}".format(tok3, tok6)
        )
    else:
      tokens.send(tok5)
    return Group(identifier.decode("utf-8"), group_statements, False)
  else:
    raise ParsingError("unexpected {!r}".format(tok1))

def _parse_label(tokens):
  label = Label()
  while True:
    try:
      tok = next(tokens)
      if "end" in tok:
        break
      stmt = _parse_stmt(tok, tokens)
      label.append(stmt)
    except StopIteration:
      raise ParsingError("unexpected end")
  return label


def parse(byte_string):
  tokens = _generate_tokens(byte_string)
  return _parse_label(tokens)
      
    
      
  
  
# vim: tabstop=2 expandtab
