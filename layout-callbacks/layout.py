import dash_html_components as html
import dash_core_components as dcc


def scatter_file():
    return html.Div(children=[
        dcc.Graph(id='scatter'),
        html.Hr(),
        file_uploarer()
    ])


def bar_file():
    return html.Div(children=[
        dcc.Graph(id='bar'),
        html.Hr(),
        file_uploarer()
    ])


def file_uploarer():
    return html.Div(children=[
            html.H4('Нарисовать график из файла CVS', style={'textAlign': 'center'}),
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
                multiple=True)

        ])
