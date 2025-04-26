from prefect import flow, task
import requests
import pandas as pd
from datetime import datetime
import pytz
import json
import boto3
import io
import pyarrow.parquet as pq
import logging

# Configuration
API_KEY = "e5571f88fb32067fe934a6793b8b3108"
LAKEFS_ENDPOINT = "http://lakefs-dev:8000/"
LAKEFS_REPO = "weather"
LAKEFS_BRANCH = "main"
LAKEFS_ACCESS_KEY = "access_key"
LAKEFS_SECRET_KEY = "secret_key"
STORAGE_OPTIONS = {
    "key": LAKEFS_ACCESS_KEY,
    "secret": LAKEFS_SECRET_KEY,
    "client_kwargs": {"endpoint_url": LAKEFS_ENDPOINT}
}
EXPECTED_SCHEMA = {
    "timestamp": "datetime64[ns, UTC]",
    "year": "int64",
    "month": "int64",
    "day": "int64",
    "hour": "int64",
    "minute": "int64",
    "created_at": "object",
    "requested_province": "string",
    "location": "string",
    "weather_main": "string",
    "weather_description": "string",
    "main.temp": "float64",
    "humidity": "int64",
    "wind_speed": "float64"
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task
def get_weather_data(province_context):
    """
    Fetch weather data from OpenWeatherMap API for a given province.
    """
    WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": province_context['lat'],
        "lon": province_context['lon'],
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(WEATHER_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        dt = datetime.now(pytz.utc)
        thai_tz = pytz.timezone('Asia/Bangkok')
        created_at = dt.astimezone(thai_tz)
        weather_dict = {
            'timestamp': dt.isoformat(),
            'year': dt.year,
            'month': dt.month,
            'day': dt.day,
            'hour': dt.hour,
            'minute': dt.minute,
            'created_at': created_at.isoformat(),
            'requested_province': province_context['province'],
            'location': data['name'],
            'weather_main': data['weather'][0]['main'],
            'weather_description': data['weather'][0]['description'],
            'main.temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed']
        }
        return weather_dict
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {province_context['province']}: {e}")
        return None

@task
def process_data(weather_data):
    """
    Process raw weather data into a Pandas DataFrame with explicit data types.
    """
    df = pd.DataFrame(weather_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Asia/Bangkok')
    string_columns = ['requested_province', 'location', 'weather_main', 'weather_description']
    for col in string_columns:
        df[col] = df[col].astype('string')
    df[['year', 'month', 'day', 'hour', 'minute', 'humidity']] = df[['year', 'month', 'day', 'hour', 'minute', 'humidity']].astype('int64')
    df[['main.temp', 'wind_speed']] = df[['main.temp', 'wind_speed']].astype('float64')
    return df

@task
def store_data(df, storage_options, lakefs_s3_path):
    """
    Store the DataFrame to lakeFS as partitioned Parquet files.
    """
    df.to_parquet(
        lakefs_s3_path,
        storage_options=storage_options,
        partition_cols=['year', 'month', 'day', 'hour'],
        index=False,
        compression='snappy'
    )

@task
def generate_summary_report(storage_options, repo, branch, expected_schema):
    """
    Generate a summary report of the dataset and store it in lakeFS.
    """
    s3 = boto3.client(
        's3',
        endpoint_url=storage_options['client_kwargs']['endpoint_url'],
        aws_access_key_id=storage_options['key'],
        aws_secret_access_key=storage_options['secret']
    )
    response = s3.list_objects_v2(Bucket=repo, Prefix=f"{branch}/data/weather.parquet/")
    if not response.get('Contents'):
        logger.warning("No data files found in lakeFS.")
        return None
    
    dfs = []
    for obj in response['Contents']:
        if obj['Key'].endswith('.parquet'):
            data = s3.get_object(Bucket=repo, Key=obj['Key'])
            table = pq.read_table(data['Body'])
            df = table.to_pandas()
            dfs.append(df)
    full_df = pd.concat(dfs, ignore_index=True)
    
    # Dataset overview
    record_count = len(full_df)
    start_time = full_df['timestamp'].min().isoformat()
    end_time = full_df['timestamp'].max().isoformat()
    time_span = (pd.to_datetime(end_time) - pd.to_datetime(start_time)).total_seconds() / 3600
    provinces = full_df['requested_province'].unique()
    num_provinces = len(provinces)
    expected_intervals = (time_span * 60) / 5  # Assuming 5-minute intervals
    expected_records = int(expected_intervals) * num_provinces
    completeness = record_count / expected_records if expected_records > 0 else 0
    has_object = any(dtype == 'object' for dtype in full_df.dtypes)
    duplicate_count = int(full_df.duplicated().sum())
    
    # Columns details
    columns_info = {
        col: {
            'dtype': str(full_df[col].dtype),
            'non_null_count': int(full_df[col].notnull().sum()),
            'unique_values': int(full_df[col].nunique()),
            'missing_values': int(full_df[col].isnull().sum())
        } for col in full_df.columns
    }
    
    # Schema compliance
    compliance_report = {}
    for col, expected_dtype in expected_schema.items():
        if col in full_df.columns:
            actual_dtype = str(full_df[col].dtype)
            compliance_report[col] = 100.0 if actual_dtype == expected_dtype else 0.0
        else:
            compliance_report[col] = 0.0  # Column missing
    
    # Sample data
    head = full_df.head(1).to_dict(orient='records')
    tail = full_df.tail(1).to_dict(orient='records')
    
    # Construct report
    report = {
        'overview': {
            'record_count': record_count,
            'start_time': start_time,
            'end_time': end_time,
            'time_span_hours': time_span,
            'completeness': completeness,
            'has_object_dtype': has_object,
            'duplicate_count': duplicate_count
        },
        'columns': columns_info,
        'schema_compliance': {
            'compliance_report': compliance_report,
            'overall_compliance': sum(compliance_report.values()) / len(compliance_report) if compliance_report else 0
        },
        'sample_data': {
            'head': head,
            'tail': tail
        }
    }
    
    # Save report to lakeFS
    report_path = f"{branch}/reports/summary.json"
    report_json = json.dumps(report, default=str)
    s3.put_object(
        Bucket=repo,
        Key=report_path,
        Body=report_json,
        ContentType='application/json'
    )

@flow(name="main-flow", log_prints=True)
def main_flow(parameters={}):
    """
    Main flow to collect, process, store weather data, and generate a summary report.
    """
    provinces = {
        "Pathum Thani": {"lat": 14.0134, "lon": 100.5304},
        "Bangkok": {"lat": 13.7367, "lon": 100.5232},
        "Chiang Mai": {"lat": 18.7883, "lon": 98.9853},
        "Phuket": {"lat": 7.9519, "lon": 98.3381}
    }
    
    weather_futures = [get_weather_data.submit({'province': p, 'lat': c['lat'], 'lon': c['lon']}) for p, c in provinces.items()]
    weather_data = [future.result() for future in weather_futures if future.result() is not None]
    
    if not weather_data:
        logger.error("No weather data collected. Exiting flow.")
        return
    
    df = process_data(weather_data)
    lakefs_s3_path = f"s3a://{LAKEFS_REPO}/{LAKEFS_BRANCH}/data/weather.parquet"
    store_data(df, STORAGE_OPTIONS, lakefs_s3_path)
    generate_summary_report(STORAGE_OPTIONS, LAKEFS_REPO, LAKEFS_BRANCH, EXPECTED_SCHEMA)

if __name__ == "__main__":
    main_flow()