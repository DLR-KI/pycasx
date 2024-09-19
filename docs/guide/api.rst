.. SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
..
.. SPDX-License-Identifier: CC-BY-4.0
API Mode
========

The API mode is a FastAPI application that exposes a REST API to interact with the ACAS X.
This endpoint can be used to create new applications with the ACAS X running on a secondary system.

Usage
-----

The API mode is per default included in the :code:`acasx` command option.
Thus, to start the API mode, simply run:

.. code-block:: bash

    pycasx acasx

This will start the API mode on the default port of 8008.
To change the port, use the ``api.port`` option:

.. code-block:: bash

    pycasx acasx api.port 8080

Endpoints
---------

The following endpoints are available to query.

:code:`/docs`
^^^^^^^^^^^^^

The documentation for the API is available at ``/docs``.
The full URL is http://localhost:8008/docs by default.

:code:`/`
^^^^^^^^^

The root endpoint (http://localhost:8008/) is used to query the status of the ACAS X.
It returns a JSON object with the following fields:

.. code-block:: json

    {
        "hcas": {
            "advisory": {
                "value": 0,
                "name": "COC"
            },
            "connector": "adsb"
        },
        "vcas": {
            "advisory": {
                "value": 4,
                "name": "CL1500"
            },
            "connector": "adsb"
        },
        "timestamp": 1318377600.0
    }

:code:`/ownship`
^^^^^^^^^^^^^^^^

This endpoint returns the current state of the ownship.

.. code-block:: json

    {
        "call_sign": "FG-4229",
        "altitude": 10732.387208,
        "vertical_speed": -0.037046,
        "true_airspeed": 507.070057184784,
        "heading": 0.652215,
        "latitude": 72.135595,
        "longitude": -22.531261,
        "timestamp": 1706103314.730101
    }

:code:`/intruders` and :code:`/intruders/{call_sign}`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This endpoint returns a list of all intruders currently tracked by the ACAS X.
The default units are:

.. list-table:: Default units for the intruder description
    :widths: 50 50
    :header-rows: 1

    * - Parameter
      - Unit
    * - Altitude
      - ft
    * - Vertical speed
      - ft/s
    * - Airspeed
      - kt
    * - Heading
      - deg
    * - Latitude
      - deg
    * - Longitude
      - deg
    * - Rho
      - ft
    * - Theta
      - deg
    * - Psi
      - deg
    * - V_own
      - ft/s
    * - V_int
      - ft/s
    * - Tau
      - s
    * - h
      - ft
    * - hdot_own
      - ft/min
    * - hdot_int
      - ft/min

For example for :code:`/intruders` this will be similar to:

.. code-block:: json

    {
        "INTRUDER": {
            "aircraft": {
                "call_sign": "INTRUDER",
                "altitude": 10000.0,
                "vertical_speed": 0.0,
                "airspeed": 451.0,
                "heading": 179.977692,
                "latitude": 64.954861,
                "longitude": -22.649997000000003
            },
            "triggers_nmac": false,
            "hcas_advisory": -1,
            "vcas_advisory": -1,
            "hcas_state_variables": {
                "rho": 80576.60919363388,
                "theta": -178.61455181770793,
                "psi": 181.25831800000003,
                "v_own": 242.19262819699622,
                "v_int": 761.2022455526394,
                "tau": -80.29262490733487,
                "s_adv": -1
            },
            "vcas_state_variables": {
                "h": 8222.950633,
                "hdot_own": -1299.29958,
                "hdot_int": 0.0,
                "tau": -80.29262490733487,
                "s_adv": -1
            },
            "timestamp": 1318377600.0
        },
        "LH857": {
            "aircraft": {
                "call_sign": "LH857",
                "altitude": 170.0,
                "vertical_speed": 0.0,
                "airspeed": 0.0,
                "heading": 44.19180200000001,
                "latitude": 63.99276900000001,
                "longitude": -22.625786
            },
            "triggers_nmac": false,
            "hcas_advisory": -1,
            "vcas_advisory": -1,
            "hcas_state_variables": {
                "rho": 86663.27074856794,
                "theta": -178.8139020362879,
                "psi": 317.044208,
                "v_own": 242.19262819699622,
                "v_int": 0.0,
                "tau": -357.8277279156412,
                "s_adv": -1
            },
            "vcas_state_variables": {
                "h": -1607.049367,
                "hdot_own": -1299.29958,
                "hdot_int": 0.0,
                "tau": -357.8277279156412,
                "s_adv": -1
            },
            "timestamp": 1318377600.0
        },
        "timestamp": 1318377600.0
    }

and for :code:`/intruders/INTRUDER` similar to:

.. code-block:: json

    {
        "aircraft": {
            "call_sign": "INTRUDER",
            "altitude": 10000.0,
            "vertical_speed": 0.0,
            "airspeed": 451.0,
            "heading": 179.951324,
            "latitude": 64.916918,
            "longitude": -22.649914
        },
        "triggers_nmac": false,
        "hcas_advisory": -1,
        "vcas_advisory": -1,
        "hcas_state_variables": {
            "rho": 81163.99381904684,
            "theta": -178.58743469905303,
            "psi": 182.94445599999997,
            "v_own": 237.5529283537475,
            "v_int": 761.2022455526394,
            "tau": -81.2774401291326,
            "s_adv": -1
        },
        "vcas_state_variables": {
            "h": 9991.170899,
            "hdot_own": -511.55333999999993,
            "hdot_int": 0.0,
            "tau": -81.2774401291326,
            "s_adv": -1
        },
        "timestamp": 1318377600.0
    }

:code:`/hcas` and :code:`/vcas`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These endpoints return just the status of the current CAS system, similar to the root endpoint.

:code:`/connector`
^^^^^^^^^^^^^^^^^^

This endpoints can be used to PUT a new connector for the ACAS X to use.
The only connector currently supported is the generic ``adsb`` connector.

An exemplary PUT request would be:

.. code-block:: bash

    curl -X 'PUT' 'http://0.0.0.0:8008/connector?connection=adsb' -H 'accept: application/json'r
