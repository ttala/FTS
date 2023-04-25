#!/usr/bin/python
from flights_call_process import *
from datetime import datetime

print('-----------####--------------')
now = datetime.now().strftime("%A %d %b %Y, %H:%M:%S")
print(f'Task starts at: {now} s')
# Query MongoDB for en-route flights
df_db = get_enRoute_flights()

# Get live flights from Airlab
raw_flights = get_airlab_flights()
df_ab = clean_filter_flights(raw_flights)

# Updating the MongoDB
updated = update_db_flights(df_ab, df_db)

# Archive and save flights on disk / volume
archive_flights(raw_flights)

now = datetime.now().strftime("%A %d %b %Y, %H:%M:%S")
print(f'Task ends with sucess at: {now} s')
print('-----------####--------------\n\n')
