# SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
#
# SPDX-License-Identifier: MIT
"""Configuration module for pycasx.

Also, list of all configuration dictionaries for typed hydra.

As hydra does not support type annotations from __future__ import, we
have to use the plain old typing module for Python 3.8 and 3.9 support.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union


@dataclass
class AutoavoidConfig:
    """Configuration for the autoavoid subsystem.

    Attributes:
        active (bool): If true, the autoavoid subsystem is active.
        mode (Optional[Literal["hcas", "vcas"]]): The mode to use.
    """

    active: bool
    mode: Optional[Literal["hcas", "vcas"]]


@dataclass
class GenericConnection:
    """Generic connection config.

    Attributes:
        host (str): Host address.
        port (int): Port.
    """

    host: str
    port: int


@dataclass
class TelnetConfig:
    """Configuration for the telnet connection.

    Mirror of the telnet configuration in pycasx.conf.launch.

    Attributes:
        port (int): The port to connect to.
        rate (int): The rate to connect at.
    """

    port: int
    rate: int


@dataclass
class LoggerConfig:
    """Configuration for the logger subcommand.

    Attributes:
        active (bool): If true, the logger is active.
        log_folder (str): The folder to log to.
        include_date (bool): If true, include the date in the log file.
        files (Dict[str, str]): The files to log to.
    """

    active: bool
    log_folder: str
    include_date: bool
    files: Dict[str, str]


@dataclass
class ACASXConfig:
    """Configuration for the ACAS X.

    Mirror of the ACAS X configuration in pycasx.conf.acasx.

    Attributes:
        update_rate (float): The update rate of the ACAS X.
        backend (str): The neural network backend to use for the CAS.
        autoavoid (AutoavoidConfig): The autoavoid configuration.
        adsb (GenericConnection): The ADS-B configuration.
        api (GenericConnection): The API configuration.
    """

    update_rate: float
    backend: str
    autoavoid: AutoavoidConfig
    logger: LoggerConfig
    adsb: GenericConnection
    api: GenericConnection


@dataclass
class WindowConfig:
    """General configuration for a window.

    Attributes:
        width (int): The width of the window.
        height (int): The height of the window.
    """

    width: int
    height: int


@dataclass
class CopyConfig:
    """Configuration for the copy command.

    Mirror of the copy configuration in pycasx.conf.copy.

    Attributes:
        fg_root (Optional[str]): The FlightGear root directory.
    """

    fg_root: Optional[str]


@dataclass
class LaunchConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for the launch command.

    Mirror of the launch configuration in pycasx.conf.launch.

    Attributes:
        background (bool): If true, run FlightGear in the background.
        disable_sound (bool): If true, disable sound.
        fg_root (Optional[str]): The FlightGear root directory.
        fgfs (Optional[str]): The path to the FlightGear executable.
        timeout (float): The timeout after which to kill FlightGear.
            Works only in non-background mode.
        fgfsrc (Optional[str]]): The path to the fgfsrc file.
        httpd (Optional[int]): The httpd port.
        telnet (Optional[TelnetConfig]): The telnet configuration.
        aircraft (Optional[str]): The aircraft to use.
        altitude (Optional[float]): The altitude of the ownship.
        heading (Optional[float]): The heading of the ownship.
        lat (Optional[float]): The latitude of the ownship.
        lon (Optional[float]): The longitude of the ownship.
        pitch (Optional[float]): The pitch of the ownship.
        roll (Optional[float]): The roll of the ownship.
        vc (Optional[float]): The vertical speed of the ownship.
        config (Optional[List[str]]): The FlightGear configuration files
            to use.
        prop (Optional[Dict[str, Any]]): The FlightGear properties to
            set.
        timeofday (Optional[str]): The time of day.
        wind (Optional[str]): The wind.
        ai_scenario (Optional[str]): The AI scenario to use.
    """

    # General
    background: bool
    disable_sound: bool
    fg_root: Optional[str]
    fgfs: Optional[str]
    timeout: float
    fgfsrc: Optional[str]

    # Connections
    httpd: Optional[int]
    telnet: Optional[TelnetConfig]

    # Ownship
    aircraft: Optional[str]
    altitude: Optional[float]
    heading: Optional[float]
    lat: Optional[float]
    lon: Optional[float]
    pitch: Optional[float]
    roll: Optional[float]
    vc: Optional[float]
    config: Optional[List[str]]
    prop: Optional[Dict[str, Any]]

    # Environment
    timeofday: Optional[str]
    wind: Optional[str]

    # Intruder
    ai_scenario: Optional[str]


@dataclass
class IntruderConfig:
    """A simple intruder config for the scenario generation.

    Attributes:
        type_ (str): The aircraft type
        class_ (str): The aircraft class
        model (str): The path to the xml model file
    """

    type_: str
    class_: str
    model: str


@dataclass
class WeightsConfig:
    """A simple dataclass to represent the weights for the scenario generation.

    Attributes:
        colliding (float): The weight for the colliding scenario
        parallel (float): The weight for the parallel scenario
        skewed (float): The weight for the skewed scenario
    """

    colliding: float
    parallel: float
    skewed: float


@dataclass
class BetaDistributionConfig:
    """A simple dataclass to represent a beta distribution.

    Attributes:
        spread (float | str): The spread of the distribution. If the
            value is a string, it will be interpreted by pint as a
            quantity.
        alpha (float): The alpha parameter
        beta (float): The beta parameter
    """

    spread: Union[float, str]
    alpha: float
    beta: float


@dataclass
class MinMaxConfig:
    """A simple dataclass to represent the min and max values.

    Attributes:
        min (float | str): The minimum value. If the value is a string,
            it will be interpreted by pint as a quantity.
        max (float | str): The maximum value. If the value is a string,
            it will be interpreted by pint as a quantity.
    """

    min_: Union[float, str]
    max_: Union[float, str]


@dataclass
class CollidingConfig:
    """A simple dataclass to represent the colliding scenario.

    Attributes:
        altitude (BetaDistributionConfig): The altitude distribution
        heading (MinMaxConfig): The heading distribution
        speed (MinMaxConfig): The speed distribution
    """

    altitude: BetaDistributionConfig
    heading: MinMaxConfig
    speed: MinMaxConfig


@dataclass
class ParallelConfig:
    """A simple dataclass to represent the parallel scenario.

    Attributes:
        altitude (BetaDistributionConfig): The altitude distribution
        horizontal (BetaDistributionConfig): The horizontal distribution
        speed (MinMaxConfig): The speed distribution
    """

    altitude: BetaDistributionConfig
    horizontal: BetaDistributionConfig
    speed: MinMaxConfig


@dataclass
class ScenarioConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for the launch command.

    Mirror of the launch configuration in pycasx.conf.launch.

    Attributes:
        dest_folder (str): The destination folder for the scenarios.
        n_scenarios (int): The number of scenarios to generate.
        sort_by_uuid (bool): Sort scenarios by UUID into separate
            folders.
        time_to_cpa (float | str): The time to CPA for the colliding
            scenario. If the value is a string, it will be interpreted
            by pint as a quantity.
        weights (WeightsConfig): The weights for the scenario
            generation.
        colliding (CollidingConfig): The colliding scenario
            configuration.
        parallel (ParallelConfig): The parallel scenario configuration.
        headless (bool): If true, run FlightGear in the background.
        disable_sound (bool): If true, disable sound.
        httpd (int): The httpd port.
        telnet (TelnetConfig): The telnet configuration.
        aircraft (str): The aircraft to use.
        altitude (float | str): The altitude of the ownship. If the
            value is a string, it will be interpreted by pint as a
            quantity.
        heading (float | str): The heading of the ownship. If the value
            is a string, it will be interpreted by pint as a quantity.
        lat (float | str): The latitude of the ownship. If the value is
            a string, it will be interpreted by pint as a quantity.
        lon (float | str): The longitude of the ownship. If the value is
            a string, it will be interpreted by pint as a quantity.
        pitch (float | str): The pitch of the ownship. If the value is a
            string, it will be interpreted by pint as a quantity.
        roll (float | str): The roll of the ownship. If the value is a
            string, it will be interpreted by pint as a quantity.
        vc (float | str): The vertical speed of the ownship. If the
            value is a string, it will be interpreted by pint as a
            quantity.
        config (List[str]): The FlightGear configuration files to use.
        prop (Dict[str, Any]): The FlightGear properties to set.
        timeofday (str): The time of day.
        wind (str): The wind.
        min_intruders (int): The minimum number of intruders.
        max_intruders (int): The maximum number of intruders.
        intruder (IntruderConfig): The intruder configuration.
    """

    # General scenario configuration
    dest_folder: str
    n_scenarios: int
    sort_by_uuid: bool

    # Colliding scenario configuration
    time_to_cpa: Union[float, str]
    weights: WeightsConfig
    colliding: CollidingConfig
    parallel: ParallelConfig

    # FlightGear
    headless: bool
    disable_sound: bool
    httpd: Optional[int]
    telnet: Optional[TelnetConfig]

    # Ownship
    aircraft: str
    altitude: Union[float, str]
    heading: Union[float, str]
    lat: Union[float, str]
    lon: Union[float, str]
    pitch: Union[float, str]
    roll: Union[float, str]
    vc: Union[float, str]
    config: List[str]
    prop: Dict[str, Any]

    # Environment
    timeofday: str
    wind: str

    # Intruder
    min_intruders: int
    max_intruders: int
    intruder: IntruderConfig


@dataclass
class ONNXConfig:
    """Configuration for the onnx command.

    Mirror of the onnx configuration in pycasx.conf.onnx.

    Attributes:
        hcas (Optional[str]): The path to the hcas folder.
        vcas (Optional[str]): The path to the vcas folder.
    """

    hcas: Optional[str]
    vcas: Optional[str]


@dataclass
class RunConfig:
    """Configuration for the run command.

    Mirror of the run configuration in cas.conf.run.

    Args:
        timeout (float): The timeout after which to kill FlightGear.
        venv_path (Optional[str]): The path to the virtual environment.
    """

    timeout: float
    venv_path: Optional[str]
