import pandas as pd

def uppercase_names(df):
    df = df.copy()
    if "name" in df.columns:
        df["name"] = df["name"].str.upper()
    return df

def list_to_df(list):
    return pd.DataFrame(list)

def strip_newlines(raw_text):
    return raw_text.replace("\n", " ").strip()

def json_records_to_cols(records):
    cols = {}
    for record in records:
        for k,v in record.items():
            if k not in cols:
                cols[k] = [v]
            else:
                cols[k].append(v)
    print(cols)
    return cols