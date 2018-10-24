"""Asyncio protocol implementation of IOBL."""
import asyncio
import logging
from datetime import timedelta
from functools import partial
from typing import Callable, List

from serial_asyncio import create_serial_connection

from .parser import (
    valid_packet,
    decode_packet,
    encode_packet
)

log = logging.getLogger(__name__)

TIMEOUT = timedelta(seconds=5)


class ProtocolBase(asyncio.Protocol):
    """Manage low level iobl protocol."""

    transport = None  # type: asyncio.Transport

    def __init__(self, loop=None, disconnect_callback=None) -> None:
        """Initialize class."""
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()
        self.packet = ''
        self.buffer = ''
        self.disconnect_callback = disconnect_callback

    def connection_made(self, transport):
        """Just logging for now."""
        self.transport = transport
        log.debug('connected')

    def data_received(self, data):
        """Add incoming data to buffer."""
        data = data.decode()
        log.debug('received data: %s', data.strip())
        self.buffer += data
        self.handle_lines()

    def handle_lines(self):
        """Assemble incoming data into per-message packets."""
        while "##" in self.buffer:
            line, self.buffer = self.buffer.split("##", 1)
            if valid_packet(line + '##'):
                self.handle_raw_packet(line + '##')
            else:
                log.warning('dropping invalid data: %s', line + '##')

    def handle_raw_packet(self, raw_packet: bytes) -> None:
        """Handle one raw incoming packet."""
        raise NotImplementedError()

    def send_raw_packet(self, packet: str):
        """Encode and put packet string onto write buffer."""
        log.debug('writing data: %s', repr(packet))
        self.transport.write(packet.encode())

    def connection_lost(self, exc):
        """Log when connection is closed, if needed call callback."""
        if exc:
            log.exception('disconnected due to exception')
        else:
            log.info('disconnected because of close/abort.')
        if self.disconnect_callback:
            self.disconnect_callback(exc)


class PacketHandling(ProtocolBase):
    """Handle translating iobl packets to/from python primitives."""

    def __init__(self, *args, packet_callback: Callable = None,
                 **kwargs) -> None:
        """Add packethandling specific initialization.

        packet_callback: called with every complete/valid packet
        received.
        """
        super().__init__(*args, **kwargs)
        if packet_callback:
            self.packet_callback = packet_callback

    def handle_raw_packet(self, raw_packet):
        """Parse raw packet string into packet dict."""
        log.debug('got packet: %s', raw_packet)
        packet = None
        try:
            packet = decode_packet(raw_packet)
        except:
            log.exception('failed to parse packet: %s', packet)

        log.debug('decoded packet: %s', packet)

        if packet:
            if 'ack' in packet or 'nack' in packet:
                # handle response packets internally
                log.debug('command response: %s', packet)
            else:
                self.handle_packet(packet)
        else:
            log.warning('no valid packet')

    def handle_packet(self, packet):
        """Process incoming packet dict and optionally call callback."""
        if self.packet_callback:
            # forward to callback
            self.packet_callback(packet)
        else:
            print('packet', packet)

    @asyncio.coroutine
    def send_packet(self, fields):
        """Concat fields and send bus_command packet to gateway."""
        self.send_raw_packet(encode_packet(fields))


class EventHandling(PacketHandling):
    """Breaks up packets into individual events with ids'."""

    def __init__(self, *args, event_callback: Callable = None,
                 ignore: List[str] = None, **kwargs) -> None:
        """Add eventhandling specific initialization."""
        super().__init__(*args, **kwargs)
        self.event_callback = event_callback
        # suppress printing of packets
        if not kwargs.get('packet_callback'):
            self.packet_callback = lambda x: None
        if ignore:
            log.debug('ignoring: %s', ignore)
            self.ignore = ignore
        else:
            self.ignore = []

    def _handle_packet(self, packet):
        """Event specific packet handling logic."""
        if self.ignore_event(packet['type'], packet['legrand_id']):
            log.debug('ignoring packet with type/id: %s', packet)
            return
        log.debug('got packet: %s', packet)
        if self.event_callback:
            self.event_callback(packet)

    def handle_packet(self, packet):
        """Apply event specific handling and pass on to packet handling."""
        self._handle_packet(packet)
        super().handle_packet(packet)

    def ignore_event(self, pkt_type, legrand_id):
        """Verify event id against list of events to ignore.

        >>> e = EventHandling(ignore=[
        ...   'test1_00',
        ...   'test2_*',
        ... ])
        >>> e.ignore_event('test1_00')
        True
        >>> e.ignore_event('test2_00')
        True
        >>> e.ignore_event('test3_00')
        False
        """
        for ignore in self.ignore:
            if (ignore == pkt_type or
                    (ignore.endswith('*') and
                     legrand_id.startswith(ignore[:-1]))):
                return True
        return False


class IoblProtocol(EventHandling):
    """Combine preferred abstractions that form complete IOBL interface."""


def create_iobl_connection(port=None, host=None, baud=115200,
                           protocol=IoblProtocol, packet_callback=None,
                           event_callback=None, disconnect_callback=None,
                           ignore=None, loop=None):
    """Create IOBL manager class, returns transport coroutine."""
    # use default protocol if not specified
    protocol = partial(
        protocol,
        loop=loop if loop else asyncio.get_event_loop(),
        packet_callback=packet_callback,
        event_callback=event_callback,
        disconnect_callback=disconnect_callback,
        ignore=ignore if ignore else [],
    )

    # setup serial connection if no transport specified
    if host:
        conn = loop.create_connection(protocol, host, port)
    else:
        baud = baud
        conn = create_serial_connection(loop, protocol, port, baud)

    return conn
