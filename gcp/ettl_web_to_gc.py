from pathlib import Path
import pandas as pd
from prefect import flow,task 
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(name="fetch_data",cache_key_fn=task_input_hash,cache_expiration=timedelta(days=1))
def download(url:str) -> pd.DataFrame:
    """ Fetch data from web into pandas"""
    df = pd.read_csv(url)
    return df


@task(name="cleaning_data",log_prints=True)
def clean(df:pd.DataFrame) -> pd.DataFrame:
    """ Cleansing data """
    print(f'after cleaning,size is {len(df)}')
    df = df.dropna()
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"])
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"])
    print(df)
    print(f'after cleaning,size is {len(df)}')
    return df

@task(name="save_to_local")
def write_to_local(df:pd.DataFrame,color:str,dataset_file:str) -> Path:
    """ Write dataframe as parquet file to local"""
    path = Path(f'data/{color}/{dataset_file}.parquet')
    df.to_parquet(path,compression='gzip')
    return path

@task(name="upload_to_gc",retries=3)
def write_to_gc(path:Path):
    """ Upload data to gc """
    gcs_block = GcsBucket.load("first-gcs-zoom")
    gcs_block.upload_from_path(from_path=path,to_path=path)
    return

@flow(name="etl_web_gc")
def write_from_web_to_gc():
    """ The Main Etl Function """
    color = 'yellow'
    year = '2020'
    month = 5
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"
    df = download(dataset_url)
    new_df = clean(df)
    path = write_to_local(new_df,color,dataset_file)
    write_to_gc(path)


if __name__ == '__main__':
    write_from_web_to_gc()

        