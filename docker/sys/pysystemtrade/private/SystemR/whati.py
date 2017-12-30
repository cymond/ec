import sys, os

# ------------------------------------------------------------
print("sys.executable: ", sys.executable)
print("os.get_cwd(): ", os.getcwd())
print("sys.version: ", sys.version)
print("sys.path")
print(sys.path)
print("--------------------------")
print("os.path: ", os.path)
print('\n'.join(sys.path))
print("os.path.dirname(__file___): ", os.path.dirname(__file__))
print(os.path.join(os.path.dirname(__file__), '..'))
print("--------------------------")
print("Try this: ", os.path.dirname(os.path.abspath(__file__)))
i = 0
while i < 3:
	print(i + 1, ": Mase is learning to code in Python")
	i = i+1
print("---------------2-----------")
print("---------------3-----------")
print("---------------4-----------")
import pandas as pd
from sqlalchemy import create_engine
print("Starting... ")
# Read control files, raw_data_files
backup_dir = "/results/"
print("Backup directory: ",backup_dir)
try:
    engine = create_engine('mysql+pymysql://root:admin@0mysql_server:3306/pkdemo')
except Exception as e:
    print("Cannot create engine: ",e)

for root, dirs, files in os.walk(backup_dir):
    for file in files:
        table = file[:-4]
        roll_df = pd.read_csv(backup_dir + file)
        print("Writing table: ", table, "to database...")
        roll_df.to_sql(name=table, con=engine, if_exists='replace', index=False)
