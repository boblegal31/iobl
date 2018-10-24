"""Command line interface for iobl library.

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

"""

import asyncio
import logging
import sys

from typing import Any, Dict, cast
import pkg_resources
from docopt import docopt

from .protocol import (
    EventHandling,
    PacketHandling,
    IoblProtocol,
    create_iobl_connection
)

PROTOCOLS = {
    'command': IoblProtocol,
    'event': EventHandling,
    'print': PacketHandling,
}


def print_callback(packet):
    """Print received & decoded packets."""
    print(packet)


def main(argv=sys.argv[1:], loop=None):
    """Parse argument and setup main program loop."""
    args = docopt(__doc__, argv=argv,
                  version=pkg_resources.require('iobl')[0].version)

    level = logging.ERROR
    if args['-v']:
        level = logging.INFO
    if args['-v'] == 2:
        level = logging.DEBUG
    logging.basicConfig(level=level)

    if not loop:
        loop = asyncio.get_event_loop()

    protocol = PROTOCOLS['command']

    conn = create_iobl_connection(
        protocol=protocol,
        host=args['--host'],
        port=args['--port'],
        baud=args['--baud'],
        loop=loop,
        ignore=None,
        packet_callback=print_callback,
    )

    transport, protocol = loop.run_until_complete(conn)

    try:
        if not args.get('--legrand_id') is None:
            if args['--comm_mode'] is None:
                args['--comm_mode'] = 'unicast'
            if args['--comm_media'] is None:
                args['--comm_media'] = 'plc'

            if args['--dimension']:
                data = cast(Dict[str, Any], {
                    'type': 'set_dimension',
                    'legrand_id': args['--legrand_id'],
                    'who': args['--who'],
                    'mode': args['--comm_mode'],
                    'media': args['--comm_media'],
                    'unit': args['--unit'],
                    'dimension': args['--what'],
                })
                val = list()
                for value in args['--val'].split(','):
                    val.append(value)

                data['values'] = val

            else:
                data = cast(Dict[str, Any], {
                    'type': 'bus_command',
                    'legrand_id': args['--legrand_id'],
                    'who': args['--who'],
                    'mode': args['--comm_mode'],
                    'media': args['--comm_media'],
                    'unit': args['--unit'],
                    'what': args['--what'],
                })

            loop.run_until_complete(
                protocol.send_packet(data))
        else:
            loop.run_forever()
    except KeyboardInterrupt:
        # cleanup connection
        transport.close()
        loop.run_forever()
    finally:
        loop.close()
