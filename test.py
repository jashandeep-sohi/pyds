#! /usr/bin/python3

# vim: filetype=python3 tabstop=2 expandtab

import doctest
import sys
import os

if __name__ == "__main__":
  os.chdir("./docs")
  failed, tested = doctest.testfile(
    "./userguide.rst",
    verbose = False,
    optionflags = doctest.ELLIPSIS
  )
  sys.exit(failed)
  
