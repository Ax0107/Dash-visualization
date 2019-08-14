import socket


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
    print('Server IP address is {}'.format(IP))
    return IP


# loading +=1

UPDATEINTERVAL = 500  # in ms
AVOID = ['Time', 'TrackNumber', 'PacketNumber']
AVOID = set(AVOID)

REDISHOST = 'localhost'
REDISPORT = 9098
REDISMAXPULL = 450  # max number of strings to pull from values list in one iteration

APPID = '1000'

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

defaults = {'dash': {'figure1': dict(trace0={'marker': {'color': 'chocolate', },
                                             'line': {'width': 5, 'color': 'dodgerblue'},
                                             'name': 'Y', 'mode': 'lines+markers',
                                              'fill': 'none'},
                                     traces=['Y'],
                                     settings=dict(config={'displayModeBar': False},
                                                   style={"display": "block", "margin-left": "auto",
                                                          "margin-right": "auto",
                                                          "width": "90vw", "height": "90vh"}),
                                     graph_type='Trajectory'
                                     )}}

#RWrapper('defaults').dash.set(defaults['dash']) not integrated, do manually now


default = {'figure': {'trace0':{'marker': {'color': 'rgba(255,255,255,1)', },
                                             'line': {'width': 5, 'color': 'rgba(255,255,255,1)'},
                                             'name': 'Y', 'mode': 'lines+markers'},
                                     'settings':{'config':{'displayModeBar': False},
                                                   'style':{"display": "block", "margin-left": "auto",
                                                          "margin-right": "auto",
                                                          "width": "90vw", "height": "90vh"}},
                                     'graph_type':'Trajectory'
                                     }}