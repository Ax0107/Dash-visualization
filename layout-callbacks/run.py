import flask
import layout
import callbacks
import dash

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

# app.layout = layout.bar_file
app.layout = layout.scatter_file

functions = []
# for opts, funcs in callbacks.Callbacks("BarFile")():
for opts, funcs in callbacks.Callbacks("ScatterFile")():
    functions.append(app.callback(*opts)(funcs))


if __name__ == '__main__':
    app.run_server(debug=True)
