import dash_html_components as html
import dash_core_components as dcc
import dash_table


def scatter_table():
    return html.Div(children=[
        table(),
        dcc.Graph(id='scatter'),
        html.Hr(),
    ])


def bar_table():
    return html.Div(children=[
        table(),
        html.Hr(),
        dcc.Graph(id='bar'),
    ])


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
        dash_table.DataTable(id='table', page_current=0,
                             page_action='custom'),
        dcc.Input(id='page-size', type='number', value='5'),
        html.Div(id='div-out', style={'display': 'none'})
        ])
