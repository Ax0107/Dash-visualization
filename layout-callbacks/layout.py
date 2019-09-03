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
        file_uploarer(),
        dash_table.DataTable(id='table', page_action='custom', page_current=0, editable=True),
        html.Div(id='div-out', style={'display': 'none'})
        ])


def table_info():
    return dbc.Card([
        dbc.CardBody([
            html.H4('Имя файла:'),
            html.A('', id='table-filename'),
            html.Hr(),
            html.H4('Размер страницы:'),
            dcc.Input(id='page-size', type='number', value='5', style={'display': 'none'}),
            html.Hr(),
            dcc.Input(id='new-column-name', placeholder='Введите имя нового столбца...', value=''),
            html.Button('Добавить новый столбец', id='btn-add-column', n_clicks=0),
            dbc.Button('Сохранить', id='btn-save-table', color='primary', style={'width': '100%'}),
            dcc.Checklist(id='table-save-all-checkbox',
                options=[
                    {'label': 'Сохрагить полностью', 'value': 'save-all'}]),
            html.Div(id='table-buttons', children=[]),
        ])
    ])

def layout():
    return html.Div([
        dbc.Row([
            dbc.Col([table()], width={"size": 8}),
            dbc.Col([table_info()], width={"size": 4}),
        ]),
        dbc.Button('Добавить новый график', id='btn-create-graph', color='primary', style={'width': "100%"}),
        dcc.Dropdown(id='graph-type',
                     options=[{'label': 'Scatter', 'value': 'scatter'},
                              {'label': 'Bar', 'value': 'bar'}],
                     value='scatter'),
        html.Div(id='created-graphs', style={'display': 'none'}),
        html.Div(id='graphs', children=[])
        ], style={'margin-left': '20%', 'margin-right': '20%'})


def row(*cols):
    cols_list = []
    for col in cols:
        cols_list.append(
            dbc.Col(col)
        )
    return dbc.Row(cols_list)


def work_card(global_id):
    cardd = dbc.Card([
            dbc.CardHeader([
                dbc.Button('X', id='button_delete-{}'.format(global_id),
                           color="primary", style={"float": "right"}),
            ]),
            dbc.CardBody([
                html.Div(id='graph-block-{}'.format(global_id), children=[
                    graph_table(global_id)
                ]),
            ]),
    ])

    return cardd


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


