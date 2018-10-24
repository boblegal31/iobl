"""Parsers."""

import re
from enum import Enum
from typing import Any, Dict, cast

UNKNOWN = 'unknown'

DELIM = '*'
SPECIAL_REQUEST = r'^\*#\d{2,4}\*\*\d{1,2}##$'
#  *#*1##
ACK = r'^\*#\*(1)##$'
#  *#*0##
NACK = r'^\*#\*(0)##$'
ACK_NACK_RE = r'|'.join([ACK, NACK])
#  *WHO*WHAT*WHERE##  *1*1*0#13236017##
BUS_COMMAND = r'^\*(\d+)\*(\d+#?\d*#?\d*#?)\*(\d*#*\d+#*\d*)##$'
#  *#WHO*WHERE
STATUS_REQUEST = r'\*#(\d+)\*(\d*#*\d+#*\d*)##$'
#  *#WHO*WHERE*DIMENSION(*VAL1*VALn)##
DIMENSION_REQUEST = r'^\*#(\d+)\*(\d*#*\d+#*\d*)\*([\d#\*]+)##$'
#  *#WHO*WHERE*#DIMENSION*VAL1*VALn##
DIMENSION_SET = r'^\*#(\d+)\*(\d*#*\d+#*\d*)\*(\d*#*\d+#*\d*)##$'

WHERE_DEFINITION = r'(\d+)?#*(\d+)?#*(\d*)$'
WHAT_DEFINITION = r'(\d+)#?(\d*)#?(\d*)#?'
DIMENSION_DEFINITION = r'([\d#]+)\*?(\d*)(.*)'
VAL_DEFINITION = r'\*?(\d+)(.*)'

bus_command_re = re.compile(BUS_COMMAND)
ack_nack_re = re.compile(ACK_NACK_RE)
special_request_re = re.compile(SPECIAL_REQUEST)
status_request_re = re.compile(STATUS_REQUEST)
dimension_req_re = re.compile(DIMENSION_REQUEST)
dimension_set_re = re.compile(DIMENSION_SET)

where_decode_re = re.compile(WHERE_DEFINITION)
what_decode_re = re.compile(WHAT_DEFINITION)
dimension_decode_re = re.compile(DIMENSION_DEFINITION)
val_decode_re = re.compile(VAL_DEFINITION)


class iobl_packet(Enum):
    """Open Packet definition."""


devicetype = {
    '1': 'light',
    '2': 'automation',
    '4': 'thermoregulation',
    '8': 'doorentry',
    '25': 'scenario',
    '13': 'management',
    '14': 'special',
    '1000': 'configuration',
    }

# """light command identification."""
light_command = {
    '1': 'on',
    '0': 'off',
    '38': 'dim_stop',
    }

# """light dimension set identification."""
light_dimension = {
    '10': 'dim_step',
    '1': 'go_to_level_time',
    }

# """shutter command identification."""
automation_command = {
    '0': 'move_stop',
    '1': 'move_up',
    '2': 'move_down',
    }

# """thermoregulation command identification."""
thermoregulation_command = {
    #"""thermoregulation command identification."""
    '50': 'setpoint',
    '51': 'override_setpoint',
    '52': 'end_override',
    '53': 'go_to_temperature',
    '54': 'stop',
    '55': 'end_stop',
    '56': 'stop_fan_speed',
    '57': 'low_fan_speed',
    '58': 'high_fan_speed',
    '59': 'confort_jour_rouge',
    }

# """scenario command identification."""
scenario_command = {
    '11': 'action',
    '16': "stop_action",
    '17': "action_for_time",
    '18': "action_in_time",
    '19': "info_scene_off"
    }

# """door entry command identification."""
door_entry_command = {
    '1': 'concierge_call',
    '19': 'locker_control'
    }

# """configuration command identification."""
configuration_command = {
    '61': 'open_learning',
    '62': 'close_learning',
    '63': 'address_erase',
    '64': 'memory_reset',
    '65': 'memory_full',
    '66': 'memory_read',
    '72': 'valid_action',
    '73': 'invalid_action',
    '68': 'cancel_id',
    '69': 'management_clock_synchronisation',
    '70': 'occupied',
    '71': 'unoccupied'
    }

# """configuration dimension identification."""
configuration_dimension = {
    '13': 'announce_id',
    '51': 'device_description_request',
    '55': 'unit_description_request',
    }

communication_mode = {
    '0': 'broadcast',
    '1': 'multicast',
    '2': 'unicast_direct',
    '3': 'unicast',
    '': 'unicast',
    }

communication_media = {
    '0': 'plc',
    '1': 'rf',
    '2': 'ir',
    '': 'plc',
    }


def valid_packet(packet: str) -> bool:
    """Verify if packet is valid."""
    return (bool(bus_command_re.match(packet)) |
            bool(ack_nack_re.match(packet)) |
            bool(status_request_re.match(packet)) |
            bool(dimension_req_re.match(packet)) |
            bool(dimension_set_re.match(packet)))


def decode_packet(packet: str) -> dict:
    """Break packet down into primitives, and do basic interpretation."""
    if bool(bus_command_re.match(packet)):
        who, what, where = bus_command_re.match(packet).group(1, 2, 3)

        data = cast(Dict[str, Any], {
            'who': devicetype.get(who),
        })

        device_type_name = {v: k for k, v in devicetype.items()}
        command = what_decode_re.match(what).group(1)

        if who == device_type_name.get('light'):
            data['what'] = light_command.get(what)
        elif who == device_type_name.get('automation'):
            data['what'] = automation_command.get(what)
        elif who == device_type_name.get('scenario'):
            data['what'] = scenario_command.get(command)
        elif who == device_type_name.get('configuration'):
            data['what'] = configuration_command.get(command)
        elif who == device_type_name.get('doorentry'):
            data['what'] = door_entry_command.get(what)
        elif who == device_type_name.get('thermoregulation'):
            data['what'] = thermoregulation_command.get(command)

        data['legrand_id'], data['unit'], data['mode'], data['media'] = parse_legrand_id(str(where))

        data['type'] = 'bus_command'
        data['command'] = ''

    elif bool(ack_nack_re.match(packet)):

        if ack_nack_re.match(packet).group(1) == '0':
            data = cast(Dict[str, Any], {
                'type': 'nack',
                'legrand_id': '',
            })
        else:
            data = cast(Dict[str, Any], {
                'type': 'ack',
                'legrand_id': '',
            })

    elif bool(status_request_re.match(packet)):

        who, where = status_request_re.match(packet).group(1, 2)
        data = cast(Dict[str, Any], {
            'type': 'status_request',
            'who': devicetype.get(who),
        })
        data['legrand_id'], data['unit'], data['mode'], data['media'] = parse_legrand_id(str(where))

    elif bool(dimension_req_re.match(packet)):

        who, where, dimension = dimension_req_re.match(packet).group(1, 2, 3)
        data = cast(Dict[str, Any], {
            'type': 'dimension_request',
            'who': devicetype.get(who),
        })
        data['legrand_id'], data['unit'], data['mode'], data['media'] = parse_legrand_id(str(where))

        data['dimension'], data['val'] = parse_dimension(dimension)

    elif bool(dimension_set_re.match(packet)):

        who, where = dimension_set_re.match(packet).group(1, 2)
        data = cast(Dict[str, Any], {
            'type': 'dimension_set',
            'who': devicetype.get(who),
        })
        data['legrand_id'], data['unit'], data['mode'], data['media'] = parse_legrand_id(str(where))

    return data


def parse_legrand_id(where: str):
    """Extract legrand id from where token."""
    result = where_decode_re.match(where)
    match1, match2, match3 = result.group(1, 2, 3)

    if match1 is not None and len(match1) > 1:
        legrandid, unit = get_id_unit(match1)
        media = communication_media.get(match2)
        mode = communication_mode.get('')
    elif match2 is not None and len(match2) > 1:
        legrandid, unit = get_id_unit(match2)
        media = communication_media.get(match3)
        if match1 is not None:
            mode = communication_mode.get(match1)
        else:
            mode = communication_mode.get('')

    return (legrandid, unit, mode, media)


def parse_dimension(dimension: str):
    """Extract dimension and vals from dimension token."""
    decoded_dim, newval, new_dimension = dimension_decode_re.match(dimension).group(1, 2, 3)

    val = list()
    if newval:
        val.append(newval)

        while new_dimension:
            newval, new_dimension = val_decode_re.match(new_dimension).group(1, 2)

            if newval:
                val.append(newval)

    return decoded_dim, val


def get_id_unit(idstr: str):
    """Extract the ID part in the ID string."""
    tmpid = hex(int(idstr))

    if len(tmpid) == 7:
        unitsize = 2
    else:
        unitsize = 1

    unit = tmpid[-unitsize:]
    legrand_id = str(int(tmpid[0:-unitsize], 0))

    return (legrand_id, unit)


def encode_packet(packet_fields: dict) -> str:
    """Call the encoding method according packet type."""
    if packet_fields.get('type') == 'bus_command':
        return encode_bus_command(packet_fields)
    elif packet_fields.get('type') == 'set_dimension':
        return encode_set_dimension(packet_fields)
    else:
        return ''


def encode_bus_command(packet_fields: dict) -> str:
    """Encode the input fields into an IOBL bus_command packet."""
    where = encode_where(packet_fields.get('legrand_id'), packet_fields.get('unit'),
                         packet_fields.get('mode'), packet_fields.get('media'))

    device_type_name = {v: k for k, v in devicetype.items()}

    if packet_fields.get('who') == 'light':
        light_command_name = {v: k for k, v in light_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + light_command_name.get(packet_fields.get('what')) + '*' + where + '##'
    elif packet_fields.get('who') == 'automation':
        automation_command_name = {v: k for k, v in automation_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + automation_command_name.get(packet_fields.get('what')) + '*' + where + '##'
    elif packet_fields.get('who') == 'thermoregulation':
        thermoregulation_command_name = {v: k for k, v in thermoregulation_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + thermoregulation_command_name.get(packet_fields.get('what')) + '*' + where + '##'
    elif packet_fields.get('who') == 'doorentry':
        door_entry_command_name = {v: k for k, v in door_entry_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + door_entry_command_name.get(packet_fields.get('what')) + '*' + where + '##'
    elif packet_fields.get('who') == 'scenario':
        scenario_command_name = {v: k for k, v in scenario_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + scenario_command_name.get(packet_fields.get('what')) + '*' + where + '##'
    elif packet_fields.get('who') == 'configuration':
        configuration_command_name = {v: k for k, v in configuration_command.items()}
        encoded_packet = '*' + device_type_name.get(packet_fields.get('who')) + '*' + configuration_command_name.get(packet_fields.get('what')) + '*' + where + '##'

    return encoded_packet


def encode_set_dimension(packet_fields: dict) -> str:
    """Encode the input fields into an IOBL set_dimension/dimension_request packet."""
    where = encode_where(packet_fields.get('legrand_id'), packet_fields.get('unit'),
                         packet_fields.get('mode'), packet_fields.get('media'))
    pkt_values = ''
    for value in packet_fields.get('values'):
        pkt_values = pkt_values + '*' + value

    device_type_name = {v: k for k, v in devicetype.items()}

    if packet_fields.get('who') == 'light':
        light_dimension_name = {v: k for k, v in light_dimension.items()}
        encoded_packet = '*#' + device_type_name.get(packet_fields.get('who')) + '*' + where + '*' + light_dimension_name.get(packet_fields.get('dimension')) + pkt_values + '##'
    elif packet_fields.get('who') == 'configuration':
        configuration_dimension_name = {v: k for k, v in configuration_dimension.items()}
        encoded_packet = '*#' + device_type_name.get(packet_fields.get('who')) + '*' + where + '*' + configuration_dimension_name.get(packet_fields.get('dimension')) + pkt_values + '##'
    return encoded_packet


def encode_where(legrandid: str, unit: str, com_mode: str, com_media: str) -> str:
    """Encode the where clause of IOBL packet."""
    where = encode_id_unit(legrandid, unit)

    communication_media_name = {v: k for k, v in communication_media.items()}
    communication_mode_name = {v: k for k, v in communication_mode.items()}

    if com_mode == 'unicast' or com_mode == 'multicast':
        if com_media == 'plc':
            where = str(where)
        else:
            where = str(where) + '#' + communication_media_name.get(com_media)

    elif com_mode == 'broadcast':
        # When in broadcast mode, the legrand_id provided shall be the source address
        if com_media == 'plc':
            where = communication_mode_name.get('broadcast') + '#' + str(where)
        else:
            where = communication_mode_name.get('broadcast') + '#' + str(where) + '#' + communication_media_name.get(com_media)

    else:
        where = '#' + str(where)

    return where


def encode_id_unit(legrandid: str, unit: str) -> str:
    """Encode the input legrand_id and unit."""
    legrandid = hex(int(legrandid))

    return int(legrandid + unit, 0)
