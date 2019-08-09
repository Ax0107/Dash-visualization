from config.const import APPID
from flask import Flask, request, redirect, make_response
import re
import pandas as pd
from itertools import count, filterfalse
import json
from redis_handler import RWrapper, Storage

from logger import logger
logger = logger('api')

server = Flask(__name__)


def to_json(data):
    return json.dumps(data)


def resp(code, data):
    return make_response(to_json(data), code)


@server.route('/dash/api/delete')
def figure_deletion():
    if request.args:
        uuid = request.args.get('uuid', 'default').lower()
        figure_id = request.args.get('figure_id')
        if figure_id is not None:
            figures = RWrapper(uuid).dash.get_children('figure')
            names = [i.__name__ for i in figures]
            if 'dash.figure{}'.format(figure_id) in names:
                logger.info('Figure with id {} exist. Deleting.'.format(figure_id))
                RWrapper(uuid).dash.child("figure{}".format(figure_id)).rem()
                mess = 'Dash.figure{} was deleted.'.format(figure_id)
                logger.info(mess)
            else:
                mess = "{}'s figure with id {} does not exist.".format(uuid, figure_id)
                logger.info(mess)
                return resp(400, mess)
        return redirect("/loading/")
    else:
        if RWrapper(APPID).loaded():
            return redirect("/graph/")
        else:
            return redirect("/loading/")


@server.route('/dash/api')
def figure_work():
    if request.args:
        logger.debug('Params: ' + str(dict(request.args)))
        uuid = request.args.get('uuid', 'default').lower()
        figure_id = request.args.get('figure_id')
        if figure_id is not None:
            return parse_params(uuid, figure_id, dict(request.args))
        else:
            logger.info('Figure id is not selected. Giving id.')
            figures = RWrapper(uuid).dash.get_children('figure')
            if len(figures):
                # Список из figure, чьё имя заканчивается на цифру?
                fig_count = list(map(lambda i: int(re.search(r'\d+$', i).group()) if re.search(r'\d+$', i) else 0,
                                     figures.pop().__name__))
                # ?
                i = next(filterfalse(set(fig_count).__contains__, count(1)))

                names = [i.__name__ for i in figures]
                logger.info('Figure id {} is already exist. Giving another id.'.format(i))
                while 'dash.figure{}'.format(i) in names:
                    i += 1
            else:
                i = 1
            logger.info('New figure id is {}'.format(i))
            # if RWrapper(uuid).dash.get_children('figure')
            return parse_params(uuid, str(i), dict(request.args))
    else:
        # if RWrapper(APPID).loaded():
        #    return redirect("/graph/")
        #else:
        return redirect("/loading/")


def parse_params(uuid, figure_id, params):
    def validate(figure_id, params):
        if figure_id:
            try:
                int(figure_id)
            except ValueError:
                mess = 'Figure_id is not integer.'
                logger.error(mess)
                return 415, mess
        else:
            mess = 'Does not have figure_id.'
            logger.error(mess)
            return 400, mess
        graph_type = params.get('graph_type')
        stream = params.get('stream')
        traces = params.get('traces')
        # print(graph_type is None, stream is None, traces is None)
        if graph_type is None or stream is None or traces is None:
            mess = 'Some variable is None!'
            logger.error(mess)
            return 400, mess
        if graph_type.lower() not in ['trajectory', 'bar', 'scatter']:
            mess = 'Graph type {} does not exist.'.format(graph_type)
            logger.error(mess)
            return 400, mess
        if RWrapper(uuid).search('S_0:'+stream+':Rlist') == []:
            mess = 'Stream {} does not exist.'.format(stream)
            logger.error(mess)
            return 400, mess
        else:
            frame, end = Storage(id='S_0:'+stream+':Rlist', preload=True).call(start=0, end=1)
            columns = list(pd.DataFrame(frame).columns)
            traces = traces.split(',')
            params['traces'] = params['traces'].split(',')
            if isinstance(traces, list):
                for trace in traces:
                    if trace not in columns:
                        mess = 'Stream {} does not have name {}.'.format(stream, trace)
                        logger.error(mess)
                        return 400, mess
            else:
                if traces not in columns:
                    mess = 'Stream {} does not have name {}.'.format(stream, trace)
                    logger.error(mess)
                    return 400, mess
        return 200, 'OK'

    code, message = validate(figure_id, params)
    if code == 200:
        figure = RWrapper(uuid).dash.child("figure{}".format(figure_id))

        logger.info('Params are valid. Setting up: graph_type, stream, traces for figure {}'.format(figure))
        try:
            params.pop('figure_id')
        except KeyError:
            pass
        valid_params = [params.pop('graph_type')] + [params.pop('stream')] + \
                       [params.pop('traces')]
        valid_params = {'graph_type': valid_params[0], 'stream': valid_params[1], 'traces': valid_params[2]}
        for param in valid_params:
            # print("{} ({}): {} ({})".format(param, type(param), valid_params[param], type(valid_params[param])))
            if param == 'traces':
                # Удаление всех прошлых ключей trace
                try:
                    figure_children = figure.val()
                    for i in figure_children.keys():
                        if 'trace' in i:
                            figure.child(i).rem()
                except AttributeError:
                    # значит, таких ключей нет
                    pass
                for i in range(0, len(valid_params[param])):
                    figure.child('trace{}'.format(i)).name.set(valid_params[param][i])
            if param == 'stream':
                valid_params['stream'] = 'S_0:' + valid_params['stream'] + ':Rlist'
            figure.child(param).set(valid_params[param])
        logger.info('OK.')
        if params != {}:
            logger.warning('There are untracked variables: '+str(params))
        # RWrapper(APPID).dash.reload.set('True')
        # RWrapper(APPID).loading()
        return redirect("/loading/")
    else:
        return resp(code, message)



if __name__ == '__main__':
    server.run()

