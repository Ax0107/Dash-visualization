from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.tools as tls
import base64
import io
import dash
import uuid
from math import isnan, nan
from ast import literal_eval
import layout


def get_file(list_of_contents, list_of_names, first_column_as_headers, separator):
    """
    Вспомогательная функция для чтения CSV
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :return: pandas data
    """

    content_type, content_string = list_of_contents[0].split(',')
    decoded = base64.b64decode(content_string)

    if 'csv' in list_of_names[0]:
        if first_column_as_headers:
            return pd.read_csv(
                   io.StringIO(decoded.decode('utf-8')),
                   sep=separator, header=0)
        else:
            return pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                sep=separator)
    elif 'xls' in list_of_names[0]:
        if first_column_as_headers:
            return pd.read_excel(io.BytesIO(decoded), header=0)
        else:
            return pd.read_excel(io.BytesIO(decoded))

    return None


# # # # # # # # Функции для отображения графиков # # # # # # # #


def table_load_selected(selected_rows, content, filename, f_header, separator, show_selected_on_graph):
    """
    Функция выводит в div-out данные о выделенных столбцах, дабы другие фунции могли
                                                                использовать эти данные
    :param data: данные таблицы
    :param selected_rows: выделенные клетки таблицы
    :return: children of div-out (строка(словарь с выделенными данными))
    """
    if content and selected_rows and show_selected_on_graph:
        df = get_file(content, filename, f_header, separator)

        data = df.to_dict('records')
        d = []
        for i in range(0, len(selected_rows)):
            row = selected_rows[i]['row']
            column = selected_rows[i]['column_id']
            value = data[row][column]
            try:
                d.append({'column': selected_rows[i]['column'], 'row': row, 'data': value})
            except KeyError:
                d.append({'column': selected_rows[i]['column'], 'row': row, 'data': None})
            except IndexError:
                pass
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


def plot_scatter(pointss, filecontent, x_column, y_column, graph_type, filename, f_header, separator, figure):
    """
    Рисует график из выделенных данных в CSV таблице
    :param pointss: точки, полученные из div-out
    :param figure: фигура графика
    :param line_selector_options: линии, которые возможно выделить (для dropdown)
    :return: новая фигура графика
    """
    graph_exec = 0
    df = get_file(filecontent, filename, f_header, separator)
    if pointss and dash.callback_context.triggered[0]['prop_id'] == 'div-out.children':
        graph_exec = 1
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
                try:
                    points.append([])
                    points[columns[i['column']]].append(i['data'])
                except IndexError:
                    pass

    elif y_column:
        graph_exec = 2
        points = []
        for i in range(len(y_column)):
            points.append(df[y_column[i]])

    if graph_exec:
        fig = tls.make_subplots(rows=1, cols=1, shared_yaxes=True, shared_xaxes=True, vertical_spacing=0.009,
                                horizontal_spacing=0.009)
        fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 50, 't': 25}
        trace = {}
        if graph_exec == 2:
            for i in range(len(y_column)):
                if x_column:
                    trace['x'] = df[x_column].to_list()
                if y_column:
                    trace['y'] = df[y_column[i]].to_list()
                trace['type'] = graph_type
                fig.append_trace(trace, 1, 1)
        elif graph_exec == 1:
            for i in range(len(points)):
                trace['y'] = points[i]
                trace['type'] = graph_type
                fig.append_trace(trace, 1, 1)
        fig['layout'].update(title='Graph', clickmode='event+select')
        return fig

    elif figure:
        return figure

    return {}


def select_on_table_from_graph(points, table_data, y_column, x_column):
    if points:
        # {'curveNumber': 0, 'pointNumber': 2, 'pointIndex': 2, 'x': 2, 'y': 2},
        table_points = []
        keys = list(table_data[0].keys())
        for i in range(len(points.get('points', 0))):
            shift = 0
            trace_num = points['points'][i]['curveNumber']
            column_id = keys[trace_num]
            column = trace_num
            if y_column:
                column_id = y_column[trace_num % len(y_column)]
                column = [i for i in range(len(keys)) if keys[i] == column_id][0]
            point_index = points['points'][i]['pointIndex']
            print(column, column_id, point_index)
            table_points.append({'column': column, 'row': point_index, 'column_id': column_id})
        return table_points
    return []


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


def show_table(n_open_upload, p_size, page, n_clicks, list_of_contents, list_of_names,
               value, existing_columns, existing_data,
               first_column_as_headers, separator):
    """
    Отображает таблицу из CSV файла
    :param n_open_upload: обработчик нажатия кнопки для открытия блока загрузки файла
    :param p_size: количество строк на странице (получается из input p-size)
    :param page: текущая страница
    :param n_clicks: обработчик нажатия кнопки для добавления новой колонки в таблицу
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :param value: название новой колонки
    :param existing_columns: колонки таблицы
    :param existing_data: данные табницы
    :param first_column_as_headers: использовать ли первую строку, как заголовок
    :param separator: разделитель для загрузки файла
    :return: table data
    """
    def get_style_upload_block(is_invisible=False):
        # # # Getting style for upload block # # #
        if is_invisible:
            return {'display': 'none'}
        else:
            return {'width': '60rem'}

    if n_open_upload and dash.callback_context.triggered[0]['prop_id'] == 'btn-open-upload-block.n_clicks':
        # TODO: Blackout for background when open block
        return [], [], '', {'display': 'none'}, get_style_upload_block(False)
    if n_clicks and dash.callback_context.triggered[0]['prop_id'] == 'btn-add-column.n_clicks':
        existing_columns.append({
            'id': value, 'name': value,
            'deletable': True
        })
        return existing_columns, existing_data, list_of_names[0], {}, get_style_upload_block(True)
    if list_of_names is not None or (dash.callback_context.triggered[0]['prop_id'] == 'table.page_current' and page):
        if first_column_as_headers and 1 in first_column_as_headers:
            first_column_as_headers = 1
        else:
            first_column_as_headers = 0
        if not separator:
            separator = ';'
        # парсинг файла
        df = get_file(list_of_contents, list_of_names, first_column_as_headers, separator)
        df = df.iloc[page * int(p_size):(page + 1) * int(p_size)]
        return [{"name": i, "id": i} for i in df.columns], df.to_dict('records'), \
                                                                list_of_names[0], {}, get_style_upload_block(True)
    return [], [], '', {'display': 'none'}, get_style_upload_block(True)


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
    Функция добавляет/удаляет график
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
            # Меняем graph_id взависимости от количества графиков этого типа
            if graph_type == 'scatter':
                if created_graphs:
                    graph_id = int(literal_eval(created_graphs)['scatter'])
            elif graph_type == 'bar':
                if created_graphs:
                    graph_id = 11 + int(literal_eval(created_graphs)['bar'])
            print(graphs)
            if graphs is not None:
                if not isinstance(graphs, list):
                    graphs = [graphs].append(layout.work_card(graph_id))
                else:
                    graphs.append(layout.work_card(graph_id))
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


def download_table(n, df, save_options, file_content, file_name, first_column_as_headers, separator, p_size, page):
    if df is None or not n:
        return [layout.build_download_button()]
    df = pd.DataFrame(df)
    if save_options and 'save-all' in save_options:
        if first_column_as_headers and 1 in first_column_as_headers:
            first_column_as_headers = 1
        else:
            first_column_as_headers = 0
        if not separator:
            separator = ';'
        df_file = get_file(file_content, file_name, first_column_as_headers, separator)
        print('Dic', df_file.to_dict('records'))

        columns_file = list(df_file.columns)
        columns_table = list(df.columns)
        if columns_file != columns_table:
            if len(columns_file) < len(columns_table):
                for i in range(len(columns_file), len(columns_table)):
                    df_file[columns_table[i]] = [None] * len(df_file)

        for j in range(int(p_size)):
            df_file.iloc[int(p_size)*int(page)+j] = df.to_dict('records')[j]
        df = df_file
    df = df.where((pd.notnull(df)), None)  # changing Nan values
    print(df.to_dict('records'))
    filename = f"{uuid.uuid1()}"
    path = f".\\files\\{filename}.csv"
    df.to_csv(path, sep=';', index=None, header=True)
    return [layout.build_download_button(path)]


def update_columns_in_new_trace_block(content, filename, f_header, separator):
    if content:
        # TODO: remove values that already selected in other selector options (needed, 'cuz options equal)
        df = get_file(content, filename, f_header, separator)
        columns = [{"label": i, "value": i} for i in df.columns]
        return columns, columns
    return [], []


def open_new_trace_block(n):
    if n:
        return {'width': '60rem'}
    return {'display': 'none'}


def delete_graph(n, style):
    if n:
        return {'display': 'none'}
    if style:
        return style
    return {}

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
        self.val.append(
            (([Output('columns-x-selector', 'options'), Output('columns-y-selector', 'options')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('first-column-as-headers', 'value'),
               State('separator', 'value')]), update_columns_in_new_trace_block))
        self.val.append(
            ((Output('new-trace-block', 'style'),
              [Input('btn-add-trace', 'n_clicks')]), open_new_trace_block))

class Table(CallbackObj):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.val.append(
            (([Output('table', 'page_action'), Output('table', 'page_current'),
               Output('page-size', 'style')],
              [Input('upload-data', 'contents')]), show_page_slider))
        self.val.append(
            (([Output('table', 'columns'), Output('table', 'data'), Output('table-filename', 'children'),
               Output('table-info', 'style'), Output('upload-block', 'style')],
              [Input('btn-open-upload-block', 'n_clicks'),
               Input('page-size', 'value'),
               Input('table', "page_current"),
               Input('btn-add-column', 'n_clicks'),
               Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('new-column-name', 'value'),
               State('table', 'columns'),
               State('table', 'data'),
               State('first-column-as-headers', 'value'),
               State('separator', 'value')]), show_table))
        self.val.append(
            (([Output('div-out', 'children')],
             [Input('table', 'selected_cells')],
             [State('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('first-column-as-headers', 'value'),
              State('separator', 'value'),
              State('show_selected_on_graph', 'value')]),
             table_load_selected))
        self.val.append(
            ((Output('table-buttons', 'children'),
             [Input('btn-save-table', 'n_clicks')],
             [State('table', 'data'),
              State('table-save-all-checkbox', 'value'),
              State('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('first-column-as-headers', 'value'),
              State('separator', 'value'),
              State('page-size', 'value'),
              State('table', 'page_current'),
              ]), download_table))


class ScatterTable(CallbackObj):
    def __init__(self, graph_id):
        super().__init__()
        self.id = graph_id
        self.val.append(
            ((Output('graph-{}'.format(self.id), 'figure'),
              [Input('div-out', 'children'),
               Input('upload-data', 'contents'),
               Input('columns-x-selector', 'value'),
               Input('columns-y-selector', 'value')],
              [State('graph-type', 'value'),
               State('upload-data', 'filename'),
               State('first-column-as-headers', 'value'),
               State('separator', 'value'),
               State('graph-{}'.format(self.id), 'figure')]), plot_scatter))
        self.val.append(
            ((Output('table', 'selected_cells'),
             [Input('graph-{}'.format(self.id), 'selectedData')],
              [State('table', 'data'),
               State('columns-y-selector', 'value'),
               State('columns-x-selector', 'value')]), select_on_table_from_graph))
        self.val.append(
            ((Output('graph-card-{}'.format(self.id), 'style'),
              [Input('btn-delete-{}'.format(self.id), 'n_clicks')],
              [State('graph-card-{}'.format(self.id), 'style')]), delete_graph))

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

