#! /usr/bin/python3

# vim: filetype=python3 tabstop=2 expandtab

import doctest
import sys

if __name__ == "__main__":
  failed, tested = doctest.testfile(
    "./docs/userguide.rst",
    verbose = True,
    optionflags = doctest.ELLIPSIS
  )
  sys.exit(failed)
  
