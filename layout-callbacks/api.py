from config.const import APPID
from flask import Flask, request, redirect, make_response
import re
from itertools import count, filterfalse
import json
from redis_handler import RWrapper, Storage
from api_parser import parse_params, save_params
from logger import logger
logger = logger('api')

server = Flask(__name__)


def to_json(data):
    return json.dumps(data)


def resp(code, data):
    return make_response(to_json(str(code)+'. '+data), code)


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
            return pparse_params(uuid, figure_id, dict(request.args), method='optional')
        else:
            return resp(400, 'Figure id is None.')
    else:
        return redirect("/loading/")


@server.route('/dash/api')
def figure_work():
    if request.args:
        logger.info('Params: ' + str(dict(request.args)))
        uuid = request.args.get('uuid', 'default').lower()
        figure_id = request.args.get('figure_id')
        if figure_id is not None:
            return pparse_params(uuid, figure_id, dict(request.args))
        else:
            logger.info('Figure id is not selected. Giving id.')
            figures = RWrapper(uuid).dash.get_children('figure')
            names = [i.__name__ for i in figures]
            if len(figures):
                fig_count = list(map(lambda i: int(re.search(r'\d+$', i).group()) if re.search(r'\d+$', i) else 0,
                                     figures.pop().__name__))
                i = next(filterfalse(set(fig_count).__contains__, count(1)))

                while 'dash.figure{}'.format(i) in names:
                    logger.debug('Figure id {} is already exist. Giving another id.'.format(i))
                    i += 1
            else:
                i = 1
            logger.info('New figure id is {}'.format(i))
            # if RWrapper(uuid).dash.get_children('figure')
            return pparse_params(uuid, str(i), dict(request.args))
    else:
        # if RWrapper(APPID).loaded():
        #    return redirect("/graph/")
        #else:
        return redirect("/loading/")


def pparse_params(uuid, figure_id, params, method=None):
    if method == 'work' or method is None:
        ans = parse_params(params, uuid=uuid, figure_id=figure_id, required_list=['graph_type', 'stream'])
    elif method == 'optional':
        ans = parse_params(params, uuid=uuid, figure_id=figure_id,
                           required_list=['figure_id', 'uuid', 'trace_id', 'line_color',
                                          'line_width', 'marker_color', 'marker_size'])
    if ans.code == 200:
        logger.info('Params are valid. Saving to Redis...')
        save_params(params, uuid, figure_id)
        logger.info('OK')
        return redirect("/loading/")
    else:
        return resp(ans.code, ans.msg)



if __name__ == '__main__':
    server.run()

