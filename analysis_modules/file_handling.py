import pandas as pd

def read_csv(file_path, index_col=0):
    '''Reads a CSV or TSV file into a DataFrame'''
    if file_path.endswith('.csv') or file_path.endswith('.csv.gz'):
        df = pd.read_csv(file_path, index_col=index_col)
    elif file_path.endswith('.tsv') or file_path.endswith('.tsv.gz'):
        df = pd.read_csv(file_path, sep='\t', index_col=index_col)
    else:
        raise ValueError("Invalid file format. Please provide a .csv, .csv.gz, .tsv, or .tsv.gz file.")
    return df

def write_csv(df, file_path, index=False):
    df.to_csv(file_path, index=index)

