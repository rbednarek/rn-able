import dash
from dash import dcc, html, Input, Output, State, no_update
import plotly.express as px
from plotly.io import from_json, to_json
import pandas as pd
from sklearn.decomposition import PCA
import io
import base64
import sys
import os
from io import StringIO
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis_modules import *
import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri, default_converter
from rpy2.robjects.conversion import localconverter
#import contextvars



app = dash.Dash(__name__, suppress_callback_exceptions=True,
                 external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    ])
app.title = "RN-able - Differential Expression Analysis"

app.layout = html.Div([
    html.H1("RN-able"),
    html.H2("Differential Expression Analysis"),
    html.Div([
        html.H3("Sample Clustering Analysis"),
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
    dcc.Store(id='metadata-store'),
    
    html.Div([
        html.H3("Differential Expression Analysis"),
        html.P("Define sample groups using lasso or box tool before running analysis. Filter treatment groups by toggling the legend."),
        html.P("(Analysis may take a little while)"),

        html.Div([
            html.Button('Define Control Group', id='create-group1', n_clicks=0),
            dcc.Input(id='group1-name', type='text', placeholder='ex. Healthy', style={'marginLeft': '10px'}),
            html.Div(id='group1-samples', style={'marginTop': '5px', 'fontStyle': 'italic'}),
        ], style={'marginBottom': '20px'}),

        html.Div([
            html.Button('Define Treatment Group', id='create-group2', n_clicks=0),
            dcc.Input(id='group2-name', type='text', placeholder='ex. Diseased', style={'marginLeft': '10px'}),
            html.Div(id='group2-samples', style={'marginTop': '5px', 'fontStyle': 'italic'}),
        ], style={'marginBottom': '20px'}),
        dcc.Loading(
            id='loading-de-analysis',
            type='default',
            children=html.Div([
                html.Button('Run DE Analysis', id='run-de', n_clicks=0),
                html.Div(id='de-error-message', style={'color': 'red', 'marginTop': '10px'}),
                dcc.Download(id='download-deresults'),
                dcc.Download(id='download-metadata'),
            ])
        )
    ], 
    id='group-assign-container', 
    style={'display': 'none', 'border': '1px solid #ccc', 'padding': '20px', 'margin-bottom': '20px'}),
    dcc.Store(id='pca-figure-store'),
    dcc.Store(id='group1-store'),
    dcc.Store(id='group2-store')
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
    return df.to_dict(orient='split')

@app.callback(
    Output('metadata-store', 'data'),
    Input('upload-metadata', 'contents'),
    State('upload-metadata', 'filename'),
    prevent_initial_call=True
)

def upload_metadata(contents, filename):
    df = parse_contents(contents, filename)
    return df.to_dict(orient='split')

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
    Output('pca-figure-store', 'data'),
    Input('run-pca', 'n_clicks'),
    State('count-data-store', 'data'),
    State('metadata-store', 'data'),
    prevent_initial_call=True
)

def run_pca(n_clicks, counts_dict, meta_df_dict=None):
    col1 = None
    col2 = None
    counts_df = pd.DataFrame(data=counts_dict['data'], index=counts_dict['index'], columns=counts_dict['columns'])
    if meta_df_dict:
        meta_df = pd.DataFrame(data=meta_df_dict['data'], index=meta_df_dict['index'], columns=meta_df_dict['columns'])
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
    if meta_df_dict:
        fig = px.scatter(pca_df, x='PC1', y='PC2', hover_name='sample',
                        color=col1 if meta_df is not None else 'blue',
                        symbol=col2 if meta_df is not None and col2 else None,
                        title='Sample PCA Plot',
                        custom_data=['sample']
                        )
    else:
        fig = px.scatter(pca_df, x='PC1', y='PC2', title='Sample PCA Plot')
    fig.update_layout(
        xaxis_title=f'PC1 ({pc1_variance:.2f}%)',
        yaxis_title=f'PC2 ({pc2_variance:.2f}%)'
    )

    return fig, to_json(fig)

@app.callback(
    Output('group-assign-container', 'style'),
    Input('pca-plot', 'figure'),
    Input('metadata-store', 'data')
)

def show_group_assign_controls(fig, metadata):
    if fig and 'data' in fig and fig['data'] and metadata:
        return {'display': 'block', 'border': '1px solid #ccc', 'padding': '20px', 'margin-bottom': '20px'}
    return {'display': 'none'}


@app.callback(
    Output('group1-store', 'data'),
    Output('group1-samples', 'children'),
    Input('create-group1', 'n_clicks'),
    State('pca-plot', 'selectedData'),
    State('pca-plot', 'relayoutData'),
    State('group1-name', 'value'),
    State('pca-figure-store', 'data'),
    prevent_initial_call=True
)

def create_group1(n_clicks, selectedData, relayoutData, group_name, fig_json):
    if n_clicks and selectedData and group_name:
        fig = from_json(fig_json)
        if relayoutData:
            hidden_labels = set(relayoutData.get('hiddenlabels', []))
        else:
            hidden_labels = set() 
        curve_to_trace = {i: trace.name for i, trace in enumerate(fig.data)}    
        selected_samples = []
        for point in selectedData['points']:
            curve_num = point['curveNumber']
            trace_name = curve_to_trace.get(curve_num, '')
            if trace_name not in hidden_labels:
                selected_samples.append(point['hovertext'])
        return selected_samples, f"Control Group: {group_name}"
    return [], ""

@app.callback(
    Output('group2-store', 'data'),
    Output('group2-samples', 'children'),
    Input('create-group2', 'n_clicks'),
    State('pca-plot', 'selectedData'),
    State('pca-plot', 'relayoutData'),
    State('group2-name', 'value'),
    State('pca-figure-store', 'data'),
    prevent_initial_call=True
)

def create_group2(n_clicks, selectedData, relayoutData, group_name, fig_json):
    if n_clicks and selectedData and group_name:
        fig = from_json(fig_json)
        if relayoutData:
            hidden_labels = set(relayoutData.get('hiddenlabels', []))
        else:
            hidden_labels = set()
        curve_to_trace = {i: trace.name for i, trace in enumerate(fig.data)}
        selected_samples = []
        for point in selectedData['points']:
            curve_num = point['curveNumber']
            trace_name = curve_to_trace.get(curve_num, '')
            if trace_name not in hidden_labels:
                selected_samples.append(point['hovertext'])
        return selected_samples, f"Treatment Group: {group_name}"
    return [], ""

@app.callback(
    Output('download-deresults', 'data'),
    Output('download-metadata', 'data'),
    Input('run-de', 'n_clicks'),
    State('group1-store', 'data'),
    State('group2-store', 'data'),
    State('group1-name', 'value'),
    State('group2-name', 'value'),
    State('count-data-store', 'data'),
    State('metadata-store', 'data'),
    prevent_initial_call=True
)
def run_de(n_clicks, group1_samples, group2_samples, group1_name, group2_name, count_data, metadata):
    if not group1_samples or not group2_samples:
        return no_update, no_update
    elif n_clicks and group1_samples and group2_samples:
        counts_df = pd.DataFrame(data=count_data['data'], index=count_data['index'], columns=count_data['columns'])
        meta_df = pd.DataFrame(data=metadata['data'], index=metadata['index'], columns=metadata['columns'])
        counts_filter = counts_df[group1_samples + group2_samples]
        meta_df_filter = meta_df.loc[group1_samples + group2_samples].copy()
        meta_df_filter['group'] = ''
        for _,row in meta_df_filter.iterrows():
            if _ in group1_samples:
                meta_df_filter.at[_, 'group'] = group1_name
            elif _ in group2_samples:
                meta_df_filter.at[_, 'group'] = group2_name
        res_df = run_de_analysis(counts_filter, meta_df_filter, group1_name, group2_name)
        meta_csv = StringIO()
        meta_df_filter.to_csv(meta_csv)
        de_results_csv = StringIO()
        res_df.to_csv(de_results_csv)
        return {'content': de_results_csv.getvalue(), 'filename': f'{group2_name}_v_{group1_name}_de_results.csv'}, {'content': meta_csv.getvalue(), 'filename': f'{group2_name}_v_{group1_name}_metadata.csv'}

@app.callback(
    Output('de-error-message', 'children'),
    Input('run-de', 'n_clicks'),
    State('group1-store', 'data'),
    State('group2-store', 'data'),
    prevent_initial_call=True
)
def both_groups_check(n_clicks, group1_samples, group2_samples):
    if not group1_samples or not group2_samples:
        return "Must select groups 1 and 2 first"
    return ""

if __name__ == '__main__':
    app.run(debug=True)
