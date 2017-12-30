#

#


def set_logging():
    import logging
    logger = logging.getLogger('Downloads')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even DEBUG messages
    file_handler = logging.FileHandler('../SystemR/admin/info.log')
    file_handler.setLevel(logging.DEBUG)

    # create a console handler to show errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create formatter and add it to handlers
    # formatter = logging.Formatter('%(message)s')
    console_formatter = logging.Formatter('{asctime} {name} {levelname:8s} {message}', datefmt='%Y%m%d %I:%M:%S%p',
                                          style='{')
    file_formatter = logging.Formatter('{asctime},{name},{levelname:8s},{message}', datefmt='%Y%m%d %I:%M:%S%p',
                                       style='{')
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

def get_capital_offset():

    return 65000

def get_IB_cap():

    from wrapper_v5 import IBWrapper, IBclient
    from swigibpy import Contract as IBcontract
    import pandas as pd

    callback = IBWrapper()
    client = IBclient(callback)

    (account_value, portfolio_data) = client.get_IB_account_data()
    account_value_df = pd.DataFrame(account_value, columns=['KEY', 'VALUE', 'CURRENCY', 'ACCOUNT'])
    account_value_df.set_index('KEY', inplace=True)
    account = float(account_value_df.loc['NetLiquidation']['VALUE'])
    return account
def update_capital(cap_file, dict):
    print("Update here", cap_file)
    print(dict)

def main():

    from sysdata.configdata import Config
    from sysdata.csvdata import csvFuturesData
    from private.SystemR.mysqldata import mysqlFuturesData
    from systems.provided.futures_chapter15.estimatedsystem import futures_system
    import pandas as pd
    import numpy as np
    import os
    from matplotlib.pyplot import show, legend, matshow
    import time

    dir_filename = "../SystemR/admin/directories.csv"
    if not os.path.isfile(dir_filename):
        logger.error("The file, {}, does not exist".format(dir_filename))
    else:
        today = time.strftime("%Y%m%d")
        # point to output files
        dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
        admin_path = dir_df.loc['ADMIN'][0]
        positions_file = admin_path  + 'positions_test/system.csv'
        history_file = admin_path + 'positions_test/history/' + today + "system.csv"
        capital_file = admin_path + 'capital_test/capital.csv'

        # **** Point to data  ****
        #data = csvFuturesData("private.SystemR.data")

        data = mysqlFuturesData()

        new_config = Config("private.SystemR.production01.yaml")
        system = futures_system(data=data,config=new_config,log_level="on")
        print("Before un-pickling...............")
        print("Items with data: ", system.get_items_with_data())  ## check empty cache

        system.unpickle_cache("private.SystemR.system.pck")

        print("After un-pickling...............")
        print("Items with data: ", system.get_items_with_data())  ## Cache is now populated. Any existing data would have been removed.
        print("Accounts.... items")
        print(system.get_itemnames_for_stage("accounts"))  ## now doesn't include ('accounts', 'portfolio', 'percentageTdelayfillTroundpositionsT')
        print("System stages")
        print(system)

        print("Sharpe: ", system.accounts.portfolio().sharpe())
        print("notional capital: ", system.accounts.get_notional_capital())
        print("Instrument list: ", system.get_instrument_list())
        instruments = pd.DataFrame(system.get_instrument_list())
        print("Profit and Loss for Whole System")
        df_sys_pnl = pd.DataFrame(system.accounts.portfolio())
        print(df_sys_pnl.tail(20))
        for i in instruments.itertuples():

            print("*****************")
            print("**** Instrument: ", i[1])
            df_notional_position = pd.DataFrame(system.accounts.get_notional_position(i[1]))
            df_actual_position = pd.DataFrame(system.accounts.get_actual_position(i[1]))
            df_buffered_position = pd.DataFrame(system.accounts.get_buffered_position(i[1], roundpositions=True))
            df_raw_carry_data = pd.DataFrame(system.data.get_instrument_raw_carry_data(i[1]))
            df_rawdata_daily_returns = pd.DataFrame(system.rawdata.daily_returns(i[1]))
            df_rawdata_daily_returns_volatility = pd.DataFrame(system.rawdata.daily_returns_volatility(i[1]))
            df_rawdata_raw_futures_roll = pd.DataFrame(system.rawdata.raw_futures_roll(i[1]))
            df_inst_pnl = pd.DataFrame(system.accounts.pandl_for_instrument_with_multiplier(i[1]))


            print("Notional Position")
            print(df_notional_position.tail(4))
            print("Actual Position")
            print(df_actual_position.tail(4))
            print("Buffered Position")
            print(df_buffered_position.tail(4))
            print("Instrument Raw Carry Data")
            print(df_raw_carry_data.tail(4))
            print("Daily Returs")
            print(df_rawdata_daily_returns.tail(4))
            print("Daily Returns Volatility")
            print(df_rawdata_daily_returns_volatility.tail(4))
            print("Raw Futures Roll")
            print(df_rawdata_raw_futures_roll.tail(4))
            print("Profit and Loss for Instrument")
            print(df_inst_pnl.tail(20))
            print("% statistics for instrument")
            print(system.accounts.pandl_for_instrument(i[1]).percent().stats())

            print("*****************")

        '''

        new_config = Config(["private.SystemR.production01.yaml", my_config_dict])

        # **** Point to data  ****
        data=csvFuturesData("private.SystemR.data")
        # **** Create the system ****
        system = futures_system(data=data, config=new_config, log_level="on")
        system.accounts.portfolio().sharpe()   # Do calculations to save in cache....
        system.pickle_cache("private.SystemR.system.pck")  ## use any file extension you like

        instruments = pd.DataFrame(system.get_instrument_list() )

        counter = 0

        # **** Get today's orders ****

        #positions_file_handle = open(positions_file, 'w')
        #history_file_handle = open(history_file, 'w')

        #linestring = 'CONTRACT,MATURITY,QUANTITY\n'
        #positions_file_handle.write(linestring)
        #history_file_handle.write(linestring)
        #positions_file_handle.close()
        #history_file_handle.close()
        print("Something closed....")
        print(instruments)

        dfBufferedPositions = pd.DataFrame(system.accounts.get_buffered_position('EDOLLAR', roundpositions=True))
        print(dfBufferedPositions[-1:])


        for i in instruments.itertuples():
            counter = counter + 1
            print(counter, i[1])

        #    dfBufferedPositions = pd.DataFrame(system.accounts.get_buffered_position_with_multiplier(i[1], roundpositions=True))
            dfBufferedPositions = pd.DataFrame(system.portfolio.get_notional_position (i[1]))
            print(dfBufferedPositions[-1:])


            df_cost_data = pd.DataFrame(system.data.get_raw_cost_data(i[1]))

            dfPriceContract = pd.DataFrame(system.data.get_instrument_raw_carry_data(i[1]))
            print(dfPriceContract)
            dfPriceContract = dfPriceContract[['PRICE', 'CARRY', 'PRICE_CONTRACT', 'CARRY_CONTRACT']]
            print(dfPriceContract)
            sub_cont_df = dfPriceContract[-1:]
            sub_price_df = dfBufferedPositions[-1:]

            linestring = i[1] + "," +  str(sub_cont_df.iloc[0]['PRICE']) + "," +  str(sub_cont_df.iloc[0]['PRICE_CONTRACT'])  \
                         + "," + str(sub_cont_df.iloc[0]['CARRY']) + "," + str(sub_cont_df.iloc[0]['CARRY_CONTRACT']) + \
                         "," + str(int(sub_price_df.iloc[0][0])) + "\n"
            print(linestring)
            positions_file_handle = open(positions_file, 'a')
            history_file_handle = open(history_file, 'a')
            positions_file_handle.write(linestring)  # python will convert \n to os.linesep
            history_file_handle.write(linestring)  # python will convert \n to os.linesep
            positions_file_handle.close()
            history_file_handle.close()

        #system.accounts.portfolio().cumsum().plot()
        #show()
        print()


        print("notional capital: ", system.accounts.get_notional_capital())

        report_path = admin_path  + 'reports_test/' +  today

        system.accounts.portfolio().resample("B").sum().to_csv(report_path + "_daily.csv")
        system.accounts.portfolio().resample("M").sum().to_csv(report_path + "_monthly.csv")
        system.accounts.portfolio().resample("A").sum().to_csv(report_path + "_annual.csv")
        system.accounts.portfolio().cumsum().to_csv(report_path + "_cum.csv")

'''
if __name__ == "__main__":

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)
