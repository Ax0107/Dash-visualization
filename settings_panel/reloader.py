
import asyncio
import logging
import subprocess

from config.const import GUNICORNPID
from redis_handler import RWrapper

redis = RWrapper()
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger('reloader')
logger.setLevel(LOG_LEVEL)
stream = logging.StreamHandler()
#stream.setLevel(LOG_LEVEL)
logger.addHandler(stream)

def get_pid():
    try:
        with open(GUNICORNPID) as f:
            content = f.readline()
            pid = int(content)
    except (ValueError, FileNotFoundError):
        logger.debug("Failed to get gunicorn pid from {}, gunicorn won't be restarted".format(GUNICORNPID))
        pid = None
    return pid


async def listen():
    while True:
        keys = redis.search('*obsolete*')
        if keys and get_pid():
            redis.loading()
            try:
                await send_signal(get_pid(), 'HUP')
            except:
                pass
            finally:
                redis.delete(keys)
                redis.loading()
        await asyncio.sleep(2)


async def send_signal(pid, signal):
    subprocess.run('kill -{} {}'.format(signal, pid))
    await asyncio.sleep(0)
