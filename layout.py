import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
import dash_daq


def graph_table(graph_id):
    return html.Div(children=[
        dcc.Graph(id='graph-{}'.format(graph_id)),
    ])


def card(card_header=None, card_body=None, card_footer=None, style=None):
    card_obj = dbc.Card(children=
        [dbc.CardHeader([card_header], style={"text-align": "center"}),
         dbc.CardBody(card_body),
         dbc.CardFooter(card_footer)],
        style=style)
    return card_obj


def color_picker(color_picker_type, graph_id):
    # ex.: line-color-1
    t = color_picker_type + '-picker-' + str(graph_id)
    return dash_daq.ColorPicker(
                    id=t,
                    label=color_picker_type,
                    value='#119DFF')


def param_input(input_type, graph_id):
    # ex.: line-width-1
    i = input_type + '-' + str(graph_id)
    return dcc.Input(id=i, type='number', value='3', style={'width': '100%'})


def dropdown(dropdown_type, graph_id):
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


def file_uploarer():
    return html.Div(children=[
            html.H4('Загрузить таблицу CVS', style={'textAlign': 'center'}),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Перетащите файл сюда или ',
                    html.A('выберите его')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                },
                multiple=True,
            )
        ])


def table():
    return html.Div(children=[
        dash_table.DataTable(id='table', page_action='custom', page_current=0, editable=True),
        html.Div(id='div-selected-data', style={'display': 'none'})
        ])


def table_info():
    return dbc.Card([
        dbc.CardBody([
            html.H4('Имя файла:'),
            html.A('', id='table-filename'),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H4('Размер страницы:'),
                    dcc.Input(id='page-size', type='number', value='5',
                              style={'display': 'none', 'height': '40px'}),
                ]),
                dbc.Col([
                    dbc.Button('next', id='table-next', n_clicks=0,
                               style={'width': '100%', 'height': '40px'}),
                    dbc.Button('previous', id='table-previous', n_clicks=0,
                               style={'width': '100%', 'height': '40px'}),
                ]),
            ]),

            html.Hr(),
            dcc.Checklist(id='show_selected_on_graph',
                          options=[
                              {'label': 'Отображать выбранное на графике', 'value': 'yes'}]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dcc.Input(id='new-column-name', placeholder='Введите имя нового столбца...', value='',
                              style={'width': '90%', 'height': '40px'})
                ]),
                dbc.Col([
                    dbc.Button('Добавить новый столбец', id='btn-add-column', n_clicks=0,
                               style={'width': '100%', 'height': '40px'}),
                ]),
            ], no_gutters=True),
            html.Hr(),
            dbc.Button('Сохранить', id='btn-save-table', color='primary', style={'width': '100%'}),
            dcc.Checklist(id='table-save-all-checkbox',
                          options=[
                                {'label': 'Сохрагить полностью', 'value': 'save-all'}]),
            html.Div(id='table-buttons', children=[]),
            html.Hr(),
            dbc.Button('Сбросить выделенное',
                       id='btn-reset-selected',
                       color='secondary', style={'width': '100%'})
        ])
    ], id='table-info', style={'display': 'none'})


def layout():
    return html.Div([
            html.Div(id='background', children=[
                dbc.NavbarSimple(
                    children=[
                        dbc.NavItem(dbc.Button('Загрузить',
                                               id='btn-open-upload-block',
                                               color='primary', style={'float': 'right', 'marginRight': '30%'})),
                        dbc.NavItem(dbc.Button('Добавить новый график',
                                               id='btn-create-graph',
                                               color='primary', style={'float': 'left', 'marginLeft': '10px'})),
                        dbc.NavItem(dbc.Button('Добавить отображение',
                                               id='btn-add-trace',
                                               color='secondary', style={'float': 'left', 'marginLeft': '20px'})),
                    ], style={'margin': '10px', 'width': '100%', 'height': '50px'}),
                html.Div(id='created-graphs', style={'display': 'none'}),
                dbc.Row(id='graphs', children=[], no_gutters=True,),
                dbc.Row([
                    dbc.Col([table()], width={"size": 8}),
                    dbc.Col([table_info()], width={"size": 4}),
                ]),
            ]),
            dbc.Card([
                dbc.CardBody([
                    dbc.Checklist(
                        options=[
                            {"label": "Использовать первую строку, как заголовки", "value": 1},
                        ],
                        value=[1],
                        id="first-column-as-headers",
                    ),
                    html.Hr(),
                    dbc.Label('Разделитель:'),
                    dbc.Input(id='separator', value=';', type="text"),
                    file_uploarer()
                ])
            ], id='upload-block'),
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(id='graph-type',
                                 options=[{'label': 'Scatter', 'value': 'scatter'},
                                          # {'label': 'Bar', 'value': 'bar'}
                                          ],
                                 value='scatter'),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([dbc.Label('X:')]),
                        dbc.Col([
                            dcc.Dropdown(
                                id='columns-x-selector',
                                options=[],
                                value=[],
                                multi=False
                            )
                        ]),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([dbc.Label('Y:')]),
                        dbc.Col([
                            dcc.Dropdown(
                                id='columns-y-selector',
                                options=[],
                                value=[],
                                multi=True
                            )
                        ]),
                    ]),

                ])
            ], id='new-trace-block'),
        ])


def work_card(global_id):
    def get_style():
        return {'width': '30%'}
    cardd = dbc.Card([
            dbc.CardHeader([
                dbc.Button('X', id='btn-delete-{}'.format(global_id),
                           color="primary", style={"float": "right"}),
            ]),
            dbc.CardBody([
                html.Div(id='graph-block-{}'.format(global_id), children=[
                    graph_table(global_id)
                ]),
            ]),
    ], id='graph-card-{}'.format(global_id))

    return dbc.Col(cardd, style=get_style())


def bar_table():
    return html.Div(children=[
        table(),
        html.Hr(),
        dcc.Graph(id='bar'),
    ])


def build_download_button(uri=None):
    """Generates a download button for the resource"""
    if uri:
        button = html.Form(
            action='/download/'+uri,
            method="get",
            children=[
               html.Button('Загрузить', type='submit'),
            ]
        )
        return button


