from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
import numpy as np
import pandas as pd
from dbutils.capital import get_capital_from_db
from wrapper_v5 import IBWrapper, IBclient
from datetime import *


def add_system_positions(downloads_df):
    import sqlalchemy
    from sysdata.configdata import Config
    from systems.provided.futures_chapter15.estimatedsystem import futures_system
    from private.SystemR.mysqldata import mysqlFuturesData

    pickle_file = "private.SystemR.system.pck"

    capital = capital = get_capital_from_db()
    capital_dict = dict(notional_trading_capital=capital)
    new_config = Config(["private.SystemR.production01.yaml", capital_dict])
    data = mysqlFuturesData()
    system = futures_system(data=data, config=new_config, log_level="on")
    system.unpickle_cache(pickle_file)

    downloads_df['SYSTEM_POSITION'] = 0
    downloads_df.reset_index(inplace=True)
    for counter, row in enumerate(downloads_df.itertuples(),1):
        position =system.accounts.get_buffered_position(row.CARVER, roundpositions=True)[-1:].iloc(0)[0]
        downloads_df.set_value(counter-1, 'SYSTEM_POSITION',position)
    downloads_df.set_index(['CARVER'], inplace=True)

    return downloads_df

def get_market_data():
    market_data_df = pd.read_sql_table(table_name='marketdata', con=engine, index_col=['CARVER'])
    return market_data_df

def get_curr_contracts():
    # From the roll-schedule, for each market, determine what markets we should have
    # and the ones we'll next roll into as of today (assume rolls up to yesterBD have happened)

    roll_table = 'roll_schedule'
    market_data = get_market_data()
    roll_df = pd.read_sql_table(table_name=roll_table, \
                                con=engine, index_col=['DATETIME'],
                                parse_dates=['DATETIME'])
    roll_df.reset_index(inplace=True)

    current_rolls = roll_df[roll_df['DATETIME'] < datetime.now()].groupby(['CARVER']).last()

    return current_rolls

def add_latest_donwloads(contracts_df):
    # Return the actual latest rows in the database...
    from private.SystemR.mysqldata import mysqlFuturesData
    yesterBD = pd.datetime.today() - pd.tseries.offsets.BDay(1)
    data = mysqlFuturesData()
    contracts_df['LAST_DOWNLOAD'] = pd.NaT
    dict_list = []
    print("****************************")
    contracts_df.reset_index(inplace=True)
    for counter, row in enumerate(contracts_df.itertuples(),1):
        last_dl_date = data.get_instrument_raw_carry_data(row.CARVER).iloc[-1:].index[0]
        contracts_df.set_value(counter-1, 'LAST_DOWNLOAD', last_dl_date)
    contracts_df.set_index(['CARVER'], inplace=True)
    return contracts_df

def get_curr_next_contracts():
    # From the roll-schedule, for each market, determine what markets we should have
    # and the ones we'll next roll into as of today (assume rolls up to yesterBD have happened)

    roll_table = 'roll_schedule'
    market_data = get_market_data()
    roll_df = pd.read_sql_table(table_name=roll_table, \
                                con=engine, index_col=['DATETIME'],
                                parse_dates=['DATETIME'])
    roll_df.reset_index(inplace=True)

    current_rolls = roll_df[roll_df['DATETIME'] < datetime.now()].groupby(['CARVER']).last()
    next_rolls = roll_df[roll_df['DATETIME'] >= datetime.now()].groupby(['CARVER']).first()
    next_rolls['DAYSTOROLL'] = 0
    next_rolls.reset_index(inplace=True)
    for counter, row in enumerate(next_rolls.itertuples(), 1):
        days_left = (row.DATETIME.date() - date.today()).days
        next_rolls.set_value(counter - 1, 'DAYSTOROLL', days_left)
    next_rolls.set_index(['CARVER'], inplace=True)
    contracts_df = current_rolls.join(next_rolls, how='left', lsuffix='_current', rsuffix='_next')
    return contracts_df

def mat_from_expiry(row):
    # Adjust
    if row['IB'] == 'NG':
        row['EXPIRY'] = int(row['EXPIRY']) + 1
        row['EXPIRY'] = str(row['EXPIRY'])
    return row.EXPIRY

callback = IBWrapper()
client = IBclient(callback)

# return brokerage account positions from IB

contracts = get_curr_next_contracts()
# Add download date...

packed = add_latest_donwloads(contracts)

print(packed)



'''
market_data_df = pd.read_sql_table(table_name='marketdata', con=engine, index_col=['CARVER'])
(account_value, portfolio_data) = client.get_IB_account_data()
port_df1 = pd.DataFrame(portfolio_data)
port_df1 = port_df1.ix[:,[0,1,2,3,6,8]]
port_df1.columns = ['IB', 'EXPIRY', 'BROKER_POSITION', 'CURRENT_PRICE', 'GAIN', 'CURRENCY']
port_df1['EXPIRY'].replace('', np.nan, inplace=True)
portfolio_positions = port_df1[pd.notnull(port_df1['EXPIRY'])].copy()
portfolio_positions['EXPIRY'] = portfolio_positions.EXPIRY.str[:6]
portfolio_positions['EXPIRY'] = portfolio_positions.apply(mat_from_expiry, axis=1)
portfolio_positions = portfolio_positions[portfolio_positions['BROKER_POSITION'] != 0]
#portfolio_positions = portfolio_positions.set_index(['IB'])
current_df = current_contracts['PRICE_CONTRACT']
market_carver = market_data_df[['IB']]
market_carver = market_carver.join(current_df, how="left")
market_carver = market_carver[pd.notnull(market_carver['PRICE_CONTRACT'])]
market_carver.reset_index(inplace=True)
market_carver.set_index(['IB'], inplace=True)
portfolio_positions.set_index(['IB'], inplace=True)
df = portfolio_positions.append(market_carver)
market_carver = market_carver.join( portfolio_positions, how="left")
print(market_carver)
portfolio_positions['CARVER'] = ""
portfolio_positions.reset_index(inplace=True)
#portfolio_positions.rename({0: 'IB'}, inplace=True)
for counter, row in enumerate(portfolio_positions.itertuples(), 1):
    carver_value = market_data_df[market_data_df['IB'] == row.IB].index.values[0]
    portfolio_positions.set_value(counter - 1, 'CARVER', carver_value)
portfolio_positions.set_index(['CARVER'], inplace=True)
print(portfolio_positions)

'''








"""

from private.SystemR.wrapper_v5 import IBWrapper, IBclient
from swigibpy import Contract as IBcontract
import pandas as pd
callback = IBWrapper()
client = IBclient(callback)
(account_value, portfolio_data) = client.get_IB_account_data()
account_value_df = pd.DataFrame(account_value, columns=['KEY', 'VALUE', 'CURRENCY', 'ACCOUNT'])
account_value_df.set_index('KEY', inplace=True)
account = float(account_value_df.loc['NetLiquidation']['VALUE'])
print(account_value_df)







from systems.provided.futures_chapter15.basesystem import futures_system
pickle_file = "private.SystemR.system.pck"
system = futures_system(log_level="on")
system.unpickle_cache(pickle_file)

system.get_instrument_list()


import pandas as pd
from sysdata.configdata import Config
from sysdata.csvdata import csvFuturesData
from private.SystemR.mysqldata import mysqlFuturesData


from systems.provided.futures_chapter15.estimatedsystem import futures_system
capital_file =   capital_file = 'admin/capital/capital.csv'
capital_df = pd.read_csv(capital_file, usecols=[0, 1, 2])
capital = capital_df[-1:].reset_index()['IB_CAPITAL'][0]
capital_dict = dict(notional_trading_capital=capital)
new_config = Config(["private.SystemR.production01.yaml", capital_dict])
data = mysqlFuturesData()
system = futures_system(data=data, config=new_config, log_level="on")
system_sharpe = system.accounts.portfolio().sharpe()


print(system.get_instrument_list())
print(system_sharpe)
print("Pickling the system....")
system.pickle_cache("private.SystemR.system.pck")
"""



