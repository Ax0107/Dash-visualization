from dash.dependencies import Input, Output, State
import dash
from redis_handler import RWrapper, Storage
import pandas as pd

# # # # # # # # Функции для callback'ов # # # # # # # #
UUID = 'test'
RW = RWrapper(UUID)


def update_figures(n, d, figure_type, selected_figure):
    """
    Добавляет/удаляет/загружает графики в/из Redis
    :param n: обработчик кнопки "добавить" (n_clicks)
    :param d: обработчик кнопки "удалить" (n_clicks)
    :param figure_type: тип фигуры из dropdown (scattergl/bar)
    :param selected_figure: выбранный график
    :return: options for dropdown, value of dropdown
    """
    value = selected_figure
    is_value_set_none = 0

    # Если мы удаляем график
    if dash.callback_context.triggered[0]['prop_id'] == 'delete-graph.n_clicks':
        RW.dash.child(selected_figure).remove()
        # Ставим значение dropdown в None
        value = None
        is_value_set_none = 1

    # Если изменён тип графика
    elif dash.callback_context.triggered[0]['prop_id'] == 'global-figure-type-selector.value' and \
            figure_type is not None and selected_figure is not None:
        RW.dash.child(selected_figure).type.set(figure_type)

    figures = []

    # Если была нажата кнопка
    if n is not None:
        # Создаём новую фигуру в Redis
        figure = 'figure{}'.format(n)
        RW.dash.set({figure: {'name': figure, 'type': figure_type}})

    if isinstance(RW.dash(), dict):
        for i in RW.dash().keys():
            if 'figure' in i:
                figures.append({'label': i, 'value': i})

    # Если мы не удаляли figure и нам не нужно ставить значение dropdown в None,
    # то ставим его в figureN
    if not is_value_set_none:
        if n is not None:
            value = 'figure{}'.format(n)
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


def update_stream(n):
    """
    Загрузка/обновление потоков из Redis
    :param n: обработчик нажатия кнопки
    :return: options for dropdown
    """
    streams = []
    # TODO: поиск по приставке
    for i in RW.search("*:Rlist"):
        i = i.decode("utf-8")
        streams.append({'label': i, 'value': i})
    return streams


def update_traces(figure, traces):
    """
    Обновление traces (в настройках линий) при выборе visible-traces из потока
    :param figure: выбранный график
    :param traces: выбранные visible-traces
    :return: options for dropdown
    """
    # TODO: загрузка значений из Redis (!!!)
    if figure != [] and figure is not None and traces is not None and traces != []:
        figure_childs = RW.dash.child(figure).val()

        existing_traces = figure_childs.get('traces', [])

        # Удаление всех прошлых ключей traces
        for i in figure_childs.keys():
            print('I:', i)
            # Если i - dict, то это trace. Иначе это просто переменная figure
            if i not in existing_traces and isinstance(i, dict):
                RW.dash.child(figure).child(i).remove()

        for i in range(0, len(traces)):
            # Сохранение всех выбранных trace
            # TODO: trace_type save
            RW.dash.child(figure).set({
                'trace{}'.format(i): {
                    'name': traces[i],
                    'name_id': traces[i]}
                }
            )
            RW.dash.child(figure).set({'traces': traces})
        # Обновляем значение переменной figure_childs с новыми traces
        figure_childs = RW.dash.child(figure).val()
        return [{'label': '{} ({})'.format(figure_childs[i]['name'], i), 'value': i}
                for i in figure_childs.keys() if i != 'traces']
    return []


def get_dict_from_str(color):
    """
    Делает из rgb-string -> rgb-dict (дабы можно было установить значение color_picker
    :param color: rgb-string
    :return: rgb-dict
    """
    if isinstance(color, str):
        color = color[3:-1].split(',')
        color = {'r': color[0], 'g': color[1], 'b': color[2], 'a': color[3]}
    return color


DEFAULT_COLOR = {'r': 255, 'g': 100, 'b': 100, 'a': 1}


def update_settings(selected_traces, trace_name, lines_type_options, lines_type_value, selected_figure):
    """
    Загружает данные из Redis
    :param selected_traces: выбранная линия
    :param trace_name: имя (name) линии
    :param lines_type_options: dropdown options
    :param lines_type_value: dropdown value
    :param selected_figure: выбранный график
    :return: trace_name, trace_line_color, trace_marker_color, trace_line_width, \
                trace_marker_size, trace_lines_type, styles (marker color-picker/marker size input), \
                    options for dropdown (lines_type)
    """
    if selected_figure != [] and selected_figure is not None and selected_traces != [] and selected_traces is not None:
        trace_settings = RW.dash.child(selected_figure).child(selected_traces).val()
        try:
            figure_settings = RW.dash.child(selected_figure).val()
        except AttributeError:
            figure_settings = {'type': 'scattergl', 'name': selected_figure}
        try:
            figure_type = figure_settings.get('type', 'scattergl')
        except AttributeError:
            figure_type = figure_settings
        trace_name = trace_settings.get('name')
        trace_marker = trace_settings.get('marker', {'color': DEFAULT_COLOR, 'width': 5})
        trace_marker_color = {'rgb': trace_marker.get('color', DEFAULT_COLOR)}
        trace_marker_color = {'rgb': get_dict_from_str(trace_marker_color['rgb'])}
        trace_marker_size = trace_marker.get('size', 10)

        if figure_type in [None, 'scattergl', 'trajectory']:
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

    return trace_name, None, None, None, None, lines_type_value, \
        {'display': 'none'}, {'display': 'none'}, lines_type_options


def save_settings_to_redis(n, selected_figure, selected_traces, trace_name, line_color, marker_color, line_width,
                           marker_size, lines_type):
    """
    Сохранение настроек в Redis
    :param n: обработчик кнопки "добавить" (n_clicks)
    :param selected_figure: выбранный графки
    :param selected_traces: выбранная линия
    :param trace_name: новое имя (name) линии
    :param line_color: цвет линии
    :param marker_color: цвет маркера
    :param line_width: ширина линии
    :param marker_size: размер маркера
    :param lines_type: тип линий графика
    :return: alert
    """
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-save-global-style.n_clicks'and selected_traces is not None\
                                                                                            and selected_traces != []:

        # Создаём словарь нужного формата
        trace_type = RW.dash.child(selected_figure).child(selected_traces).val().get('type', 'scattergl')
        settings = to_settings_type(selected_figure, selected_traces, trace_type, trace_name,
                                    line_color, marker_color, line_width, marker_size, lines_type)
        try:
            # Создаём ключ для того, чтобы отловить сохранение настроек и перезагрузить графики
            settings.update({'dash-reload': True})
            RW.dash.set(settings)
            return [True, 'success', 'Настройки сохранены']
        except:
            return [True, 'danger', 'Произошла ошибка при сохранении данных. Настройки не сохранены']
    return [False, 'success', '']


def to_settings_type(selected_figure, selected_traces, trace_type,
                     new_trace_name, line_color, marker_color, line_width, marker_size, lines_type):
    """
    Преобразует данные к правильному типу (напр.: данные с color-picker в виде dict -> str)
    :param selected_figure: выбранный графки
    :param selected_traces: выбранная линия
    :param trace_type: тип линии линии
    :param new_trace_name: новое имя (name) линии
    :param line_color: цвет линии
    :param marker_color: цвет маркера
    :param line_width: ширина линии
    :param marker_size: размер маркера
    :param lines_type: тип линий графика
    :return: settings (dict)
    """
    setting = []
    if selected_traces is not None:
        trace_name = RW.dash.child(selected_figure).child(selected_traces).val().get('name', new_trace_name)

        # Преобразование формата получаемого color_picker в rgb-string
        try:
            line_color = 'rgb({},{},{},{})'.format(line_color['rgb']['r'], line_color['rgb']['g'],
                                                   line_color['rgb']['b'], line_color['rgb']['a'])
        except KeyError:
            # Если данные уже приведены к нужному типу
            pass

        if trace_type == 'scattergl':
            # Преобразование формата получаемого color_picker в rgb-string
            try:
                marker_color = 'rgb({},{},{},{})'.format(marker_color['rgb']['r'], marker_color['rgb']['g'],
                                                         marker_color['rgb']['b'], marker_color['rgb']['a'])
            except KeyError:
                # Если данные уже приведены к нужному типу
                pass

            setting = {selected_figure: {selected_traces: {
                                                'line': {'color': line_color, 'width':  line_width},
                                                'marker': {'color': marker_color, 'size': marker_size},
                                         'name': new_trace_name, 'name_id': trace_name, 'mode': lines_type}}}
        else:
            setting = {selected_figure: {selected_traces: {
                'marker': {'color': line_color, 'size': line_width},
                'name': new_trace_name, 'name_id': trace_name, 'mode': lines_type}}}
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


def show_edit_block(a, b):
    """
    Показывает блок с настройками линий, если выбранны:
    :param a: отображаемые линии
    :param b: поток
    :return: block style
    """
    if a not in [[], None] and b not in [[], None]:
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


def show_settings_for_figure_block(value):
    """
    Показывает следующий блок (с выбором потока и т.д.), если выбран график
    :param value: dropdown-figures value
    :return: style
    """
    if value is not None and value != []:
        return {}
    return {'display': 'none'}

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
        # При нажатии кнопки "открыть" показывается settings-panel
        self.val.append(
            ((Output('global-settings-panel', 'style'),
              [Input('btn-open-global-style', 'n_clicks')]),
             show_settings_block))

        # Загрузка данных о потоках
        self.val.append(
            ((Output('global-stream-selector', 'options'),
              [Input('btn-open-global-style', 'n_clicks')]), update_stream))

        # Юзер: *создаёт график*

        # Создание и обновление всех графиков в Redis
        self.val.append(
            (([Output('global-figures-selector', 'options'),
              Output('global-figures-selector', 'value')],
              [Input('create-graph', 'n_clicks'),
               Input('delete-graph', 'n_clicks'),
               Input('global-figure-type-selector', 'value')],
              [State('global-figures-selector', 'value')]), update_figures))

        # Юзер: *выбирает график*

        # Показ следующего блока настроек, если выбран график
        self.val.append(
            ((Output('children-figures', 'style'),
              [Input('global-figures-selector', 'value')]), show_settings_for_figure_block))

        # Юзер: *выбирает поток для отрисовки графика*

        # Показ возможных данных для отрисовки из потока
        self.val.append(
            ((Output('global-visible-traces-selector', 'options'),
              [Input('global-stream-selector', 'value')]), update_stream_traces))

        # Обновление данных traces для графика в Redis
        self.val.append(
            ((Output('global-traces-selector', 'options'),
             [Input('global-figures-selector', 'value'),
              Input('global-visible-traces-selector', 'value')]), update_traces))

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

              [Input('global-traces-selector', 'value')],
              [State('global-input-trace-name', 'value'),
               State('global-lines-type', 'options'),
               State('global-lines-type', 'value'),
               State('global-figures-selector', 'value')]), update_settings))

        self.val.append(
            ((Output('global-edit-block', 'style'),
              [Input('global-visible-traces-selector', 'value'),
               Input('global-stream-selector', 'value')]), show_edit_block))

        # Сохранение данных о traces в Redis
        self.val.append(
            (([Output('alert', 'is_open'),
               Output('alert', 'color'),
               Output('alert', 'children')],
              [Input('btn-save-global-style', 'n_clicks')],
              [State('global-figures-selector', 'value'),
               State('global-traces-selector', 'value'),
               State('global-input-trace-name', 'value'),
               State('global-color-picker-line', 'value'),
               State('global-color-picker-marker', 'value'),
               State('global-input-line-width', 'value'),
               State('global-input-marker-size', 'value'),
               State('global-lines-type', 'value')]), save_settings_to_redis))

