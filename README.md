<!--
SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>

SPDX-License-Identifier: CC-BY-4.0
-->

<h1 align="center">
<img src="https://raw.githubusercontent.com/DLR-KI/pycasx/main/docs/_static/pyCASX_logo.svg" alt="pyCASX Logo" width="300">
</h1><br>

# `pyCASX` &ndash; A Python implementation of ACAS Xa and ACAS Xu for Flightgear

[![The latest version of pycasx can be found on PyPI.](https://img.shields.io/pypi/v/pycasx.svg)](https://pypi.python.org/pypi/pycasx)
[![Information on what versions of Python pycasx supports can be found on PyPI.](https://img.shields.io/pypi/pyversions/pycasx.svg)](https://pypi.python.org/pypi/pycasx)
[![prek](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/j178/prek/master/docs/assets/badge-v0.json)](https://github.com/j178/prek)
[![Prek checks](https://github.com/DLR-KI/pycasx/actions/workflows/prek.yaml/badge.svg)](https://github.com/DLR-KI/pycasx/actions/workflows/prek.yaml)
[![Python tests (pytest)](https://github.com/DLR-KI/pycasx/actions/workflows/pytest.yml/badge.svg)](https://github.com/DLR-KI/pycasx/actions/workflows/pytest.yml)
[![Docs status](https://readthedocs.org/projects/pycasx/badge/)](https://pycasx.readthedocs.io/)
[![REUSE status](https://api.reuse.software/badge/github.com/DLR-KI/pycasx)](https://api.reuse.software/info/github.com/DLR-KI/pycasx)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13815668.svg)](https://doi.org/10.5281/zenodo.13815668)

Implementation of ACAS Xa and ACAS Xu with neural networks for FlightGear.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [`pyCASX` – A Python implementation of ACAS Xa and ACAS Xu for Flightgear](#pycasx--a-python-implementation-of-acas-xa-and-acas-xu-for-flightgear)
  - [Description](#description)
  - [Installation](#installation)
    - [Requirements](#requirements)
    - [Users](#users)
      - [Installation via `uvx`](#installation-via-uvx)
      - [Installation via `uv`](#installation-via-uv)
    - [Development](#development)
    - [VS Code](#vs-code)
  - [Usage](#usage)
    - [Launching ACAS X](#launching-acas-x)
    - [Other options](#other-options)
      - [`onnx` or `make_onnx`](#onnx-or-make_onnx)
      - [`launch`](#launch)
      - [`acasx`](#acasx)
    - [Overwriting parameters](#overwriting-parameters)
  - [Citation](#citation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Description

Implementation of Horizontal- and VerticalCAS using neural networks for [FlightGear](https://www.flightgear.org/).
The HCAS and VCAS implementations are based upon Stanford Intelligent Systems Laboratory's [HorizontalCAS](https://github.com/sisl/HorizontalCAS) and [VerticalCAS](https://github.com/sisl/VerticalCAS).

## Installation

Please read the following sections carefully.
Please also see the documentation at <https://pycasx.readthedocs.io>.

### Requirements

- Python 3.11 or higher (3.14 is currently not supported)
- [FlightGear](https://www.flightgear.org/) 2020.3.18 or higher

### Users

If you only want to use `pycasx` as a command-line tool and not develop it, you can install it via `uv` or `uvx`.
However, `uvx` is recommended, as it will install the package in an isolated environment and thus not interfere with other packages.

#### Installation via `uvx`

Install `pycasx` via

```shell
uvx install git+https://https://github.com/DLR-KI/pycasx.git
```

#### Installation via `uv`

**This is not recommended! Proceed at your own risk! For just using the package, `uvx` is recommended**

First, clone the repository

```shell
git clone https://https://github.com/DLR-KI/pycasx.git
```

_Optional:_ create yourself a virtual environment and activate it.

```shell
uv venv
source .venv/bin/activate
```

Now, install the package via

```shell
uv sync
```

for basic features.

### Development

First, clone the repository into a directory of your choice:

```shell
git clone https://https://github.com/DLR-KI/pycasx.git
```

Then, it is recommended to create a virtual environment for the software:

```shell
uv venv
source .venv/bin/activate
```

Afterwards, install the software and its dependencies:

```shell
uv sync
```

### VS Code

For VS Code, we provide a set of recommended extensions.
Please install them to smooth the development process.
You'll find them in your extensions tab under the _Workspace Recommendations_ section.

## Usage

This package provides a command-line interface with the `pycasx` command.
General information is available via `pycasx [-h|--help]` and the current version via `pycasx [-v|--version]`.
All other commands are explained in the following.

### Launching ACAS X

You can launch FlightGear via

```shell
pycasx launch
```

Once FlightGear is up and running, just run:

```shell
pycasx acasx
```

This will start the ACAS X with the default settings.

### Other options

#### `onnx` or `make_onnx`

```shell
pycasx onnx
```

Convert the provided `.nnet` files into `.onnx` files.
This is required if one wants to use the ONNX or PyTorch backend.
**BE WARNED: BOTH THE ONNX AND PYTORCH BACKEND ARE EXPERIMENTAL AND NOT FULLY TESTED. THE RESULTING ADVISORIES ARE NOT VALID!**

#### `launch`

```shell
pycasx launch
```

Launch FlightGear with options defined in [`pycasx/cli/launch.py`](./pycasx/cli/launch.py).

#### `acasx`

```shell
pycasx acasx
```

Runs the ACAS X with the default settings.
This includes the API backend to fetch the advisories via REST calls.
Please see the official documentation for more information.

### Overwriting parameters

Every launch script has a set of default parameters.
Those are handled via [Hydra](https://hydra.cc/).
Accordingly, overwriting parameters can be achieved by following the [Hydra documentation](https://hydra.cc/docs/advanced/override_grammar/basic/).

Nevertheless, overwriting (or adding) new default properties for `pycasx launch` is not as straight forward as one might try.
The correct syntax to overwrite (or add) a default property is

```shell
pycasx launch ++prop='{/autopilot/settings/target-speed-kt: 123456789}'
```

## Citation

If you found our work useful, please cite our paper:

```text
@InProceedings{Christensen2024,
  author    = {Christensen, Johann Maximilian and Anilkumar Girija, Akshay and Stefani, Thomas and Durak, Umut and Hoemann, Elena and K{\"{o}}ster, Frank and Kr{\"{u}}ger, Thomas and Hallerbach, Sven},
  booktitle = {36th {IEEE} International Conference on Tools with Artificial Intelligence ({ICTAI})},
  date      = {2024-10},
  title     = {Advancing the AI-Based Realization of ACAS X Towards Real-World Application},
}
```
