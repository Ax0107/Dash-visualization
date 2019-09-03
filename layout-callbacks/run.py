import flask
import layout
import callbacks
import dash
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP]

server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)

app.config.suppress_callback_exceptions = True
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True

app.layout = layout.layout


@app.server.route('/download/<path:path>')
def download_table(path):
    return flask.send_from_directory('.\\', path, attachment_filename='table.csv', as_attachment=True, conditional=True)


functions = []
for opts, funcs in callbacks.Callbacks("BasicLayout", 0)():
    functions.append(app.callback(*opts)(funcs))
for opts, funcs in callbacks.Callbacks("Table", 0)():
    functions.append(app.callback(*opts)(funcs))

for i in range(0, 10):
    for opts, funcs in callbacks.Callbacks("ScatterTable", i)():
        functions.append(app.callback(*opts)(funcs))
for i in range(10, 20):
    for opts, funcs in callbacks.Callbacks("BarTable", i)():
        functions.append(app.callback(*opts)(funcs))


if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
