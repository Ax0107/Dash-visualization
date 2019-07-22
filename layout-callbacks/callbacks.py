from dash.dependencies import Input, Output, State
import pandas as pd
import numpy as np
import plotly.tools as tls
import base64
import io


def parse_contents(contents, filename):
    """
    Вспомогательная функция для парсинга CVS.
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


# # # # # # # # Функции для отображения графиков # # # # # # # #


def plot_bar_from_file(list_of_contents, list_of_names):
    style = {'display': 'none'}
    points = [[0, 0], [0, 0]]
    if list_of_names is not None:
        # парсинг файла
        content = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        # заголовки CSV
        titles = list(content[0][0].keys())[0]
        # Если количество заголовков для X-axis совпадает с Y-axis
        if len(titles.split(';')) % 2 == 0:
            # Проходимся по content, сплитим данные по ; и потом транспонируем,
            # дабы получить массивы для каждой компоненте
            points = np.array([np.array(item[titles].split(';')).astype('int64') for item in content[0]]).transpose()
            style = {}
    return {
        'data': [
            {'x': points[i], 'y': points[i+1], 'name': '', 'type': 'bar'} for i in range(0, len(points), 2)
        ],
        'layout': {
            'title': 'График (из файла)'
        }
    }, style


def plot_scatter_from_file(list_of_contents, list_of_names):
    style = {'display': 'none'}
    points = [0]
    if list_of_names is not None:
        # парсинг файла
        content = [
            parse_contents(c, n) for c, n in
            zip(list_of_contents, list_of_names)]
        # заголовки CSV
        titles = list(content[0][0].keys())[0]
        if len(titles.split(';')) == 1:
            # Проходимся по content, получаем данные
            points = np.array([item[titles] for item in content[0]])
            style = {}
        else:
            # Проходимся по content, сплитим данные по ; и потом транспонируем,
            # дабы получить массивы для каждой компоненте
            points = np.array([np.array(item[titles].split(';')).astype('int64') for item in content[0]]).transpose()
            style = {}

            fig = tls.make_subplots(rows=1, cols=1, shared_yaxes=True, shared_xaxes=True, vertical_spacing=0.009,
                                    horizontal_spacing=0.009)
            fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 50, 't': 25}
            for v in points:
                fig.append_trace({'y': v, 'type': 'scatter'}, 1, 1)
            fig['layout'].update(title='Graph')
            return fig, style
    return {
        'data': [{
            'type': 'scatter',
            'y': points
        }],
        'layout': {
            'title': 'График (из файла)'
        }
    }, style


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


class ScatterFile(CallbackObj):
    def __init__(self):
        super().__init__()
        self.val.append(
            (([Output('scatter', 'figure'), Output('scatter', 'style')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')]), plot_scatter_from_file))


class BarFile(CallbackObj):
    def __init__(self):
        super().__init__()
        self.val.append(
            (([Output('bar', 'figure'), Output('bar', 'style')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')]), plot_bar_from_file))
