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
          iobl [-v | -vv] [options] <who=> <what=> <legrand_id=> <unit=> [<comm_mode=> <comm_media=>]
          iobl (-h | --help)
          iobl --version

        Options:
          -p --port=<port>   Serial port to connect to [default: /dev/ttyACM0],
                               or TCP port in TCP mode.
          --baud=<baud>      Serial baud rate [default: 115200].
          --host=<host>      TCP mode, connect to host instead of serial port.
          -m=<handling>      How to handle incoming packets [default: event].
          -h --help          Show this screen.
          -v                 Increase verbosity
          --version          Show version.

    <who=> must be completed with the class of device to control. For the moment, only AUTOMATION (shutter command) and SCENARIO classes have been tested so far.
    <what=> must be completed with the action requested. For AUTOMATION class, the action is either move_up, move_down or move_stop.
    <legrand_id=> must be completed with the "legrand_id" of the device to control. The legrand_id is usually indicated on the back of the device.
    <unit=> must be completedunit number in the device to control. Ususally, for an AUTOMATION class device, unit shall be 2.
    <comm_mode=> may be completed with the communication mode to use : unicast, multicast or broadcast. Defaults to unicast.
    <comm_media=> may be completed with the communication media to use : PLC, IR, RF. Only PLC has been tested so far. Defaults to PLC.

Intercept and display IOBL packets:

.. code-block:: bash

    $ iobl
        {'what': 'move_down', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}
        {'what': 'move_up', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}
        {'what': 'move_stop', 'type': 'command', 'unit': '2', 'mode': 'unicast', 'who': 'automation', 'legrand_id': '123456', 'media': 'plc', 'command': ''}

Move up or down a shutter device:

.. code-block:: bash

    $ iobl who=automation what=move_up legrand_id=123456 unit=1
    $ iobl who=automation what=move_down legrand_id=123456 unit=1

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

