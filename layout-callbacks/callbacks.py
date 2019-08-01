from dash.dependencies import Input, Output, State
import dash
from redis_handler import RWrapper


# # # # # # # # Функции для callback'ов # # # # # # # #
UUID = 'test'
RW = RWrapper(UUID)


def update_figures(n):
    figures = []
    try:
        for i in RW.dash().keys():
            if 'figure' in i:
                figures.append({'label': i, 'value': i})
    except:
        pass
    return figures


def update_traces(figure):
    result_traces = []
    if figure is not None:
        traces = RW.dash()[figure]
        for trace in traces:
            if trace == 'traces':
                continue
            settings = traces[trace]
            name = settings['name']
            result_traces.append({'label': '{} ({})'.format(name, trace), 'value': trace})
    return result_traces


def update_settings(selected_figure, selected_traces, trace_name, lines_type_options, lines_type_value):
    if selected_traces is not None:
        trace = selected_traces
        trace_settings = RW.dash()[selected_figure][trace]
        print(trace_settings)

        # TODO: Более красивый код (ибо делать try-except каждый раз невыносимо)
        # Тут идёт установка значений, хранящихся в Redis
        # Если значение не установлено, то мы ловим KeyError и устанавливаем какое-то значение по-умолчанию
        # Возможно TODO: default settings?

        try:
            trace_type = trace_settings['type']
        except KeyError:
            trace_type = 'scattergl'
        try:
            trace_name = trace_settings['name']
        except KeyError:
            trace_name = trace
        try:
            trace_line_color = {'rgb': trace_settings['line']['color']}
            trace_line_width = trace_settings['line']['width']
        except KeyError:
            trace_line_color = None
            trace_line_width = 5

        if trace_type == 'scattergl':
            try:
                trace_marker_color = {'rgb': trace_settings['marker']['color']}
                trace_marker_size = trace_settings['marker']['size']
            except KeyError:
                trace_marker_color = None
                trace_marker_size = 15

            try:
                trace_lines_type = trace_settings['mode']
            except KeyError:
                trace_lines_type = 'lines+markers'

            return trace_name, trace_line_color, trace_marker_color, trace_line_width, \
                trace_marker_size, trace_lines_type, \
                {}, {}, [{'label': 'Маркеры', 'value': 'markers'},
                         {'label': 'Линии', 'value': 'lines'},
                         {'label': 'Маркеры и линии', 'value': 'lines+markers'}]

        else:
            trace_lines_type = 'vertical'
            return trace_name, trace_line_color, None, trace_line_width, None, trace_lines_type, \
                {'display': 'none'}, {'display': 'none'}, \
                [{'label': 'Вертикальные столбцы', 'value': 'vertical'},
                 {'label': 'Горизонтальные столбцы', 'value': 'horizontal'}]

    return trace_name, None, None, None, None, lines_type_value, \
        {'display': 'none'}, {'display': 'none'}, lines_type_options


def save_settings_to_redis(n, selected_figure, selected_traces, trace_name, line_color, marker_color, line_width,
                           marker_size, lines_type):
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-save-global-style.n_clicks':

        # Создаём словарь нужного формата
        trace_type = RW.dash()[selected_figure][selected_traces]['type']
        settings = to_settings_type(selected_figure, selected_traces, trace_type, trace_name, line_color, marker_color, line_width,
                                    marker_size, lines_type)

        try:
            # Создаём ключ для того, чтобы отловить сохранение настроек и перезагрузить графики
            settings[0].update({'dash-reload': True})
            RW.dash.set(settings[0])
            return [True, 'success', 'Настройки сохранены']
        except IndexError:
            pass
        except:
            return [True, 'danger', 'Произошла ошибка при сохранении данных. Настройки не сохранены']
    return [False, 'success', '']


def to_settings_type(selected_figure, selected_traces, trace_type, trace_name, line_color, marker_color, line_width, marker_size, lines_type):
    setting = []
    if selected_traces is not None:
        if trace_type == 'scattergl':
            setting = {selected_figure: {'trace{}'.format(selected_traces): {
                                                'line': {'color': line_color['rgb'], 'width':  line_width},
                                                'marker': {'color': marker_color['rgb'], 'size': marker_size},
                                         'name': trace_name, 'mode': lines_type}}}
        else:
            setting = {selected_figure: {'trace{}'.format(selected_traces): {
                'marker': {'color': line_color['rgb'], 'width': line_width},
                'name': trace_name, 'mode': lines_type}}}
    return setting


def show_edit_block(v):
    if v is not None and v != []:
        return {}
    return {'display': 'none'}


def show_settings_block(value):
    if value:
        if value % 2 != 0:
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
        self.val.append(
            ((Output('global-settings-panel', 'style'),
              [Input('btn-open-global-style', 'n_clicks')]),
             show_settings_block))
        self.val.append(
            ((Output('global-edit-block', 'style'),
              [Input('global-traces-selector', 'value')]), show_edit_block))

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

              [Input('global-figures-selector', 'value'),
               Input('global-traces-selector', 'value')],
              [State('global-input-trace-name', 'value'),
               State('global-lines-type', 'options'),
               State('global-lines-type', 'value')]), update_settings))
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
        self.val.append(
            ((Output('global-figures-selector', 'options'),
              [Input('btn-open-global-style', 'n_clicks')]), update_figures))
        self.val.append(
            ((Output('global-traces-selector', 'options'),
             [Input('global-figures-selector', 'value')]), update_traces))

