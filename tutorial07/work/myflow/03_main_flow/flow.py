import requests
import pandas as pd
from datetime import datetime
import pytz
from prefect import flow, task # Prefect flow and task decorators

@task
def get_weather_data(province_context={'province':None, 'lat':None, 'lon':None}):
    # API endpoint and parameters
    WEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
    API_KEY = "e5571f88fb32067fe934a6793b8b3108"  # Replace with your actual API key
    province=province_context['province']
    
    params = {
        "lat": province_context['lat'],
        "lon": province_context['lon'],
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        # Make API request
        response = requests.get(WEATHER_ENDPOINT, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        # Convert timestamp to datetime
        # created_at = datetime.fromtimestamp(data['dt'])

        dt = datetime.now()
        thai_tz = pytz.timezone('Asia/Bangkok')
        created_at = dt.replace(tzinfo=thai_tz)


        timestamp = datetime.now()
        
        # Create dictionary with required fields
        weather_dict = {
            'timestamp': timestamp,
            'year': timestamp.year,
            'month': timestamp.month,
            'day': timestamp.day,
            'hour': timestamp.hour,
            'minute': timestamp.minute,
            'created_at': created_at,
            'requested_province':province,
            'location': data['name'],
            'weather_main': data['weather'][0]['main'],
            'weather_description': data['weather'][0]['description'],
            'main.temp': data['main']['temp']
        }
        
        # Create DataFrame
        # df = pd.DataFrame([weather_dict])
        
        # return df
        return weather_dict

    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except KeyError as e:
        print(f"Error processing data: Missing key {e}")
        return None
@flow(name="main-flow", log_prints=True)
def main_flow(parameters={}):
    provinces = {
    "Pathum Thani":{
        "lat": 14.0134,
        "lon": 100.5304
    },
    "Bangkok":{
            "lat": 13.7367,
            "lon": 100.5232
    },
    "Chiang Mai":{
        "lat": 18.7883,
        "lon": 98.9853
    },
    "Phuket":{
        "lat": 7.9519,
        "lon": 98.3381
    }
}
    # for province in provinces.keys:
    #     province_context={
    #         'province':province,
    #         'lat':provinces[province]['lat'],
    #         'lon':provinces[province]['lon'],
    #     }
    #     get_weather_data(province_context)
        
    df=pd.DataFrame([get_weather_data(
        {
            'province':province,
            'lat':provinces[province]['lat'],
            'lon':provinces[province]['lon'],
        }
    ) for province in list(provinces.keys())])
    
        # lakeFS credentials from your docker-compose.yml
    ACCESS_KEY = "access_key"
    SECRET_KEY = "secret_key"
    
    # lakeFS endpoint (running locally)
    lakefs_endpoint = "http://lakefs-dev:8000/"
    
    # lakeFS repository, branch, and file path
    repo = "weather"
    branch = "main"
    path = "weather.parquet"
    
    # Construct the full lakeFS S3-compatible path
    lakefs_s3_path = f"s3a://{repo}/{branch}/{path}"
    
    # Configure storage_options for lakeFS (S3-compatible)
    storage_options = {
        "key": ACCESS_KEY,
        "secret": SECRET_KEY,
        "client_kwargs": {
            "endpoint_url": lakefs_endpoint
        }
    }
    df.to_parquet(
        lakefs_s3_path,
        storage_options=storage_options,
        partition_cols=['year','month','day','hour'],
        
    )