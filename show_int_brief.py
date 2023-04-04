#!/usr/bin/python3
#
# $Id: show_int_brief.py,v 0.0.3 2023/04/04 14:12:19 vp@dtel-ix.net Exp $
# - Added check if DDM data available
#
# $Id: show_int_brief.py,v 0.0.2 2023/03/28 18:19:21 vp@dtel-ix.net Exp $
# - Added matching by interface name
#
# $Id: show_int_brief.py,v 0.0.1 2023/03/18 14:52:43 vp@dtel-ix.net Exp $
# - Initial public release
#
#{{{
#
# Usage:
#
# 1. This script depends on Arista EOS JSON RPC API. It is intended to be run on your
#    Arista EOS device by authorized users as a built-in command, so you need to enable
#    API via UNIX socket first:
#
#    management api http-commands
#       protocol unix-socket
#       no shutdown
#
# 2. Place the script in a common accessible place (say /usr/local/bin), set appropriate
#    permissions on it (chmod a+x /usr/local/bin/show_int_brief.py) and configure an
#    alias to call it from CLI:
#
#    alias "sh(o|ow)? int(e|er|erf|erfa|erfac|erface|erfaces)? br(i|ie|ief)?"
#       10 bash /usr/local/bin/show_int_brief.py
#
# 3. Relogin.
#
# 4. Now you can call it from CLI like that: show interfaces brief [ pattern ]
#
#    Pattern is optional and is matched as regular expression to description and interface
#    name fields.
#
#    Logical interfaces are skipped in the output.
#
#    As a result you'll receive brief information about interface and phy's (single row
#    per interface, so the data is grepable) containing:
#
#    - brief interface name;
#    - single-letter interface and protocol status;
#    - interface description (cut to 30 symbols max);
#    - common type description of transceiver installed into port;
#    - interface TX/RX load in %;
#    - TX/RX signal power in dBm by lanes
#
#    e. g.:
#
# switch# sh int br flow
# Interface State/ Description                  Type              TX/RX                             TX/RX signal power, dBm
#           Proto                                               load, %       Lane 1       Lane 2       Lane 3       Lane 4
#
# Et3/72    C/U    sflow:eno33np0               10GBASE-LR          0/0     0.8/-1.7                             
# Et4/72    C/U    sflow:eno34np1               10GBASE-LR          0/0     0.8/-0.8                             
# Po10      C/U    sflow:bond0                  LAG-20G             0/0
#
#}}}
#
#{{{
import jsonrpclib
import logging
import json
import sys
import re
#}}}
#
# Setting common variables (say constants)
#
DEBUG = False
REGEX = '.*'
#
# Write debug messages to log and/or console
#
#{{{
def log(msg):
    # logging.basicConfig(filename = 'PortAuto.log', level = logging.DEBUG)
    logging.basicConfig(level = logging.DEBUG)
    logging.debug(msg)
    if DEBUG == True: print(msg)
#}}}
#
# Run specified command(-s), return result
#
#{{{
def run_cmds(s, commands, format = 'json'):
    try:
        result = s.runCmds(1, commands, format)
    except jsonrpclib.ProtocolError:
        errorResponse = jsonrpclib.loads(jsonrpclib.history.response)
        log("Failed to run command: %s. %s" % (commands, errorResponse['error']['data'][0]['errors'][-1]))
        sys.exit(1)
    return result
#}}}
#
# Get transceiver TX/RX signal power by lanes, format and
# return a single string, containing the data
#
#{{{
def get_power(if_name):
    out = run_cmds(s, [ str.format('show interfaces %s transceiver dom' % if_name) ])
    string = ''
    if 'parameters' not in out[0]['interfaces'][if_name]: return '        -/-'
    out = out[0]['interfaces'][if_name]['parameters']
    for lane in out['rxPower']['channels']:
        if string != '': string = string + '  '
        tx = str.format('%.1f' % out['txPower']['channels'][lane])
        rx = str.format('%.1f' % out['rxPower']['channels'][lane])
        string = string + str.format("%11s" % (tx + '/' + rx))
    return string
#}}}
#
# Get interface TX/RX load in %, format and return a single string,
# containing the data
#
#{{{
def get_bps(if_name, bandwidth, status):
    out = run_cmds(s, [ str.format('show interfaces %s' % if_name) ])
    proto = 'D'
    string = '-/-'
    if out[0]['interfaces'][if_name]['lineProtocolStatus'] == 'up': proto = 'U'
    out = out[0]['interfaces'][if_name]['interfaceStatistics']
    if status == 'connected':
        tx = int(100 * out['outBitsRate'] / bandwidth)
        rx = int(100 * out['inBitsRate'] / bandwidth)
        string = str.format("%s/%s" % (tx, rx))
    return(string, proto)
#}}}
#
if len(sys.argv) > 1: REGEX = sys.argv[1]
s = jsonrpclib.Server('unix:/var/run/command-api.sock')
out = run_cmds(s, ['show interfaces status'])
print("""Interface State/ Description                  Type              TX/RX                             TX/RX signal power, dBm
          Proto                                               load, %       Lane 1       Lane 2       Lane 3       Lane 4\n""")
for if_name in (out[0]['interfaceStatuses']):
    i = out[0]['interfaceStatuses'][if_name]
    if i['interfaceType'] == 'dot1q-encapsulation': continue
    if not re.search(REGEX, i['description'], flags = re.I) and not re.search(REGEX, if_name, flags = re.I): continue
    short_name = re.sub('(hernet|rt-Channel|agement)', '', if_name)
    status, power, bandwidth, proto = 'U', '', '-/-', 'D'
    description = re.sub('^(.{24})(.{3,})$', '\\1...', i['description'])
    if i['linkStatus'] == 'disabled':
        status = 'D'
    elif i['linkStatus'] == 'connected':
        status = 'C'
    elif i['linkStatus'] == 'errdisabled':
        status = 'E'
    elif i['linkStatus'] == 'notconnect':
        status = '-'
    if re.match('Po', short_name): i['interfaceType'] = str.format("LAG-%iG" % int(i['bandwidth'] / 1000000000));
    if re.match('(Not Present|Unknown)', i['interfaceType']): i['interfaceType'] = 'N/A'
    if re.match('Et', if_name) and i['interfaceType'] != 'N/A': power = get_power(if_name)
    if re.match('(Et|Po)', if_name) and i['interfaceType'] != 'N/A':
        bandwidth, proto = get_bps(if_name, i['bandwidth'], i['linkStatus'])
    sys.stdout.write("%-9s %-6s %-28s %-15s %7s  %-40s\n" % (
		short_name,
		status + '/' + proto,
		description,
		i['interfaceType'],
		bandwidth,
		power
    ))
