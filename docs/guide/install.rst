.. SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
..
.. SPDX-License-Identifier: CC-BY-4.0

Install Guide
=============

Please read the following sections carefully before installing the software to avoid any problems.

Requirements
------------

* Python 3.8 or higher (3.12 is currently not supported)
* `FlightGear <https://www.flightgear.org/>`_ 2020.3.18 or higher

Users
-----

.. TIP::
    If you only want to use :code:`pycasx` as a command-line tool and not develop it, you can install it via :code:`pip` or :code:`pipx`.
    However, :code:`pipx` is recommended, as it will install the package in an isolated environment and thus not interfere with other packages.

Installation via :code:`pipx`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure you have `pipx <https://pipx.pypa.io/stable/>`_ installed.
If not, install it via

.. code-block:: bash

    python3 -m pip install --user pipx
    python3 -m pipx ensurepath

Afterwards, install `pycasx` via

.. code-block:: bash

    pipx install git+https://https://github.com/DLR-KI/pycasx.git

Installation via :code:`pip`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. WARNING::
    This is not recommended!
    Proceed at your own risk!
    For just using the package, :code:`pipx` is recommended.

First, clone the repository into a directory of your choice:

.. code-block:: bash

    git clone https://https://github.com/DLR-KI/pycasx.git

Then, it is recommended to create a virtual environment for the software:

.. code-block:: bash

    pip install virtualenv
    virtualenv .pycasx-venv
    source .pycasx-venv/bin/activate

Afterwards, install the software and its dependencies:

.. code-block:: bash

    pip install -e .

.. NOTE::
    For some virtual environments, especially with Windows, you might need to use :code:`python` instead of :code:`python3` and might also need to use :code:`python -m pip` instead of :code:`pip`.

Developers
----------

Installation
^^^^^^^^^^^^

First, clone the repository into a directory of your choice:

.. code-block:: bash

    git clone https://https://github.com/DLR-KI/pycasx.git

Then, it is recommended to create a virtual environment for the software:

.. code-block:: bash

    pip install virtualenv
    virtualenv .pycasx-venv
    source .pycasx-venv/bin/activate

Afterwards, install the software and its dependencies:

.. code-block:: bash

    pip install -e '.[all]'

Next, install the provided pre-commit hooks:

.. code-block:: bash

    pre-commit install

pre-commit
^^^^^^^^^^

Prior to any commit, the hooks defined in `.pre-commit-config.yaml <https://https://github.com/DLR-KI/pycasx/-/blob/main/.pre-commit-config.yaml>`_ will be ran.
A failure in any hook will block the commit.
Although, most of the errors, like formatting, will correct themselves.
You just have to re-add all changed files and commit again.
Be also aware, that the pipeline can take a few seconds to complete.

Alternatively, you can run the pipeline at any time to invoke changes before they block commits with

.. code-block:: bash

    pre-commit run --all-files

Running the pre-commit pipeline manually once before the first commit is recommended.
It will install all required tools and dependencies and you'll see what's going on.
Otherwise you might be surprised why committing takes so long.

VS Code
^^^^^^^

For VS Code, we provide a set of recommended extensions.
Please install them to smooth the development process.
You'll find them in your extensions tab under the *Workspace Recommendations* section.
