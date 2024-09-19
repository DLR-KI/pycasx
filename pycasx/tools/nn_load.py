# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Function to load all neural network models from ONNX files."""
from __future__ import annotations

from pathlib import Path

import onnx
from onnx2torch import convert
from onnx.onnx_ml_pb2 import ModelProto
from torch.fx import GraphModule

from pycasx.tools.NNet.nnet import NNet


def load_nnet_from_path(nnet_path: Path | str) -> dict[str, NNet]:
    """Load all neural network models from NNet files.

    Args:
        nnet_path (Path | str): Path to the NNet files.

    Returns:
        dict[str, NNet]: Dictionary of neural network models.
    """
    nnet_models: dict[str, NNet] = {}
    nnet_path = Path(nnet_path).resolve()
    for model_path in nnet_path.glob("*.nnet"):
        model_name = model_path.stem
        nnet_models[model_name] = NNet(str(model_path))
    return nnet_models


def load_onnx_from_path(onnx_path: Path | str) -> dict[str, ModelProto]:
    """Load all neural network models from ONNX files.

    Args:
        onnx_path (Path | str): Path to the ONNX files.

    Returns:
        dict[str, ModelProto]: Dictionary of neural network models.
    """
    onnx_models: dict[str, ModelProto] = {}
    onnx_path = Path(onnx_path).resolve()
    for model_path in onnx_path.glob("*.onnx"):
        model_name = model_path.stem
        onnx_models[model_name] = onnx.load(str(model_path))
    return onnx_models


def load_torch_from_path(onnx_path: Path | str) -> dict[str, GraphModule]:
    """Load all neural network models from ONNX files.

    Args:
        onnx_path (Path | str): Path to the ONNX files.

    Returns:
        dict[str, GraphModule]: Dictionary of neural network models.
    """
    torch_models: dict[str, GraphModule] = {}
    onnx_path = Path(onnx_path).resolve()
    for model_path in onnx_path.glob("*.onnx"):
        model_name = model_path.stem
        torch_models[model_name] = convert(
            onnx.load(str(model_path)), save_input_names=True
        )
    return torch_models
