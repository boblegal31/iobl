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
  -m=<handling>          How to handle incoming packets [default: command].
  -h --help              Show this screen.
  -v                     Increase verbosity
  --version              Show version.
Commands:
  -w --who=<who>         Device class to send command to.
  -W --what=<what>       Command type to send to device.
  -l --legrand_id=<id>   Legrand id of the device to send command to.
  -u --unit=<unit>       Sub unit in the device to send command to.
Optionnal command args:
  -m --comm_mode=<mode>  Communication mode to use (unicast, multicast, broadcst,...).
  -M --comm_media=<media>  Communication media to use (plc, ir,...).

"""

import asyncio
import logging
import sys

import pkg_resources
from docopt import docopt
from collections import defaultdict
from typing import Any, Callable, Dict, Generator, cast

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
    print (packet)

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

    if args['-m'] is None:
        protocol = PROTOCOLS['command']
    else:
        protocol = PROTOCOLS[args['-m']]

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
            data = cast(Dict[str, Any], {
                'type': 'command',
                'legrand_id' : args['--legrand_id'],
                'who' : args['--who'],
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
