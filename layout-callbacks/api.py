from config.const import APPID
from flask import Flask, request, redirect
import re
import pandas as pd
from ast import literal_eval
from itertools import count, filterfalse

from redis_handler import RWrapper, Storage

from logger import logger
logger = logger('api')

server = Flask(__name__)


@server.route('/dash/api')
def parse_params():
    if request.args:
        figure_id = request.args.get('figure_id', None)
        uuid = request.args.get('uuid', 'default')
        figure = RWrapper(uuid).dash.child("figure{}".format(figure_id))
        if figure:
            parse_params(uuid, figure, dict(request.args))
        else:
            figures = RWrapper(uuid).dash.get_children('figure')
            fig_count = list(map(lambda i: int(re.search(r'\d+$', i).group()) if re.search(r'\d+$', i) else 0, figures.pop().__name__))
            i = next(filterfalse(set(fig_count).__contains__, count(1)))
            parse_params(RWrapper(uuid).dash.child('figure' + str(i)), request.args)

        return redirect("/loading/")
    else:
        if RWrapper(APPID).loaded():
            return redirect("/graph/")
        else:
            return redirect("/loading/")


def parse_params(uuid, figure, params):
    def validate(figure, params):
        logger.debug('Params: '+str(dict(params)))
        if not figure:
            logger.error('Figure does not exist.')
            return 0
        graph_type = params.get('graph_type')
        stream = params.get('stream')
        traces = params.get('traces')
        # print(graph_type is None, stream is None, traces is None)
        if graph_type is None or stream is None or traces is None:
            logger.error('Some variable is None!')
            return 0
        if graph_type.lower() not in ['trajectory', 'bar', 'scatter']:
            logger.error('Graph type {} does not exist.'.format(graph_type))
            return 0
        if RWrapper(uuid).search('S_0:'+stream+':Rlist') == []:
            logger.error('Stream {} does not exist.'.format(stream))
            return 0
        else:
            frame, end = Storage(id='S_0:'+stream+':Rlist', preload=True).call(start=0, end=1)
            columns = list(pd.DataFrame(frame).columns)
            traces = traces.split(',')
            params['traces'] = params['traces'].split(',')
            if isinstance(traces, list):
                for trace in traces:
                    if trace not in columns:
                        logger.error('Stream {} does not have name {}.'.format(stream, trace))
                        return 0
            else:
                if traces not in columns:
                    logger.error('Stream {} does not have name {}.'.format(stream, traces))
                    return 0
        return params
    if validate(figure, params):
        logger.info('Params are valid. Setting up: graph_type, stream, traces for figure {}'.format(figure))
        valid_params = [params.pop('graph_type')] + [params.pop('stream')] + \
                       [params.pop('traces')] + [params.pop('figure_id')]
        valid_params = {'graph_type': valid_params[0], 'stream': valid_params[1], 'traces': valid_params[2],
                        'figure_id': valid_params[3]}
        for param in valid_params:
            # print("{} ({}): {} ({})".format(param, type(param), valid_params[param], type(valid_params[param])))
            if param == 'traces':
                # Удаление всех прошлых ключей trace
                try:
                    # figure_children = RWrapper(uuid).dash.child("figure{}".format(valid_params['figure_id'])).val()
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

if __name__ == '__main__':
    server.run()

