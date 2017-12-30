#from dbutils.capital import get_trade_capital
from private.SystemR.mysqldata import mysqlFuturesData
from systems.provided.futures_chapter15.estimatedsystem import futures_system
import pandas as pd
from sqlalchemy import create_engine
from dbutils.ibwrapper import get_net_liquidation
from dbutils.capital import get_capital_from_db
engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
capital_table = "capital"

def get_offset():
    return 0

def set_capital(nlv, offset):
    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    try:
        capital_df = pd.read_sql_table(table_name=capital_table, con=engine, index_col=['DATE'])
    except Exception as e:
        print("Read failed ", e)

    capital_df.loc[today] = {"IB_CAPITAL": nlv, "OFFSET": offset}
    capital_df.reset_index(inplace=True)
    try:
        capital_df.to_sql(name=capital_table, con=engine, if_exists='replace', index=False)
    except Exception as e:
        print("Write failed ", e)

    print("... managed to set table ????...")

def get_config(net_liquidation_value):
    from sysdata.configdata import Config
    config_dict = dict(notional_trading_capital=net_liquidation_value)
    config = Config(["private.SystemR.production01.yaml", config_dict])
    return config

def main():
    print("In PROD!!!!!!")
    data = mysqlFuturesData()
    try:
        net_liquidation = get_net_liquidation()
        offset = get_offset()
        trading_capital = net_liquidation + offset
        set_capital(net_liquidation, offset)        # Set the latest trade capital in database
    except Exception as e:
        print("IB read failed", e)
        trading_capital = get_capital_from_db()

    print("Trading Capital: ", trading_capital)

    configuration = get_config(trading_capital)
    system = futures_system(data = data, config = configuration, log_level="on")

    print("Instrument List")
    print(system.get_instrument_list())
    print()
    print(system.accounts.portfolio().stats())
    print("Pickling the system....")

    system.pickle_cache("", fullfilename="/results/system.pck")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
