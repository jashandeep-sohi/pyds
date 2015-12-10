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

from . import values
from re import compile as re_compile
from weakref import WeakValueDictionary, ref, proxy

__all__ = (
  "Statements",
  "Label",
  "GroupStatements",
  "ObjectStatements",
  "Statement",
  "Attribute",
  "Group",
  "Object",
)

class _DoubleLinkNode(object):
  """
  Used internally as the nodes of doubly linked list.
  """
  
  __slots__ = ("prev", "next", "value", "__weakref__")
  
  def __init__(self, value = None):
    self.value = value

class _DoubleLinkedNodes(object):
  """
  A simple double linked list used internally.
  """
  
  def __init__(self):
    self.root_hard = _DoubleLinkNode()
    self.root = proxy(self.root_hard)
    self.root.next = self.root
    self.root.prev = ref(self.root_hard)
    self.length = 0

  def insert_node(self, node, index): 
    node_after = self.get_node(index)
    node_before = node_after.prev
    
    node.next = node_after
    node.prev = node_before
    
    node_before().next = node
    node_after.prev = ref(node)
    
    self.length += 1
  
  def get_node(self, index):
    if index > len(self)/2:
      node = self.root
      for _ in range(len(self)-index):
        node = node.prev()
    else:
      node = self.root.next
      for _ in range(index):
        node = node.next
    return node
  
  def remove_node(self, node):
    node_before, node_after = node.prev, node.next
    
    node_before().next = node_after
    node_after.prev = node_before
    
    self.length -= 1
  
  def __len__(self):
    return self.length 
  
class Statements(object, metaclass = abc.ABCMeta):
  """
  Base class for a sequence of PDS statements.
  
  .. note::
      This is an abstract base class and therefore cannot be instantiated
      directly.
      
  .. seealso:: 
      :class:`Label`, :class:`GroupStatements`, :class:`ObjectStatements`
  """
  
  @property
  def _max_identifier_width(self):
    return max(
      10,
      max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
    )
  
  @abc.abstractmethod
  def __init__(self, *statements):
    self._nodes = _DoubleLinkedNodes()
    self._dict = WeakValueDictionary()
    
    for statement in statements:
      self.append(statement)
               
  def _insert(self, index, statement):
    index = max(0, len(self) + index) if index < 0 else min(len(self), index)
    new_node = _DoubleLinkNode(statement)
    self._nodes.insert_node(new_node, index)
    self._dict[statement.identifier] = new_node
  
  def _append(self, statement):
    self._insert(len(self), statement)
  
  def insert(self, index, statement):
    """
    Insert the statement `statement` at index `index`.
    
    Parameters
      - `index` (:obj:`int`)
        
        The index at which to insert the statement.
        
        `index` can be any integer (positive or negative). If negative, it's 
        taken to mean the index from the end. For example, 
        ``s.insert(-10, stmt)`` is the same as ``s.insert(len(s)-10, stmt)``.
        
        If `index` is out of range and positive, then `statement` is appended to
        the end. If it's out of range and negative, then `statement` is
        prepended to the begining.
        
      - `statement` (:class:`Attribute`, :class:`Group` or :class:`Object`)
        
        The statement to insert. It must be an instance of either
        :class:`Attribute`, :class:`Group` or :class:`Object`.
        
        Also, `statement`'s identifier must not be the same as any other
        statement previously inserted.
       
    Raises
      - :exc:`TypeError`
        
        If `statement` is not an instance of either :class:`Attribute`,
        :class:`Group` or :class:`Object`.
        
      - :exc:`ValueError`
        
        If `statements`'s identifier is not unique.
    """
    if not isinstance(statement, (Attribute, Group, Object)):
      raise TypeError(
        "statement is not an instance of Attribute, Group or Object"
      )
    
    if statement.identifier in self:
      raise ValueError(
        "statement with identifier {!r} already exists".format(
          statement.identifier
        )
      )
    self._insert(index, statement)
    
  def append(self, statement):
    """
    Append the statement `statement`.
    
    .. note::
        Calling ``s.append(stmt)`` is the same as calling
        ``s.insert(len(s), stmt)``.
        See :meth:`insert` for further documentation.
    """
    self.insert(len(self), statement)
  
  def get(self, index):
    """
    Return the statement at index `index`.
    
    Parameters
      - `index` (:obj:`int`)
      
        The index from where to return the statement.
        
        `index` can be any integer (positive or negative). If negative, it's
        taken to mean the index from the end. For example, ``s.get(-10)`` is the
        same as ``s.get(len(s)-10)``.
      
    Raises
      - :exc:`IndexError`
      
        If `index` is out of range.
    """
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      return self._nodes.get_node(index).value
       
  def pop(self, index):
    """
    Remove and return the statement at index `index`.
    
    Parameters
      - `index` (:obj:`int`)
      
        The index from where to remove and return the statement. 
        
        `index` can be any integer (positive or negative). If negative, it's 
        taken to mean the index from the end. For example, ``s.pop(-10)`` is the
        same as ``s.pop(len(s)-10)``.
      
    Raises
      - :exc:`IndexError`
      
        If `index` is out of range.
    """
    index = len(self) + index if index < 0 else index
    if index >= len(self) or index < 0:
      raise IndexError("index out of range")
    else:
      node = self._nodes.get_node(index)
      self._nodes.remove_node(node)
      return node.value
  
  def __setitem__(self, key, value):
    """
    Create and insert a new statement using `key` and `value`.
    
    Parameters
      - `key` (:obj:`str`)
        
        The identifier of the new statement.
        
        If `value` is an instance of :class:`Value`, then `key` must be a valid
        identifier such that a new :class:`Attribute` can be instantiated as,
        ``Attribute(key, value)``.
        
        If `value` is an instance of :class:`GroupStatements`, then `key` must
        be a valid identifier such that a new :class:`Group` can be instantiated
        as, ``Group(key, value)``.
        
        If `value` is an instance of :class:`ObjectStatements`, then `key` must
        be a valid identifier such that a new :class:`Object` can be 
        instantiated as, ``Object(key, value)``.
        
      - `value` (:class:`Value`, :class:`GroupStatements` or
        :class:`ObjectStatements`)
        
        `value` determines the type of the new statement.
        
        If `value` is an instance of :class:`Value`, then an :class:`Attribute`
        statement is created.
        
        If `value` is an instance of :class:`GroupStatements`, then a
        :class:`Group` statement is created.
        
        If `value` is an instance of :class:`ObjectStatements`, then an
        :class:`Object` statement is created.
        
    Raises
      - :exc:`TypeError`
      
        If `value` is not an instance of :class:`Value`,
        :class:`GroupStatements` or :class:`ObjectStatements`.
      
      - :exc:`ValueError`
      
        If `key` is not a valid identifier.
    """
    try:
      stmt = Attribute(key, value)
    except TypeError:
      try:
        stmt = Group(key, value)
      except TypeError:
        try:
          stmt = Object(key, value)
        except TypeError:
          raise TypeError("value type is not correct")
    try:
      old_node = self._dict[stmt.identifier]
    except KeyError:
      self._append(stmt)
    else:
      old_node.value = stmt
  
  def __getitem__(self, key):
    """
    Return the value of the statement whose identifier is `key`.
    
    Parameters
      - `key` (:obj:`str`)
      
        The identifier of the statement. `key` is case-insensitive.
      
    Raises
      - :exc:`KeyError`
      
        If a statement with an identifier equal to `key` does not exist.
    """
    return self._dict[key.upper()].value.value
    
  def __delitem__(self, key):
    """
    Remove the statement whose identifier is `key`.
    
    Parameters
      - `key` (:obj:`str`)
      
        The identifier of the statement. `key` is case-insensitive.
      
    Raises
      - :exc:`KeyError`
      
        If a statement with an identifier equal to `key` does not exist.
    """
    node = self._dict[key.upper()]
    self._nodes.remove_node(node)
    del node
  
  def __contains__(self, key):
    """
    Test if a statement exists whose identifier is `key`.
    Return :obj:`True` if it exists, and :obj:`False` otherwise.
    
    Parameters
      - `key` (:obj:`str`)
        
        The identifier of the statement. `key` is case-insensitive.
    """
    try:
      self[key]
    except KeyError:
      return False
    else:
      return True
    
  def __iter__(self):
    """
    Return an :obj:`iterator` that iterates over the statements. 
    
    Called by :func:`iter`.
    """
    current_node = self._nodes.root.next
    while current_node is not self._nodes.root:
      yield current_node.value
      current_node = current_node.next
  
  def __reversed__(self):
    """
    Return an :obj:`iterator` that iterates over the statements in reverse
    order.
    
    Called by :func:`reversed`.
    """
    current_node = self._nodes.root.prev()
    while current_node is not self._nodes.root:
      yield current_node.value
      current_node = current_node.prev()
    
  def __len__(self):
    """
    Return the number of statements.
    
    Called by :func:`len`.
    """
    return len(self._nodes)
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    width = str(self._max_identifier_width)
    return "\r\n".join(
      stmt._format("", width) for stmt in iter(self)
    )
      
  def __bytes__(self):
    """
    Return the object's PDS serialization :obj:`str` as an ascii :obj:`bytes` 
    string.
    
    .. seealso::
        :meth:`__str__`
    
    Called by :func:`bytes`.
    """
    return str(self).encode("ascii")

class Label(Statements):
  """
  Represents a PDS label.
  
  Parameters
    - `*statements` (list of either :class:`Attribute`, :class:`Group` or 
      :class:`Object` arguments)
      
      Statements to intially insert.
  
  Raises
    - :exc:`TypeError`
      
      If any of the `*statements` is not an instance of either 
      :class:`Attribute`, :class:`Group` or :class:`Object`.
      
    - :exc:`ValueError`
      
      If any of the `*statements`'s identifier is not unique.
  """
  
  def __init__(self, *statements):
    super().__init__(*statements)
  
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return "{}\r\nEND ".format(super().__str__())
    
       
class GroupStatements(Statements):
  """
  Container for statements of a PDS group statement.
  
  Parameters
    - `*statements` (list of either :class:`Attribute`, :class:`Group` or 
      :class:`Object` arguments)
      
      Statements to intially insert.
  
  Raises
    - :exc:`TypeError`
      
      If any of the `*statements` is not an instance of either 
      :class:`Attribute`, :class:`Group` or :class:`Object`.
      
    - :exc:`ValueError`
      
      If any of the `*statements`'s identifier is not unique.
  """
  
  def __init__(self, *statements):
    super().__init__(*statements)  
  
  @Statements._max_identifier_width.getter
  def _max_identifier_width(self):
    return max(map(len, (stmt.identifier for stmt in iter(self))), default = 0)
  
  
  def insert(self, index, statement):
    """
    Insert the statement `statement` at index `index`.
    
    Parameters
      - `index` (:obj:`int`)
        
        The index at which to insert the statement.
        
        `index` can be any integer (positive or negative). If negative, it's 
        taken to mean the index from the end. For example, 
        ``s.insert(-10, stmt)`` is the same as ``s.insert(len(s)-10, stmt)``.
        
        If `index` is out of range and positive, then `statement` is appended to
        the end. If it's out of range and negative, then `statement` is
        prepended to the begining.
        
      - `statement` (:class:`Attribute`)
        
        The statement to insert. It must be an instance of :class:`Attribute`.
        
        Also, `statement`'s identifier must not be the same as any other
        statement previously inserted.
       
    Raises
      - :exc:`TypeError`
        
        If `statement` is not an instance of :class:`Attribute`.
        
      - :exc:`ValueError`
        
        If `statements`'s identifier is not unique.
    """
    if not isinstance(statement, (Attribute)):
      raise TypeError(
        "statement is not an instance of Attribute"
      )
    
    if statement.identifier in self:
      raise ValueError(
        "statement with identifier {!r} already exists".format(
          statement.identifier
        )
      )
    self._insert(index, statement)
  
  def __setitem__(key, value):
    """
    Create and insert a new statement using `key` and `value`.
    
    Parameters
      - `key` (:obj:`str`)
        
        The identifier of the new statement.
        
        `key` should be a valid identifier such that a new :class:`Attribute`
        can be instantiated as, ``Attribute(key, value)``
        
      - `value` (:class:`Value`)
        
        The value of the statement. It must be an instance of :class:`Value`.
        
    Raises
      - :exc:`TypeError`
      
        If `value` is not an instance of :class:`Value`.
      
      - :exc:`ValueError`
      
        If `key` is not a valid identifier.
    """
    stmt = Attribute(key, value)
    try:
      old_node = self._dict[stmt.identifier]
    except KeyError:
      self._append(stmt)
    else:
      old_node.value = stmt
    
    
class ObjectStatements(Statements):
  """
  Container for statements of a PDS object statement.
  
  Parameters
    - `*statements` (list of either :class:`Attribute`, :class:`Group` or 
      :class:`Object` arguments)
      
      Statements to intially insert.
  
  Raises
    - :exc:`TypeError`
      
      If any of the `*statements` is not an instance of either 
      :class:`Attribute`, :class:`Group` or :class:`Object`.
      
    - :exc:`ValueError`
      
      If any of the `*statements`'s identifier is not unique.
  """
  
  def __init__(self, *statements):
    super().__init__(*statements)

class Statement(object, metaclass = abc.ABCMeta):
  """
  Base class for PDS statements.
  
  .. note::
      This is an abstract base class and therefore cannot be instantiated
      directly.
  
  .. seealso::
      :class:`Attribute`, :class:`Group`, :class:`Object`
        
  """
  
  _VALID_IDENT_RE = re_compile(r"""(?xi)
    (?!(?:end|group|begin_group|end_group|object|begin_object|end_object)$)
    (?:[a-z](?:_?[a-z0-9])*)
  """)
    
  @abc.abstractmethod
  def __init__(self, identifier, value, validate_identifier = True):    
    if validate_identifier and not self._VALID_IDENT_RE.fullmatch(identifier):
      raise ValueError("invalid identifier {!r}".format(identifier))
    
    self.identifier = identifier.upper()
    self.value = value
          
  def __str__(self):
    """
    Return a PDS serialized string (:obj:`str`) representing the object.
    
    Called by :func:`str`.
    """
    return self._format("")  

class Attribute(Statement):
  """
  Represents a PDS attribute assignment statement.
  
  Parameters
    - `identifier` (:obj:`str`)
    
      Identifier of the attribute.
    
    - `value` (:class:`Value`)
    
      Value of the attribute. This should be an instance of one of the
      non-abstract subclasses of :class:`Value`.
      
    - `validate_identifier` (:obj:`True` or :obj:`False`)
    
      Whether `identifier` should be checked to see if it's a valid identifer
      for a PDS attribute assignment statement. Default is :obj:`True`.
      
  Raises
    - :exc:`TypeError`
      
      If `value` is not a instance of :class:`Value`.
      
    - :exc:`ValueError`
    
      If `validate_identifier` is :obj:`True` and 
      `identifier` is not a valid identifier for an attribute assignment
      statement.
      
  Attributes
    .. attribute:: identifier
        
        Identifier of the attribute.
        A :obj:`str` instance.
        Read-only.
    
    .. attribute:: value
        
        Value of the attribute.
        An instance of one of the non-abstract subclasses of :class:`Value`.
        Read-only.
  """
  
  _VALID_IDENT_RE = re_compile("""(?xi)
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
    if not isinstance(value, values.Value):
      raise TypeError("value is not an instance of Value")
    super().__init__(identifier, value, validate_identifier)
      
  def _format(self, indent, width = ""):
    return "{}{} = {}".format(
      indent,
      format(self.identifier, width),
      self.value
    )
          
class Group(Statement):
  """
  Represents a PDS group statement.
  
  Parameters
    - `identifier` (:obj:`str`)
    
      Identifier of the group.
    
    - `group_statements` (:class:`GroupStatements`)
    
      Nested statements of the group.
      
    - `validate_identifier` (:obj:`True` or :obj:`False`)
    
      Whether `identifier` should be checked to see if it's a valid identifer
      for a PDS group statement. Default is :obj:`True`.
      
  Raises
    - :exc:`TypeError`
      
      If `group_statements` is not a instance of :class:`GroupStatements`.
      
    - :exc:`ValueError`
    
      If `validate_identifier` is :obj:`True` and 
      `identifier` is not a valid identifier for a group statement.
      
  Attributes
    .. attribute:: identifier
        
        Identifier of the group statement.
        A :obj:`str` instance.
        Read-only.
    
    .. attribute:: statements
        
        Nested statements of the group statement.
        A :class:`GroupStatements` instance.
        Read-only.
    
    .. attribute:: value
        
        Same as :attr:`statements`.
  """
        
  def __init__(self, identifier, group_statements, validate_identifier = True):
    if not isinstance(group_statements, GroupStatements):
      raise TypeError("group_statements is not an instance of GroupStatements")
      
    self.statements = group_statements
    super().__init__(identifier, self.statements, validate_identifier)
    
  def _format(self, indent, width = "9"):
    sub_width = str(self.statements._max_identifier_width)
    sub_indent = indent + " "
    return "{}{} = {}{}{}{} = {}".format(
      indent,
      format("GROUP", width),
      self.identifier,
      "\r\n{}\r\n".format("\r\n".join(
        stmt._format(sub_indent, sub_width) for stmt in iter(self.statements)
      )) if len(self.statements) else "\r\n",
      indent,
      format("END_GROUP", width),
      self.identifier
    )
     
class Object(Statement):
  """
  Represents a PDS object statement.
  
  Parameters
    - `identifier` (:obj:`str`)
    
      Identifier of the object.
    
    - `object_statements` (:class:`ObjectStatements`)
    
      Nested statements of the object.
      
    - `validate_identifier` (:obj:`True` or :obj:`False`)
    
      Whether `identifier` should be checked to see if it's a valid identifer
      for a PDS object statement. Default is :obj:`True`.
      
  Raises
    - :exc:`TypeError`
      
      If `object_statements` is not a instance of :class:`ObjectStatements`.
      
    - :exc:`ValueError`
    
      If `validate_identifier` is :obj:`True` and 
      `identifier` is not a valid identifier for an object statement.
      
  Attributes
    .. attribute:: identifier
        
        Identifier of the object statement.
        A :obj:`str` instance.
        Read-only.
    
    .. attribute:: statements
        
        Nested statements of the object statement.
        A :class:`ObjectStatements` instance.
        Read-only.
    
    .. attribute:: value
        
        Same as :attr:`statements`.
  """
  
  def __init__(self, identifier, object_statements, validate_identifier = True):
    if not isinstance(object_statements, ObjectStatements):
      raise TypeError(
        "object_statements is not an instance of ObjectStatements"
      )
      
    self.statements = object_statements
    super().__init__(identifier, self.statements, validate_identifier)
    
  def _format(self, indent, width = "10"):
    sub_width = str(self.statements._max_identifier_width)
    sub_indent = indent + " "
    return "{}{} = {}{}{}{} = {}".format(
      indent,
      format("OBJECT", width),
      self.identifier,
      "\r\n{}\r\n".format("\r\n".join(
        stmt._format(sub_indent, sub_width) for stmt in iter(self.statements)
      )) if len(self.statements) else "\r\n",
      indent,
      format("END_OBJECT", width),
      self.identifier
    )
