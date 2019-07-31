from dash.dependencies import Input, Output, State
import dash

# # # # # # # # Функции для отображения графиков # # # # # # # #

def save_settings_to_redis(n, settings):
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-save-global-style.n_clicks':
        print(settings)
        return [True, 'success', 'Настройки сохранены']
    return [False, 'success', '']


def put_to_storage(line_color, marker_color, line_width, marker_size):
    settings_storage = [{'line': {'color': line_color['rgb'], 'width':  line_width},
                         'marker': {'color': marker_color['rgb'], 'size': marker_size}}]
    return settings_storage


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
            ((Output('settings-storage', 'value'),
              [Input('global-color-picker-line', 'value'),
               Input('global-color-picker-marker', 'value'),
               Input('global-input-line-width', 'value'),
               Input('global-input-marker-size', 'value')]), put_to_storage))
        self.val.append(
            (([Output('alert', 'is_open'),
               Output('alert', 'color'),
               Output('alert', 'text')],
              [Input('btn-save-global-style', 'n_clicks'),
               Input('settings-storage', 'value')]), save_settings_to_redis))
