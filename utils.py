import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR,"data")

os.makedirs(DATA_DIR,exist_ok=True)

def load_csv_schema(file_name, schema, seed_df=None):

    path = os.path.join(DATA_DIR,file_name)

    if not os.path.exists(path):

        if seed_df is None:
            df = pd.DataFrame(columns=schema)
        else:
            df = seed_df

        df.to_csv(path,index=False)
        return df

    df = pd.read_csv(path)

    for col in schema:
        if col not in df.columns:
            df[col] = None

    return df

