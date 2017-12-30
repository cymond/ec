import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
roll_table = "roll_schedule"

rolls_df = pd.read_csv("admin/roll_history.csv", \
                      dtype={'CARVER':str, 'PRICE_CONTRACT': str, \
                              'CARRY_CONTRACT':str},\
                      parse_dates=['DATETIME'])

rolls_df.sort_values(['CARVER', 'DATETIME'], inplace=True)


print(rolls_df)

try:
    rolls_df.to_sql(name=roll_table, con=engine, if_exists='replace', index=False)
except Exception as e:
    print("Problem with database update: ", e)
