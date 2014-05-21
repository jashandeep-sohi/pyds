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
  """
  """
  __slots__ = ("prev", "next", "value", "__weakref__")
  
  def __init__(self, value = None):
    """
    """
    self.value = value

class Statements(object):
  """
  """
  
  def __init__(self):
    """
    """
    self._root_node_hard = _DoubleLinkNode()
    self._root_node = _weak_proxy(self._root_node_hard)
    self._root_node.next = self._root_node
    self._root_node.prev = self._root_node
    self._length = 0
    
    self._dict = _WeakValueDict()
      
  def _insert_node(self, node, index):
    """
    """    
    node_after = self._get_node(index)
    node_before = node_after.prev
    
    node.next = node_after
    node.prev = node_before
    
    node_before.next = node
    node_after.prev = _weak_proxy(node)
    
    self._length += 1
    return node
  
  def _get_node(self, index):
    """
    """
    if index > len(self)/2:
      node = self._root_node
      for _ in range(len(self)-index):
        node = node.prev
    else:
      node = self._root_node.next
      for _ in range(index):
        node = node.next
    return node
  
  def _remove_node(self, node):
    """
    """
    node_before, node_after = node.prev, node.next
    
    node_before.next = node_after
    node_after.prev = node_before
    
    self._length -= 1
    return node  
    
  def _insert(self, statement, index):
    """
    """
    index = max(0, len(self) + index) if index < 0 else min(len(self), index)
    new_node = self._insert_node(_DoubleLinkNode(statement), index)
    self._dict[statement.identifier] = new_node
  
  def insert(self, statement, index):
    """
    """
    if isinstance(statement, Statement):
      self._insert(statement, index)
    else:
      raise TypeError()
    
  def append(self, statement):
    """
    """
    self.insert(statement, len(self))
  
  def get(self, index):
    """
    """
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      return self._get_node(index).value
      
  
  def pop(self, index):
    """
    """
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      return self._remove_node(self._get_node(index)).value
  
  def __setitem__(self, key, value):
    """
    """
    if isinstance(value, Value):
      self._insert(Attribute(key, value), len(self))
      
    elif isinstance(value, GroupStatements):
      self._insert(Group(key, value), len(self))
      
    elif isinstance(value, ObjectStatements):
      self._insert(Object(key, value), len(self))
      
    else:
      raise TypeError()
  
  def __getitem__(self, key):
    """
    """
    return self._dict[key.upper()].value.value
    
  def __delitem__(self, key):
    """
    """
    node = self._remove_node(self._dict[key.upper()])
    del node
  
  def __contains__(self, key):
    """
    """
    try:
      self[key]
    except KeyError:
      return False
    else:
      return True
    
  def __iter__(self):
    """
    """
    current_node = self._root_node.next
    while current_node is not self._root_node:
      yield current_node.value
      current_node = current_node.next
  
  def __reversed__(self):
    """
    """
    current_node = self._root_node.prev
    while current_node is not self._root_node:
      yield current_node.value
      current_node = current_node.prev
    
  def __len__(self):
    """
    """
    return self._length
    
  def __repr__(self):
    """
    """
    return "<{}.{}>".format(
      self.__module__,
      type(self).__name__
    )
    
  def __str__(self):
    return "\r\n".join(str(statement) for statement in iter(self))
    

class GroupStatements(Statements):
  pass
  
class ObjectStatements(Statements):
  pass

class Statement(object):
  
  def __init__(self, identifier, value):
    self.identifier = identifier
    self.value = value

class Attribute(Statement):
  
  def __init__(self, identifier, value):
    super().__init__(identifier, value)
  
class Group(Statement):

  def __init__(self, identifier, group_statements):
    super().__init__(identifier, group_statements)
  
class Object(Statement):

  def __init__(self, identifier, object_statements):
    super().__init__(identifier, object_statements)
  
class Value(object):
  pass

################
# Functions
################

def _generate_tokens(byte_str):
  """
  """
  line_no = 1
  line_pos = -1
  for match in ODL_LEX_TOK_RE.finditer(byte_str):
    name = match.lastgroup
    if name == "newline":
      line_no += 1
      line_pos = match.end("newline") - 1
      continue
    value = match.group(name)
    yield {
      "name": name,
      "groups": {
        group_name: match.group(group_index)
      for group_name, group_index in ODL_LEX_TOK_GROUPS_INDEX[name].items()
      },
      "line": line_no,
      "column": match.start(name) - line_pos
    }

  
    
  
  
# vim: tabstop=2 expandtab
