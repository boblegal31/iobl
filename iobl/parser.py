"""Parsers."""

import re
from collections import defaultdict
from enum import Enum
from typing import Any, Callable, Dict, Generator, cast

UNKNOWN = 'unknown'

DELIM = '*'
SPECIAL_REQUEST = '^\*#\d{2,4}\*\*\d{1,2}##$'
ACK = '^\*#\*(1)##$'  #  *#*1##
NACK = '^\*#\*(0)##$' #  *#*0##
ACK_NACK_RE = '|'.join ([ACK, NACK])
BUS_COMMAND = '^\*(\d+)\*(\d+#?\d*#?\d*#?)\*(\d*#*\d+#*\d*)##$' #  *WHO*WHAT*WHERE##  *1*1*0#13236017##
STATUS_REQUEST = '\*#(\d+)\*(\d*#*\d+#*\d*)##$'     #  *#WHO*WHERE
DIMENSION_REQUEST = '^\*#(\d+)\*(\d*#*\d+#*\d*)\*([\d#]+)\**([\d\*]*)##$' #  *#WHO*WHERE*DIMENSION(*VAL1*VALn)##
DIMENSION_SET = '^\*(\d+)\*(\d*)#*([\d#]*)\*(\d*#*\d+#*\d*)##$' #  *#WHO*WHERE*#DIMENSION*VAL1*VALn##

WHERE_DEFINITION = '(\d+)?#*(\d+)?#*(\d*)$'
WHAT_DEFINITION = '(\d+)#?(\d*)#?(\d*)#?'

bus_command_re = re.compile(BUS_COMMAND)
ack_nack_re = re.compile(ACK_NACK_RE)
special_request_re = re.compile(SPECIAL_REQUEST)
status_request_re = re.compile(STATUS_REQUEST)
dimension_request_re = re.compile(DIMENSION_REQUEST)
dimension_set_re = re.compile(DIMENSION_SET)

where_decode_re = re.compile(WHERE_DEFINITION)
what_decode_re = re.compile(WHAT_DEFINITION)

BUS_COMMAND_TEMPLATE = '*{who}*{what}*{where}'


class iobl_packet(Enum):
    """Packet source identification."""

devicetype = {
    '1':'light',
    '2':'automation',
    '4':'thermoregulation',
    '8':'doorentry',
    '25':'scenario',
    '13':'management',
    '14':'special',
    '1000':'configuration',
    }

light_command = {
    #"""switch command identification."""
    '1':'on',
    '0':'off',
    '38':'dim_stop',
    }

automation_command = {
    #"""shutter command identification."""
    '0':'move_stop',
    '1':'move_up',
    '2':'move_down',
    }

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

scenario_command = {
    #"""scenario command identification."""
    '11': 'action',
    '16': "stop_action",
    '17': "action_for_time",
    '18': "action_in_time",
    '19': "info_scene_off"
    }

door_entry_command = {
    #"""door entry command identification."""
    '1': 'concierge_call',
    '19': 'locker_control'
    }

configuration_command = {
    #"""configuration command identification."""
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

communication_mode = {
    '0':'broadcast',
    '1':'multicast',
    '2':'unicast_direct',
    '3':'unicast',
    '':'unicast',
    }

communication_media = {
    '0':'plc',
    '1':'rf',
    '2':'ir',
    '':'plc',
    }


def valid_packet(packet: str) -> bool:
    """Verify if packet is valid.

    """
    return bool(bus_command_re.match(packet)) | bool(ack_nack_re.match(packet)) | bool(status_request_re.match(packet)) | bool(dimension_request_re.match(packet)) | bool(dimension_set_re.match(packet))


def decode_packet(packet: str) -> dict:
    """Break packet down into primitives, and do basic interpretation."""

    if bool(bus_command_re.match(packet)):
        who, what, where = bus_command_re.match(packet).group(1,2,3)
    
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
        data['type'] = 'command'
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

    return data


def parse_legrand_id(where: str):
    """Extract legrand id from where token."""
    result = where_decode_re.match(where)
    match1, match2, match3 = result.group(1,2,3)
    
    if not match1 is None and len(match1) > 1:
        legrandid, unit = get_id_unit(match1)
        media = communication_media.get(match2)
        mode = communication_mode.get('')
    elif not match2 is None and len(match2) > 1:
        legrandid, unit = get_id_unit(match2)
        media = communication_media.get(match3)
        if not match1 is None:
            mode = communication_mode.get(match1)
        else:
            mode = communication_mode.get('')

    return (legrandid, unit, mode, media)

def get_id_unit(idstr: str):
    """Extract the ID part in the ID string"""
    tmpid = hex(int(idstr))
    
    if len(tmpid) == 7:
        UnitSize = 2
    else:
        UnitSize = 1
    
    Unit = tmpid[-UnitSize:]
    theId = str(int(tmpid[0:-UnitSize], 0))
    
    return (theId, Unit)

def encode_packet(packet: dict) -> str:
    if packet.get('type') == 'command':
        where = encode_id_unit(packet.get('legrand_id'), packet.get('unit'))
    
        communication_media_name = {v: k for k, v in communication_media.items()}
        device_type_name = {v: k for k, v in devicetype.items()}
    
        if packet.get('mode') == 'unicast' or packet.get('mode') == 'multicast':
            if packet.get('media') == 'plc':
                where = '#' + str(where)
            else:
                where = '#' + str(where) + '#' + communication_media_name.get(packet.get('media'))
    
        elif packet.get('mode') == 'broadcast':
            if packet.get('media') == 'plc':
                where = communication_mode.get('broadcast') + '#' + where
            else:
                where = communication_mode.get('broadcast') + '#' + where + '#' + communication_media_name.get(packet.get('media'))
    
        if packet.get('who') == 'light':
            light_command_name = {v: k for k, v in light_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + light_command_name.get(packet.get('what')) + '*'+ where + '##'
        elif packet.get('who') == 'automation':
            automation_command_name = {v: k for k, v in automation_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + automation_command_name.get(packet.get('what')) + '*'+ where + '##'
        elif packet.get('who') == 'thermoregulation':
            thermoregulation_command_name = {v: k for k, v in thermoregulation_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + thermoregulation_command_name.get(packet.get('what')) + '*'+ where + '##'
        elif packet.get('who') == 'doorentry':
            door_entry_command_name = {v: k for k, v in door_entry_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + door_entry_command_name.get(packet.get('what')) + '*'+ where + '##'
        elif packet.get('who') == 'scenario':
            scenario_command_name = {v: k for k, v in scenario_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + scenario_command_name.get(packet.get('what')) + '*'+ where + '##'
        elif packet.get('who') == 'configuration':
            configuration_command_name = {v: k for k, v in configuration_command.items()}
            encoded_packet = '*' + device_type_name.get(packet.get('who')) + '*' + configuration_command_name.get(packet.get('what')) + '*'+ where + '##'
    
        return (encoded_packet)
    else:
        return ''


def encode_id_unit (legrandid: str, unit: str) -> str:
    theId = hex(int(legrandid))
    
    return (int(theId + unit, 0))


