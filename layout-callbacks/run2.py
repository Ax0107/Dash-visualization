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

app.layout = layout.layout_settings_panel

functions = []
for opts, funcs in callbacks.Callbacks("SettingsPanel")():
    functions.append(app.callback(*opts)(funcs))

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True)
