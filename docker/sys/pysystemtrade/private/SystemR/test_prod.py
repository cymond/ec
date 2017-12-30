
from syscore.accounting import account_test

from syscore.pdutils import turnover
from sysdata.configdata import Config
from sysdata.csvdata import csvFuturesData
from private.SystemR.mysqldata import mysqlFuturesData


from systems.provided.futures_chapter15.estimatedsystem import futures_system
#from systems.provided.moretradingrules.morerules import breakout
import pandas as pd
import numpy as np
from matplotlib.pyplot import show, legend, matshow

import time

def set_logging():
    import logging
    logger = logging.getLogger('Downloads')
    logger.setLevel(logging.DEBUG)


    # create file handler which logs even DEBUG messages
    file_handler = logging.FileHandler(logging_file)
    file_handler.setLevel(logging.DEBUG)

    # create a console handler to show errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter and add it to handlers
    # formatter = logging.Formatter('%(message)s')
    console_formatter = logging.Formatter('{asctime} {name} {levelname:8s} {message}', datefmt='%Y%m%d %I:%M:%S%p',\
                                          style='{')
    file_formatter = logging.Formatter('{asctime},{name},{levelname:8s},{message}', datefmt='%Y%m%d %I:%M:%S%p', \
                                       style='{')
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def get_capital_offset():
    '''
    <201701 : 65000
    201702  : 50000
    201703  : 40000
    201704  : 30000
    201705  : 20000
    201706  : 10000
    201707  : 0

    '''
    return 50000

def get_IB_cap():

    from wrapper_v5 import IBWrapper, IBclient
    from swigibpy import Contract as IBcontract
    import pandas as pd
    print("in get_IB_cap")
    callback = IBWrapper()
    client = IBclient(callback)
    print("made callback...")
    (account_value, portfolio_data) = client.get_IB_account_data()
    account_value_df = pd.DataFrame(account_value, columns=['KEY', 'VALUE', 'CURRENCY', 'ACCOUNT'])
    account_value_df.set_index('KEY', inplace=True)
    account = float(account_value_df.loc['NetLiquidation']['VALUE'])
    return account
def update_capital(cap_file, dict):
    print("Update here", cap_file)
    print(dict)

def main():

    import sys,os



    # **** Get capital from capital_file
    cap_df = pd.read_csv(capital_file,  usecols=[0,1,2])
    cap_df.columns = ['DATE', 'IB_CAPITAL','OFFSET']
    if cap_df.empty:
        capital = 450000
    else:
        capital = cap_df[-1:].reset_index(drop=True)[0:]['IB_CAPITAL'][0]
        offset = cap_df[-1:].reset_index(drop=True)[0:]['OFFSET'][0]

    print(" ***ib capital: ", capital)
    print("***offset: ", offset)

    # Save to file the daily capital
    cap_dict = {'DATE': today, 'IBCAP': capital, 'CORRECTION': offset}
    update_capital(capital_file, cap_dict)

    my_config_dict = dict(notional_trading_capital=capital)
    print(my_config_dict)
    new_config = Config(["private.SystemR.test_downloads.yaml", my_config_dict])

    # new_config = Config("private.SystemR.production01.yaml")
    # pointer to data
    #data = csvFuturesData("private.SystemR.data")

    # **** Create the system ****
    #system = futures_system(data=data, config=new_config, log_level="on")

    #new_config = Config("private.SystemR.production01.yaml")
    # pointer to data
    #data=csvFuturesData("private.SystemR.data")
    data = mysqlFuturesData()

    system = futures_system(data=data, config=new_config, log_level="on")

    instruments = pd.DataFrame(system.get_instrument_list() )
    print("Pickle the system....")
   # system.pickle_cache("private.SystemR.system.pck")

    print(instruments)


    counter = 0
    linestring = 'CONTRACT,MATURITY,QUANTITY\n'
    positions_file_handle = open(positions_file, 'w')
    history_file_handle = open(history_file, 'w')
    positions_file_handle.write(linestring)
    history_file_handle.write(linestring)
    positions_file_handle.close()
    history_file_handle.close()
    for i in instruments.itertuples():

        counter = counter + 1
        print("*****************")
        print("***Insturment***", i)
        print("**** i[1]", i[1])
        print("*****************")
        dfBufferedPositions = pd.DataFrame(system.accounts.get_buffered_position(i[1], roundpositions=True))
    #    dfBufferedPositions = pd.DataFrame(system.portfolio.get_notional_position (i[1]))
        dfPriceContract = pd.DataFrame(system.data.get_instrument_raw_carry_data(i[1]))
        dfPriceContract = dfPriceContract[['PRICE_CONTRACT']]
        sub_cont_df = dfPriceContract[-1:]
        sub_price_df = dfBufferedPositions[-1:]

        linestring = i[1] + "," +  str(sub_cont_df.iloc[0]['PRICE_CONTRACT'])   + "," + str(int(sub_price_df.iloc[0][0])) + "\n"
        print(linestring)
        positions_file_handle = open(positions_file, 'a')
        history_file_handle = open(history_file, 'a')
        positions_file_handle.write(linestring)  # python will convert \n to os.linesep
        history_file_handle.write(linestring)  # python will convert \n to os.linesep
        positions_file_handle.close()
        history_file_handle.close()

    #system_ne.portfolio.get_instrument_list

    print(system.accounts.portfolio().stats())

    #system.accounts.portfolio().cumsum().plot()

    #show()
    print()

    print("notional capital: ", system.accounts.get_notional_capital())

    report_path = admin_path  + 'test/reports/' +  today
    monthly_sr = system.accounts.portfolio().resample("M").sum()
    monthly_df = monthly_sr.to_frame()
    monthly_df.columns = ['GAIN']
    monthly_df["GAIN"] = monthly_df["GAIN"].fillna(0)
    monthly_df['PERCENT'] = monthly_df["GAIN"]/3910
    system.accounts.portfolio().resample("B").sum().to_csv(report_path + "_daily.csv")
    monthly_df.to_csv(report_path + "_monthly.csv")
    system.accounts.portfolio().resample("A").sum().to_csv(report_path + "_annual.csv")
    system.accounts.portfolio().cumsum().to_csv(report_path + "_cum.csv")
    print("Now writing to Documents folder...")


if __name__ == "__main__":

    today = time.strftime("%Y%m%d")

    dir_filename = "../SystemR/admin/directories.csv"
    # point to output files
    dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
    admin_path = dir_df.loc['ADMIN'][0]
    positions_file = admin_path + 'test/positions/system.csv'
    history_file = admin_path + 'test/positions/history/' + today + "system.csv"
    capital_file = admin_path + 'test/capital/capital.csv'
    logging_file = admin_path + 'test/info.log'

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)




"""
print("sys.executable: ", sys.executable)
    print("os.get_cwd(): ", os.getcwd())
    print("sys.version: ", sys.version)
    print("sys.path")
    print(sys.path)
    print("--------------------------")
    print("os.path: ", os.path)
    print("os.path.dirname(__file___): ",os.path.dirname(__file__))
    print(os.path.join(os.path.dirname(__file__), '..'))
    print("--------------------------")
    print("Try this: ", os.path.dirname(os.path.abspath(__file__)))"""