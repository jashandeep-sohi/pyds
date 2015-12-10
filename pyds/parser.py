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

from . import statements
from . import values
from re import compile as re_compile

__all__ = (
  "ParsingError",
  "parse",
)

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

ODL_LEX_TOK_RE = re_compile(
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
    units = values.Units(units.decode("utf-8"))
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
      return values.Sequence2D(*gen_values())
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
      return values.Sequence1D(*gen_values())
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
    return values.Set(*gen_values())
  elif "identifier" in tok1:
    return values.Identifier(tok1["identifier"].decode("utf-8"), False)
  elif "symbol" in tok1:
    return values.Symbol(tok1["string"].decode("utf-8"), False)
  elif "text" in tok1:
    return values.Text(tok1["string"].decode("utf-8"), False)
  elif "date" in tok1:
    return values.Date(tok1["year"], tok1["month"], tok1["day"])
  elif "time" in tok1:
    return values.Time(
      tok1["hour"],
      tok1["minute"],
      tok1["second"],
      bool(tok1["utc"]),
      tok1["zone_hour"],
      tok1["zone_minute"]
    )
  elif "date_time" in tok1:
    return values.DateTime(
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
    return values.Integer(tok1["integer"], units) 
  elif "based_integer" in tok1:
    units = _parse_units(tokens)
    return values.BasedInteger(
      tok1["radix"], tok1["digits"].decode("utf-8"), units
    )
  elif "real" in tok1:
    units = _parse_units(tokens)
    return values.Real(tok1["real"], units)
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
    return statements.Attribute(identifier.decode("utf-8"), value, False)  
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
    return statements.Attribute(identifier.decode("utf-8"), value, False)
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
    object_statements = statements.ObjectStatements()
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
    return statements.Object(identifier.decode("utf-8"), object_statements, False)
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
    group_statements = statements.GroupStatements()
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
    return statements.Group(identifier.decode("utf-8"), group_statements, False)
  else:
    raise ParsingError("unexpected {!r}".format(tok1))

def _parse_label(tokens):
  """
  Build and return a Label object using the statment objects returned by
  repeatedly calling _parse_stmt until an "end" _Token is encountered.
  """
  label = statements.Label()
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
