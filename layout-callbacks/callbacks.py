from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.tools as tls
import base64
import io
import dash
from ast import literal_eval
import layout


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


def plot_bar_from_table(pointss, selected_bars, bar_color, bar_width, bar_type, figure, bar_selector_options):
    """
    Рисует Bar из выделенных данных таблицы
    :param pointss: dict полученный из div-out (см. table_load_selected)
    :return: bar-figure
    """
    print('POINTS!', pointss)
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
            print(points)
    return {
           'data': [
               {'x': points[i], 'y': points[i + 1], 'name': '', 'type': 'bar'} for i in range(0, len(points), 2)
           ],
           'layout': {
               'title': 'График (bar)'
           }
    }, style


def plot_scatter_from_table(pointss, selected_lines, line_color, line_width, marker_color, marker_size,
                            lines_type, figure, line_selector_options):
    """
    Рисует Scatter из выделенных данных в таблице-CSV
    :param pointss: dict полученный из div-out (см. table_load_selected)
    :return: graph-figure
    """
    # Проверяем, был ли triggered из-за изменение настроек графика
    if dash.callback_context.triggered[0]['prop_id'] not in 'div-out.children':
        # Преобразование цвета в строку типа "rgba(0,0,0,0)"
        try:
            line_color = line_color['hex']
            marker_color = marker_color['hex']
        except TypeError:
            line_color = line_color
            marker_color = marker_color
        return change_style_of_graph(selected_lines, line_color, line_width, marker_color, marker_size, lines_type, figure), {}, line_selector_options

    if pointss:
        # Дальше идёт преобразование данных к нужному типу
        pointss = literal_eval(pointss)
        columns = set([i['column'] for i in pointss])
        count = len(columns)

        # создаём лист типа {X: 0, Y: 1, Z: 2} (X,Y,Z - числа в таблице),
        # дабы при выделении в таблице данных не с нулевого столбца, мы могли обращаться к points
        # по индексу 0, 1, 2 и т.д. (иначе, столбец = индекс и ловим IndexError)
        columns = dict(zip(list(columns), list(range(0, count))))
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

        line_selector_options = []
        for v in range(0, len(points)):
            fig.append_trace({'y': points[v], 'type': 'scatter'}, 1, 1)
            line_selector_options.append({'label': v, 'value': v})
        fig['layout'].update(title='Graph')
        style = {}
        return fig, style, line_selector_options
    return {}, {'display': 'none'}, []


def change_style_of_graph(selected_lines, line_color, line_width, marker_color, marker_size, lines_type, figure):
    for i in selected_lines:
        try:
            figure['data'][i]['line'] = {'color': line_color, 'width': line_width}
            figure['data'][i]['mode'] = lines_type
            figure['data'][i]['marker'] = {'color': marker_color, 'size': marker_size}
        except IndexError:
            figure['data'][i].append({
                'line': {'color': line_color, 'width': line_width},
                'marker': {'color': marker_color, 'size': marker_size}
            }
            )
    return figure


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


def show_graph_block(value):
    if value == 'scatter':
        return {}
    elif value == 'bar':
        return {}
    else:
        return {'display': 'none'}


def show_edit_block(value):
    print(value)
    if value % 2 == 0:
        return {'display': 'none'}
    else:
        return {}


def create_graph(n_clicks, graph_type, graphs):
    if n_clicks:
        print(graphs)
        if graph_type == 'scatter':
            graph_callbacks = ScatterTable(n_clicks)
            if graphs is not None:
                graphs['props']['children'].append(layout.work_card(n_clicks))
            else:
                graphs = layout.work_card(n_clicks)

            return graphs
        return graphs

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


class BasicLayout(CallbackObj):
    def __init__(self):
        super().__init__()
        self.graphs = []
        self.val.append(
            ((Output('graphs', 'children'),
              [Input('btn-create-graph', 'n_clicks'),
               Input('graph-type', 'value')],
              [State('graphs', 'children')]), create_graph))


class Table(BasicLayout):
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
    def __init__(self, graph_id):
        super().__init__()
        self.id = graph_id
        self.val.append(
            ((Output('graph-block-{}'.format(self.id), 'style'),
              [Input('graph-type-{}'.format(self.id), 'value')]),
             show_graph_block))
        self.val.append(
            ((Output('graph-edit-{}'.format(self.id), 'style'),
              [Input('btn-open-style-{}'.format(self.id), 'n_clicks')]),
             show_edit_block))
        self.val.append(
            (([Output('graph-{}'.format(self.id), 'figure'),
               Output('graph-{}'.format(self.id), 'style'),
               # Output('line-selector-{}'.format(self.id), 'options')
               ],
              [Input('div-out', 'children'),
               Input('line-selector-{}'.format(self.id), 'value'),
               Input('line-color-picker-{}'.format(self.id), 'value'),
               Input('line-width-{}'.format(self.id), 'value'),
               Input('lines-type-{}'.format(self.id), 'value')],
              [State('graph-{}'.format(self.id), 'figure'),
               State('line-selector-{}'.format(self.id), 'options')]), plot_bar_from_table))


class ScatterTable(Table):
    def __init__(self, graph_id):
        super().__init__()
        self.id = graph_id
        self.val.append(
            ((Output('graph-edit-{}'.format(self.id), 'style'),
              [Input('btn-open-style-{}'.format(self.id), 'n_clicks')]),
             show_edit_block))
        self.val.append(
            (([Output('graph-{}'.format(self.id), 'figure'),
               Output('graph-{}'.format(self.id), 'style'),
               Output('line-selector-{}'.format(self.id), 'options')],
              [Input('div-out', 'children'),
               Input('line-selector-{}'.format(self.id), 'value'),
               Input('line-color-picker-{}'.format(self.id), 'value'),
               Input('line-width-{}'.format(self.id), 'value'),
               Input('marker-color-picker-{}'.format(self.id), 'value'),
               Input('marker-size-{}'.format(self.id), 'value'),
               Input('lines-type-{}'.format(self.id), 'value')],
              [State('graph-{}'.format(self.id), 'figure'),
               State('line-selector-{}'.format(self.id), 'options')]), plot_scatter_from_table))

