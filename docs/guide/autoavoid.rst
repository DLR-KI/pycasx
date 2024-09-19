.. SPDX-FileCopyrightText: 2024 German Aerospace Center (DLR) <https://dlr.de>
..
.. SPDX-License-Identifier: CC-BY-4.0

Autoavoid
==========

The :code:`pyCASX` packages comes with a basic autoavoid command.
The command is indented only to extend the functionality of FlightGear's built-in autopilot by allowing to apply ACAS X advisories provided by the :code:`pyCASX` package.

Preparation
-----------

The autoavoid command is intended to work with a modified version of the [737-200](https://github.com/FGMEMBERS/737-200).
Currently, the modding has to be performed manually, later versions will ship a custom airplane already pre-modded.

Modding the 737-200
^^^^^^^^^^^^^^^^^^^

In the root directory of the 737-200, open the file :code:`Systems/737-autoflight.xml` and replace two controllers.

:code:`altitude-hold`
"""""""""""""""""""""

Replace the first stage of the :code:`altitude-hold` controller with the following code:

.. code-block:: xml

    <pi-simple-controller>
        <name>Altitude Hold (Altimeter) Stage #1</name>
        <debug>false</debug>
        <enable>
            <prop>autopilot/locks/altitude</prop>
            <value>altitude-hold</value>
        </enable>
        <input>
            <prop>position/altitude-ft</prop>
        </input>
        <reference>
            <prop>autopilot/settings/target-altitude-ft</prop>
        </reference>
        <output>
            <prop>autopilot/internal/target-climb-rate-fps</prop>
        </output>
        <config>
            <Kp>0.05</Kp>
            <Ki>0.0</Ki>
            <u_min>-25.0</u_min>
            <u_max>40.0</u_max>
        </config>
    </pi-simple-controller>

:code:`wing-leveler`
""""""""""""""""""""

Replace the :code:`wing-leveler` controller with the following code:

.. code-block:: xml

    <pid-controller>
        <name>Wing Leveler (Turn Indicator)</name>
        <debug>false</debug>
        <enable>
            <prop>autopilot/locks/heading</prop>
            <value>wing-leveler</value>
        </enable>
        <input>
            <prop>orientation/roll-deg</prop>
        </input>
        <reference>
            <prop>autopilot/settings/target-bank-angle-deg</prop>
        </reference>
        <output>
            <prop>controls/flight/aileron</prop>
        </output>
        <config>
            <Kp>0.02</Kp>
            <beta>1.0</beta>
            <alpha>0.1</alpha>
            <gamma>0.0</gamma>
            <Ti>10.0</Ti>
            <Td>0.00001</Td>
            <u_min>-1.0</u_min>
            <u_max>1.0</u_max>
        </config>
    </pid-controller>


Usage
-----

The autoavoid command is a simple command line tool, integrated into the :code:`pycasx acasx` command, that can be used to control the autopilot of the 737-200.
It uses the advisories provided by the :code:`pyCASX` package to control the autopilot.

The autoavoid can be started by running the following command:

.. code-block:: bash

    pycasx acasx autoavoid.active=True autoavoid.mode=[hcas|vcas]

The :code:`autoavoid.active` parameter is disabled by default to not interfere with the normal operation of the autopilot.
