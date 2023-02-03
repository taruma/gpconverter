
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, html, State, dcc
import pylayout
from solummaa import solummaa
import json
from pyconfig import appConfig
import pandas as pd

APP_TITLE = appConfig.DASH_APP.APP_TITLE
HEAD_TITLE = appConfig.DASH_APP.HEAD_TITLE
UPDATE_TITLE = appConfig.DASH_APP.UPDATE_TITLE
DEBUG = appConfig.DASH_APP.DEBUG

# BOOTSTRAP THEME
THEME = appConfig.TEMPLATE.THEME
DBC_CSS = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.7/dbc.min.css"
)

# MAIN APP
app = Dash(
    name=APP_TITLE,
    external_stylesheets=[getattr(dbc.themes, THEME), DBC_CSS],
    title=HEAD_TITLE,
    update_title=UPDATE_TITLE,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    prevent_initial_callbacks=True,
)

server = app.server

app.layout = dbc.Container(
    [
        html.Br(),
        pylayout.HTML_TITLE,
        html.Br(),
        dcc.Store("store-gpt-summary"),
        dcc.Store("store-gpt-records"),
        dcc.Store("store-info-data"),
        pylayout.HTML_ROW_UPLOAD,
        html.Br(),
        pylayout.HTML_ROW_INFO,
        html.Br(),
        pylayout.HTML_ROW_DOWNLOAD,
        dcc.Download(id="download-json"),
        dcc.Download(id="download-records-json"),
        dcc.Download(id="download-records-csv"),
        html.Br(),
        pylayout.HTML_FOOTER,
    ],
    fluid=False,
    class_name="dbc my-3",
)

# CALLBACK
@app.callback(
    Output("store-gpt-summary", "data"),
    Output("store-gpt-records", "data"),
    Output("store-info-data", "data"),
    Output("button-json", "disabled"),
    Output("button-records-json", "disabled"),
    Output("button-records-csv", "disabled"),
    Output("info-loading", "children"),
    Output("button-records-csv", "outline"),
    Input("dcc-upload", "contents"),
    State("dcc-upload", "filename"),
    State("dcc-upload", "last_modified"),
)
def callback_upload(contents, filename, filedate):
    import io
    import base64

    _, content_string = contents.split(",")
    content_decoded = base64.b64decode(content_string)
    zip_str = io.BytesIO(content_decoded)

    gpt_summary = solummaa.read_gpt_from_zip(zip_str)

    group_version = gpt_summary['INFO']['group_version']
    datetime = gpt_summary['INFO']['datetime']
    computation_name = gpt_summary['INFO']['computation_name']
    total_load_case = gpt_summary['INFO']['total_load_case']
    total_pile = gpt_summary['INFO']['total_pile']

    markdown = f"""
    #### filename: **{filename}**
    #### group version: **{group_version}**
    #### datetime: **{datetime}**
    #### computation name: **{computation_name}**
    #### total load case: **{total_load_case}**
    #### total pile: **{total_pile}**
    """
    
    markdown = '\n'.join([i.strip() for i in markdown.splitlines() if i != ''])
    
    gpt_records = solummaa.gpt_records_from_summary(gpt_summary)

    metadata = {
        'filename': filename,
        'filedate': filedate,
    }

    return gpt_summary, gpt_records, metadata, False, False, False, dcc.Markdown(markdown, id="info-md", className="text-center"), True

@app.callback(
    Output("download-json", "data"),
    Input("button-json", "n_clicks"),
    State("store-gpt-summary", "data"),
    State("store-info-data", "data")
)
def callback_process(_, gpt_summary, metadata):
    data = json.dumps(gpt_summary)
    filename = metadata['filename'].split('.')[0]
    return {'content': data, 'filename': f'{filename}_summary.json'}

@app.callback(
    Output("download-records-json", "data"),
    Input("button-records-json", "n_clicks"),
    State("store-gpt-records", "data"),
    State("store-info-data", "data")
)
def callback_process(_, gpt_records, metadata):
    data = json.dumps(gpt_records)
    filename = metadata['filename'].split('.')[0]
    return {'content': data, 'filename': f'{filename}_records.json'}

@app.callback(
    Output("download-records-csv", "data"),
    Input("button-records-csv", "n_clicks"),
    State("store-gpt-records", "data"),
    State("store-info-data", "data")
)
def callback_process(_, gpt_records, metadata):
    filename = metadata['filename'].split('.')[0]
    dataframe = pd.DataFrame.from_records(gpt_records)
    return dcc.send_data_frame(dataframe.to_csv, f"{filename}_records.csv")

if __name__ == "__main__":
    app.run_server(debug=DEBUG)
