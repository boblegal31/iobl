Python IOBL library
===================

Library and CLI tools for interacting with Legrand In One PLC devices.
It uses a Legrand 882 13 device to communicate with PLC devices.
Based on the RFLink library (http://www.nemcon.nl/blog2/) and on the work 
by Michel Taverna (http://code.google.com/p/boxio/)

Requirements
------------

- Python 3.4 (or higher)

Description
-----------

This package is created as a library for the Home assistant legrandinone component implementation. A CLI has been created mainly for debugging purposes but may be extended in the future for more real-world application if needed.

Installation
------------

.. code-block:: bash

    $ pip install iobl

Usage
-----


.. code-block:: bash

    $ iobl -h
        Command line interface for iobl library.

        Usage:
          iobl [-v | -vv] [options]
          iobl [-v | -vv] [options] [commands [optionnal command args]]
          iobl (-h | --help)
          iobl --version

        Options:
          -p --port=<port>       Serial port to connect to [default: /dev/ttyACM0],
                                   or TCP port in TCP mode.
          --baud=<baud>          Serial baud rate [default: 115200].
          --host=<host>          TCP mode, connect to host instead of serial port.
          -h --help              Show this screen.
          -v                     Increase verbosity
          --version              Show version.
        Commands:
          -w --who=<who>         Device class to send command to.
          -W --what=<what>       Command type to send to device.
          -l --legrand_id=<id>   Legrand id of the device to send command to.
          -u --unit=<unit>       Sub unit in the device to send command to.
        Optionnal command args:
          -d --dimension         Send a dimension_set/request command (bus_command otherwise)
          --val=<values>         Values for dimension set command, comma separated list
          -m --comm_mode=<mode>  Communication mode to use (unicast, multicast,...).
          -M --comm_media=<media>  Communication media to use (plc, ir,...).

Intercept and display IOBL packets:

.. code-block:: bash

    $ iobl
        {'what': 'move_down', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}
        {'what': 'move_up', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}
        {'what': 'move_stop', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}

Move up or down a shutter device:

.. code-block:: bash

    $ iobl --who=automation --what=move_up --legrand_id=123456 --unit=2
    $ iobl --who=automation --what=move_down --legrand_id=123456 --unit=2

Send a dimension_request packet for requesting DEVICE_DESCRIPTION:

.. code-block:: bash

    $ iobl --who=configuration --what=device_description_request --legrand_id=123456 --unit=2 -d

Send a set_dimension packet for setting the DIM Level:

.. code-block:: bash

    $ iobl --who=light --what=go_to_level_time --legrand_id=123456 --unit=2 -d --val=11

Use of TCP mode instead of serial port:

.. code-block:: bash

    $ iobl --host 1.2.3.4 --port 1234

Debug logging is shown in verbose mode for debugging:

.. code-block:: bash

    $ iobl -vv
        DEBUG:asyncio:Using selector: EpollSelector
        DEBUG:iobl.protocol:connected
        DEBUG:iobl.protocol:received data: *2*2*#1975298##
        DEBUG:iobl.protocol:got packet: *2*2*#1975298##
        DEBUG:iobl.protocol:decoded packet: {'who': 'automation', 'what': 'move_up', 'media': None, 'type': 'command', 'unit': '2', 'legrand_id': '220880', 'command': '', 'mode': 'unicast'}
        DEBUG:iobl.protocol:got packet: {'who': 'automation', 'what': 'move_up', 'media': None, 'type': 'command', 'unit': '2', 'legrand_id': '220880', 'command': '', 'mode': 'unicast'}
        {'legrand_id': '220880', 'type': 'command', 'media': None, 'command': '', 'mode': 'unicast', 'who': 'automation', 'unit': '2', 'what': 'move_up'}

