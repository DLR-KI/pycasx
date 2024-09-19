# SPDX-FileCopyrightText: 2018 Stanford Intelligent Systems Laboratory
#
# SPDX-License-Identifier: MIT
"""Read a NNet.

The file was adapted from <https://github.com/sisl/NNet>.
The original file was licensed under MIT License.
The original license is included below.

The MIT License (MIT)

Copyright (c) 2018 Stanford Intelligent Systems Laboratory

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import annotations

from typing import Any, Literal, overload

import numpy as np
import numpy.typing as npt


@overload
def read_nnet(nnet_file: str) -> tuple[list[npt.NDArray], list[npt.NDArray]]: ...


@overload
def read_nnet(nnet_file: str, with_norm: Literal[True]) -> tuple[
    list[npt.NDArray],
    list[npt.NDArray],
    list[float],
    list[float],
    list[float],
    list[float],
]: ...


@overload
def read_nnet(
    nnet_file: str, with_norm: Literal[False]
) -> tuple[list[npt.NDArray], list[npt.NDArray]]: ...


def read_nnet(nnet_file: str, with_norm=False) -> (
    tuple[list[np.ndarray], list[np.ndarray]]
    | tuple[
        list[np.ndarray],
        list[np.ndarray],
        list[float],
        list[float],
        list[float],
        list[float],
    ]
):  # pylint: disable=too-many-locals
    """Read a .nnet file and return list of weight matrices and bias vectors.

    Inputs:
        nnet_file: (string) .nnet file to read
        with_norm: (bool) If true, return normalization parameters

    Returns:
        weights: List of weight matrices for fully connected network
        biases: List of bias vectors for fully connected network
    """

    # Open NNet file
    with open(nnet_file, encoding="utf-8") as f:
        # Skip header lines
        line = f.readline()
        while line[:2] == "//":
            line = f.readline()

        # Extract information about network architecture
        record = line.split(",")
        num_layers = int(record[0])
        int(record[1])

        line = f.readline()
        record = line.split(",")
        layer_sizes = np.zeros(num_layers + 1, "int")
        for i in range(num_layers + 1):
            layer_sizes[i] = int(record[i])

        # Skip extra obsolete parameter line
        f.readline()

        # Read the normalization information
        line = f.readline()
        input_mins = [float(x) for x in line.strip().split(",") if x]

        line = f.readline()
        input_maxes = [float(x) for x in line.strip().split(",") if x]

        line = f.readline()
        means = [float(x) for x in line.strip().split(",") if x]

        line = f.readline()
        ranges = [float(x) for x in line.strip().split(",") if x]

        # Read weights and biases
        weights: list[Any] = []
        biases: list[Any] = []
        for layernum in range(num_layers):
            previous_layer_size = layer_sizes[layernum]
            current_layer_size = layer_sizes[layernum + 1]
            weights.append([])
            biases.append([])
            weights[layernum] = np.zeros((current_layer_size, previous_layer_size))
            for i in range(current_layer_size):
                line = f.readline()
                aux = [float(x) for x in line.strip().split(",")[:-1]]
                for j in range(previous_layer_size):
                    weights[layernum][i, j] = aux[j]
            # biases
            biases[layernum] = np.zeros(current_layer_size)
            for i in range(current_layer_size):
                line = f.readline()
                x = float(line.strip().split(",")[0])
                biases[layernum][i] = x

    if with_norm:
        return weights, biases, input_mins, input_maxes, means, ranges
    return weights, biases
