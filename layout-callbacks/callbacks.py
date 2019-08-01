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


def update_settings(selected_figure, selected_traces, options, value):
    if selected_traces is not None:
        for trace in selected_traces:
            trace_type = RW.dash()[selected_figure][trace]['type']
            if trace_type == 'scattergl':
                return {}, {}, [{'label': 'Маркеры', 'value': 'markers'},
                                {'label': 'Линии', 'value': 'lines'},
                                {'label': 'Маркеры и линии', 'value': 'lines+markers'}], 'lines+markers'
            else:
                return {'display': 'none'}, {'display': 'none'}, \
                       [{'label': 'Вертикальные столбцы', 'value': 'vertical'},
                        {'label': 'Горизонтальные столбцы', 'value': 'horizontal'}], 'vertical'
    return {'display': 'none'}, {'display': 'none'}, options, value


def save_settings_to_redis(n, settings):
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-save-global-style.n_clicks':
        try:
            settings[0].update({'dash-reload': True})
            RW.dash.set(settings[0])
        except:
            return [True, 'danger', 'Произошла ошибка при подключении к Resis. Настройки не сохранены']
        return [True, 'success', 'Настройки сохранены']
    return [False, 'success', '']


def put_to_storage(selected_figure, selected_traces, line_color, marker_color, line_width, marker_size, lines_type):
    settings_storage = []
    if selected_traces is not None:
        for i in range(0, len(selected_traces)):
            setting = {selected_figure: {'trace{}'.format(i):
                             {'line': {'color': line_color['rgb'], 'width':  line_width},
                             'marker': {'color': marker_color['rgb'], 'size': marker_size}, 'mode': lines_type}}}
            settings_storage.append(setting)
    return settings_storage


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
            ((Output('settings-storage', 'value'),
              [Input('global-figures-selector', 'value'),
               Input('global-traces-selector', 'value'),
               Input('global-color-picker-line', 'value'),
               Input('global-color-picker-marker', 'value'),
               Input('global-input-line-width', 'value'),
               Input('global-input-marker-size', 'value'),
               Input('global-lines-type', 'value')]), put_to_storage))
        self.val.append(
            (([Output('global-card-marker-color', 'style'),
               Output('global-card-marker-size', 'style'),
               Output('global-lines-type', 'options'),
               Output('global-lines-type', 'value')],
              [Input('global-figures-selector', 'value'),
               Input('global-traces-selector', 'value')],
              [State('global-lines-type', 'options'),
               State('global-lines-type', 'value')]), update_settings))
        self.val.append(
            (([Output('alert', 'is_open'),
               Output('alert', 'color'),
               Output('alert', 'children')],
              [Input('btn-save-global-style', 'n_clicks'),
               Input('settings-storage', 'value')]), save_settings_to_redis))
        self.val.append(
            ((Output('global-figures-selector', 'options'),
              [Input('btn-open-global-style', 'n_clicks')]), update_figures))
        self.val.append(
            ((Output('global-traces-selector', 'options'),
             [Input('global-figures-selector', 'value')]), update_traces))

