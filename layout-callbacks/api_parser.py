from redis_handler import RWrapper, Storage
from logger import logger
import pandas as pd

logger = logger('api')


"""This module validates parameters passed by API
Import parse_params from here"""


def populate_kwargs(params, kwargs):
    # get data for cross-validation here
    if 'stream' in params:
        kwargs['Storage'] = Storage(id='S_{}:Trajectory:Rlist'.format(params['stream']), preload=False)
    return kwargs


class BaseContainer(object):
    def __init__(self, **kwargs):
        for key in kwargs.keys():
            setattr(self, key, kwargs[key])


class Parameter(BaseContainer):
    def __init__(self, value, **kwargs):
        self.name = None
        self.type = None
        self.params = None
        
        self.value = value
        self.selector_options = []
        super().__init__(**kwargs)
        self.selector = True if self.selector_options else False

        # if not self.type and self.name:
        #    logger.info('To enable type check for {} set expected type in api_parser.match_class'.format(self.name))

    def validate_basic(self):
        if self.selector:
            if self.value not in self.selector_options:
                return 400, '{} cannot be {}, allowed options are {}'.format(self.name,
                                                                             self.value,
                                                                             self.selector_options)
        if self.type and type(self.value) != self.type:
            try:
                self.value = {"<class 'str'>": str(self.value),
                              "<class 'int'>": int(self.value),
                              "<class 'float'>": float(self.value)}[str(self.type)]
            except TypeError:
                return 415, '{} expected. Received {}={}.'.format(self.type, self.name, self.value)
            except ValueError:
                return 415, '{} expected. Received {}={}.'.format(self.type, self.name, self.value)
        return 200, 'Value of {} set to {}'.format(self.name,self.value)

    def validate(self):
        # placeholder to overwrite in children classes
        return self.validate_basic()

    def save(self, figure):
        # placeholder to overwrite in children classes
        return 200, 'OK'


class ResponseStack(object):
    """Object to hold API response codes


    obj.status(func) - returns 'OK' or 'ERROR'
    obj.stack(list) -  of (code,msg) which may be sent to client
    obj.code(int) - 200 or last(currently) error code

    """
    # TODO: write a func to compose error msg to client if there is more than 1 error

    def __init__(self):
        self.code = 200
        self.stack = []
        self.msg = ''

    def push(self, msg):
        if msg[0] != 200 and msg[0] != 201:
            # decide what response code to set here
            logger.warning('failed to parse parameters. {}'.format(msg))
            self.code = msg[0]
            self.msg = msg[1]
        self.stack.append(msg)

    def status(self):
        if self.code == 200:
            return 'OK'
        else:
            return 'ERROR'


def parse_params(params, uuid='default', figure_id=1, required_list=[], **kwargs):
    """Parser entrance point
    Usage:
    Params([parameters_to_parse],required_list=[Arbitrary parameter names], **kwargs)

    kwargs reserved for future use

    :return ResponseStack obj
    """

    responses = ResponseStack()
    kwargs = populate_kwargs(params, kwargs)

    params['uuid'] = uuid
    params['figure_id'] = figure_id

    if params.get('graph_type', '').lower() == 'trajectory':
        required_list.append('stream')
    if params.get('stream') is not None:
        required_list.append('graph_type')

    for key in params.keys():
        responses.push(match_class(name=key, params=params, value=params[key], **kwargs).validate())
        try:
            required_list.remove(key)
        except:
            pass
    if required_list:
        responses.push((400, 'Missing required parameters - {}'.format(required_list)))
    return responses


def save_params(params, uuid='default', figure_id=1, **kwargs):
    """
    Save params to Redis

    :return: responses stack
    """
    responses = ResponseStack()
    kwargs = populate_kwargs(params, kwargs)
    figure = RWrapper(uuid).dash.__getattr__('figure{}'.format(figure_id))
    figure.graph_type.set(params.get('graph_type', 'trajectory'))
    for key in params.keys():
        if key not in ['uuid', 'figure_id']:
            responses.push(match_class(name=key, params=params, value=params[key], **kwargs).save(figure))
    return responses


class ParameterTemplate(Parameter):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)


class Stream(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'stream_id'

    def validate(self):
        if RWrapper().search('S_{}:*'.format(self.value)) == []:
            mess = 'Stream with id {} does not exist.'.format(self.value)
            logger.error(mess)
            return 400, mess
        return self.validate_basic()

    def save(self, figure):
        stream = 'S_{}:Trajectory:Rlist'.format(self.params['stream'])
        figure.stream.set(stream)
        return 201, 'Created'


class Traces(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def delete_traces(self):
        # Deleting traces keys
        try:
            figure = RWrapper(self.params['uuid']).child('figure{}'.format(self.params['figure_id']))
            figure_children = figure.val()
            for i in figure_children.keys():
                if 'trace' in i:
                    figure.child(i).rem()
        except AttributeError:
            # значит, таких ключей нет
            pass

    def check_trace(self, name):
        if RWrapper().search('{}:dash.figure{}.{}.name*'.format(self.params['uuid'], self.params['figure_id'], name)) == []:
            return 0
        return 1

    class TraceName(Parameter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        def validate(self):
            stream, _ = Storage(id='S_{}:Trajectory:Rlist'.format(self.params.get('stream')),
                                preload=False).call(start=0, end=1)
            columns = list(pd.DataFrame(stream).columns)
            traces = self.value.split(',')
            for trace in traces:
                if trace not in columns:
                    mess = 'Stream {} does not have name {}.'.format(self.params.get('stream'), trace)
                    logger.error(mess)
                    return 400, mess
            return self.validate_basic()

    class Color(Parameter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def validate_format(self):
            if isinstance(self.value, str):
                if not len(self.value) >= 13 or not self.value[:5] == 'rgba(' or not self.value[-1] == ')':
                    return 0
                value_splited = self.value[5:-1].split(',')

                try:
                    {'r': int(value_splited[0]), 'g': int(value_splited[1]), 'b': int(value_splited[2]),
                     'a': int(value_splited[3])}
                except Exception:
                    return 0
            else:
                return 0
            return 1

        def validate(self):
            if not self.validate_format():
                mess = 'Color {} is not in valid format. Correct format: rbga(1,1,1,1)'.format(self.value)
                logger.error(mess)
                return 400, mess
            return self.validate_basic()

    class TraceLineColor(Color):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        def save(self, figure):
            figure.child(self.name).line_color.set(self.value)
            return 201, 'Created'

    class TraceMarkerColor(Color):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        def save(self, figure):
            figure.child(self.name).marker_color.set(self.value)
            return 201, 'Created'

    class TraceLineWidth(Parameter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def save(self, figure):
            figure.child(self.name).line_width.set(self.value)
            return 201, 'Created'

    class TraceMarkerSize(Parameter):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)

        def save(self, figure):
            figure.child('trace{}'.format(self.params['trace_id'])).marker_size.set(self.value)
            return 201, 'Created'

    def validate(self):
        if not self.params.get('traces_deleted', True):
            self.delete_traces()

        try:
            child = self.name.split('.')[1]
        except IndexError:
            return 400, 'Invalid trace child'
        classes = {
            'name': self.TraceName,
            'line_color': self.TraceLineColor,
            'line_width': self.TraceLineWidth,
            'marker_color': self.TraceMarkerColor,
            'marker_size': self.TraceMarkerSize,
        }
        if self.name.split('.')[0]+'.name' not in self.params and not self.check_trace(self.name.split('.')[0]):
            return 400, 'You have to set up {}.name firstly.'.format(self.name.split('.')[0])

        try:
            ans = classes.get(child, None)(name=self.name, params=self.params, value=self.value).validate()
        except:
            return 400, 'Invalid trace parameter'
        if ans[0] == 200:
            return self.validate_basic()
        else:
            return ans[0], ans[1]

    def save(self, figure):
        figure.child(self.name).set(self.value)
        return 201, 'Created'


class TraceId(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self):
        uuid = self.params.get('uuid', 'default')
        if uuid != 'default' and RWrapper(uuid).search('*figure{}.trace{}*'.format(
                                                        self.params['figure_id'],
                                                        self.value)) == []:
            return 400, 'Trace with id {} for figure{} for uuid {} does not exist.'.format(self.value,
                                                                                           self.params['figure_id'],
                                                                                           uuid)
        return 200, 'OK'


class FigureId(Parameter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'figure_id'

    def validate(self):
        is_creation = False
        if 'graph_type' in self.params or 'stream' in self.params:
            is_creation = True

        if not is_creation:
            uuid = self.params.get('uuid', 'default')
            if RWrapper(uuid).search('{}:dash.figure{}*'.format(uuid, self.value)) == []:
                return 400, 'Figure with id {} for uuid {} does not exist'.format(self.value, self.params['uuid'])
        return 200, 'OK'






def match_class(**kwargs):
    name = kwargs.get('name')

    exact_match = {'uuid': (ParameterTemplate, dict(type=str)),
                   'figure_id': (FigureId, {}),
                   'stream': (Stream, {}),
                   'graph_type': (ParameterTemplate, dict(selector_options=['trajectory', 'bar', 'scatter'])),
                   }

    ClassName, add_params = exact_match.get(name, (None, kwargs))
    traces_deleted = False
    if ClassName:
        if add_params:
            kwargs = {**kwargs, **add_params}
        return ClassName(**kwargs)
    elif 'trace' in name and name != 'traces':
        kwargs['traces_deleted'] = traces_deleted
        if not traces_deleted:
            traces_deleted = True
        return Traces(**kwargs)
    else:
        tmp = BaseContainer

        def tmp_validate():
            return 200, 'Untracked variable: {}'.format(name)

        setattr(tmp, 'validate', tmp_validate)
        return tmp









