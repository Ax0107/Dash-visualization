import multiprocessing
from config.const import *

bind = "{}:{}".format(GUNICORNHOST, GUNICORNPORT)


workers = multiprocessing.cpu_count() * 2 + 1
""" Number of worker processes - maximum is cpu_count multiprocessing.cpu_count() * 2 + 1 
Warning: each worker takes about 100 mb of ram
"""

timeout = 50
"""Workers silent for more than this many seconds are killed and restarted."""

max_requests = 500
"""Any value greater than zero will limit the number of requests a work will process before automatically restarting. 
This is a simple method to help limit the damage of memory leaks. """


max_requests_jitter = 500
"""The maximum jitter to add to the max_requests setting.
The jitter causes the restart per worker to be randomized by randint(0, max_requests_jitter). 
This is intended to stagger worker restarts to avoid all workers restarting at the same time."""

accesslog = '/home/sysadmin/gunicorn_access.log'
errorlog = '/home/sysadmin/gunicorn_error.log'
pidfile = GUNICORNPID
