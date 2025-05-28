from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pg_models import Base, Airline, Airport
import configparser
import os, csv
import psycopg2
from dotenv import load_dotenv


load_dotenv()

#config_path = '/home/ttyeri/work/flights-tracking/flights_tracking_stats/config.ini'

# Init the engine
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
    return conn


def load_airport(csv_file):
    try:
        connect = postgre_connect()
        if not connect:
            print('Connection failed !')
            return
        cursor = connect.cursor()
    
        # Droping table if already exists.
        cursor.execute("DROP TABLE IF EXISTS airport")
        sql = "CREATE TABLE airport (\
                iata VARCHAR(7) PRIMARY KEY,\
                city VARCHAR(124) NOT NULL,\
                name VARCHAR(124) NOT NULL,\
                country VARCHAR(124) NOT NULL\
        );"
        cursor.execute(sql)
        connect.commit()
        sql_insert = "INSERT INTO airport (iata, name, city, country) values(%s,%s,%s,%s)"
        data = []
        with open(csv_file, 'r', encoding="utf-8") as fn:
            csv_reader = csv.reader(fn, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'{csv_file}\nColumn names are {", ".join(row)}')
                    id_iata = row.index('iata')
                    id_name = row.index('name')
                    id_city = row.index('city')
                    id_country = row.index('country')
                    line_count += 1
                elif row[0]:
                    airport = (row[id_iata], row[id_name], row[id_city], row[id_country])
                    cursor.execute(sql_insert, airport)
            
            connect.commit()
    except (Exception, psycopg2.Error) as error:
        print(error)
        import pdb;pdb.set_trace()
    
    finally:
        # closing database connection.
        if connect:
            cursor.close()
            connect.close()


def load_airline(csv_file):
    try:
        connect = postgre_connect()
        if not connect:
            print('Connection failed !')
            return
        cursor = connect.cursor()
    
        # Droping table if already exists.
        cursor.execute("DROP TABLE IF EXISTS airline")
        sql = "CREATE TABLE airline (\
                iata VARCHAR(7) PRIMARY KEY,\
                name VARCHAR(124) NOT NULL,\
                country VARCHAR(124) NOT NULL\
        );"
        cursor.execute(sql)
        connect.commit()
        sql_insert = "INSERT INTO airline (iata, name, country) values(%s,%s,%s)"
        data = []
        with open(csv_file, 'r', encoding="utf-8") as fn:
            csv_reader = csv.reader(fn, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'{csv_file}\nColumn names are {", ".join(row)}')
                    id_iata = row.index('iata')
                    id_name = row.index('name')
                    id_country = row.index('country')
                    line_count += 1
                elif row[0]:
                    airport = (row[id_iata], row[id_name], row[id_country])
                    cursor.execute(sql_insert, airport)
            
            connect.commit()
    except (Exception, psycopg2.Error) as error:
        print(error)
        import pdb;pdb.set_trace()
    
    finally:
        # closing database connection.
        if connect:
            cursor.close()
            connect.close()


# then create them new and load them using reference csv's
if '__main__' == __name__:

    # session = get_session(engine)
    script_dir = os.path.dirname(__file__)
    csv_file = os.path.join(script_dir, r'airlines.csv')
    load_airline(csv_file)
    csv_file = os.path.join(script_dir, r'airports.csv')
    load_airport(csv_file)
    # session.close()
