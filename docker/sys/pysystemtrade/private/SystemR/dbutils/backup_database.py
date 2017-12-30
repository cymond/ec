import pandas as pd
from sqlalchemy import create_engine
backup_dir = "/backup/"
engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
control_tables = ["roll_schedule", "instrumentconfig","costs_analysis", "marketdata"]
dict = {}
for table in control_tables:
    var_df = table + "df"
    var_df = pd.read_sql_table(table_name=table, con=engine)
    dict[table] = var_df
    print("retrieving " + table + "...")
    #print(var_df)
    filename = backup_dir + table + ".csv"
    var_df.to_csv(filename, index=False)
for row in dict["marketdata"].itertuples():
    print("===============================================")

    symbol = row.CARVER.lower()
    print("Backing up files for symbol: ", symbol)
    files = []
    if row.SECTYPE == 'FUT':
        # backup PRICE and CARRY streams
        price_tab = symbol + "_price"
        carry_tab = symbol + "_carrydata"
        for table in [price_tab, carry_tab]:
            filename = backup_dir + table + ".csv"
            try:
                df = pd.read_sql_table(table_name=table, con=engine)
                df.to_csv(filename, index=False)
            except Exception as e:
                print(e, " Can't access table: ", table)
        # backup raw data
        for line in (dict["roll_schedule"][(dict["roll_schedule"]['CARVER'] == row.CARVER)]).itertuples():
            # collect PRICE and CARRY maturities
            files.append(symbol + str(line.CARRY_CONTRACT))
            files.append(symbol + str(line.PRICE_CONTRACT))
        for x in (list(set(files))): # remove duplicates
            try:
                var_df = pd.read_sql_table(table_name=x, con=engine)
                filename = backup_dir + x + ".csv"
                var_df.to_csv(filename, index=False)
            except Exception as e:
                print(e, " Can't access table: ", x)
    elif row.SECTYPE == 'CASH':
        table = row.CARVER + "fx"
        try:
            df = pd.read_sql_table(table_name=table, con=engine)
            filename = table + ".csv"
            df.to_csv(filename, index=False)
        except Exception as e:
            print(e, " Can't access table: ", table)






#for row in dict["roll_schedule"].itertuples():
#    print(row)

# Backup the raw data for each market
# For each market in marketdata backup a;; corresponding raw data contracts in roll-schedule
