.. SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
..
.. SPDX-License-Identifier: CC-BY-4.0
..
.. pyCASX documentation master file, created by
    sphinx-quickstart on Tue Dec 12 14:35:10 2023.
    You can adapt this file completely to your liking, but it should at least
    contain the root `toctree` directive.

:code:`pyCASX` -- A Python implementation of ACAS X\ :sub:`A` and ACAS X\ :sub:`U` for Flightgear
=================================================================================================

Implementation of ACAS X\ :sub:`A` and ACAS X\ :sub:`U` with neural networks for FlightGear.

Description
-----------

Implementation of Horizontal- and VerticalCAS using neural networks for `FlightGear <https://www.flightgear.org/>`_.
The HCAS and VCAS implementations are based upon Stanford Intelligent Systems Laboratory's `HorizontalCAS <https://github.com/sisl/HorizontalCAS>`_ and `VerticalCAS <https://github.com/sisl/VerticalCAS>`_.

General Information
-------------------

If you are just using :code:`pyCASX` for Flightgear, you can skip the developer guide and the API reference.
But if you want to contribute to the project, you should read the developer guide and especially follow the install instructions there.

.. toctree::
    :maxdepth: 1
    :caption: User Guide

    guide/install
    guide/quick_start
    guide/autoavoid
    guide/api

.. toctree::
    :maxdepth: 1
    :caption: Python API Reference

Indices and tables
-------------------

* :ref:`genindex`
* :ref:`search`
* :ref:`modindex`
