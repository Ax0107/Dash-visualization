# -*- coding: utf-8 -*-
import asyncio
import json
import logging
from colorlog import ColoredFormatter
import re
import time
import traceback
from datetime import datetime

import pandas as pd
import redis
from bs4 import BeautifulSoup

from config.const import REDISHOST, REDISPORT, REDISMAXPULL, TIMEZONE,APPID


LOG_LEVEL = logging.DEBUG
logger = logging.getLogger('redis hook')
LOGFORMAT = "  %(log_color)s- %(name)s-%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)
logger.addHandler(stream)

r = redis.Redis(
    host=REDISHOST,
    port=REDISPORT)


def getbuiltin_method(method, val):
    "Hacky wrapper, needs rewriting"
    if method == 'list':
        return re.findall("\w+", val)
    elif method=='bytes':
        return int(val)
    else:
        try:
            return getattr(__builtins__, method)(val)
        except:
            return __builtins__[method](val)


def remove_values_from_list(the_list, val):
    return [value for value in the_list if value != val]


async def arange(start, count, step):
    for i in range(start, count, step):
        yield (i)


def prepare(redis_resp, utc, step):
    # converts values to float and UTC time to local time
    if redis_resp:
        df = pd.DataFrame(json.loads(i) for i in redis_resp)
        df = df.drop_duplicates(subset='Time', keep='last')
        for column in df.columns:
            try:
                df[column] = pd.to_numeric(df[column])
            except ValueError as e:
                logger.warning(traceback.format_exc())
                logger.warning('Could not cast to numeric type:{column}'.format(column=column))
        df.index = pd.to_datetime(df['Time'], utc=utc, unit='s')
        df.index = df.index.tz_convert(TIMEZONE)

        if type(step) is str:
            logger.debug('resampling with {} step'.format(step))
            df = df.resample(step).median()
        # df.index = df.index.astype('str')  # plotly converts time to UTC otherwise
        return df
    else:
        logger.debug('Cache empty')
        return None


class Storage(object):

    def __init__(self, id='0:Trajectory:Rlist', step='500ms', preload=True):
        self.step = step
        self.id = id
        self.redis_wrapper = RWrapper()
        if preload:
            to_df, self.end = self.redis_wrapper.pull(self.id, 0, 0)
            if to_df is not None and type(to_df) is pd.DataFrame and not to_df.empty:
                self.df = prepare(to_df, False, step)

    def get_size(self):
        return self.redis_wrapper.get_size(self.id)

    def call(self, step=0, start=0, end=0, utc=True, all=False):
        to_df, end = self.redis_wrapper.pull(self.id, start, end)
        df = prepare(to_df, utc, step)
        if all:
            size = self.redis_wrapper.get_size(self.id)
            while end < size:
                tmp, end = self.redis_wrapper.pull(self.id, end, 0)
                tmp = prepare(tmp, utc, step)
                df = df.append(tmp)
        return df, end


class RWrapper(object):
    """Interface for handling Redis-stored data
    Redis is expected to store
    keys in id:key:type format

    Ids may be:
    user uuid for storing user-related data
    S_number for storing stream data
    Number
    Reserved ids :
    1-1000 for APPID's

    Keys is expected to be nested, i.e. dash.figure1.trace.marker.color
    Keys should not overlap, for example there shouldn't be a key dash if there is a key dash.figure1.settings

    Supported types are
    int,float (bool values are converted to int)
    str (preferrably not longer than 64 bytes)
    list - for short lists, stored as string
    Rlist - redis lists, for storing large amounts of data

    Access to nested keys provided via Getter class.
    Usage:
    RWrapper(id).nested.named.key.func()
    Callable methods of Getter

    val() returns value at key. Interchangeable with directly calling an instance
    If you provide only partial key name, returns nested dict. RWrapper(id).dash.figure1.trace1.marker.size.val() would return int,
    RWrapper(id).dash.figure1.trace1() would return {marker{size:..}...}

    set() - puts key into Redis. Same logic as val()

    rem() removes key. Same logic as val()

    child() - getter for next element. Example:trace=trace1; RWrapper(id).dash.figure1.child(trace).val()

    get_children() - returns set of child elements

    """

    def __init__(self, uuid=None):
        #logger.info('Started redis')
        self.uuid = uuid
        self.r = r

    @staticmethod
    def loading(val=1):
        key_loading = '{}:counterLoading:int'.format(APPID)
        if val > 0:
            RWrapper(APPID).counterLoading.set(int(RWrapper(APPID).counterLoading() or 0) + val)
            RWrapper(APPID).loaded.set(0)
        else:
            RWrapper(APPID).counterLoading.set(0)
        return RWrapper(APPID).counterLoading()

    async def push_xml(self, xml):
        """Pushes XML Into Redis List, assuming the time counted from stream start
            :param xml: valid xml to parse
            :return: None
        """
        if xml:
            bull = BeautifulSoup(xml, features='xml')
            await asyncio.sleep(0)
            for i in bull.children:
                if i.name:
                    attrs = i.attrs
                    id = 'S_' +attrs.pop('TrackNumber', '0')
                    if int(i.attrs['PacketNumber']) == 0 or self.r.get(i.name + '.starttime:int') is None:
                        self.r.set(id + ':' + i.name + '.starttime:int', int(time.time() - float(i.attrs['Time'])))
                    try:
                        attrs['Time'] = float(attrs['Time']) + float(self.r.get(id + ':' + i.name + '.starttime:int'))
                    except Exception as e:
                        logger.error(traceback.format_exc())
                        logger.error('cannot get start time!', e)
                        pass
                    self.r.rpush(id + ':' + i.name + ':Rlist', json.dumps(attrs))
                    await asyncio.sleep(0)
                    size = self.get_size(i.name)
                    if size > 35000:
                        self.r.ltrim(i.name, -10000, -1)  # remove in prod

    def pull(self, id, start=0, end=0):
        """
        :param id: Redis key
        :param start:  From
        :param end: To
        :return: list[start:end] of byte-strings
        """
        if end == 0:
            end = self.r.llen(id)
        if not start:
            start = 0
        if end > start + REDISMAXPULL:
            end = start + REDISMAXPULL
        li = self.r.lrange(id, start, end)
        return li, end

    def get_size(self, id):
        """

        :param id: Redis key
        :return: List size(element-vise)
        """
        return self.r.llen(id)

    def get_item(self, id, index):
        """

        :param id: Redis key of a list
        :param index:
        :return: byte-string at list[index]
        """
        return self.r.lindex(id, index)

    def get_item_str(self,id, index):
        resp = self.r.lindex(id, index)
        if resp:
            data = json.loads(self.r.lindex(id, index))
            if 'Time' in data.keys():
                data['Time'] = datetime.fromtimestamp(data['Time']).strftime('%H:%M:%S:%f')
                return json.dumps(data)

    def get_redis(self, keys):
        """

        :param keys: list of redis keys
        :return: dict {key:val ...}
        """
        dict_data = {}  # Here will lay default settings
        for key in keys:
            key = key.decode("utf-8")
            try:
                _, param, type_value = key.split(':')
                if type_value == 'NoneType':
                    logger.info('Key {} is of type NoneType. Ignoring'.format(key))
                    continue
            except ValueError:
                raise ValueError("Trying to get more than one key."
                                 "Implemented only for uuid:key:type named keys."
                                 "Passed key is {}".format(key))
            try:
                dict_data = self.put_key(param,
                                         getbuiltin_method(type_value, self.r.get(key).decode("utf-8")), dict_data)

            except redis.exceptions.ResponseError as e:
                if 'WRONGTYPE' in repr(e):
                    raise ValueError("Tried to get more than one key, "
                                     "one of which is a {}".format(type_value))

        return dict_data

    def get_one_key(self, key):
        """
        :param key: Redis key
        :return: value at key
        """
        key = key.decode("utf-8")
        _, _, type_value = key.split(':')
        try:
            return getbuiltin_method(type_value, self.r.get(key).decode("utf-8"))
        except redis.exceptions.ResponseError:
            redis_type = self.r.type(key).decode()
            logger.warning('Ambiguous. Trying to get value of a Redis {}'.format(redis_type))
            if redis_type == 'list':
                logger.debug('For getting stream data use Storage(id).call(*args) instead')
                return self.pull(key)[0]
            else:
                raise AttributeError('{}.val() not implemented'.format(redis_type))

    def put_key(self, param, value, dict_little={}):
        """
        Recursively fills dict with redis values
        :param param: str to search in Redis
        :param value: redis key val
        :param dict_little: intermediate result
        :return: dict
        """
        params = param.split('.', 1)
        if len(params) == 1:
            dict_little[params[0]] = value
        else:
            dict_little[params[0]] = self.put_key(params[1], value, dict_little.get(params[0], {}))
        return dict_little

    def search(self, search_string):
        """search for Redis keys
        :param search_string: строка поиска
        :return: список ключей Redis
        """
        return self.r.keys(search_string)

    def delete(self, keys):
        for key in keys:
            self.r.delete(key)

    def __getattr__(self, name):
        setattr(self, name, Getter(self.uuid, name))
        return getattr(self, name)


class Getter(RWrapper):
    """Template class for redis access
    """

    def __init__(self, uuid=0, name=''):
        super().__init__(uuid)
        self.uuid = uuid
        self.__name__ = name

    def __comp__(self, d):
        *_, name = self.__name__.split('.')
        for key in d.keys():
            if key == name:
                return d[key]
            elif isinstance(d[key], dict):
                return self.__comp__(d[key])
        return {}

    def child(self, name):
        return self.__getattr__(name)

    def get_children(self, search_str=''):
        """
        :param search_str:
        :return: list of child objects with names containing search_str
        """
        return set([getattr(self, i.decode().partition(self.uuid + ':' + self.__name__)[2].split('.')[1].split(':')[0]) \
                    for i in self.keys_list() if search_str in i.decode()])

    def val(self):
        """
        value of a redis Key
        :return: val or dict {key:val}
        """

        keys = self.keys_list()
        if len(keys) > 1:
            # TODO default search = default.name
            default_dict = self.get_redis(self.r.keys(':'.join(('defaults', self.__name__))))
            # Overwrite defaults with client settings, NOT merges recursively
            result = {**default_dict, **self.get_redis(keys)}
            return self.__comp__(result)
        elif len(keys) == 1:
            return self.get_one_key(keys[0])
        else:
            # TODO pass default value here
            if self.uuid != 'defaults':
                default = getattr(RWrapper('defaults'), self.__name__).val()
                if default:
                    return default
            else:
                logger.info(AttributeError('No such keys in Redis - {}:{}. Returning empty string'.format(self.uuid, self.__name__)))
                return ''

    def keys_list(self):
        """
        :return: list of keys derived from this oblect class
        """
        search_string = ':'.join((self.uuid, self.__name__)) if self.uuid else self.__name__
        return self.r.keys(search_string + ':*') or self.r.keys(search_string + '*')

    def set(self, val):
        if isinstance(val, dict):
            for key in val.keys():
                self.__getattr__(key).set(val[key])
        else:
            try:
                self.r.set(':'.join((self.uuid, self.__name__)) + ':' + type(val).__name__, val)
            except redis.exceptions.DataError:
                logger.debug('{} value is a {}, putting to redis via its __str__() method'.format(
                    ':'.join((self.uuid, self.__name__)) + ':' + type(val).__name__,
                    type(val).__name__))
                self.r.set(':'.join((self.uuid, self.__name__)) + ':' + type(val).__name__, val.__str__())

    def __getattr__(self, name):
        setattr(self, name, Getter(self.uuid, '.'.join((self.__name__, name))))
        return getattr(self, name)

    def __call__(self):
        return self.val()

    def __str__(self):
        return self.__name__

    def rem(self):
        keys = self.keys_list()
        logger.debug('Deleting Redis keys {}'.format(keys))
        self.delete(keys)
