.. SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
..
.. SPDX-License-Identifier: CC-BY-4.0

Quick Start
===========

This package provides a command-line interface with the :code:`pycasx` command.
General information is available via :code:`pycasx [-h|--help]` and the current version via :code:`pycasx [-v|--version]`.
All other commands are explained in the following.

Launching ACAS X
----------------

You can launch FlightGear via

.. code-block:: bash

    pycasx launch

Once FlightGear is up and running, just run:

.. code-block:: bash

    pycasx acasx

This will start the ACAS X with the default settings.

Command Line Interface
----------------------

The :code:`pyCASX` package comes with a command line interface (CLI) that allows to run different applications.
Following are the most common commands.

:code:`onnx` or :code:`make_onnx`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pycasx onnx

Convert the provided :code:`.nnet` files into :code:`.onnx` files.
This is required if one wants to use the ONNX or PyTorch backend.

.. WARNING::
    Both the ONNX and PyTorch backend are experimental and not fully tested.
    The resulting advisories are not necessarily valid!

:code:`launch`
^^^^^^^^^^^^^^

.. code-block:: bash

    pycasx launch

Launch FlightGear with options defined in `pycasx/cli/launch.py <https://https://github.com/DLR-KI/pycasx/-/blob/main/pycasx/cli/launch.py>`_.

:code:`acasx`
^^^^^^^^^^^^^^

.. code-block:: bash

    pycasx acasx


Runs the ACAS X with the default settings.
This includes the API backend to fetch the advisories via REST calls.
Please see the official documentation for more information.

Overwriting parameters
----------------------

Every launch script has a set of default parameters.
Those are handled via `Hydra <https://hydra.cc/>`_.
Accordingly, overwriting parameters can be achieved by following the `Hydra documentation <https://hydra.cc/docs/advanced/override_grammar/basic/>`_.

Nevertheless, overwriting (or adding) new default properties for :code:`pycasx launch` is not as straight forward as one might try.
The correct syntax to overwrite (or add) a default property is


.. code-block:: bash

    pycasx launch ++prop='{/autopilot/settings/target-speed-kt: 123456789}'
