#! /usr/bin/python3
import doctest
import sys

if __name__ == "__main__":
  failed, tested = doctest.testfile(
    "./docs/userguide.rst",
    verbose = True,
    optionflags = doctest.ELLIPSIS
  )
  sys.exit(failed)
  
