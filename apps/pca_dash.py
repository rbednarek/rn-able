import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import pandas as pd
from sklearn.decomposition import PCA
import io
import base64
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis_modules import *



app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Differential Expression Analysis"

app.layout = html.Div([
    html.H1("Differential Expression Analysis"),
    html.Div([
        html.Label("Upload Count Data:"),
        html.Div([
            dcc.Upload(
                id='upload-count-data',
                children=html.Button("Upload File"),
                multiple=False
            ),
            html.Span(id='counts-filename', style={"marginLeft": "10px", "fontStyle": "italic"})

        ], style={'display':'flex', 'alignItems':'center'}),

        html.Br(),
        html.Label("Upload Metadata (Optional):"),
        html.Div([
            dcc.Upload(
                id='upload-metadata',
                children=html.Button("Upload File"),
                multiple=False
            ),
            html.Span(id='metadata-filename', style={"marginLeft": "10px", "fontStyle": "italic"})
        ], style={'display':'flex', 'alignItems':'center'}),

        html.Br(),
        html.Button("Run PCA", id='run-pca', n_clicks=0),
    ], style={"padding": "20px", "border": "1px solid #ccc", "margin-bottom": "20px"}),

    html.Hr(),
    dcc.Loading(
        id='loading-pca',
        children=html.Div(
            id='pca-plot-container',
            children=dcc.Graph(id='pca-plot'),
            style={'display': 'None'}
        ),
        type='default'
    ),

    dcc.Store(id='count-data-store'),
    dcc.Store(id='metadata-store')
])

@app.callback(
    Output('counts-filename', 'children'),
    Input('upload-count-data', 'filename')
)
def show_counts_filename(filename):
    if filename:
        return f"{filename}"
    return ""

@app.callback(
    Output('metadata-filename', 'children'),
    Input('upload-metadata', 'filename')
)
def show_metadata_filename(filename):
    if filename:
        return f"{filename}"
    return ""


def parse_contents(contents, filename):
    x, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if filename.endswith('.tsv') or filename.endswith('.tsv.gz'):
        sep = '\t'
    elif filename.endswith('.csv') or filename.endswith('.csv.gz'):
        sep = ','    
    try:
        if filename.endswith('.gz'):
            with gzip.open(io.BytesIO(decoded), 'rt', encoding='utf-8') as f:
                df = pd.read_csv(f, sep=sep, index_col=0)
        else:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=sep, index_col=0)
    except Exception as e:
        return None
    return df

@app.callback(
    Output('count-data-store', 'data'),
    Input('upload-count-data', 'contents'),
    State('upload-count-data', 'filename'),
    prevent_initial_call=True
)

def upload_countdata(contents, filename):
    df = parse_contents(contents, filename)
    return df.to_dict()

@app.callback(
    Output('metadata-store', 'data'),
    Input('upload-metadata', 'contents'),
    State('upload-metadata', 'filename'),
    prevent_initial_call=True
)

def upload_metadata(contents, filename):
    df = parse_contents(contents, filename)
    return df.to_dict()

@app.callback(
    Output('pca-plot-container', 'style'),
    Input('run-pca', 'n_clicks')
)
def show_pca_plot(n_clicks):
    if n_clicks and n_clicks > 0:
        return {'display': 'block'}
    return {'display': 'none'}

@app.callback(
    Output('pca-plot', 'figure'),
    Input('run-pca', 'n_clicks'),
    State('count-data-store', 'data'),
    State('metadata-store', 'data'),
    prevent_initial_call=True
)

def run_pca(n_clicks, counts_dict, meta_df_dict=None):
    col1 = None
    col2 = None
    counts_df = pd.DataFrame.from_dict(counts_dict)
    if meta_df_dict:
        meta_df = pd.DataFrame.from_dict(meta_df_dict)
        col1 = meta_df.columns[0]
        if len(meta_df.columns) > 1:
            col2 = meta_df.columns[1]
    else:
        meta_df = None
    
    pca_df, pc1_variance, pc2_variance = plot_count_pca(count_df=counts_df,
                            plot=False,
                            meta_df=meta_df,
                            col1=col1 if col1 else None,
                            col2=col2 if col2 else None)
    pca_df['sample'] = pca_df.index
    print(pca_df)
    fig = px.scatter(pca_df, x='PC1', y='PC2', hover_name='sample',
                     color=col1 if meta_df is not None else 'blue',
                     symbol=col2 if meta_df is not None and col2 else None,
                     title='Sample PCA Plot',
                     custom_data=['sample']
                    )
    fig.update_layout(
        xaxis_title=f'PC1 ({pc1_variance:.2f}%)',
        yaxis_title=f'PC2 ({pc2_variance:.2f}%)'
    )

    return fig

if __name__ == '__main__':
    app.run(debug=True)
