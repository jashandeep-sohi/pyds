.. vim: filetype=rst tabstop=1 expandtab

pyds
====
Python interface to NASA's PDS (Planetary Data System) labels.

Dependencies
------------
- Python 3.4+

Documentation
-------------
Documentation is available at http://pyds.sohi.link

Usage
-----
Here's a quick overview on how to use the module. Refer to the documentation
for more details.

First, parse the PDS label::

 import pyds
 import mmap
 
 # Use a mmap to avoid loading the entire file into memory
 fobj = open("path/to/label.img", "rb")
 fobj_mm = mmap.mmap(fobj.fileno(), 0)
 
 label = pyds.parse(fobj_mm)
 
Then, use the label object to access different attributes of the label::

 # Get the total number of statements
 len(label)
 
 # Get a statement by index
 label.get(1)
 
 # Get a statement's identifier
 label.get(1).identifier
 
 # Get a statement's value
 label.get(1).value
 
 # Get a statement's value by its identifier
 label["key"]
 
 # Get nested values of PDS groups and objects
 label["a"]["b"]["c"]
 
 # Check if a statement exists with the given identifier
 "a" in label
 "b" in label["a"]
 
Similarly, the label object can also be modified::
 
 # Append/insert a statement by index
 label.append(pyds.Attribute("pi", pyds.Real(3.14)))
 label.insert(-1, pyds.Attribute("e", pyds.Real(2.71)))
 
 # Append a statement using a new identifier
 label["new_ident"] = pyds.Integer(10)
 
 # Change a statement's value using its identifier
 label["old_ident"] = pyds.Integer(7)
 
 # Change nested values of PDS groups and objects
 label["a"]["b"]["c"] = pyds.Integer(5)
 
 # Remove a statement by index
 label.pop(1)
 
 # Remove a statement by its identifier
 del label["a"]
 del label["a"]["b"]["c"]
 
Finally, to save the label, serialize the label object to a PDS byte string::

 bytes(label)
