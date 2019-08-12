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


@server.route('/dash/api/optional')
def figure_optional():
    if request.args:
        uuid = request.args.get('uuid', 'default').lower()
        figure_id = request.args.get('figure_id')
        if figure_id is not None:
            return parse_params(uuid, figure_id, dict(request.args), method='optional')
        else:
            return resp(400, 'Figure id is None.')
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


def parse_params(uuid, figure_id, params, method=None):
    def validate_optional(figure_id, params):
        if figure_id:
            try:
                int(figure_id)
            except ValueError:
                mess = 'Figure_id is not integer.'
                logger.error(mess)
                return 415, mess, params
            try:
                figure = RWrapper(uuid).dash.child('figure{}'.format(figure_id))
                figure.val()
            except AttributeError:
                mess = 'Does not have figure with id {} for user {}.'.format(figure_id, uuid)
                logger.error(mess)
                return 400, mess, params
        else:
            mess = 'Does not have figure_id.'
            logger.error(mess)
            return 400, mess, params
        graph_type = params.get('graph_type')
        trace = params.get('trace_id')
        line_color = params.get('line_color')
        line_width = params.get('line_width')
        marker_color = params.get('marker_color')
        marker_size = params.get('marker_size')
        if graph_type is None:
            try:
                graph_type = figure.graph_type.val()
            except AttributeError:
                mess = 'Graph type must be string, not None'
                logger.error(mess)
                return 400, mess, params
        params['graph_type'] = graph_type
        logger.debug('Loaded graph_type from Redis - {}'.format(graph_type))
        if trace is None:
            mess = 'Trace_id must be number, not None'
            logger.error(mess)
            return 400, mess, params
        else:
            try:
                int(trace)
            except ValueError:
                mess = 'Trace is not integer.'
                logger.error(mess)
                return 415, mess, params
            try:
                figure.child('trace{}'.format(trace)).val()
            except AttributeError:
                mess = 'Trace with id {} does not exist. Make sure, you select a trace, when creating a figure.'
                logger.error(mess)
                return 400, mess, params
        if graph_type.lower() not in ['trajectory', 'bar', 'scatter']:
            mess = 'Graph type {} does not exist.'.format(graph_type)
            logger.error(mess)
            return 400, mess, params
        if graph_type.lower() == 'bar':
            if marker_color is None or marker_size is None:
                mess = 'Graph type bar needed marker color and marker size params.'
                logger.error(mess)
                return 400, mess, params
        else:
            if line_color is None or line_width is None or marker_color is None or marker_size is None:
                mess = 'Graph type {} needed more params. ' \
                       '(line_color, line_width, marker_color, marker_size)'.format(graph_type)
                logger.error(mess)
                return 400, mess, params

            # Проверка формата цвета
            def check_format(color):
                """
                Проверяет формат rgb-string
                :param color: rgb-string
                :return: true/false
                """
                if isinstance(color, str):
                    # print('C:', color, color[5:-1])
                    color_splited = color[5:-1].split(',')
                    try:
                        {'r': int(color_splited[0]), 'g': int(color_splited[1]), 'b': int(color_splited[2]),
                         'a': int(color_splited[3])}
                    except IndexError:
                        return 0
                    except ValueError:
                        return 0
                return 1
            for color in [line_color, marker_color]:
                if color is not None:
                    if not check_format(color):
                        mess = 'Color {} is not in valid format. Correct format: rbga(1,1,1,1)'.format(color)
                        logger.error(mess)
                        return 400, mess, params
        return 200, 'OK', params

    def validate_work(figure_id, params):
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
                    mess = 'Stream {} does not have name {}.'.format(stream, traces)
                    logger.error(mess)
                    return 400, mess
        return 200, 'OK'
    if method is None or method == 'work':
        code, message = validate_work(figure_id, params)
    elif method == 'optional':
        code, message, params = validate_optional(figure_id, params)
    else:
        logger.warning('Method {} do not exist.'.format(method))
        return resp(500, 'Method {} do not exist.'.format(method))
    if code == 200:
        figure = RWrapper(uuid).dash.child("figure{}".format(figure_id))
        if method is None or method == 'work':
            logger.info('Params are valid. Setting up: graph_type, stream, traces for figure {}'.format(figure))
            valid_params = {'graph_type': params.pop('graph_type'), 'stream': params.pop('stream'),
                            'traces': params.pop('traces')}
            for param in valid_params:
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
                        figure.child('trace{}'.format(i)).name_id.set(valid_params[param][i])
                if param == 'stream':
                    valid_params['stream'] = 'S_0:' + valid_params['stream'] + ':Rlist'
                figure.child(param).set(valid_params[param])
        elif method == 'optional':
            logger.info('Params are valid. Setting up: lines and markers for figure {}'.format(figure))
            trace = params.pop('trace_id')
            valid_params = {'graph_type': params.pop('graph_type'), 'marker_color': params.pop('marker_color'), 'marker_size': params.pop('marker_size')}
            if valid_params['graph_type'] != 'bar':
                valid_params.update({'line_color': params.pop('line_color'),
                                     'line_width': params.pop('line_width')})
            for param in valid_params:
                parent = param.split('_')[0]
                child = param.split('_')[1]
                figure.child('trace{}'.format(trace)).child(parent).child(child).set(valid_params[param])
            figure.graph_id.set(valid_params['graph_type'])
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

