from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.tools as tls
import base64
import io
import dash
import uuid
import json
from ast import literal_eval
import layout


def get_file(list_of_contents, list_of_names, first_column_as_headers, separator):
    """
    Вспомогательная функция для чтения CSV
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :param first_column_as_headers: использовать ли первую строку, как заголовки
    :param separator: разделитель
    :return: pandas data
    """

    content_type, content_string = list_of_contents[0].split(',')
    decoded = base64.b64decode(content_string)

    if 'csv' in list_of_names[0]:
        if first_column_as_headers:
            return pd.read_csv(
                   io.StringIO(decoded.decode('utf-8')),
                   sep=separator, header=0, dtype=object)
        else:
            return pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                sep=separator, dtype=object)
    elif 'xls' in list_of_names[0]:
        if first_column_as_headers:
            return pd.read_excel(io.BytesIO(decoded), header=0, dtype=object)
        else:
            return pd.read_excel(io.BytesIO(decoded), dtype=object)

    return None


# # # # # # # # Функции для отображения графиков # # # # # # # #

def table_load_selected(selected_rows, show_selected_on_graph, content, filename, f_header, separator, table_data):
    """
    Функция выводит в div-selected-data данные о выделенных столбцах, дабы другие фунции могли
                                                                использовать эти данные
    :param selected_rows: выделенные данные в таблице
    :param show_selected_on_graph: выводить ли данные в div-selected-data 
                    (показывать ли выделенное на таблице на графике)
    :param content: данные загруженного файла
    :param filename: имя загруженного файла
    :param f_header: используется ли первая строка, как заголовки
    :param separator: разделитель
    :param table_data: ...
    :return: div-selected-data json
    """
    if show_selected_on_graph and content and selected_rows:
        df = get_file(content, filename, f_header, separator)
        data = df.to_dict('records')
        d = []
        # selected_rows = pd.DataFrame(selected_rows)
        for i in range(0, len(selected_rows)):
            row = selected_rows[i]['row']
            column = selected_rows[i]['column_id']
            try:
                if column in table_data[row]:
                    value = table_data[row][column]
                else:
                    value = data[row][column]
            except (KeyError, IndexError):
                value = data[row][column]
            d.append({'column': selected_rows[i]['column'], 'row': row, 'data': value})
        return [json.dumps(d)]
    return ['']


def plot_bar_from_table(selected_points, figure):
    """
    Рисует Bar из выделенных данных таблицы
    :param selected_points: json полученный из div-selected-data (см. table_load_selected)
    :return: bar-figure
    """
    style = {'display': 'none'}
    points = [[0], [0]]
    if selected_points:
        # Дальше идёт преобразование данных к нужному типу
        selected_points = literal_eval(selected_points)
        columns = set([i['column'] for i in selected_points])
        count = len(columns)

        # создаём лист типа {X: 0, Y: 1, Z: 2},
        # дабы при выделении в таблице данных не с нулевого столбца, мы могли обращаться к points
        # по индексу 0, 1, 2 и т.д. (иначе, столбец = индекс)
        columns = dict(zip(list(columns), list(range(0,count))))
        if count % 2 == 0:
            points = [[]]
            for i in selected_points:
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


def plot_scatter(selected_points, filecontent, x_column, y_column, graph_type, filename,
                 f_header, separator, figure, p_size, page_current, table_data):
    """
    Рисует график из выделенных данных на CSV таблице или после выбора new_trace
    :param selected_points: dict полученный из div-selected-data (см. table_load_selected)
    :param filecontent: данные из загруженного ранее файла
    :param y_column: отображаемые y столбцы
    :param x_column: отображаемые x столбцы
    :param graph_type: тип графика
    :param filename: имя загруженного ранее файла
    :param f_header: используется ли первую строка (загруженного ранее файла), как заголовки
    :param separator: разделитель загруженного ранее файла
    :param figure: фигура графика
    :param p_size: размер страницы таблицы
    :param page_current: текущая страница таблицы
    :param table_data: ...
    ...
    :return: graph figure
    """

    # Для отслеживания модели поведения в соответсвии с ситуацией
    # (загрузка из div-selected-data или из выделенных данных на графике)
    graph_exec = 0
    df = get_file(filecontent, filename, f_header, separator)
    if selected_points and dash.callback_context.triggered[0]['prop_id'] == 'div-selected-data.children':
        graph_exec = 1
        points = json.loads(selected_points)
        points = pd.DataFrame(points, index=None)
        columns_values = points['column'].unique()
        # Для обращения к индексам по счёту (при выделении данных не с 0 индекса или с пропусками колонок)
        columns_values = dict(zip(list(range(0, len(columns_values))), list(columns_values)))
        points = [points.loc[points['column'] == columns_values[i]]['data'].tolist() for i in columns_values]

    elif y_column:
        graph_exec = 2
        points = []
        df_table = pd.DataFrame(table_data)
        for i in range(len(y_column)):
            for j in range(int(p_size)*int(page_current), int(p_size)*int(page_current)+int(p_size)):
                df[y_column[i]][j] = df_table[y_column[i]][j]
            points.append(df[y_column[i]])

    if graph_exec:
        # Создаём график
        fig = tls.make_subplots(rows=1, cols=1, shared_yaxes=True, shared_xaxes=True, vertical_spacing=0.009,
                                horizontal_spacing=0.009, print_grid=False)
        fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 50, 't': 25}
        trace = {}
        # Ситуация 2 (выбор new_trace)
        if graph_exec == 2:
            for i in range(len(y_column)):
                if x_column:
                    trace['x'] = df[x_column].to_list()
                if y_column:
                    trace['y'] = df[y_column[i]].to_list()
                trace['type'] = graph_type
                fig.append_trace(trace, 1, 1)
        # Ситуация 1 (загрузка из div-selected-data)
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
    """
    Выделяет выбранные на графике данные в таблице
    :param points: выделенные на графике точки
    :param table_data:
    :param y_column: отображаемые y столбцы
    :param x_column: отображаемые x столбцы
    :return: данные для таблицы
    """
    # TODO: использовать x_column (выделять/передавать его?). Сейчас: игнорируется
    if points:
        # формат получаемых данных:
        # {'curveNumber': 0, 'pointNumber': 2, 'pointIndex': 2, 'x': 2, 'y': 2},
        table_points = []
        keys = list(table_data[0].keys())
        for i in range(len(points.get('points', 0))):
            trace_num = points['points'][i]['curveNumber']
            column_id = keys[trace_num]
            column = trace_num
            if y_column:
                column_id = y_column[trace_num % len(y_column)]
                column = [i for i in range(len(keys)) if keys[i] == column_id][0]
            point_index = points['points'][i]['pointIndex']
            table_points.append({'column': column, 'row': point_index, 'column_id': column_id})
        return table_points
    return []


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


def disable_creation_more_than_one_graph(func):
    # # # # # # # # Disabling creation more than 1 graph (more - need to finish writing) # # # # # # # #
    # TODO: Решить вопрос с callback'ами к таблице и т.п. (возможно, создавать новую для каждого графика?)
    def wrapper(*args):
        created_graphs = args[2]
        # func = create_graph
        if len(args) == 4:
            graphs = args[3]
            if created_graphs and int(literal_eval(created_graphs).get('scatter', 0)) == 2:
                return graphs
            else:
                return func(*args)
        # func = set_created_graphs
        elif len(args) == 3:
            if created_graphs and int(literal_eval(created_graphs).get('scatter', 0)) == 2:
                return created_graphs
            else:
                return func(*args)
        # func = delete_graph
        elif len(args) == 2:
            return {}
    return wrapper


@disable_creation_more_than_one_graph
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
    if dash.callback_context.triggered[0]['prop_id'] == 'created-graphs.children':
        if n_clicks:
            # Меняем graph_id взависимости от количества графиков этого типа
            if graph_type == 'scatter':
                if created_graphs:
                    graph_id = int(literal_eval(created_graphs)['scatter'])
            elif graph_type == 'bar':
                if created_graphs:
                    graph_id = 11 + int(literal_eval(created_graphs)['bar'])
            if graphs is not None:
                if not isinstance(graphs, list):
                    graphs = [graphs].append(layout.work_card(graph_id))
                else:
                    graphs.append(layout.work_card(graph_id))
            else:
                graphs = layout.work_card(graph_id)
    return graphs


@disable_creation_more_than_one_graph
def set_created_graphs(n_clicks, graph_type, created_graphs):
    """
    Функция обновляет значчения created_graphs
    :param n_clicks: неиспользуемая переменная (предназначена для получения callback'а)
    :param graph_type: тип графика
    :param created_graphs: state created_graphs
    :return: изменённыый created_graphs
    """

    if dash.callback_context.triggered[0]['prop_id'] == 'btn-create-graph.n_clicks':
        if created_graphs is not None:
            try:
                n = int(literal_eval(created_graphs)[graph_type]) + 1
                created_graphs = literal_eval(created_graphs)
                created_graphs.update({graph_type: n})
            except (KeyError, TypeError):
                created_graphs.update({graph_type: 1})
            return str(created_graphs)
        return str({graph_type: 1})
    return created_graphs


# disable deleting
@disable_creation_more_than_one_graph
def delete_graph(n, style):
    if n:
        return {'display': 'none'}
    if style:
        return style
    return {}


def download_table(n, df, save_options, file_content, file_name, first_column_as_headers, separator, p_size, page):
    """
    Создаёт файл в директории "files" и возвращает кнопку для его загрузки
    :param n: n_clicks кнопки "save"
    :param df: table data
    :param save_options: checkbox_value сохранять ли файл полностью
    :param file_content: контент загруженного файла
    :param file_name: имя файла
    :param first_column_as_headers: используется ли первая строчка, как заголовок (файл)
    :param separator: разделитель (файл)
    :param p_size: размер страницы (table)
    :param page: текущая страница (table)
    :return: кнопка для загрузки файла
    """
    if df is None or not n:
        return [layout.build_download_button()]
    df = pd.DataFrame(df)
    # Переворачиваем Dataframe, потому что считывается он в обратном порядке
    # Баг Dash? TODO: разобраться, можно ли правильно считывать table_data
    df = df.iloc[:, ::-1]

    if first_column_as_headers and 1 in first_column_as_headers:
        first_column_as_headers = 1
    else:
        first_column_as_headers = 0
    if not separator:
        separator = ';'

    if save_options and 'save-all' in save_options:
        # Получение Dataframe из загруженного ранее файла
        df_file = get_file(file_content, file_name, first_column_as_headers, separator)
        columns_file = list(df_file.columns)
        columns_table = list(df.columns)
        # Если был создан новый столбец, добавляем его в df_file
        if columns_file != columns_table:
            if len(columns_file) < len(columns_table):
                for i in range(len(columns_file), len(columns_table)):
                    df_file[columns_table[i]] = [None] * len(df_file)
        for j in range(0, int(p_size)):
            # Пропуск заголовков для записи (уже записаны)
            df_file.iloc[int(p_size)*int(page)+j] = df.to_dict('records')[j]
        df = df_file
    df = df.where((pd.notnull(df)), '')  # changing Nan values
    filename = f"{uuid.uuid1()}"
    path = f".\\files\\{filename}.csv"
    df.to_csv(path, sep=separator, index=None)
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
               Input('table', 'page_current'),
               Input('btn-add-column', 'n_clicks'),
               Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('new-column-name', 'value'),
               State('table', 'columns'),
               State('table', 'data'),
               State('first-column-as-headers', 'value'),
               State('separator', 'value')]), show_table))
        self.val.append(
            (([Output('div-selected-data', 'children')],
             [Input('table', 'selected_cells'),
              Input('show_selected_on_graph', 'value')],
             [State('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('first-column-as-headers', 'value'),
              State('separator', 'value'),
              State('table', 'data')]),
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
              [Input('div-selected-data', 'children'),
               Input('upload-data', 'contents'),
               Input('columns-x-selector', 'value'),
               Input('columns-y-selector', 'value')],
              [State('graph-type', 'value'),
               State('upload-data', 'filename'),
               State('first-column-as-headers', 'value'),
               State('separator', 'value'),
               State('graph-{}'.format(self.id), 'figure'),
               State('page-size', 'value'),
               State('table', 'page_current'),
               State('table', 'data')]), plot_scatter))
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
              [Input('div-selected-data', 'children')],
              [State('graph-{}'.format(self.id), 'figure')]), plot_bar_from_table))

