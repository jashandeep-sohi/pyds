Installation
============
There are number of ways to install pds, the easiest of which is using `pip`_
(or `pip + git`_ for the development version).

Dependencies
------------
* Python 3000 (3.4+)
* pip (optional)
 
pip
--- 
Installing the latest release with pip is as simple as:
 
.. code-block:: sh
   
   $ pip install pds

Source
------
To install the latest release from source, grab the latest release archive
from https://github.com/jashandeep-sohi/pds/releases and then use the included
distuitls setup script to install. For example:

.. code-block:: sh

   $ wget 'https://github.com/jashandeep-sohi/pds/releases/download/v0.2.0/pds-0.2.0.tar.bz2'
   $ tar xfj pds-0.2.0.tar.bz2
   $ cd pds-0.2.0
   $ python setup.py install

Git
---
You can get the latest development version by clonning the development repo and
installing from there:

.. code-block:: sh 
   
   $ git clone 'https://github.com/jashandeep-sohi/pds.git'
   $ cd pds
   $ python setup.py install

pip + Git
---------
You can also get the latest development version using pip:
 
.. code-block:: sh
 
   $ pip install 'git+https://github.com/jashandeep-sohi/pds.git'

.. vim: tabstop=1 expandtab
