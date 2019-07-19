from rediska import Rediska
import plotly.tools as tls
import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import flask

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

r = Rediska()
params = r.get_all_params()  # все доступные параметры для отображения
objects = r.count_of_objects()  # количество объектов

# Создание layout
app.layout = html.Div(children=[
    html.Div(children=[
            html.Div(id='hoverData'),
            dcc.Graph(id='graph'),
            html.Hr(),
            html.H3('Параметр:', id='aaa'),
            dcc.Dropdown(
                    id='selector',
                    options=[{'label': i, 'value': i} for i in params],
                    value='x', multi=True,
                ),
            dcc.Checklist(
                id='ob-num',
                options=[
                    {'label': 'Учитывать номер объекта', 'value': '1'},
                ]),
            dcc.Dropdown(
                id='object-selector',
                options=[{'label': i, 'value': i} for i in range(0, objects)],
                value='0', style={'display': 'none'}
            ),
        ], style={'width': '70%', 'margin-left': '15%'})])


@app.callback(Output('object-selector', 'style'),
              [Input('ob-num', 'value')])
def update_objects_selector(v):
    """
    Отображает/скрывает slider для выбора объекта в зависимости от value checkbox'а
    :param v: выбран ли флажок checkbox
    :return: style of slider
    """
    if v:
        return {}
    else:
        return {'display': 'none'}


@app.callback(
    Output('graph', 'figure'),
    [Input('selector', 'value'),
     Input('object-selector', 'value'),
     Input('ob-num', 'value')])
def update_output(values, obj, i):
    """
    Обновляет график
    :param values: активные параметры
    :param obj: выбранный объект
    :param i: контролировать ли объект
    :return: graph-figure
    """
    if not i:
        obj = -1
    if not isinstance(values, list):
        values = [values]

    fig = tls.make_subplots(rows=1, cols=1, shared_yaxes=True, shared_xaxes=True, vertical_spacing=0.009,
                            horizontal_spacing=0.009)
    fig['layout']['margin'] = {'l': 30, 'r': 10, 'b': 50, 't': 25}
    time = r.get_data_for_object(obj, 'Time')
    for v in values:
        points = r.get_data_for_object(obj, v)
        fig.append_trace({'x': time, 'y': points, 'hoverinfo': "none", 'type': 'scatter', 'name': v}, 1, 1)

    fig['layout'].update(title='Graph')
    return fig


@app.callback(Output('hoverData', 'children'),
              [Input('graph', 'hoverData'),
               Input('selector', 'value')])
def update_hover_data(hover_data, values):
    """
    Обновляет hover данные в виде таблицы
    :param hover_data: данные hover
    :param values: активные параметры
    :return: таблица hover данных
    """
    if hover_data:
        if not isinstance(values, list):
            values = [values]
        leigh = len(hover_data['points'])
        data_string = ' '
        for i in range(0, leigh):
            data_string = data_string + str(hover_data['points'][i]['y']) + "|"
        data = data_string.split('|')
        data = [{'0': values[v], '1': data[v]} for v in range(0, len(values))]
        card = dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    id='table',
                    columns=[
                             {"name": ['Момент времени: {}'.format(str(hover_data['points'][0]['x'])),
                                       'Параметр'], "id": '0'},
                             {"name": ['Момент времени: {}'.format(str(hover_data['points'][0]['x'])),
                                       'Значение'], "id": '1'}],
                    data=data,
                    style_cell={'textAlign': 'left'},
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_cell_conditional=[{
                            'if': {'column_id': c},
                            'textAlign': 'left'
                        } for c in ['0', '1']
                    ],
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ],
                    merge_duplicate_headers=True),
            ]),
            html.Hr(),
        ], style={
            'width': '100%',
            'font-size': '26px',
            'text-align': 'left'})
        return card


if __name__ == '__main__':
    app.run_server(debug=True)
