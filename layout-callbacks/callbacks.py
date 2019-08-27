from dash.dependencies import Input, Output, State
import dash
from redis_handler import RWrapper, Storage
import pandas as pd

from logger import logger
logger = logger('callbacks')


# # # # # # # # Функции для callback'ов # # # # # # # #
UUID = 'test'
RW = RWrapper(UUID)


def update_figures(n, d, u, selected_figure):
    """
    Добавляет/удаляет/загружает графики в/из Redis
    :param n: обработчик кнопки "добавить" (n_clicks)
    :param d: обработчик кнопки "удалить" (n_clicks)
    :param selected_figure: выбранный график
    :return: options for dropdown, value of dropdown
    """
    value = selected_figure

    figures = []
    counter_figures = 0
    try:
        if isinstance(RW.dash(), dict):
            for i in RW.dash().keys():
                if 'figure' in i:
                    counter_figures += 1
                    figures.append({'label': i, 'value': i})
    except AttributeError:
        logger.debug('No dash keys in Redis.')

    # Если мы удаляем график (value = None)
    if dash.callback_context.triggered[0]['prop_id'] == 'delete-graph.n_clicks':
        if selected_figure not in [[], None]:
            RW.dash.child(selected_figure).rem()
            # Удаление selected_figure из figures
            figures = [i for i in figures if i['value'] != selected_figure]
        value = None
    # Если мы создаём график (value = new figure id)
    elif dash.callback_context.triggered[0]['prop_id'] == 'create-graph.n_clicks':
        # Создаём новую фигуру в Redis
        figure = 'figure{}'.format(counter_figures + 1)
        RW.dash.set({figure: {'name': figure, 'graph_type': 'scatter'}})
        figures.append({'label': figure, 'value': figure})
        value = figure
    # Если мы обновяем figures, то просто возвращаем фигуры
    elif dash.callback_context.triggered[0]['prop_id'] == 'btn-update.n_clicks':
        value = None
    return figures, value


def update_stream_traces(value):
    """
    Загрузка/обновление traces из потока
    :param value: id потока
    :return: options for dropdown
    """
    figures = []
    if value is not None:
        frame, end = Storage(id=value, preload=True).call(start=0, end=1)
        cols = list(pd.DataFrame(frame).columns)
        for i in cols:
            figures.append({'label': i, 'value': i})
    return figures


def update_stream():
    """
    Загрузка потоков из Redis
    :return: options for dropdown
    """
    streams = []
    for i in RW.search("S_0:*:Rlist"):
        i = i.decode("utf-8")
        streams.append({'label': i.split(':')[1], 'value': i})
    return streams


def update_traces(traces, figure):
    """
    Обновление traces (в настройках линий) при выборе visible-traces из потока
    :param figure: выбранный график
    :param traces: выбранные visible-traces
    :return: options for dropdown
    """
    if figure != [] and figure is not None and traces is not None and traces != []:
        figure_children = RW.dash.child(figure).val()
        existing_traces = [figure_children[i]['name']
                           for i in figure_children.keys() if 'trace' in i and i != 'traces']

        # Удаление всех прошлых ключей traces
        for i in figure_children.keys():
            # Если i - dict, то это trace. Иначе это просто переменная figure
            if i not in existing_traces and isinstance(i, dict):
                RW.dash.child(figure).child(i).remove()

        for i in range(0, len(traces)):
            # Сохранение всех выбранных trace
            RW.dash.child(figure).set({
                'trace{}'.format(i): {
                    'name': traces[i],
                    'name_id': traces[i]}
                }
            )
        # Обновляем значение переменной figure_children с новыми traces
        figure_children = RW.dash.child(figure).val()
        # print(figure_children)
        return [{'label': '{} ({})'.format(figure_children[i]['name'], i), 'value': i}
                for i in figure_children.keys() if i not in ['traces', 'name', 'graph_type', 'stream']]
    return []


def get_dict_from_str(color):
    """
    Делает из rgb-string -> rgb-dict (дабы можно было установить значение color_picker
    :param color: rgb-string
    :return: rgb-dict
    """
    if isinstance(color, str):
        # print('C:', color, color[5:-1])
        color_splited = color[5:-1].split(',')
        try:
            color = {'r': int(color_splited[0]), 'g': int(color_splited[1]), 'b': int(color_splited[2]), 'a': int(color_splited[3])}
        except:
            logger.warning('Can not get color-dict from string.')
    return color


DEFAULT_COLOR = {'r': 255, 'g': 100, 'b': 100, 'a': 1}


def update_settings(selected_traces, n, trace_name, lines_type_options, lines_type_value, selected_figure):
    """
    Загружает данные из Redis
    :param selected_traces: выбранная линия
    :param n: обработчик нажатий кнопки сброс
    :param trace_name: имя (name) линии
    :param lines_type_options: dropdown options
    :param lines_type_value: dropdown value
    :param selected_figure: выбранный график
    :return: trace_name, trace_line_color, trace_marker_color, trace_line_width, \
                trace_marker_size, trace_lines_type, styles (marker color-picker/marker size input), \
                    options for dropdown (lines_type)
    """
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-reset.n_clicks':
        return trace_name, {'rgb': DEFAULT_COLOR}, {'rgb': DEFAULT_COLOR}, 5, \
                10, 'lines+markers', \
                {}, {}, [{'label': 'Маркеры', 'value': 'markers'},
                         {'label': 'Линии', 'value': 'lines'},
                         {'label': 'Маркеры и линии', 'value': 'lines+markers'}]
    if selected_figure != [] and selected_figure is not None and selected_traces != [] and selected_traces is not None:
        trace_settings = RW.dash.child(selected_figure).child(selected_traces).val()
        logger.debug('Figure {} was load'.format(selected_figure))
        try:
            figure_settings = RW.dash.child(selected_figure).val()
        except AttributeError:
            figure_settings = {'graph_type': 'scatter', 'name': selected_figure}
        try:
            figure_type = figure_settings.get('graph_type', 'scatter')
        except AttributeError:
            figure_type = figure_settings
        trace_name = trace_settings.get('name')
        trace_marker = trace_settings.get('marker', {'color': DEFAULT_COLOR, 'width': 5})
        trace_marker_color = {'rgb': trace_marker.get('color', DEFAULT_COLOR)}
        trace_marker_color = {'rgb': get_dict_from_str(trace_marker_color['rgb'])}
        trace_marker_size = trace_marker.get('size', 10)

        if figure_type.lower() in [None, 'scatter', 'trajectory']:
            trace_lines_type = trace_settings.get('mode', 'lines+markers')

            trace_line = trace_settings.get('line', {'color': DEFAULT_COLOR, 'width': 5})
            trace_line_color = {'rgb': trace_line.get('color', DEFAULT_COLOR)}
            trace_line_color = {'rgb': get_dict_from_str(trace_line_color['rgb'])}
            trace_line_width = trace_line.get('width', 5)

            return trace_name, trace_line_color, trace_marker_color, trace_line_width, \
                trace_marker_size, trace_lines_type, \
                {}, {}, [{'label': 'Маркеры', 'value': 'markers'},
                         {'label': 'Линии', 'value': 'lines'},
                         {'label': 'Маркеры и линии', 'value': 'lines+markers'}]

        elif figure_type == 'bar':
            trace_lines_type = 'vertical'
            return trace_name, trace_marker_color, None, trace_marker_size, None, trace_lines_type, \
                {'display': 'none'}, {'display': 'none'}, \
                [{'label': 'Вертикальные столбцы', 'value': 'vertical'},
                 {'label': 'Горизонтальные столбцы', 'value': 'horizontal'}]

    return None, None, None, None, None, lines_type_value, \
        {'display': 'none'}, {'display': 'none'}, lines_type_options


def save_settings_to_redis(n, visible_traces, selected_figure, graph_type, selected_traces, selected_stream, trace_name, line_color, marker_color, line_width,
                           marker_size, lines_type):
    """
    Сохранение настроек в Redis
    :param selected_figure: выбранный графки
    :param graph_type: тип графика
    :param selected_traces: выбранная линия
    :param selected_stream: выбранный поток
    :param trace_name: новое имя (name) линии
    :param line_color: цвет линии
    :param marker_color: цвет маркера
    :param line_width: ширина линии
    :param marker_size: размер маркера
    :param lines_type: тип линий графика
    :return: alert
    """
    # if list(set(map(lambda i: i not in [None, []], [selected_figure, selected_stream, visible_traces])))[0]:
    if selected_figure not in [None, []]:
        if line_color in [{'rgb': DEFAULT_COLOR}, 'rgba(255,100,100,1)']:
            line_color = None
            RW.dash.child(selected_figure).child(selected_traces).line.color.rem()
        if marker_color in [{'rgb': DEFAULT_COLOR}, 'rgba(255,100,100,1)']:
            marker_color = None
            RW.dash.child(selected_figure).child(selected_traces).marker.color.rem()
        if marker_size == 10:
            marker_size = None
            RW.dash.child(selected_figure).child(selected_traces).marker.size.rem()
        if line_width == 5:
            line_width = None
            RW.dash.child(selected_figure).child(selected_traces).line.width.rem()
        # Создаём словарь нужного формата
        settings = to_settings_type(trace_name, line_color, marker_color, line_width,
                                    marker_size, lines_type, selected_figure, graph_type,
                                    selected_traces, selected_stream)

        if dash.callback_context.triggered[0]['prop_id'] == 'btn-save.n_clicks':
            # Создаём ключ для того, чтобы отловить сохранение настроек и перезагрузить графики
            settings.update({'dash_reload': True})

        try:
            figure_children = RW.dash.child(selected_figure).val()
            existing_traces = figure_children.get('traces', [])
            # Удаление всех прошлых ключей traces
            for i in figure_children.keys():
                if 'trace' in i and i != 'traces':
                    if figure_children[i]['name_id'] not in existing_traces:
                        RW.dash.child(selected_figure).child(i).rem()
            traces = []
            for i in range(0, len(visible_traces)):
                # Сохранение всех выбранных trace
                RW.dash.child(selected_figure).set({
                    'trace{}'.format(i): {
                        'name': visible_traces[i],
                        'name_id': visible_traces[i]}
                }
                )
                traces.append(visible_traces[i])
            RW.dash.child(selected_figure).traces.set(traces)
            RW.dash.set(settings)
            if dash.callback_context.triggered[0]['prop_id'] == 'btn-save.n_clicks':
                return [True, 'success', 'Настройки сохранены']
        except:
            if dash.callback_context.triggered[0]['prop_id'] == 'btn-save.n_clicks':
                return [True, 'danger', 'Произошла ошибка при сохранении данных. Настройки не сохранены']
    return [False, 'success', '']


def to_settings_type(new_trace_name, line_color, marker_color, line_width,
                     marker_size, lines_type, selected_figure, graph_type,
                     selected_traces, selected_stream):
    """
    Преобразует данные к правильному типу (напр.: данные с color-picker в виде dict -> str)
    :param selected_figure: выбранный графки
    :param graph_type: тип графика
    :param selected_traces: выбранная линия
    :param selected_stream: выбранный поток
    :param graph_type: тип линии линии
    :param new_trace_name: новое имя (name) линии
    :param line_color: цвет линии
    :param marker_color: цвет маркера
    :param line_width: ширина линии
    :param marker_size: размер маркера
    :param lines_type: тип линий графика
    :return: settings (dict)
    """
    setting = {selected_figure: {}}
    if selected_stream not in [None, []]:
        setting[selected_figure].update({'stream': selected_stream})
    if graph_type not in [None, []]:
        setting[selected_figure].update({'graph_type': graph_type})
    if selected_traces not in [None, []]:
        try:
            trace_name = RW.dash.child(selected_figure).child(selected_traces).val().get('name', new_trace_name)
        except AttributeError:
            trace_name = new_trace_name
        setting[selected_figure].update({selected_traces: {}})
        if line_color is not None:
            # Преобразование формата получаемого color_picker в rgb-string
            try:
                line_color = 'rgba({},{},{},{})'.format(line_color['rgb']['r'], line_color['rgb']['g'],
                                                        line_color['rgb']['b'], line_color['rgb']['a'])
            except KeyError:
                # Если данные уже приведены к нужному типу
                pass
            except TypeError:
                # Если до этого не было выбрано значение line_color
                pass
            setting[selected_figure].update({selected_traces: {
                'line': {'color': line_color}}})

        if line_width is not None:
            if setting[selected_figure][selected_traces].get('line') is not None:
                setting[selected_figure][selected_traces]['line'].update({'width': line_color})
            else:
                setting[selected_figure].update({selected_traces: {
                                'line': {'width': line_color}}})

        if graph_type.lower() in ['scatter', 'trajectory']:
            if marker_color is not None:
                # Преобразование формата получаемого color_picker в rgb-string
                try:
                    marker_color = 'rgba({},{},{},{})'.format(marker_color['rgb']['r'], marker_color['rgb']['g'],
                                                              marker_color['rgb']['b'], marker_color['rgb']['a'])
                except KeyError:
                    # Если данные уже приведены к нужному типу
                    pass
                except TypeError:
                    # Если до этого не было выбрано значение marker_color
                    pass
                setting[selected_figure][selected_traces].update({
                    'marker': {'color': marker_color}})

            if marker_size is not None:
                if setting[selected_figure][selected_traces].get('marker') is not None:
                    setting[selected_figure][selected_traces]['marker'].update({'size': marker_size})
                else:
                    setting[selected_figure].update({selected_traces: {
                        'marker': {'size': marker_size}}})

        setting[selected_figure][selected_traces].update({'name': new_trace_name,
                                                          'name_id': trace_name, 'mode': lines_type})
    return setting


def load_traces_from_redis_for_figure(figure_name):
    """
    Загружает все traces из Redis для выбранного графика
    :param figure_name: выбранный графки
    :return: options for dropdown
    """
    traces = RW.dash.child(figure_name).val()
    result_traces = []
    for trace in traces:
        if trace == 'traces':
            continue
        settings = traces[trace]
        name = settings.get('name', trace)
        result_traces.append({'label': '{} ({})'.format(name, trace), 'value': trace})
    return result_traces


def show_edit_block(traces, stream):
    """
    Показывает блок с настройками линий, если выбранны:
    :param traces: отображаемые линии
    :param stream: поток
    :return: block style
    """
    if traces not in [[], None] and stream not in [[], None]:
        return {}
    return {'display': 'none'}


def show_settings_block(value):
    """
    Показывает блок, если нажата кнопка
    :param value: обработчик кнопки
    :return: style
    """
    if value:
        if value % 2 != 0:
            return {}
    return {'display': 'none'}


def load_settings_for_figure_block(figure):
    """
    Показывает следующий блок (с выбором потока и т.д.), если выбран график
    :param figure: выбранный график
    :return: style
    """

    if figure is not None and figure != []:
        figure_settings = RW.dash.child(figure).val()
        logger.debug('Loaded figure settings:'+str(figure_settings))
        stream_options = update_stream()
        stream_value = figure_settings.get('stream')
        traces = figure_settings.get('traces', [])
        graph_type = figure_settings.get('graph_type', 'scatter').lower()
        return {}, graph_type, stream_options, stream_value, traces, None
    return {'display': 'none'}, 'scatter', update_stream(), None, None, None

# # # # # # # # Классы Callback # # # # # # # #


class Callbacks(object):
    def __init__(self, name):
        self.name = name

    def __call__(self):
        return globals()[self.name]()()


class CallbackObj(object):
    def __init__(self, **kwargs):
        self.val = []

    def __call__(self):
        return self.val


class SettingsPanel(CallbackObj):
    def __init__(self):
        super().__init__()

        # Юзер: *создаёт график*

        # Создание и удаление всех графиков в Redis
        self.val.append(
            (([Output('global-figures-selector', 'options'),
              Output('global-figures-selector', 'value')],
              [Input('create-graph', 'n_clicks'),
               Input('delete-graph', 'n_clicks'),
               Input('btn-update', 'n_clicks')],
              [State('global-figures-selector', 'value')]), update_figures))

        # Юзер: *выбирает график*

        # Показ следующего блока настроек, если выбран график
        # Загрузка figure_type, stream, visible_traces из Redis
        self.val.append(
            (([Output('children-figures', 'style'),
               Output('global-figure-type-selector', 'value'),
               Output('global-stream-selector', 'options'),
               Output('global-stream-selector', 'value'),
               Output('global-visible-traces-selector', 'value'),
               Output('global-traces-selector', 'value')],
              [Input('global-figures-selector', 'value')]), load_settings_for_figure_block))

        # Юзер: *выбирает поток для отрисовки графика*
        # Показ возможных данных для отрисовки из потока
        self.val.append(
            ((Output('global-visible-traces-selector', 'options'),
              [Input('global-stream-selector', 'value')]), update_stream_traces))

        # Сохранение stream, graph_type, visible_traces в Redis
        self.val.append(
            ((Output('global-traces-selector', 'options'),
             [Input('global-visible-traces-selector', 'value')],
             [State('global-figures-selector', 'value')]), update_traces))

        # При выборе конкретной линии в edit-block
        # Загрузка данных color-picker, input (etc.) исходя из данных в Redis
        self.val.append(
            (([
               # Outputs для установки значений из Redis (загрузки данных)
               Output('global-input-trace-name', 'value'),
               Output('global-color-picker-line', 'value'),
               Output('global-color-picker-marker', 'value'),
               Output('global-input-line-width', 'value'),
               Output('global-input-marker-size', 'value'),
               Output('global-lines-type', 'value'),

               # Outputs для скрытия/показа некоторых Card (исходя из типа графика)
               Output('global-card-marker-color', 'style'),
               Output('global-card-marker-size', 'style'),
               Output('global-lines-type', 'options')],

              [Input('global-traces-selector', 'value'),
               Input('btn-reset', 'n_clicks')],
              [State('global-input-trace-name', 'value'),
               State('global-lines-type', 'options'),
               State('global-lines-type', 'value'),
               State('global-figures-selector', 'value')]), update_settings))

        self.val.append(
            ((Output('global-edit-block', 'style'),
              [Input('global-visible-traces-selector', 'value')],
              [State('global-stream-selector', 'value')]), show_edit_block))

        # При нажатии кнопки "открыть" показывается line-settings
        self.val.append(
            ((Output('global-settings-panel', 'style'),
              [Input('btn-open-global-style', 'n_clicks')]),
             show_settings_block))

        # Сохранение данных о конкретной линии trace + stream, graph_type, visible_traces в Redis
        self.val.append(
            (([Output('alert', 'is_open'),
               Output('alert', 'color'),
               Output('alert', 'children')],
              [Input('btn-save', 'n_clicks'),
               Input('global-visible-traces-selector', 'value')],
              [State('global-figures-selector', 'value'),
               State('global-figure-type-selector', 'value'),
               State('global-traces-selector', 'value'),
               State('global-stream-selector', 'value'),
               State('global-input-trace-name', 'value'),
               State('global-color-picker-line', 'value'),
               State('global-color-picker-marker', 'value'),
               State('global-input-line-width', 'value'),
               State('global-input-marker-size', 'value'),
               State('global-lines-type', 'value')]), save_settings_to_redis))

