# SPDX-FileCopyrightText: 2018 Stanford Intelligent Systems Laboratory
#
# SPDX-License-Identifier: MIT
"""Convert NNet to onnx.

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

import numpy as np
import onnx
from loguru import logger
from onnx import helper, numpy_helper
from onnx.onnx_ml_pb2 import OperatorSetIdProto, TensorProto

from pycasx.tools.NNet.utils.normalize_nnet import normalize_nnet
from pycasx.tools.NNet.utils.read_nnet import read_nnet


def nnet_to_onnx(
    nnet_file: str,
    onnx_file: str = "",
    output_var: str = "y_out",
    input_var: str = "X",
    normalize_network: bool = False,
) -> None:  # pylint: disable=too-many-locals
    """Convert a .nnet file to onnx format.

    Args:
        nnet_file (string): .nnet file to convert to onnx
        onnx_file (string): name for the created .onnx file
        output_var (string): name of the output variable in
            onnx
        input_var (string): name of the input variable in
        normalize_network (bool): if true, adapt the network weights and
            biases so that networks and inputs do not need to be
            normalized. Default is False.
    """
    if normalize_network:
        weights, biases, input_mins, input_maxes, _, _ = normalize_nnet(
            nnet_file, with_norm=True
        )
    else:
        weights, biases, input_mins, input_maxes, _, _ = read_nnet(
            nnet_file, with_norm=True
        )

    input_size = weights[0].shape[1]
    output_size = weights[-1].shape[0]
    num_layers = len(weights)

    # Default onnx filename if none specified
    if onnx_file == "":
        onnx_file = nnet_file[:-4] + "onnx"

    # Initialize graph
    inputs = [
        helper.make_tensor_value_info(
            input_var,
            TensorProto.FLOAT,
            [input_size],
        )
    ]
    outputs = [
        helper.make_tensor_value_info(
            output_var,
            TensorProto.FLOAT,
            [output_size],
        )
    ]
    operations = []
    initializers = []

    # Add input limits
    if normalize_network:
        operations.append(
            helper.make_node(
                "Split",
                [input_var, "S0"],
                [f"S_{i:d}" for i in range(input_size)],
                axis=0,
            )
        )
        initializers.append(
            numpy_helper.from_array(np.ones((input_size,), dtype=np.int64), name="S0")
        )
        for i in range(input_size):
            operations.append(
                helper.make_node(
                    "Clip",
                    [f"S_{i:d}", f"min_input{i:d}", f"max_input{i:d}"],
                    [f"C_{i:d}"],
                )
            )
            initializers.append(
                numpy_helper.from_array(
                    np.asarray(input_mins[i], dtype=np.float32),
                    name=f"min_input{i:d}",
                )
            )
            initializers.append(
                numpy_helper.from_array(
                    np.asarray(input_maxes[i], dtype=np.float32),
                    name=f"max_input{i:d}",
                )
            )
        operations.append(
            helper.make_node(
                "Concat", [f"C_{i:d}" for i in range(input_size)], ["C0"], axis=0
            )
        )
        input_var = "C0"

    # Loop through each layer of the network and add operations and initializers
    for i in range(num_layers):
        # Use outputVar for the last layer
        output_name = f"H{i:d}"
        if i == num_layers - 1:
            output_name = output_var

        # Weight matrix multiplication
        operations.append(
            helper.make_node("MatMul", [f"W{i:d}", input_var], [f"M{i:d}"])
        )
        initializers.append(
            numpy_helper.from_array(weights[i].astype(np.float32), name=f"W{i:d}")
        )

        # Bias add
        operations.append(
            helper.make_node("Add", [f"M{i:d}", f"B{i:d}"], [output_name])
        )
        initializers.append(
            numpy_helper.from_array(biases[i].astype(np.float32), name=f"B{i:d}")
        )

        # Use Relu activation for all layers except the last layer
        if i < num_layers - 1:
            operations.append(helper.make_node("Relu", [f"H{i:d}"], [f"R{i:d}"]))
            input_var = f"R{i:d}"

    # Create the graph and model in onnx
    graph_proto = helper.make_graph(
        operations, "nnet2onnx_Model", inputs, outputs, initializers
    )
    op = OperatorSetIdProto()
    op.version = 13
    model_def = helper.make_model(graph_proto, opset_imports=[op])

    # Log the conversion
    logger.info(
        f"Converted NNet model at {nnet_file}\n\tto an ONNX model at {onnx_file}"
    )

    # Log additional statements
    logger.debug(f"Readable GraphProto:\n{helper.printable_graph(graph_proto)}")

    # Save the ONNX model
    onnx.save(model_def, onnx_file)


def main() -> None:
    """Convert nnet file to onnx.

    Read user inputs from sys.argv and run nnet2onnx function for
    different numbers of inputs.

    Raises:
        ValueError: if no .nnet file is specified via sys.argv
    """
    if len(sys.argv) <= 1:
        raise ValueError("Need to specify which .nnet file to convert to ONNX!")
    nnet_file = sys.argv[1]
    if len(sys.argv) > 2:
        onnx_file = sys.argv[2]
        if len(sys.argv) > 3:
            output_name = sys.argv[3]
            nnet_to_onnx(nnet_file, onnx_file, output_name)
        else:
            nnet_to_onnx(nnet_file, onnx_file)
    else:
        nnet_to_onnx(nnet_file)


if __name__ == "__main__":
    main()
