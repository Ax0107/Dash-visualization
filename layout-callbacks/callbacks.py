from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.tools as tls
import base64
import io
import dash
from ast import literal_eval


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


def get_file(list_of_contents, list_of_names):
    """
    Вспомогательная функция для чтения CSV
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :return: pandas data
    """
    content_type, content_string = list_of_contents[0].split(',')
    decoded = base64.b64decode(content_string)
    if 'csv' in list_of_names[0]:
        df = pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
        return df
    return None


# # # # # # # # Функции для отображения графиков # # # # # # # #


def table_load_selected(data, selected_rows):
    """
    Функция выводит в div-out данные о выделенных столбцах, дабы другие фунции могли
                                                                использовать эти данные
    :param data: данные таблицы
    :param selected_rows: выделенные клетки таблицы
    :return: children of div-out (строка(словарь с выделенными данными))
    """
    if data and selected_rows:
        d = []
        for i in range(0, len(selected_rows)):
            row = selected_rows[i]['row']
            column = selected_rows[i]['column_id']
            d.append({'column': selected_rows[i]['column'], 'row': row, 'data': data[row][column]})
        return [str(d)]
    return ['']


def plot_bar_from_table(pointss):
    """
    Рисует Bar из выделенных данных таблицы
    :param pointss: dict полученный из div-out (см. table_load_selected)
    :return: bar-figure
    """
    style = {'display': 'none'}
    points = [[0], [0]]
    if pointss:
        # Дальше идёт преобразование данных к нужному типу
        pointss = literal_eval(pointss)
        columns = set([i['column'] for i in pointss])
        count = len(columns)

        # создаём лист типа {X: 0, Y: 1, Z: 2},
        # дабы при выделении в таблице данных не с нулевого столбца, мы могли обращаться к points
        # по индексу 0, 1, 2 и т.д. (иначе, столбец = индекс)
        columns = dict(zip(list(columns), list(range(0,count))))
        if count % 2 == 0:
            points = [[]]
            for i in pointss:
                try:
                    points[columns[i['column']]].append(i['data'])
                except IndexError:
                    points.append([])
                    points[columns[i['column']]].append(i['data'])
            style = {}
    return {
           'data': [
               {'x': points[i], 'y': points[i + 1], 'name': '', 'type': 'bar'} for i in range(0, len(points), 2)
           ],
           'layout': {
               'title': 'График (bar)'
           }
    }, style


def plot_scatter_from_table(pointss):
    """
    Рисует Scatter из выделенных данных таблицы
    :param pointss: dict полученный из div-out (см. table_load_selected)
    :return: scatter-figure
    """
    style = {'display': 'none'}
    points = [0]
    if pointss:
        # Дальше идёт преобразование данных к нужному типу
        pointss = literal_eval(pointss)
        columns = set([i['column'] for i in pointss])
        count = len(columns)

        # создаём лист типа {X: 0, Y: 1, Z: 2} (X,Y,Z - числа в таблице),
        # дабы при выделении в таблице данных не с нулевого столбца, мы могли обращаться к points
        # по индексу 0, 1, 2 и т.д. (иначе, столбец = индекс и ловим IndexError)
        columns = dict(zip(list(columns), list(range(0, count))))
        if 1:
            points = []
            for i in pointss:
                try:
                    points[columns[i['column']]].append(i['data'])
                except IndexError:
                    points.append([])
                    points[columns[i['column']]].append(i['data'])
            fig = tls.make_subplots(rows=1, cols=1, shared_yaxes=True, shared_xaxes=True, vertical_spacing=0.009,
                                    horizontal_spacing=0.009)
            fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 50, 't': 25}
            for v in points:
                fig.append_trace({'y': v, 'type': 'scatter'}, 1, 1)
            fig['layout'].update(title='Graph')
            style = {}
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


def show_table(p_size, page, list_of_contents, list_of_names):
    """
    Отображает таблицу из CSV файла
    :param p_size: количество строк на странице (получается из input p-size)
    :param page: текущая страница
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :return: table data
    """
    if list_of_names is not None or dash.callback_context.triggered == 'table.page_current':
        # парсинг файла
        df = get_file(list_of_contents, list_of_names)
        df = df.iloc[page * int(p_size):(page + 1) * int(p_size)]

        table_data = []
        # тут идут преобразования данных из таблицы из {'1;2': '1;2'} в {'1': '1', '2': '2'}
        #                                                                   из-за кривости считывания
        for i in range(0, len(df.to_dict('records'))):
            keys = list(df.to_dict('records')[i].keys())
            a = {}
            data = df.to_dict('records')[i][keys[0]]
            if not isinstance(data, int):
                data = data.split(';')
                for k in range(0, len(keys[0].split(';'))):
                    a.update({keys[0].split(';')[k]: data[k]})
            else:
                a.update({keys[0]: data})
            table_data.append(a)

        return [{"name": i, "id": i} for i in df.columns[0].split(';')], table_data
    return [], []


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


class Table(CallbackObj):
    def __init__(self):
        super().__init__()
        self.val.append(
            (([Output('table', 'columns'), Output('table', 'data')],
              [Input('page-size', 'value'),
               Input('table', "page_current"),
               Input('upload-data', 'contents')],
              [State('upload-data', 'filename')]), show_table))
        self.val.append(
            (([Output('div-out', 'children')],
             [Input('table', 'data'),
              Input('table', 'selected_cells')]),
             table_load_selected))


class BarTable(Table):
    def __init__(self):
        super().__init__()
        self.val.append(
            (([Output('bar', 'figure'), Output('bar', 'style')],
              [Input('div-out', 'children')]), plot_bar_from_table))


class ScatterTable(Table):
    def __init__(self):
        super().__init__()
        self.val.append(
            (([Output('scatter', 'figure'), Output('scatter', 'style')],
              [Input('div-out', 'children')]), plot_scatter_from_table))
