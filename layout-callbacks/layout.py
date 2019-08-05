import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_daq


def card(id, card_header=None, card_body=None, style=None):
    card_obj = dbc.Card(id=id, children=[
        dbc.CardHeader([card_header], style={"text-align": "center"}),
        dbc.CardBody(card_body)],
        style=style)
    return card_obj


def color_picker(color_picker_type, graph_id=None, is_global=False):
    if is_global:
        return dash_daq.ColorPicker(
            id="global-color-picker-{}".format(color_picker_type),
            value={'hex': '#000000', 'rgb': {'r': 0, 'g': 0, 'b': 0, 'a': 1}})

    t = color_picker_type + '-picker-' + str(graph_id)
    return dash_daq.ColorPicker(
                    id=t,
                    value={'hex': '#000000', 'rgb': {'r': 0, 'g': 0, 'b': 0, 'a': 1}})


def param_input(input_type, graph_id=None, is_global=False):
    if is_global:
        return dcc.Input(id="global-input-{}".format(input_type),
                         type='number', value='3', style={'width': '100%'})
    # ex.: line-width-1
    i = input_type + '-' + str(graph_id)
    return dcc.Input(id=i, type='number', value='3', style={'width': '100%'})


def dropdown(dropdown_type, multi=False, graph_id=None, is_global=False):
    ids = {
        'mode': 'lines-type-{}'.format(graph_id),
        'traces': 'traces-selector-{}'.format(graph_id)
    }
    if is_global:
        ids = {'mode': 'global-lines-type',
               'figures': 'global-figures-selector',
               'stream': 'global-stream-selector',
               'figure-traces': 'global-visible-traces-selector',
               'traces': 'global-traces-selector',
               'type': 'global-figure-type-selector'}
    try:
        empty_dropdown = dcc.Dropdown(
            id=ids[dropdown_type],
            options=[],
            multi=multi
        )
        # TODO: Optimize memory in this dict
        dd = {
            'type': dcc.Dropdown(
                        id=ids[dropdown_type],
                        options=[{'label': 'scatter', 'value': 'scattergl'},
                                 {'label': 'bar', 'value': 'bar'}],
                        value='scattergl',
                        multi=multi
              ),
            'mode':
              dcc.Dropdown(
                        id=ids[dropdown_type],
                        options=[{'label': 'Маркеры', 'value': 'markers'},
                                 {'label': 'Линии', 'value': 'lines'},
                                 {'label': 'Маркеры и линии', 'value': 'lines+markers'}],
                        value='lines+markers',
                        multi=multi
              ),
            'stream': empty_dropdown,
            'figures': empty_dropdown,
            'figure-traces': empty_dropdown,
            'traces': empty_dropdown,
            }[dropdown_type]
    except KeyError:
        raise KeyError('KeyError Dropdown')
    return dd


def layout_settings_panel():
    return html.Div([
        dbc.Alert("Настройки успешно сохранены", id='alert', color="success", dismissable=True, is_open=False),
        dcc.Store(id='settings-storage', storage_type='local'),
        dcc.Input(id='is-setting-by-loading', value=0, style={'display': 'none'}),
        settings_panel()
        ], style={'width': '40%', 'margin-left': '30%'})


def settings_panel():
    cardd = dbc.Card([
            dbc.CardHeader([
                html.H3('Глобальные настройки')
            ]),
            dbc.CardBody([
                dbc.Button('Открыть/закрыть настройки стилей', id='btn-open-global-style',
                           color="secondary", style={"width": "100%"}),
                html.Div(id='global-settings-panel', style={'display': 'none'}, children=[
                    html.Hr(),
                    html.H5('График:'),
                    dropdown('figures', is_global=True),
                    dbc.Col([
                        dbc.Button('Добавить новый', id='create-graph',
                                   color='primary', style={"width": "50%", 'margin-top': '10px'}),
                        dbc.Button('Удалить', id='delete-graph',
                                   color='danger', style={"width": "50%", 'margin-top': '10px'}),
                    ]),
                    html.Hr(),
                    html.Div(id='children-figures', children=[
                        html.H5('Тип графика'),
                        dropdown('type', is_global=True),
                        html.Hr(),
                        html.H5('Поток:'),
                        dropdown('stream', is_global=True),
                        html.Hr(),
                        html.H5('Отображаемые данные:'),
                        dropdown('figure-traces', multi=True, is_global=True),
                        html.Hr(),
                        dbc.Card([
                            dbc.CardHeader([html.H4('Настройки графика')]),
                            dbc.CardBody([
                                dropdown('traces', is_global=True),
                                dbc.Row([
                                    dbc.Col([
                                        card('global-card-trace-name', 'Имя trace',
                                             dcc.Input(id="global-input-trace-name",
                                                       type='text', style={'width': '100%'})),
                                        dbc.Row([
                                            dbc.Col([
                                                card('global-card-line-color', 'Цвет линии', color_picker('line', is_global=True)),
                                                card('global-card-line-width', 'Ширина линии', param_input('line-width', is_global=True)),
                                            ]),
                                            dbc.Col([
                                                card('global-card-marker-color', 'Цвет маркера', color_picker('marker', is_global=True)),
                                                card('global-card-marker-size', 'Размер маркера', param_input('marker-size', is_global=True)),
                                            ]),
                                        ]),
                                    ])
                                ]),
                                # режим линии (маркер, маркеры+линия, линия)
                                card('card-line-type-selector', "Тип линии", dropdown('mode', is_global=True))
                            ]),

                            dbc.CardFooter([
                                dbc.Button('Сохранить', id='btn-save-global-style',
                                           color="primary", style={"width": "100%"}),
                            ])
                        ], id='global-edit-block')
                    ])
                ]),
            ]),
    ])

    return cardd

