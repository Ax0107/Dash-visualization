import socket
import logging


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


"""_________________________________LOG_SETTINGS__________________________________"""

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = "%(log_color)s %(asctime)s %(name)s-%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
LOG_NAME_FORMAT = "%Y-%m-%d.log"
Handler = logging.StreamHandler()


# loading +=1
APPID = 0

UPDATEINTERVAL = 1000  # in ms
AVOID = ['Time', 'TrackNumber', 'PacketNumber']
AVOID = set(AVOID)

REDISHOST = 'localhost'
REDISPORT = 9098
REDISMAXPULL = 450  # max number of strings to pull from values list in one iteration

TIMEZONE = 'Europe/Moscow'

""" List of timezones:

import pytz 
pytz.all_timezones

"""

TCP = WEBSOCKET = HOST = get_ip()

PORT = 8000
TCPPORT = 5678
WEBSOCKETPORT = 5679

"""____________________________________GUNICORN____________________________________"""

GUNICORNHOST = HOST
GUNICORNPORT = '8000'  # Don't forget to add virtual proxy in Apache/Nginx
GUNICORNPID = '/home/sysadmin/gunicorn.pid'

"""Redis config is in config/redis. cfg"""

"""Default values for graph settings"""


defaults = {'dash': {'figure1': dict(trace0={'marker': {'color': {'a': 0.26, 'g': 171, 'b': 251, 'r': 227}, 'size': 15},
                                         'line': {'width': 5, 'color': {'a': 0.54, 'g': 171, 'r': 237, 'b': 251}},
                                         'type': 'scattergl', 'name': 'X', 'mode': 'lines+markers',
                                         'visible': 'legendonly', 'fill': 'none'},
                                 traces=['X'],
                                 settings=dict(config={'displayModeBar': False},
                                               style={"display": "block", "margin-left": "auto", "margin-right": "auto",
                                                      "width": "90vw", "height": "90vh"}),
                                graph_type='Trajectory'
                                 )}}



