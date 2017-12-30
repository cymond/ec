import pandas as pd
from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
capital_table = "capital"


def get_capital_from_db():
    capital_df = pd.read_sql_table(table_name=capital_table, con=engine, index_col=['DATE'])
    capital = (int(capital_df[-1:].iloc[0]['IB_CAPITAL'] * 100) + int(capital_df[-1:].iloc[0]['OFFSET'] * 100)) / 100
    return capital

def get_capital_df():
    capital_df = pd.read_sql_table(table_name=capital_table, con=engine, index_col=['DATE'])
    nlv = (int(capital_df[-1:].iloc[0]['IB_CAPITAL'] * 100) + int(capital_df[-1:].iloc[0]['OFFSET'] * 100)) / 100
    return capital_df


def get_offset():
    return 0


def set_capital(nlv, offset):
    import datetime
    print("in set capital...")
    today = datetime.date.today().strftime('%Y%m%d')
    print("today: ", today)

    try:
        capital_df = pd.read_sql_table(table_name=capital_table, con=engine, index_col=['DATE'])
    except Exception as e:
        print("Read failed ", e)
    print("read table ????...")
    capital_df.loc[today] = {"IB_CAPITAL": nlv, "OFFSET": offset}
    capital_df.reset_index(inplace=True)
    try:
        capital_df.to_sql(name=capital_table, con=engine, if_exists='replace', index=False)
    except Exception as e:
        print("Write failed ", e)

    print("... managed to set table ????...")


def get_IB_net_liquidation():
    from private.SystemR.wrapper_v5 import IBWrapper, IBclient
    callback = IBWrapper()
    client = IBclient(callback)
    (account_value, portfolio_data) = client.get_IB_account_data()
    net_liquidation = float([value for (key,value, currency, account) in account_value if key == 'NetLiquidation'][0])
    return net_liquidation



def get_trade_capital():
    try:
        # get nlv from IB
        nlv = get_IB_net_liquidation()
        print("in get trade capital, nlv: ", nlv)
        offset = get_offset()
        trade_capital = nlv + offset
        print("got trade capital: ", trade_capital)
        # save value to database
        # set_capital(nlv, offset)
    except Exception as e:
        # get nlv from database
        print("Problem getting liquidation value: ", e)
        capital_df = get_capital_df()
        capital_cents = int(capital_df[-1:].iloc[0]['IB_CAPITAL'] * 100)
        offset_cents = get_offset() * 100
        trade_capital = (capital_cents + offset_cents) / 100
    return trade_capital
