# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Translate the NNet files into ONNX files."""

from pathlib import Path

import hydra
from hydra.core.config_store import ConfigStore

from pycasx.conf import ONNXConfig
from pycasx.tools.NNet.converters.nnet_to_onnx import nnet_to_onnx

ROOT_FOLDER = Path(Path(__file__).parent.parent, "assets", "neural_networks")
HCAS_FOLDER = Path(ROOT_FOLDER, "hcas")
VCAS_FOLDER = Path(ROOT_FOLDER, "vcas")


cs = ConfigStore.instance()
cs.store(name="onnx_", node=ONNXConfig)


@hydra.main(version_base=None, config_path="pkg://pycasx.conf", config_name="onnx")
def convert_to_onnx(cfg: ONNXConfig) -> None:
    """Convert NNet to onnx.

    Search for all .NNet files in the default directory and convert them
    to onnx model files.

    Args:
        cfg (ONNXConfig): The configuration for the onnx command.
    """
    hcas_folder = HCAS_FOLDER if cfg.hcas is None else Path(cfg.hcas)
    vcas_folder = VCAS_FOLDER if cfg.vcas is None else Path(cfg.vcas)
    for nnet_file in hcas_folder.glob("*.nnet"):
        nnet_to_onnx(str(nnet_file.resolve()), normalize_network=True)
    for nnet_file in vcas_folder.glob("*.nnet"):
        nnet_to_onnx(str(nnet_file.resolve()), normalize_network=True)
