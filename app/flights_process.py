import requests
import configparser
import pandas as pd
from datetime import datetime
import time
import os
import tarfile
import background
from pymongo import MongoClient
import psycopg2
from dotenv import load_dotenv


load_dotenv()

#config_path = '/home/ttyeri/work/flights-tracking/flights_tracking_stats/config.ini'

def mongo_connect():
    user = os.getenv('MONGO_USERNAME')
    password = os.getenv('MONGO_PASSWORD')
    instance_id = os.getenv('MONGO_ID')
    region = os.getenv('MONGO_REGION')
    #private_network_id = os.getenv('MONGO', 'PRIV_NET_ID')
    tls_certificate = os.path.join('..','mgdb-mongodb.pem')

        
    #db_url = f'mongodb+srv://{user}:{password}@{host}/?retryWrites=true&w=majority'
    db_url = f"mongodb+srv://{user}:{password}@{instance_id}.mgdb.{region}.scw.cloud/?tls=true&tlsCAFile={tls_certificate}"
        
    print(db_url)
    try:
        client = MongoClient(db_url)
    except Exception as ex:
        print(ex)
        import pdb;pdb.set_trace()
    return client

def postgre_connect():
    user = os.getenv('POSTGRESQL_USERNAME')
    password = os.getenv('POSTGRESQL_PASSWORD')
    host = os.getenv('POSTGRESQL_HOST')
    database = os.getenv('POSTGRESQL_DB')
    port = os.getenv('POSTGRESQL_PORT')
    conn = None
    try:
        conn = psycopg2.connect(host=host,database=database,user=user,password=password,port=port)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None
    return conn


def airlab_config():
    api_key = os.getenv('AIRLAB_KEY')
    url = os.getenv('AIRLAB_URL')

    params = {'api_key': api_key}

    return url, params


# Method to make an API call and get all the flight status in real time.
# It returns the result as a pandas dataframe
def get_airlab_flights():
    url_base, params = airlab_config()
    endpoint = 'flights'
    url = url_base + endpoint

    try:
        result = requests.get(url, params=params)
    except requests.exceptions.RequestException as ex:
        raise SystemExit(ex)

    if result.status_code != 200:
        raise RuntimeError(f"Unexpected error during the API call\n{result.text}")
    json_content = result.json()

    return json_content


# Clean and filtering the call API for only Europeans flights (France, Italy, Spain, German, England)
def clean_filter_flights(json_result):
    conn = postgre_connect()
    cursor = conn.cursor()
    # Querying airline db
    cursor.execute('SELECT * FROM airline')
    tupl = cursor.fetchall()
    data = []
    for row in tupl:
        data.append(row)
    airlines = pd.DataFrame(data, columns=('iata', 'name', 'country'))
    # Querying airport db
    cursor.execute("SELECT * FROM airport WHERE country in ('France', 'Italy', 'Spain', 'Germany', 'United Kingdom')")
    tupl = cursor.fetchall()
    data = []
    for row in tupl:
        data.append(row)
    airports = pd.DataFrame(data, columns=('iata', 'name', 'city', 'country'))

    # Closing cursor and connection
    cursor.close()
    conn.close()

    df_airlines = airlines.set_index('iata', drop=False)
    df_airlines = df_airlines[["iata", "name"]].rename(columns={'name':'airline_name', 'iata':'airline_iata'})
    df_airports = airports.set_index('iata', drop=False)
    df_airports_dep = df_airports[["iata", "city", "country", "name"]] \
    .rename(columns={'name':'dep_airport', 'iata':'dep_iata', "country":"dep_country", "city":"dep_city"})
    df_airports_arr = df_airports[["iata", "city", "country", "name"]] \
    .rename(columns={'name':'arr_airport', 'iata':'arr_iata', "country":"arr_country", "city":"arr_city"})
    iata_list = list(df_airlines.index)

    # Filtering API response for 'en-route' and European
    data_df = pd.DataFrame(json_result['response']).set_index('flight_iata', drop=False)
    data_df = data_df[data_df["airline_iata"].isin(iata_list)]
    data_df = data_df[data_df['status'] == 'en-route']
 
    # Cleaning data
    data_df.drop_duplicates(inplace=True, subset=['flight_iata'])  # Drop duplicate flights number
    data_df.insert(0, 'created_at', datetime.now().strftime("%A %d %b %Y, %H:%M:%S")) # Add current timestamp colum
    data_df.insert(0, 'updated_at', datetime.now().strftime("%A %d %b %Y, %H:%M:%S"))

    data_df = data_df.merge(df_airlines, how='left', on='airline_iata')
    data_df = data_df.merge(df_airports_dep, how='left', on='dep_iata')
    data_df = data_df.merge(df_airports_arr, how='left', on='arr_iata')

    #data_df = data_df.drop('dep_iata', axis=1)
    data_df = data_df.drop(['arr_iata', 'dep_iata', 'dir', 'v_speed', 'squawk', 'flight_icao', 'airline_icao'], axis=1)

    subset = ['flight_iata', 'airline_iata', 'arr_airport', 
              'arr_city', 'arr_country', 'arr_airport', 'dep_airport', "dep_country", "arr_country"]
    data_df.dropna(subset=subset, inplace=True)
    data_df = data_df.set_index('flight_iata', drop=False)


    return data_df


# Method to get info for a single flight from Airlab
def get_flight_info(iata):
    url_base, params = airlab_config()
    endpoint = 'flight'
    params['flight_iata'] =iata
    url = url_base + endpoint
    try:
        result = requests.get(url, params=params)
    except requests.exceptions.RequestException as ex:
        raise SystemExit(ex)
    if result.status_code != 200:
        raise RuntimeError(f"Unexpected error during the API call\n{result.text}")
    try:
        result = result.json()['response']
        for var in ['lng', 'lat', 'dep_city', 'arr_city']:
            if var not in result:
                return 0
        if "airline_name" not in result:
            result["airline_name"] = "N/A"
        if "dep_actual_utc" not in result:
            result["dep_actual_utc"] = "N/A"
        if "arr_actual_utc" not in result:
            result["arr_actual_utc"] = "N/A"
        if "arr_time_utc" not in result:
            result["arr_time_utc"] = "N/A"
        if "dep_time_utc" not in result:
            result["dep_time_utc"] = "N/A"
        if "delayed" not in result:
            result["delayed"] = "N/A"
        return result
    except KeyError as ex:
        return 0


# Get all the flights from mongodb
def get_all_flights():
    client = mongo_connect()
    db = client['dst']['flights']
    data = list(db.find({}))
    client.close()
    if len(data) > 0:
        df = pd.DataFrame(data).set_index('flight_iata', drop=False)
        return df
    return pd.DataFrame([])


# Get the list of "en-route" flights from mongodb and return a dataframe or None if the db is empty
def get_enRoute_flights():
    client = mongo_connect()
    db = client['dst']['flights']
    data = list(db.find({"status": "en-route"}))
    client.close()
    if len(data) > 0:
        df = pd.DataFrame(data).set_index('flight_iata', drop=False)
        return df
    return pd.DataFrame([])

# Update the flights in the db using the new ones from Airlab API
@background.task
def update_db_flights(current_flights, db_flights):
    new_flights = []
    list_index = list(db_flights.index)
    if db_flights.empty: # if mongodb is empty, load the current flights in db
        current_flights = change_fields(current_flights)
        load_flights_to_mongodb(current_flights)
    else:
        for num_, flight in current_flights.iterrows():
            iata = flight['flight_iata']
            if iata in list_index:
                try:
                    db_flights.loc[iata, 'lat'].append(flight['lat'])
                    db_flights.loc[iata, 'lng'].append(flight['lng'])
                    db_flights.loc[iata, 'status'] = flight['status']
                    db_flights.loc[iata, 'updated_at'] = datetime.now().strftime("%A %d %b %Y, %H:%M:%S")
                    list_index.remove(iata)     
                except Exception as ex:
                    print(ex)
                    import pdb;pdb.set_trace()  
            else:
                new_flights.append(flight)

        # Change status for flights that aren't any more in real time fligth
        for iata in list_index:
            db_flights.loc[iata, 'status'] = 'landed'
 
        if len(new_flights) > 0:
            new_flights_df = pd.DataFrame(new_flights)
            new_flights_df = change_fields(new_flights_df)
            load_flights_to_mongodb(new_flights_df)
   

        # Update db with previous and new flights
        load_flights_to_mongodb(db_flights)

    return db_flights

  
def change_fields(data):
    data["lat"] = data["lat"].apply(lambda x: [x])
    data["lng"] = data["lng"].apply(lambda x: [x])
    return data


# This method insert the flights into the db if its empty, otherwise its update the flights in the db
def load_flights_to_mongodb(flights):
    client = mongo_connect()
    db = client['dst']['flights']
    
    if db.count_documents({}) == 0:
        db.insert_many(flights.to_dict('records'))
    else:
        dic_flight = flights.to_dict('records')
        to_be_insert = []
        for flight in dic_flight:
            if db.count_documents({'flight_iata': flight.get('flight_iata')}):
                db.update_one({'flight_iata': flight.get('flight_iata')}, {'$set': {'lat': flight.get('lat'),
                        'lng': flight.get('lng'), 'status': flight.get('status')}}, upsert=True)
            else:
                to_be_insert.append(flight)
        if len(to_be_insert) > 0:
            db.insert_many(to_be_insert)



# Create an json from flights and archive it
def archive_flights(flights):
    cwd = os.getcwd()
    path_archive = os.path.join(cwd, 'storage')
    if not os.path.exists(path_archive):
        os.makedirs(path_archive)
    fname = time.strftime("%Y%m%d-%H%M%S")
    path_fne = os.path.join(path_archive, fname)
    with open(path_fne, 'w', encoding='utf8') as fn:
        data = flights.to_json(orient = 'records', default_handler=str)
        fn.write(data)

    tar_file = path_fne + '.tar.gz'
    tar = tarfile.open(tar_file, "w:gz")
    tar.add(tar_file)
    tar.close()
    os.remove(path_fne)

def get_dates(flights):
    flights = flights.sort_values(by='created_at')
    start_date = flights.head(1)
    ends_date = flights.tail(1)
    start_date = start_date.split(',')[0]
    ends_date = ends_date.split(',')[0]
    return start_date, ends_date

if __name__ == '__main__':
    df = get_airlab_flights()
    data = clean_filter_flights(df)
    current_flights = get_airlab_flights()
    db_flights = get_enRoute_flights()
    try:
        update_db_flights(current_flights=current_flights, db_flights=db_flights)
    except Exception as ex:
        print(ex)
        import pdb;pdb.set_trace()
    print('### finish ###')
    