# SPDX-FileCopyrightText: 2018 Stanford Intelligent Systems Laboratory
#
# SPDX-License-Identifier: MIT
"""Convert onnx to NNet.

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
import sys
import warnings

import numpy as np
import onnx
from loguru import logger
from onnx import numpy_helper

from pycasx.tools.NNet.utils.write_nnet import write_nnet


def add(input_name, graph, biases, node):
    if not len(node.input) == 2:
        raise ValueError("Add node does not have two inputs.")

        # Find the name of the bias vector, which should be the
        # other input to the node
    bias_index = 0
    if node.input[0] == input_name:
        bias_index = 1
    bias_name = node.input[bias_index]

    # Extract the value of the bias vector from the initializers
    biases += [
        numpy_helper.to_array(inits)
        for inits in graph.initializer
        if inits.name == bias_name
    ]

    # Update inputName to be the output of this node
    input_name = node.output[0]
    return input_name


def matmul(input_name, graph, weights, node):
    if not len(node.input) == 2:
        raise ValueError("MatMul node does not have two inputs.")

        # Find the name of the weight matrix, which should be
        # the other input to the node
    weight_index = 0
    if node.input[0] == input_name:
        weight_index = 1
    weight_name = node.input[weight_index]

    # Extract the value of the weight matrix from the initializers
    weights += [
        numpy_helper.to_array(inits)
        for inits in graph.initializer
        if inits.name == weight_name
    ]

    # Update inputName to be the output of this node
    input_name = node.output[0]
    return input_name


def relu(node):
    input_name = node.output[0]
    return input_name


def onnx_to_nnet_helper(graph, input_name, output_name):
    # Search through nodes until we find the input_name.
    # Accumulate the weight matrices and bias vectors into lists.
    # Continue through the network until we reach output_name.
    # This assumes that the network is "frozen", and the model uses
    # initializers to set weight and bias array values.
    weights = []
    biases = []

    # Loop through nodes in graph
    for node in graph.node:
        # Ignore nodes that do not use inputName as an input to the node
        if input_name in node.input:
            # This supports three types of nodes: MatMul, Add, and Relu
            # The .nnet file format specifies only feedforward
            # fully-connected Relu networks, so these operations are
            # sufficient to specify nnet networks. If the onnx model
            # uses other operations, this will break.
            if node.op_type == "MatMul":
                input_name = matmul(input_name, graph, weights, node)

            elif node.op_type == "Add":
                input_name = add(input_name, graph, biases, node)

            # For the .nnet file format, the Relu's are implicit, so we
            # just need to update the input
            elif node.op_type == "Relu":
                input_name = relu(node)

            # If there is a different node in the model that is not
            # supported, through an error and break out of the loop
            else:
                warnings.warn(
                    f"Node operation type {node.op_type} not supported!",
                    category=RuntimeWarning,
                    stacklevel=5,
                )
                weights = []
                biases = []
                break

            # Terminate once we find the outputName in the graph
            if output_name == input_name:
                break

    return weights, biases, input_name


def onnx_to_nnet(
    onnx_file,
    input_mins=None,
    input_maxes=None,
    means=None,
    ranges=None,
    nnet_file="",
    input_name="",
    output_name="",
):  # pylint: disable=too-many-arguments
    """Write a .nnet file from an onnx file
    Args:
        onnx_file: (string) Path to onnx file
        input_mins: (list) optional, Minimum values for each neural
            network input.
        input_maxes: (list) optional, Maximum values for each neural
            network output.
        means: (list) optional, Mean value for each input and value for
            mean of all outputs, used for normalization
        ranges: (list) optional, Range value for each input and value
            for range of all outputs, used for normalization
        input_name: (string) optional, Name of operation corresponding to
            input.
        output_name: (string) optional, Name of operation corresponding
            to output.
    """

    nnet_file = nnet_file if nnet_file != "" else onnx_file[:-4] + "nnet"

    model = onnx.load(onnx_file)
    graph = model.graph

    if not input_name:
        if not len(graph.input) == 1:
            raise ValueError("No input name specified.")
        input_name = graph.input[0].name
    if not output_name:
        if not len(graph.output) == 1:
            raise ValueError("No output name specified.")
        output_name = graph.output[0].name

    weights, biases, input_name = onnx_to_nnet_helper(graph, input_name, output_name)

    # Check if the weights and biases were extracted correctly from the graph
    if not output_name == input_name:
        raise ValueError(f"Could not find output name {output_name} in graph!")
    if len(weights) <= 0:
        raise ValueError("Could not extract weights from graph!")
    if len(weights) != len(biases):
        raise ValueError("Number of weights and biases do not match!")

    input_size = weights[0].shape[0]

    # Default values for input bounds and normalization constants
    input_mins = (
        input_mins
        if input_mins is not None
        else input_size * [np.finfo(np.float32).min]
    )
    input_maxes = (
        input_maxes
        if input_maxes is not None
        else input_size * [np.finfo(np.float32).max]
    )
    means = means if means is not None else (input_size + 1) * [0.0]
    ranges = ranges if ranges is not None else (input_size + 1) * [1.0]

    # Print statements
    logger.info(
        f"Converted ONNX model at {onnx_file}\n\tto an NNet model at {nnet_file}"
    )

    # Write NNet file
    write_nnet(
        weights,
        biases,
        input_mins,
        input_maxes,
        means,
        ranges,
        nnet_file,
    )


def main() -> None:
    # Read user inputs and run onnx2nnet function
    # If non-default values of input bounds and normalization constants
    # are needed, this function should be run from a script instead of
    # the command line.
    if len(sys.argv) <= 1:
        raise ValueError("Need to specify which ONNX file to convert to .nnet!")

    warnings.warn(
        "WARNING: Using the default values of input bounds and normalization constants",
        category=RuntimeWarning,
        stacklevel=5,
    )
    onnx_file = sys.argv[1]
    if len(sys.argv) > 2:
        nnet_file = sys.argv[2]
        onnx_to_nnet(onnx_file, nnet_file=nnet_file)
    else:
        onnx_to_nnet(onnx_file)


if __name__ == "__main__":
    main()
