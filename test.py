#! /usr/bin/python
import doctest

if __name__ == "__main__":
  doctest.testfile(
    "./docs/userguide.rst", 
    verbose = True, 
    optionflags = doctest.ELLIPSIS
  )
