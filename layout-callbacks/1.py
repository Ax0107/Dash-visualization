import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import uuid
import os
import flask
stylesheets = [
    "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.7.2/css/bulma.min.css", # Bulma
]

# create app
app = dash.Dash(
    __name__,
    external_stylesheets=stylesheets
)


app.layout = html.Div(
    className="section",
    children=[
        dcc.Textarea(
            id="text-area",
            className="textarea",
            placeholder='Enter a value...',
            style={'width': '300px'}
        ),
        html.Button(
            id="enter-button",
            className="button is-large is-outlined",
            children=["enter"]
        ),
        html.Div(
            id="download-area",
            className="block",
            children=[]
        )
    ]
)

def build_download_button(uri):
    """Generates a download button for the resource"""
    button = html.Form(
        action='/download/'+uri,
        method="get",
        children=[
            html.Button(
                className="button",
                type="submit",
                children=[
                    "download"
                ]
            )
        ]
    )
    return button

@app.callback(
    Output("download-area", "children"),
    [
        Input("enter-button", "n_clicks")
    ],
    [
        State("text-area", "value")
    ]
)
def show_download_button(n_clicks, text):
    if text is None:
        return
    filename = f"{uuid.uuid1()}"
    path = f".\\files\\{filename}"
    with open(path, "w") as file:
        file.write(text)
    uri = path
    return [build_download_button(uri)]


@app.server.route('/download/<path:path>')
def download_table(path):
    return flask.send_from_directory('.\\', path, attachment_filename='table.csv', as_attachment=True, conditional=True)


if __name__ == '__main__':
    app.run_server(debug=True)
