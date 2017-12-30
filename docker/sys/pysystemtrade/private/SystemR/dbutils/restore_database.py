import os,time
import pandas as pd
from sqlalchemy import create_engine
print("Starting... ")
# Read control files, raw_data_files
backup_dir = "/backup/"
time.sleep(2)
engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
# created the engine
print("Created the engine....")
for root, dirs, files in os.walk(backup_dir):
    print("Looping...")
    print(files)
    for file in files:
        print(backup_dir + file)
        table = file[:-4]
        roll_df = pd.read_csv(backup_dir + file)
        print("Writing table: ", table, "to database...")
        roll_df.to_sql(name=table, con=engine, if_exists='replace', index=False)



