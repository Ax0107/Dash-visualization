from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.tools as tls
import base64
import io
import dash
import uuid
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
        return pd.read_csv(
               io.StringIO(decoded.decode('utf-8')))
    elif 'xls' in list_of_names[0]:
        return pd.read_excel(io.BytesIO(decoded))

    return None


# # # # # # # # Функции для отображения графиков # # # # # # # #


def table_load_selected(selected_rows, data):
    """
    Функция выводит в div-out данные о выделенных столбцах, дабы другие фунции могли
                                                                использовать эти данные
    :param data: данные таблицы
    :param selected_rows: выделенные клетки таблицы
    :return: children of div-out (строка(словарь с выделенными данными))
    """
    print('SELECTED ROWS', selected_rows)
    if data and selected_rows:
        d = []
        for i in range(0, len(selected_rows)):
            row = selected_rows[i]['row']
            column = selected_rows[i]['column_id']
            try:
                d.append({'column': selected_rows[i]['column'], 'row': row, 'data': data[row][column]})
            except KeyError:
                d.append({'column': selected_rows[i]['column'], 'row': row, 'data': None})
        return [str(d)]
    return ['']


def plot_bar_from_table(pointss, figure):
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


def plot_scatter_from_table(pointss, figure):
    """
    Рисует график из выделенных данных в CSV таблице
    :param pointss: точки, полученные из div-out
    :param figure: фигура графика
    :param line_selector_options: линии, которые возможно выделить (для dropdown)
    :return: новая фигура графика
    """
    print('pointss:', pointss)
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
        return fig
    return {}


def select_on_table_from_graph(points, table_data):
    if points:
        print(points)
        print(table_data)
        # d.append({'column': selected_rows[i]['column'], 'row': row, 'data': data[row][column]})
        # {'points': [
        # {'curveNumber': 0, 'pointNumber': 2, 'pointIndex': 2, 'x': 2, 'y': 2},
        # {'curveNumber': 1, 'pointNumber': 2, 'pointIndex': 2, 'x': 2, 'y': 10},
        # {'curveNumber': 2, 'pointNumber': 2, 'pointIndex': 2, 'x': 2, 'y': 2}]
        table_points = []
        possible_table_points = []
        for i in range(len(points.get('points', 0))):
            for it in range(len(table_data)):
                keys = list(table_data[it].keys())
                for jt in range(len(keys)):
                    if str(points['points'][i]['y']) == table_data[it][keys[jt]]:
                        if len(possible_table_points):
                            if possible_table_points[-1]['column'] in [jt+1, jt-1] \
                                    or possible_table_points[0]['row'] in [it+1, it-1]:
                                table_points.append(({'column': jt, 'row': it, 'column_id': keys[jt]}))
                                table_points.append(possible_table_points[0])
                        possible_table_points.append({'column': jt, 'row': it, 'column_id': keys[jt]})
                        break
        return table_points
    return []


def denormalize_csv(df):
    data = []
    keys = list(df.to_dict('records')[0].keys())
    key_string = 'values'
    for i in range(len(df.to_dict('records'))):
        values_string = ''
        for k in keys:
            value = df.to_dict('records')[i][k]
            values_string += value + ";"
        data.append({key_string: values_string})
    return pd.DataFrame(data)


def normalize_csv(df):
    # тут идут преобразования данных из таблицы из {'1;2': '1;2'} в {'1': '1', '2': '2'}
    #                                                                   из-за кривости считывания формата
    # print('Normalizing data: ', end='')
    if df.to_dict('records'):
        table_data = []

        keys = list(df.to_dict('records')[0].keys())
        splited_keys = keys[0].split(';')
        for i in range(0, len(df.to_dict('records'))):
            # if (len(df.to_dict('records'))//10) % (i+1) == 0:
            #     print('*', end='')
            a = {}
            data = df.to_dict('records')[i][keys[0]]
            if isinstance(data, str):
                data = data.split(';')
                for k in range(0, len(splited_keys)):
                    a.update({splited_keys[k]: data[k]})
            else:
                a.update({keys[0]: data})
            table_data.append(a)
        # print('\n')
        return pd.DataFrame(table_data)


def show_table(p_size, page, list_of_contents, n_clicks, value, existing_columns, existing_data, list_of_names):
    """
    Отображает таблицу из CSV файла
    :param p_size: количество строк на странице (получается из input p-size)
    :param page: текущая страница
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :return: table data
    """
    if n_clicks and dash.callback_context.triggered[0]['prop_id'] == 'btn-add-column.n_clicks':
        existing_columns.append({
            'id': str(len(existing_columns)+1), 'name': value,
            'deletable': True
        })
        return existing_columns, existing_data, list_of_names[0]
    if list_of_names is not None or (dash.callback_context.triggered[0]['prop_id'] == 'table.page_current' and page):
        # парсинг файла
        df = get_file(list_of_contents, list_of_names)
        df = df.iloc[page * int(p_size):(page + 1) * int(p_size)]
        if 'csv' in list_of_names[0]:
            df = normalize_csv(df)
        return [{"name": i, "id": i} for i in df.columns], df.to_dict('records'), list_of_names[0]
    return [], [], ''


def show_edit_block(value):
    if value:
        if value % 2 != 0:
            return {}
    return {'display': 'none'}


def show_page_slider(l):
    if l:
        return 'custom', 0, {}
    return 'none', 0, {'display': 'none'}


def create_graph(n_clicks, graph_type, created_graphs, graphs):
    """
    Функция добавляет новый график
    :param n_clicks: количество кликов на кнопку "добавить"
    :param graph_type: тип графика (scatter/bar etc.)
    :param created_graphs: количество созданныъ графиков по типам
    :param graphs: div с children - графиками
    :return: layout с новым добавленным графиком
    """
    # Изначально graph_id = n_clicks
    graph_id = n_clicks
    # print(dash.callback_context.triggered[0]['prop_id'])
    if dash.callback_context.triggered[0]['prop_id'] == 'created-graphs.children':
        if n_clicks:
            # Меняем graph_id и выдаём  взависимости от типа графика
            if graph_type == 'scatter':
                if created_graphs:
                    graph_id = int(literal_eval(created_graphs)['scatter'])
            elif graph_type == 'bar':
                if created_graphs:
                    graph_id = 11 + int(literal_eval(created_graphs)['bar'])

            if graphs is not None and not isinstance(graphs, list):
                graphs['props']['children'].append(layout.work_card(graph_id))
            else:
                graphs = layout.work_card(graph_id)
    return graphs


def set_created_graphs(n_clicks, graph_type, created_graphs):
    """
    Функция обновляет значчения created_graphs
    :param n_clicks: неиспользуемая переменная (предназначена для получения callback'а)
    :param graph_type: тип графика
    :param created_graphs: state created_graphs
    :return: изменённыый created_graphs
    """
    if dash.callback_context.triggered[0]['prop_id'] == 'btn-create-graph.n_clicks':
        # print(created_graphs)
        if created_graphs is not None:
            try:
                n = int(literal_eval(created_graphs)[graph_type]) + 1
                created_graphs = literal_eval(created_graphs)
                created_graphs.update({graph_type: n})
            except KeyError or TypeError:
                created_graphs = literal_eval(created_graphs)
                created_graphs.update({graph_type: 1})
            return str(created_graphs)
        return str({graph_type: 1})
    return created_graphs


def download_table(n, df, save_options, file_content, file_name, p_size, page):
    if df is None or not n:
        return [layout.build_download_button()]
    df = pd.DataFrame(df)
    if save_options and 'save-all' in save_options:
        df_file = get_file(file_content, file_name)
        if 'csv' in file_name[0]:
            df = denormalize_csv(df)
            for j in range(int(p_size)):
                df_file.iloc[int(p_size)*int(page)+j] = df.to_dict('records')[j]['values']
        else:
            for j in range(int(p_size)):
                df_file.iloc[int(p_size)*int(page)+j] = df.to_dict('records')[j]
        df = normalize_csv(df_file)

    print(df.to_dict('records'))
    filename = f"{uuid.uuid1()}"
    path = f".\\files\\{filename}.csv"
    df.to_csv(path, sep=';', index=None, header=True)
    return [layout.build_download_button(path)]


# # # # # # # # Классы Callback # # # # # # # #


class Callbacks(object):
    def __init__(self, name, graph_id):
        self.name = name
        self.graph_id = graph_id

    def __call__(self):
        return globals()[self.name](self.graph_id)()


class CallbackObj(object):
    def __init__(self, **kwargs):
        self.val = []

    def __call__(self):
        return self.val


class BasicLayout(CallbackObj):
    def __init__(self, id):
        super().__init__()
        self.graphs = []
        self.id = id
        self.val.append(
            ((Output('graphs', 'children'),
              [Input('btn-create-graph', 'n_clicks'),
               Input('graph-type', 'value'),
               Input('created-graphs', 'children')],
              [State('graphs', 'children')]), create_graph))
        self.val.append(
            ((Output('created-graphs', 'children'),
              [Input('btn-create-graph', 'n_clicks'),
               Input('graph-type', 'value')],
              [State('created-graphs', 'children')]), set_created_graphs))


class Table(CallbackObj):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.val.append(
            (([Output('table', 'page_action'), Output('table', 'page_current'),
               Output('page-size', 'style')],
              [Input('upload-data', 'contents')]), show_page_slider))
        self.val.append(
            (([Output('table', 'columns'), Output('table', 'data'), Output('table-filename', 'children')],
              [Input('page-size', 'value'),
               Input('table', "page_current"),
               Input('upload-data', 'contents'),
               Input('btn-add-column', 'n_clicks')],
              [State('new-column-name', 'value'),
               State('table', 'columns'),
               State('table', 'data'),
               State('upload-data', 'filename')]), show_table))
        self.val.append(
            (([Output('div-out', 'children')],
             [Input('table', 'selected_cells')],
             [State('table', 'data')]),
             table_load_selected))
        self.val.append(
            ((Output('table-buttons', 'children'),
             [Input('btn-save-table', 'n_clicks')],
             [State('table', 'data'),
              State('table-save-all-checkbox', 'value'),
              State('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('page-size', 'value'),
              State('table', 'page_current'),
              ]), download_table))


class ScatterTable(CallbackObj):
    def __init__(self, graph_id):
        super().__init__()
        self.id = graph_id
        self.val.append(
            ((Output('graph-{}'.format(self.id), 'figure'),
              [Input('div-out', 'children')],
              [State('graph-{}'.format(self.id), 'figure')]), plot_scatter_from_table))
        self.val.append(
            ((Output('table', 'selected_cells'),
             [Input('graph-{}'.format(self.id), 'selectedData')],
              [State('table', 'data')]), select_on_table_from_graph))

class BarTable(CallbackObj):
    def __init__(self, graph_id):
        super().__init__()
        self.id = graph_id
        self.val.append(
            ((Output('graph-edit-{}'.format(self.id), 'style'),
              [Input('btn-open-style-{}'.format(self.id), 'n_clicks')]),
             show_edit_block))
        self.val.append(
            ((Output('graph-{}'.format(self.id), 'figure'),
              [Input('div-out', 'children')],
              [State('graph-{}'.format(self.id), 'figure')]), plot_bar_from_table))

