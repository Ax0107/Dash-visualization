import base64
import io
import random

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import time

import pandas as pd

import flask

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

# Создание layout
app.layout = html.Div(children=[
    html.Div(children=[
            dcc.Graph(id='graph'),
            html.H4('Количество точек на графике:'),
            dcc.Slider(
                id='slider',
                min=0,
                max=1000,
                step=10,
                value=500,
                # generating marks for slider
                # makes marks in every 100 steps of slider
                marks=dict(zip([i for i in range(0, 1000, 100)], [str(i) for i in range(0, 1000, 100)]))
            ),
            html.Hr(),
            html.Button('Сгенерировать график рандомно', id='button', style={'width': "100%"}),
            html.Hr(),
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
                    multiple=True
                ),
            html.Hr(),
            dcc.Input(id='is_file_uploaded', value='0', style={'display': 'none'})
            ])
        ], style={'width': '70%', 'margin-left': '15%'})


def parse_contents(contents, filename):
    """
    Функция для парсинга CVS.
    :param contents: контент файла
    :param filename: имя файла
    :return: лист с значениями из CVS
    """
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            return df.to_dict('records')
    except Exception as e:
        print(e)
    return 1


@app.callback(Output('is_file_uploaded', 'value'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def set_file_uploaded_to_true(data, fn):
    if data:
        return '0'
    return '1'


@app.callback(Output('graph', 'figure'),
              [Input('slider', 'value'),
               Input('button', 'n_clicks'),
               Input('is_file_uploaded', 'value'),
               Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(count_of_points, n_clicks, is_file_uploaded, list_of_contents, list_of_names):
    """
    Функция для обновления графика.
    :param count_of_points: количество точек для генерации (рандомно)
    :param n_clicks: количество кликов на кнопку генерации
    :param is_file_uploaded: был ли загружен файл
    :param list_of_contents: переменная для получения файла (контект)
    :param list_of_names: переменная для получения файла (название)
    :return: график
    """
    # TODO: сделать сброс и рандомную генерацию графика после загрузки файла (сейчас просто не работает)
    if list_of_contents is not None and list_of_names is not None and bool(is_file_uploaded):
        content = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        points = [int(content[0][i]['1']) for i in range(0, len(content[0]))]
        return {
                'data': [{
                    'type': 'scatter',
                    'y': points
                }],
                'layout': {
                    'title': 'График (из файла)'
                }
        }
    return {
        'data': [{
            'type': 'scatter',
            'y': [random.randint(1, 10) for i in range(count_of_points)]
        }],
        'layout': {
            'title': 'График (сгенерированный)'
        }
    }


if __name__ == '__main__':
    app.run_server(debug=True)
