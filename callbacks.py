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


def get_file(list_of_contents, list_of_names=['csv'], first_column_as_headers=0, separator=';'):
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
        df = get_file(content, list_of_names=filename, first_column_as_headers=f_header, separator=separator)
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
                value = None
            d.append({'column': selected_rows[i]['column'], 'row': row, 'data': value})
        return [json.dumps(d)]
    return ['']


def plot_scatter(selected_points, filecontent, x_column, y_column, clicks_reset, graph_type, filename,
                 f_header, separator, figure, p_size, page_current, table_data):
    """
    Рисует график из выделенных данных на CSV таблице или после выбора new_trace
    :param selected_points: dict полученный из div-selected-data (см. table_load_selected)
    :param filecontent: данные из загруженного ранее файла
    :param y_column: отображаемые y столбцы
    :param x_column: отображаемые x столбцы
    :param clicks_reset: количество нажатий на кнопку для сброса выделенного
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
    df = get_file(filecontent, list_of_names=filename, first_column_as_headers=f_header, separator=separator)
    if selected_points and dash.callback_context.triggered[0]['prop_id'] == 'div-selected-data.children':
        graph_exec = 1
        points = json.loads(selected_points)
        points = pd.DataFrame(points, index=None)
        columns_values = points['column'].unique()
        # Для обращения к индексам по счёту (при выделении данных не с 0 индекса или с пропусками колонок)
        columns_values = dict(zip(list(range(0, len(columns_values))), list(columns_values)))
        points = [points.loc[points['column'] == columns_values[i]]['data'].tolist() for i in columns_values]

    elif dash.callback_context.triggered[0]['prop_id'] \
            in ['columns-y-selector.value', 'btn-reset-selected.n_clicks']:
        graph_exec = 2
        points = []
        if y_column:
            df_table = pd.DataFrame(table_data)
            for i in range(len(y_column)):
                for j in range(int(p_size)*int(page_current), int(p_size)*int(page_current)+int(p_size)):
                    df[y_column[i]][j] = \
                        df_table[y_column[i]][j]
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
    if points and table_data:
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


def show_table(n_open_upload, file_content, next_n, previous_n, 
               p_size, page, n_clicks, file_name,
               df, columns, save_options,
               value, first_column_as_headers, separator):
    """
    Отображает таблицу из CSV файла
    :param n_open_upload: обработчик нажатия кнопки для открытия блока загрузки файла
    :param p_size: количество строк на странице (получается из input p-size)
    :param page: текущая страница
    :param n_clicks: обработчик нажатия кнопки для добавления новой колонки в таблицу
    :param list_of_contents: контент файла
    :param list_of_names: имя файла
    :param value: название новой колонки
    :param columns: колонки таблицы
    :param df: данные табницы
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
        if df:
            _columns = [column['name'] for column in columns]
            i = 1
            v_name = value
            while value in _columns:
                value = v_name + "." + str(i)
                i += 1
            del v_name, _columns
        columns.append({
            'id': value, 'name': value,
            'renamable': True, 'deletable': True,
        })
        return columns, df, file_name[0], {}, get_style_upload_block(True)

    if file_name is not None or (dash.callback_context.triggered[0]['prop_id'] == 'table.page_current' and page):
        if df:

            _, df = get_changed_table(df, columns, ['save-all'], file_content, file_name,
                                      first_column_as_headers, separator, p_size, page)
        else:
            # парсинг файла
            first_column_as_headers, separator = get_normal_settings(first_column_as_headers, separator)
            df = get_file(file_content, list_of_names=file_name,
                          first_column_as_headers=first_column_as_headers, separator=separator)
        df = df.iloc[page * int(p_size):(page + 1) * int(p_size)]
        print('res:', df)
        return [{"name": i, "id": i, 'renamable': True, 'deletable': True}
                for i in df.columns], df.to_dict('records'), file_name[0], {}, get_style_upload_block(True)
    return [], [], '', {'display': 'none'}, get_style_upload_block(True)


def show_edit_block(value):
    if value:
        if value % 2 != 0:
            return {}
    return {'display': 'none'}


def show_page_slider(l, clicks_next, clicks_previous, page_size, df, page_current, page_size_style):
    if l:
        try:
            page_size_style.pop('display')
        except KeyError:
            # Значит, в style уже нет display, продолжаем
            pass
        page = page_current
        if dash.callback_context.triggered[0]['prop_id'] == 'table-next.n_clicks':
            page += 1
        elif dash.callback_context.triggered[0]['prop_id'] == 'table-previous.n_clicks':
            page -= 1
        elif dash.callback_context.triggered[0]['prop_id'] == 'page-size.value':
            page = 0
        df = get_file(df)
        
        if page * int(page_size) + int(page_size) > len(df):
            previous_btn_disabled = False
            next_btn_disabled = True
        elif page == 0:
            previous_btn_disabled = True
            next_btn_disabled = False
        else:
            previous_btn_disabled = False
            next_btn_disabled = False

        return 'native', page, page_size_style, next_btn_disabled, previous_btn_disabled
    if page_size_style:
        page_size_style['display'] = 'none'
    else:
        page_size_style = {'display': 'none'}
    return 'native', 0, page_size_style, False, True


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


def get_normal_settings(first_column_as_headers, separator):
    if first_column_as_headers and 1 in first_column_as_headers:
        first_column_as_headers = 1
    else:
        first_column_as_headers = 0
    if not separator:
        separator = ';'
    return first_column_as_headers, separator


def get_changed_table(df, columns, save_options, file_content, file_name,
                      first_column_as_headers, separator, p_size, page):

    if first_column_as_headers and 1 in first_column_as_headers:
        first_column_as_headers = 1
    else:
        first_column_as_headers = 0
    if not separator:
        separator = ';'
    df_file = get_file(file_content, list_of_names=file_name,
                       first_column_as_headers=first_column_as_headers, separator=separator)
    _df = pd.DataFrame(df)

    old_columns = list(df_file.columns)
    new_columns = [column['name'] for column in columns]
    edited_columns = [x for x in old_columns if x not in new_columns]
    changed_names = {}
    created_columns = []
    deleted_columns = []
    for i in range(0, len(new_columns)):
        if new_columns[i] not in old_columns:
            if i < len(old_columns):
                print(old_columns[i], '->', new_columns[i])
                changed_names[old_columns[i]] = new_columns[i]
            else:
                created_columns.append(new_columns[i])

    # # Убираем удалённые колонки
    # for i in range(len(old_columns)):
    #     if old_columns[i] not in new_columns:
    #         deleted_columns.append(old_columns[i])
    # for i in deleted_columns:
    #     if i in old_columns:
    #
    #         old_columns.pop(old_columns.index(i))

    # Задаём порядок
    df_file = df_file[old_columns]
    df = df_file[int(page)*int(p_size):int(page)*int(p_size)+int(p_size)]
    for i in created_columns:
        df[i] = None
        df_file[i] = None
    print('SDSD\n', df, '\n========')

    for i in range(len(old_columns)):
        if old_columns[i] in changed_names.keys():
            old_columns[i] = changed_names[old_columns[i]]

    df.columns = old_columns+created_columns
    df_file.columns = old_columns+created_columns

    for column in edited_columns:
        if column in df.columns:
            # Если user удалил строку, то удаляем её и из old_columns за ненадобностью
            old_columns.pop(old_columns.index(column))

    # Копируем df, чтобы не потерять созданные колонки, если таковые имеются
    _df = df
    print('Changed_names:', changed_names)
    # Задаём значения созданных колонок
    # for i in range(0, len(new_columns)):
    #     if new_columns[i] not in old_columns:
    #         if new_columns[i] not in edited_columns:
    #             old_columns.append(new_columns[i])
    #         try:
    #             _df[new_columns[i]]
    #         except KeyError:
    #             # Ошибка возникает, если в новой колонке нет данных
    #             _df[new_columns[i]] = None
    #         df[new_columns[i]] = _df[new_columns[i]]
    #         df_file[new_columns[i]] = None
    # del _df

    if save_options and 'save-all' in save_options:
        # Отключение ложного срабатывания предупреждения
        # (https://stackoverflow.com/questions/20625582/how-to-deal-with-settingwithcopywarning-in-pandas)
        pd.options.mode.chained_assignment = None

        df = df[int(page)*int(p_size):int(page)*int(p_size)+int(p_size)].append(
            df_file[int(page)*int(p_size)+int(p_size):], sort=False)

    df = df.where((pd.notnull(df)), '')  # changing Nan values
    return df, df_file


def download_table(n, df, columns, save_options, file_content, file_name, first_column_as_headers, separator, p_size, page):
    """
    Создаёт файл в директории "files" и возвращает кнопку для его загрузки
    :param n: n_clicks кнопки "save"
    :param df: table data
    :param columns: изменённые (или нет) заголовки table
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
    df, _ = get_changed_table(df, columns, save_options, file_content, file_name,
                              first_column_as_headers, separator, p_size, page)
    first_column_as_headers, separator = get_normal_settings(first_column_as_headers, separator)
    filename = f"{uuid.uuid1()}"
    path = f".\\files\\{filename}.csv"
    df.to_csv(path, sep=separator, index=None)
    return [layout.build_download_button(path)]


def update_columns_in_new_trace_block(content, filename, f_header, separator):
    if content:
        # TODO: remove values that already selected in other selector options (needed, 'cuz options equal)
        df = get_file(content, list_of_names=filename, first_column_as_headers=f_header, separator=separator)
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
               Output('page-size', 'style'),
               Output('table-next', 'disabled'),
               Output('table-previous', 'disabled'),
               ],
              [Input('upload-data', 'contents'),
               Input('table-next', 'n_clicks'),
               Input('table-previous', 'n_clicks'),
               Input('page-size', 'value')],
              [State('upload-data', 'contents'),
               State('table', 'page_current'),
               State('page-size', 'style')]), show_page_slider))

        self.val.append(
            (([Output('table', 'columns'), Output('table', 'data'), Output('table-filename', 'children'),
               Output('table-info', 'style'), Output('upload-block', 'style')],
              [Input('btn-open-upload-block', 'n_clicks'),
               Input('upload-data', 'contents'),
               Input('table-next', 'n_clicks'),
               Input('table-previous', 'n_clicks'),
               Input('page-size', 'value'),
               Input('table', 'page_current'),
               Input('btn-add-column', 'n_clicks')],
              [State('upload-data', 'filename'),
               State('table', 'data'),
               State('table', 'columns'),
               State('table-save-all-checkbox', 'value'),
               State('new-column-name', 'value'),
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
              State('table', 'columns'),
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
               Input('columns-y-selector', 'value'),
               Input('btn-reset-selected', 'n_clicks')],
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


