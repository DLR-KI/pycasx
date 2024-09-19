# SPDX-FileCopyrightText: 2018 Stanford Intelligent Systems Laboratory
#
# SPDX-License-Identifier: MIT
"""Normalizes a NNet.

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

from typing import Literal, overload

import numpy as np
import numpy.typing as npt

from pycasx.tools.NNet.utils.read_nnet import read_nnet
from pycasx.tools.NNet.utils.write_nnet import write_nnet


@overload
def normalize_nnet(
    read_nnet_file: str,
) -> tuple[list[npt.NDArray], list[npt.NDArray]]: ...


@overload
def normalize_nnet(read_nnet_file: str, write_nnet_file: str) -> None: ...


@overload
def normalize_nnet(
    read_nnet_file: str, write_nnet_file: str, with_norm: bool
) -> None: ...


@overload
def normalize_nnet(
    read_nnet_file: str, *, with_norm: Literal[False]
) -> tuple[list[npt.NDArray], list[npt.NDArray]]: ...


@overload
def normalize_nnet(read_nnet_file: str, *, with_norm: Literal[True]) -> tuple[
    list[npt.NDArray],
    list[npt.NDArray],
    list[float],
    list[float],
    list[float],
    list[float],
]: ...


@overload
def normalize_nnet(
    read_nnet_file: str, write_nnet_file: None, with_norm: Literal[False]
) -> tuple[list[npt.NDArray], list[npt.NDArray]]: ...


@overload
def normalize_nnet(
    read_nnet_file: str, write_nnet_file: None, with_norm: Literal[True]
) -> tuple[
    list[npt.NDArray],
    list[npt.NDArray],
    list[float],
    list[float],
    list[float],
    list[float],
]: ...


def normalize_nnet(
    read_nnet_file: str, write_nnet_file: str | None = None, with_norm: bool = False
):
    weights, biases, input_mins, input_maxes, means, ranges = read_nnet(
        read_nnet_file, with_norm=True
    )

    num_inputs = weights[0].shape[1]
    # weights[-1].shape[0]  # That's a pointless statement

    # Adjust weights and biases of first layer
    for i in range(num_inputs):
        weights[0][:, i] /= ranges[i]
    biases[0] -= np.matmul(weights[0], means[:-1])

    # Adjust weights and biases of last layer
    weights[-1] *= ranges[-1]
    biases[-1] *= ranges[-1]
    biases[-1] += means[-1]

    # Nominal mean and range vectors
    nom_means = np.zeros(num_inputs + 1)
    nom_ranges = np.ones(num_inputs + 1)

    if write_nnet_file is not None:
        write_nnet(
            weights,
            biases,
            input_mins,
            input_maxes,
            nom_means,
            nom_ranges,
            write_nnet_file,
        )
        return None
    if with_norm:
        return weights, biases, input_mins, input_maxes, means, ranges
    return weights, biases


def main():
    read_nnet_file = "../nnet/TestNetwork.nnet"
    write_nnet_file = "../nnet/TestNetwork3.nnet"
    normalize_nnet(read_nnet_file, write_nnet_file)


if __name__ == "__main__":
    main()
