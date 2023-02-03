import dash_bootstrap_components as dbc
from dash import html, dcc
from pyconfig import appConfig


HTML_TITLE = html.Div(
    [
        html.H1(appConfig.DASH_APP.APP_TITLE, className="float fw-bold fs-1"),
        html.Span(
            [appConfig.GITHUB_REPO, "@", appConfig.VERSION], className="text-muted"
        ),
        html.Br(),
        html.Span(
            dcc.Markdown("created by **fiako**dev"), className="text-muted"
        ),
    ],
    className="text-center",
)

DCC_UPLOAD = html.Div(
    dcc.Upload(
        id="dcc-upload",
        children=html.Div(
            [
                dbc.Button(
                    "select files (.zip)",
                    color="primary",
                    outline=False,
                    class_name="fs-4 text-center",
                    id="button-upload",
                )
            ]
        ),
        multiple=False,
        disable_click=False,
    ),
)

HTML_ROW_UPLOAD = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [DCC_UPLOAD],
                    width="auto",
                )
            ],
            justify="center",
        )
    ],
)

HTML_ROW_INFO = html.Div(
    [
        dcc.Loading(dcc.Markdown("## upload **single** `.gp[8/11/12]t` file as `.zip` file", className="text-center"),id="info-loading"),
    ]
)

HTML_ROW_DOWNLOAD = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [dbc.Button(
                        "Download Summary (json)",
                        color="success",
                        class_name="fs-4 fw-bold m-1",
                        id="button-json",
                        disabled=True,
                    )],
                ),
                dbc.Col(
                    [dbc.Button(
                        "Download Records (csv)",
                        color="info",
                        class_name="fs-4 fw-bold m-1",
                        id="button-records-csv",
                        outline=False,
                        disabled=True,
                    )],
                ),
                dbc.Col(
                    [dbc.Button(
                        "Download Records (json)",
                        color="warning",
                        class_name="fs-4 fw-bold m-1",
                        id="button-records-json",
                        disabled=True,
                    )],
                ),
            ],
            justify="center",
            class_name="text-center"
        )
    ],
)

HTML_FOOTER = html.Div(
    html.Footer(
        [
            html.Span("\u00A9"),
            " 2023 ",
            html.A(
                "PT. FIAKO Enjiniring Indonesia",
                href="https://fiako.engineering",
                target="_blank",
            ),
            ".",
        ],
        className="text-center",
    )
)
