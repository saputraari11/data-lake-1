from pathlib import Path
import pandas as pd
from prefect import flow,task
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp import GcpCredentials

@task(name="download_data")
def extract_from_lake(color:str,year:int,month:int) -> Path:
    """ Fetch data from data lake """
    gcs_path = f'data/{color}/{color}_tripdata_{year}-{month:02}.parquet'
    gcs_load = GcsBucket.load('first-gcs-zoom')
    gcs_load.get_directory(from_path=gcs_path,local_path=f'../')
    return Path(f'../{gcs_path}')

@task(name="transform")
def transform(path:Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df["passenger_count"].fillna(0, inplace=True)
    return df

@task(name="load_data")
def load_to_bq(df:pd.DataFrame):
    """ Write DataFrame into Warehouse """
    gcp_credentials_block = GcpCredentials.load("gcs-credential-first")
    df.to_gbq(
    destination_table="trips_data_all.belajar",
    project_id="pro-habitat-376010",
    chunksize=500_000,
    if_exists="append",
    credentials=gcp_credentials_block.get_credentials_from_service_account()
    )



@flow(name="etl_lake_to_wh")
def etl_lake_to_wh():
    """ The Main ETL flow to load data into Big Query """
    color = 'yellow'
    year = 2020
    month = 5
    path = extract_from_lake(color,year,month)
    df = transform(path)
    load_to_bq(df)


if __name__ == '__main__':
    etl_lake_to_wh()
