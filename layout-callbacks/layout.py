import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_daq


def card(card_header=None, card_body=None, card_footer=None, style=None):
    card_obj = dbc.Card(children=
        [dbc.CardHeader([card_header], style={"text-align": "center"}),
         dbc.CardBody(card_body),
         dbc.CardFooter(card_footer)],
        style=style)
    return card_obj


def color_picker(color_picker_type, graph_id=None, is_global=False):
    if is_global:
        return dash_daq.ColorPicker(
            id="global-color-picker-{}".format(color_picker_type),
            label=color_picker_type,
            value={'hex': '#000000', 'rgb': {'r': 0, 'g': 0, 'b': 0, 'a': 1}})

    t = color_picker_type + '-picker-' + str(graph_id)
    return dash_daq.ColorPicker(
                    id=t,
                    label=color_picker_type,
                    value={'hex': '#000000', 'rgb': {'r': 0, 'g': 0, 'b': 0, 'a': 1}})


def param_input(input_type, graph_id=None, is_global=False):
    if is_global:
        return dcc.Input(id="global-input-{}".format(input_type),
                         type='number', value='3', style={'width': '100%'})
    # ex.: line-width-1
    i = input_type + '-' + str(graph_id)
    return dcc.Input(id=i, type='number', value='3', style={'width': '100%'})


def dropdown(dropdown_type, graph_id=None, is_global=False):
    if is_global:
        return {'mode':
                dcc.Dropdown(
                        id='global-lines-type',
                        options=[{'label': 'Маркеры', 'value': 'markers'},
                                 {'label': 'Линии', 'value': 'lines'},
                                 {'label': 'Маркеры и линии', 'value': 'lines+markers'}],
                        value='lines+markers'
                    ),
                'line': dcc.Dropdown(
                            id='global-line-selector',
                            options=[],
                            multi=True
                )}[dropdown_type]
    return {'mode':
            dcc.Dropdown(
                    id='lines-type-{}'.format(graph_id),
                    options=[{'label': 'Маркеры', 'value': 'markers'},
                             {'label': 'Линии', 'value': 'lines'},
                             {'label': 'Маркеры и линии', 'value': 'lines+markers'}],
                    value='lines+markers'
                ),
            'line': dcc.Dropdown(
                        id='line-selector-{}'.format(graph_id),
                        options=[],
                        multi=True
            )}[dropdown_type]


def row(*cols):
    cols_list = []
    for col in cols:
        cols_list.append(
            dbc.Col(col)
        )
    return dbc.Row(cols_list)


def layout_settings_panel():
    return html.Div([
        dbc.Alert("Настройки успешно сохранены", id='alert', color="success", dismissable=True, is_open=False),
        dcc.Store(id='settings-storage', storage_type='local'),
        settings_panel()
        ], style={'width': '30%'})


def settings_panel():
    cardd = dbc.Card([
            dbc.CardHeader([
                html.H3('Глобальные настройки')
            ]),
            dbc.CardBody([
                dbc.Button('Открыть/закрыть настройки стилей', id='btn-open-global-style',
                           color="secondary", style={"width": "100%"}),
                html.Div(id='global-settings-panel', style={'display': 'none'}, children=[
                    dropdown('line', is_global=True),
                    dbc.Row([
                        dbc.Col(html.Div([
                            color_picker('line', is_global=True),
                            param_input('line-width', is_global=True),
                            color_picker('marker', is_global=True),
                            param_input('marker-size', is_global=True),
                        ])),
                    ]),
                    # режим линии (маркер, маркеры+линия, линия)
                    card("Тип линии", dropdown('mode', is_global=True))
                ])
            ]),
            dbc.CardFooter([
                dbc.Button('Сохранить', id='btn-save-global-style',
                           color="primary", style={"width": "100%"}),
            ])
    ])

    return cardd

