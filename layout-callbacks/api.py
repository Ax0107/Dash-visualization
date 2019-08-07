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


@server.route('/dash/api/add')
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
    def validate(params):
        logger.debug('Params: '+str(dict(params)))
        figure_id = params.get('figure_id')
        graph_type = params.get('graph_type')
        stream = params.get('stream')
        traces = params.get('traces')
        # print(graph_type is None, stream is None, traces is None)
        if figure_id is None or graph_type is None or stream is None or traces is None:
            logger.error('Some var is None!')
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
    if validate(params):
        logger.info('Params are valid.')
        for param in params:
            # print("{} ({}): {} ({})".format(param, type(param), params[param], type(params[param])))
            if param == 'traces':
                # Удаление всех прошлых ключей trace
                try:
                    figure_children = RWrapper(uuid).dash.child("figure{}".format(params['figure_id'])).val()
                    existing_traces = figure_children.get('traces', [])
                    for i in figure_children.keys():
                        # Если i - dict, то это trace. Иначе это просто переменная figure
                        if i not in existing_traces and isinstance(i, dict):
                            RWrapper(uuid).dash.child(figure).child(i).rem()
                except AttributeError:
                    # значит, таких ключей нет
                    pass
                for i in range(0, len(params[param])):
                    RWrapper(uuid).dash.figure.child('trace{}'.format(i)).name.set(params[param][i])
            if param == 'stream':
                params['stream'] = 'S_0:' + params['stream'] + ':Rlist'
            RWrapper(uuid).dash.child("figure{}".format(params['figure_id'])).child(param).set(params[param])

        # RWrapper(APPID).dash.reload.set('True')
        # RWrapper(APPID).loading()

if __name__ == '__main__':
    server.run()

