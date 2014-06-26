# pyds - A Python module to read & write Planetary Data System (PDS) labels. 
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

from weakref import WeakValueDictionary as _WeakValueDict, ref as _weak_ref
from weakref import ref as _weak_ref, proxy as _weak_proxy
from re import compile as _re_compile
from collections.abc import MutableSet as _MutableSet
from collections.abc import MutableSequence as _MutableSequence
from datetime import date as _date, time as _time, datetime as _datetime
import abc

################
# Classes
################

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
    self.root = _weak_proxy(self.root_hard)
    self.root.next = self.root
    self.root.prev = _weak_ref(self.root_hard)
    self.length = 0

  def insert_node(self, node, index): 
    node_after = self.get_node(index)
    node_before = node_after.prev
    
    node.next = node_after
    node.prev = node_before
    
    node_before().next = node
    node_after.prev = _weak_ref(node)
    
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
    self._dict = _WeakValueDict()
    
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
  
  _VALID_IDENT_RE = _re_compile(r"""(?xi)
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
  
  _VALID_IDENT_RE = _re_compile("""(?xi)
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
  
  _VALID_RE = _re_compile(r"""(?xi)
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
  
  _VALID_RE = _re_compile(r'[\x00-\x21\x23-\x7f]*')
    
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
  
  _VALID_RE = _re_compile(r'[\x20-\x26\x28-\x7e]+')
  
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
  
  _VALID_RE = _re_compile("""(?xi)
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

class Set(Value, _MutableSet):
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

class Sequence1D(Value, _MutableSequence):
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
      

class _Token(dict):
  """
  Used internally to represent tokens.
  """
  
  __slots__ = ("name",)  
  
  def __init__(self, name, *args, **kwargs):
    self.name = name
    super().__init__(*args, **kwargs)
    
  def __repr__(self):
    return repr(self[self.name].decode("utf-8"))
    

class ParsingError(Exception):
  """
  An exception raised if there is an error parsing a string into one of the
  objects representing a PDS construct.
  """
  pass
  

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
# Functions
################

def _generate_tokens(byte_str):
  """
  Generate _Token objects using the ODL_LEX_TOK_RE sepc.
  Generator/iterator supports stepping back using the send() method.
  """
  
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
  """
  Parse and return the tokens into a Units object if possible.
  Other wise return an empty string.
  """
  
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
    units = None
  return units

def _parse_value(tok1, tokens):
  "Return a Value subclass depending on what the tokens are."
  
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
  "Return a subclass of Statement depending what the tokens are."
  
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
  """
  Build and return a Label object using the statment objects returned by
  repeatedly calling _parse_stmt until an "end" _Token is encountered.
  """
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
  """
  Return a :class:`Label` parsed from `byte_string`.
  
  Parameters
    - `byte_string` (:obj:`bytes` or :class:`mmap.mmap`)
      
      A string of bytes that contains a valid PDS label. Other data may follow
      the PDS label, but `bytes` must start with a valid PDS label.
      
      
  Raises
    - :exc:`ParsingError`
    
      If `byte_string` does not start with a valid PDS label.      
  """
  tokens = _generate_tokens(byte_string)
  return _parse_label(tokens)
        
# vim: tabstop=2 expandtab
