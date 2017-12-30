import pandas as pd
from dbutils.panama import update_series
from dbutils.panama import update_fx
from sqlalchemy import create_engine
from wrapper_v2 import IBWrapper, IBclient
from swigibpy import Contract as IBcontract
callback = IBWrapper()
ib_client = IBclient(callback)

engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
print("retrieving roll schedule...")
roll_schedule_df = pd.read_sql_table(table_name="roll_schedule", con=engine)
print("retrieving market data...")
marketdata_df = pd.read_sql_table(table_name="marketdata", con=engine)
print("processing updates...")
for row in marketdata_df.itertuples():
    market = row.CARVER
    if row.SECTYPE == 'FUT':
    #if market in ['AUD']:
        market_series = row
        roll_df = roll_schedule_df[roll_schedule_df['CARVER'] == row.CARVER]
        print("========================", row.CARVER, "==========================================================")
        print(roll_df)
        print("==================================================================================================")
        coll = update_series(engine, ib_client, market_series, roll_df)
    elif row.SECTYPE == 'CASH':
        print("========================", row.CARVER, "==========================================================")
        update_fx(engine, ib_client, row)
        print("==================================================================================================")


