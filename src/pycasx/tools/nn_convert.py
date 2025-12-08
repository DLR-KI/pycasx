# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Functions to convert different NN formats to each other."""

from onnx.onnx_ml_pb2 import ModelProto
from onnx2torch import convert
from torch.fx import GraphModule


def onnx_to_torch(nets: dict[str, ModelProto]) -> dict[str, GraphModule]:
    """Convert ONNX models to PyTorch models.

    Args:
        nets (dict[str, ModelProto]): Dictionary of ONNX models.

    Returns:
        dict[str, GraphModule]: Dictionary of PyTorch models.
    """
    converted = {}
    for name, model in nets.items():
        converted[name] = convert(model, save_input_names=True)

    return converted
