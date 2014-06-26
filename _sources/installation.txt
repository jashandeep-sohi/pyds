Installation
============
There are numerous of ways to install :mod:`pyds`, the easiest of which is using
`pip`_ (or `pip + git`_ for the development version).

Dependencies
------------
* Python 3000 (3.4+)
* :mod:`pip` (optional)
 
pip
--- 
Installing the latest release with :mod:`pip` is as simple as:
 
.. code-block:: sh
   
   $ pip install pyds

Source
------
To install the latest release from source, first grab the latest release archive
from https://github.com/jashandeep-sohi/pyds/releases and then use the included
distuitls setup script to install:

.. code-block:: sh

   $ wget 'https://github.com/jashandeep-sohi/pyds/releases/download/v0.2.0/pyds-0.2.0.tar.bz2'
   $ tar xfj pyds-0.2.0.tar.bz2
   $ cd pyds-0.2.0
   $ python setup.py install

Git
---
You can get the latest development version by clonning the development
repository and installing from there:

.. code-block:: sh 
   
   $ git clone 'https://github.com/jashandeep-sohi/pyds.git'
   $ cd pyds
   $ python setup.py install

pip + Git
---------
You can also get the latest development version using :mod:`pip`:
 
.. code-block:: sh
 
   $ pip install 'git+https://github.com/jashandeep-sohi/pyds.git'

.. vim: tabstop=1 expandtab
