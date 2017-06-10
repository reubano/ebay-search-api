AMZN Search API |travis|
========================

.. |travis| image:: https://img.shields.io/travis/nerevu/prometheus-api/master.svg
    :target: https://travis-ci.org/nerevu/prometheus-api

===============

Introduction
------------

This is a RESTful API for searching Amazon sites

* MacOS X 10.7.4
* Python 2.7.1

Requirements
------------

prometheus requires the following in order to run properly:

* `Python >= 2.7 <http://www.python.org/download>`_

Preparation
-----------

Check that the correct version of Python is installed

    python -V

Installation
------------

Install prometheus using either pip (recommended)

    sudo pip install prometheus

or easy_install

    sudo easy_install prometheus

Using prometheus
-----------------

Usage
^^^^^

    prometheus [options] <argument>

Examples
^^^^^^^^

*normal usage*

    prometheus argument

*stdin*

    cat file | prometheus -

*options*

    prometheus -dc TZS  argument

Options
^^^^^^^

      -c currency, --currency=currency      set currency, defaults to 'USD'
      -d, --debug                           enables debug mode, displays the
                                            options and arguments passed to the
                                            parser
      -v, --verbose                         verbose output
      -h, --help                            show this help message and exit
      --version                             show the program version and exit

Arguments
^^^^^^^^^

+---------+---------------------------------------------------------------------+
| file    |  the source file, enter '-' to read data from standard input        |
+---------+---------------------------------------------------------------------+

LICENSE
-------

prometheus is distributed under the `MIT License <http://opensource.org/licenses/mit-license.php>`_, the same as `anotherprogram <http://opensource.org/licenses/alphabetical>`_ on which this program depends.
