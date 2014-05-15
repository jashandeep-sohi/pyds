# pds
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

from collections.abc import MutableMapping
from weakref import proxy as _proxy, ref as _ref, WeakValueDictionary as _WeakValueDict
import re
from string import Formatter as _Formatter


################
# Constants
################

# PDS labels are written in ODL (object description language)
#
# The following tuple defines all lexial tokens of ODL. Lexical tokens **may**
# be seperated by ascii whitespace. Only ascii chars are allowed.
#
# Each token is defined by a tuple of the form:
# (token_name, token_re, token_re_group_names)
# 
# - token_name is the a string specifing the token name/type,
# - token_re is a regexp string. Wirte this regexp assuming re.X & re.S flags
#   are set. A token_re may contain catching groups (i.e. (..)) but not named
#   catching groups (i.e. (?P<name>...)). Any catching groups should be named
#   in token_re_group_names.
# - token_re_group_names is a tuple of group names for any catching groups in
#   token_re. The order should match.
#   If there are no groups in token_re specify an empty tuple.
#
# The order in which the tokens are specified matters.
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
    ("year", "doy_month", "day", "hour", "min", "sec", "zulu", "zone_hour", "zone_min")
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
    "special_char",
    "(\*\*|[=,*/^<>(){}])",
    ()
  ) 
)

ODL_LEX_TOK_RE = re.compile(
  r"""(?xs)
  [ \t\r\n\v\f]*
  (?:
    {}
  )
  [ \t\r\n\v\f]*
  """.format(
    "|".join("(?P<{}>{})".format(n,r) for n,r,g in ODL_LEX_TOK_SPEC)
  ).encode()
)

# This dict maps each tokens groups to the corresponding group index in
# ODL_LEX_TOK_RE.
ODL_LEX_TOK_GROUPS_INDEX = {}
for n,r,g in ODL_LEX_TOK_SPEC:
  ODL_LEX_TOK_GROUPS_INDEX[n] = {
    g_name: ODL_LEX_TOK_RE.groupindex[n]+i+1 for i,g_name in enumerate(g)
  }



###############
# Classes
###############

class _Token(object):
  __slots__ = ("name", "value", "groups")
  def __init__(self, name, value,  groups):
    self.name = name
    self.value = value
    self.groups = groups
  def __repr__(self):
    return "<Token name={}, value={}, groups={}>".format(
      self.name,
      self.value,
      self.groups
    )


class _DoubleLinkedNode(object):
  """
   A _DoubleLinkNode can be used to build doubly linked lists.
   It's prev & next attributes intially point to itself (weak refed).
   An assignment to the prev attribute is automatticaly weak refed behind the
   scenes.
  """
  __slots__ = ("_prev", "next", "value", "__weakref__")
  @property
  def prev(self):
    return self._prev()
  @prev.setter
  def prev(self, v):
    self._prev = _ref(v)
    
  def __init__(self, value):
    self.value = value
    self.next = _proxy(self)
    self.prev = self
    

class Label(object):
  """
  This class represents the PDS label. Each PDS label is composed of a sequence
  of comments & statements.
  """
  def __init__(self):
    self._root_node = _DoubleLinkedNode(None)
    self._statement_dict = _WeakValueDict()
    self._len = 0
  
  def _append_node(self, node):
    node.next = self._root_node
    node.prev = self._root_node.prev
    node.prev.next = node
    self._root_node.prev = node
    self._len += 1
    return node
  
  def _remove_node(self, node):
    prev, next = node.prev, node.next
    next.prev = prev
    prev.next = next
    self._len -= 1
  
  def __getitem__(self, key):
    return self._statement_dict[key].value
    
  def __setitem__(self, key, value):
    self._statement_dict[key] = self._append_node(_DoubleLinkedNode(value))
  
  def __delitem__(self, key):
    self._remove_node(self._statement_dict[key])
  
  def __contains__(self, key):
    try:
      self[key]
    except KeyError:
      return False
    else:
      return True
  
  def __len__(self):
    return self._len
    
  def __iter__(self):
    node = self._root_node.next
    while node is not self._root_node:
      yield node.value
      node = node.next
      
  def __repr__(self):
    return ", ".join(self)
  
  
class Identifier(object):
  pass

class Statement(object):
  def __init__(self, identifier, value):
    self.identifier = identifier
    self.value = value
  

##############
# Functions
##############

def _generate_tokens(byte_str):
  for match in ODL_LEX_TOK_RE.finditer(byte_str):
    yield _Token(
      match.lastgroup,
      match.group(match.lastgroup),
      {
        k: match.group(v) 
          for k,v in ODL_LEX_TOK_GROUPS_INDEX[match.lastgroup].items()
      }
    )
      
    
  
  

# vim: tabstop=2 expandtab
