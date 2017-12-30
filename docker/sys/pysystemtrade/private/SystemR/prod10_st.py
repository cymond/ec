import pandas as pd
import numpy as np
import time
import os
import logging

def set_logging():
    logger = logging.getLogger('Downloads')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even DEBUG messages
    file_handler = logging.FileHandler('admin/logs/stitching.log')
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

def main():
    from datetime import datetime
    from datetime import timedelta
    from dateutil.parser import parse

    dir_filename = "admin/directories.csv"
    if not os.path.isfile(dir_filename):
        logger.error("The file, {}, does not exist".format('directories.csv'))
    else:
        dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
        admin_path = dir_df.loc['ADMIN'][0]  # /home/pete/Documents/Python Packages/sysIB/private/data/
        destination_path = dir_df.loc['DESTINATION'][0]  # /home/pete/Repos/pysystemtrade/private/SystemR/data/
        market_data_filename = admin_path + 'marketdata.csv'
        market_data_df = pd.read_csv(market_data_filename, dtype={'CARRY': str, 'PRICE': str})
        # 'current_markets_df' contains for each market the most recent (by DATEFROM) row where DONE == 1
        # 'next_markets_df' contains for each market the next (by DATEFROM) row where DONE == 0
        #print(market_data_df)
        temp_df = market_data_df[market_data_df.DONE == 1].sort_values(by=['CARVER', 'DATEFROM'], ascending=[1, 1])
        curr_markets_df = temp_df.groupby('CARVER').tail(1).set_index(['CARVER'])
        temp_df = market_data_df[market_data_df.DONE == 0].sort_values(by=['CARVER', 'DATEFROM'], ascending=[1, 1])
        next_markets_df = temp_df.groupby('CARVER').head(1)
        market_data_copy = market_data_df.set_index(['CARVER','DATEFROM']).copy()
        #print(next_markets_df)

        market_data_update = False
        print(next_markets_df)
        for market in next_markets_df.itertuples():
            #print(market)
            '''
            Pandas(
                Index=6,
                CARVER='CAC',
                DATEFROM='2016-11-11',
                DELTA=nan,
                DONE=0,
                QUANDL='FCE',
                IB='CAC40',
                SECTYPE='FUT',
                CURRENCY='EUR',
                Q_EXCHANGE='LIFFE',
                IB_EXCHANGE='MONEP',
                MULTIPLIER=10,
                PRICE='201612',
                CARRY='201701'
                  )
            '''

            #print(market.CARVER)
            #dt = parse(next_df.iloc[0]['DATEFROM'])
            # print(dt)
            #curr_price_mat = str(market_df.iloc[0]['PRICE'])[:6]
            #next_price_mat = str(next_df.iloc[0]['PRICE'])[:6]
            #days_to_roll = dt - datetime.now()
            #print( datetime.now().date() - timedelta(1), parse(market.DATEFROM).date())
            yesterday = datetime.now().date() - timedelta(1)
            #print("market.DATEFROM: ", type(market.DATEFROM))
            stitch_date = pd.to_datetime(market.DATEFROM)
            #print("stitch_date: ", type(stitch_date))
            if yesterday >= stitch_date.date():
                #print("Time To Roll!")
                legacy_price_file = destination_path + market.CARVER + '_price.csv'
                legacy_carry_file = destination_path + market.CARVER + '_carrydata.csv'
                legacy_price_df = pd.read_csv(legacy_price_file, index_col=0, parse_dates=True)
                legacy_carry_df = pd.read_csv(legacy_carry_file, index_col=0, parse_dates=True,
                                              dtype={'CARRY_CONTRACT': str, 'PRICE_CONTRACT': str})
                # Check that legacy_price_df has an entry on stitch_date
                #stitch_date64 = np.datetime64(stitch_date)
                if not stitch_date in legacy_price_df.index:
                    logger.error("SPLICING  : {:<10}, stitch date {}, not in legacy PICE file".format(market.CARVER, stitch_date))
                    continue
                # Check that market data agrees with legacy_carr_df
                last_carry_p_mat = legacy_carry_df.iloc[-1].PRICE_CONTRACT
                last_carry_c_mat = legacy_carry_df.iloc[-1].CARRY_CONTRACT
                #print(curr_markets_df)
                curr_price_maturity = curr_markets_df.loc[market.CARVER].PRICE[:6]
                curr_carry_maturity = curr_markets_df.loc[market.CARVER].CARRY[:6]
                next_price_maturity = market.PRICE[:6]
                next_carry_maturity = market.CARRY[:6]
                print("curr_price_maturity: ", curr_price_maturity, "last_carry_p_mat: ", last_carry_p_mat)
                print("next_price_maturity: ", next_price_maturity)
                #print(curr_price_maturity == last_carry_p_mat)
                if curr_price_maturity != last_carry_p_mat:
                    logger.error(
                        "MISMATCH  : {:<10}, PRICE lookup: {} & legacy carry file: {}".format(market.CARVER, curr_price_maturity,
                                                                                              last_carry_p_mat))
                    continue
                if curr_carry_maturity != last_carry_c_mat:
                    logger.error(
                        "MISMATCH  : {:<10}: CARRY lookup: {} & legacy carry file: {}".format(market.CARVER, curr_carry_maturity,
                                                                                              last_carry_c_mat))
                    continue
                # Check 1. downloaed PRICE file exists (CARRY) doesn't have to exist!
                # Check 2. Stitch date row is in both legacy_price_df and new downloaded price maturity
                quandl_price_file = admin_path + "downloads/quandl/" + market.CARVER + '/' + next_price_maturity + '.csv'
                quandl_carry_file = admin_path + "downloads/quandl/" + market.CARVER + '/' + next_carry_maturity + '.csv'
                ib_price_file = admin_path + "downloads/ib/" + market.CARVER + '/' + next_price_maturity + '.csv'
                ib_carry_file = admin_path + "downloads/ib/" + market.CARVER + '/' + next_carry_maturity + '.csv'
                quandl_price_match = False
                ib_price_match = False
                price_file = False
                if os.path.isfile(quandl_price_file):
                    price_file = True
                    quandl_price_df = pd.read_csv(quandl_price_file, usecols=[0, 1], index_col=0, parse_dates=True)
                    quandl_price_df.columns = ['PRICE']
                    if not quandl_price_df.empty:
                        # Check if stitch_date in df
                        quandl_price_df_index = quandl_price_df.index
                        if not stitch_date in quandl_price_df.index:
                            logger.warn("SPLICING  : {:<10}, No match for stitch date {}, in Quandl PICE file".format(market.CARVER, stitch_date))
                        else:
                            #print(quandl_price_df)
                            quandl_price_match = True
                            quandl_price_df = quandl_price_df.loc[market.DATEFROM:]
                if os.path.isfile(ib_price_file):
                    price_file = True
                    ib_price_df = pd.read_csv(ib_price_file, usecols=[0, 1], index_col=0, parse_dates=True)
                    ib_price_df.columns = [ 'PRICE']
                    if not ib_price_df.empty:
                        # Check if stitch_date in df
                        if not stitch_date in ib_price_df.index:
                            logger.warn("SPLICING  : {:<10}, No match for stitch date {}, in IB PICE file".format(market.CARVER,
                                                                                                              stitch_date))
                        else:
                            ib_price_match = True
                            ib_price_df = ib_price_df.loc[market.DATEFROM:]

                if not price_file:
                    logger.error("NO FILE   : {:<10}: No Quandl or IB PRICE files!".format(market.CARVER))
                    continue
                else:
                    ''' Let's perform the stitch
                    1. Check if IB and Quandl are in sinc. Otherwise use Quandl
                    '''
                    if not quandl_price_match and not ib_price_match:
                        logger.error("SPLICING  : {:<10}, No stitch date match in both Quandl and IB downloads".format(market.CARVER))
                        continue
                    else:
                        if quandl_price_match and ib_price_match:
                            if quandl_price_df.equals(ib_price_df):
                                logger.info("SPLICING  : {:<10}: Quandl and IB PRICE download files match".format(market.CARVER))
                            else:
                                logger.info("SPLICING  : {:<10}: Quandl and IB PRICE download files DO NOT match".format(market.CARVER))
                        if not quandl_price_match:
                            new_price_df = ib_price_df.copy()
                            logger.info("SPLICING  : {:<10}: Using IB PRICE download files to splice".format(market.CARVER))
                        else:
                            new_price_df = quandl_price_df.copy()
                            logger.info("SPLICING  : {:<10}: Using Quandl PRICE download files to splice".format(market.CARVER))
                        '''# Determine delta for splice
                        '''#
                        print("BEFORE legacy PRICE series")
                        print(legacy_price_df.tail(4))
                        print(new_price_df.tail(4))
                        print("this: ", new_price_df.index)
                        old_value = legacy_price_df.loc[stitch_date]['PRICE']
                        # Final check to ensure that stith_date is available in chosen download price stream
                        if not stitch_date in new_price_df.index:
                            logger.info("SPLICING  : {:<10}: No splice_date match in BOTH download files".format(market.CARVER))
                            continue
                        new_value = new_price_df.loc[market.DATEFROM]['PRICE']
                        delta = new_value - old_value
                        '''# Perform stitch
                        '''#
                        market_data_copy.set_value((market.CARVER,market.DATEFROM), 'DELTA', delta )
                        market_data_copy.set_value((market.CARVER, market.DATEFROM), 'DONE', 1)
                        market_data_update = True
                        #print(market_data_copy)

                        legacy_price_df['PRICE'] = legacy_price_df['PRICE'] + delta
                        appended_price_df = new_price_df.copy()
                        legacy_price_df = legacy_price_df[:market.DATEFROM][:-1].append(appended_price_df)
                        legacy_price_df.index.name = 'DATETIME'
                        print("Delta: ", delta)
                        print("AFTER legacy PRICE series")
                        print(legacy_price_df.tail(4))
                        #DEBUG

                        legacy_price_df.to_csv(legacy_price_file)
                        print(legacy_price_df)
                        logger.info("SPLICING  : {:<10}: Stitched PRICE saved to file {}".format(market.CARVER, market.CARVER + '_price.csv'))
                #legacy_price_df.to_csv(legacy_price_file)
                # Now perform the CARRY stitching ase well...
                # At least 3 columns (PRICE,CARRY,PRICE_CONTRACT)  MUST be updated to match the PRICE series
                # First we must test if there is a new CARRY file. Some contracts do not trade until let in the cycle and
                # Blanks need to be filled in the CARRY columna until then
                quandl_carry_rows = False
                ib_carry_rows = False
                carry_file = False
                if os.path.isfile(quandl_carry_file):
                    carry_file = True
                    quandl_carry_df = pd.read_csv(quandl_carry_file, usecols=[0, 1], index_col=0, parse_dates=True)
                    quandl_carry_df.columns = [ 'PRICE']
                    quandl_carry_df = quandl_carry_df[market.DATEFROM:]
                    if not quandl_carry_df.empty:
                       quandl_carry_rows = True
                if os.path.isfile(ib_carry_file):
                    carry_file = True
                    ib_carry_df = pd.read_csv(ib_carry_file, usecols=[0, 1], index_col=0, parse_dates=True)
                    ib_carry_df.columns = [ 'PRICE']
                    ib_carry_df = ib_carry_df[market.DATEFROM:]
                    if not ib_carry_df.empty:
                        ib_carry_rows = True

                # If no CARRY rows, inset blanks for CARRY mat
                # If only ib_carry_rows, use ib_carry_rows
                # Otherwise use quandl_carry_rows
                legacy_carry_df = legacy_carry_df[:stitch_date][:-1]
                dfToAppend = appended_price_df
                price_last_date = appended_price_df[-1:].index[0]

                if not carry_file or (not quandl_carry_rows and not ib_carry_rows):
                    dfConcat = dfToAppend.copy()
                    dfConcat["CARRY"] = ""
                else:
                    if not(quandl_carry_rows) and (ib_carry_rows):
                        logger.info("SPLICING  : {:<10}: Using IBr CARRY download files to splice".format(market.CARVER))
                        dfConcat = pd.concat([dfToAppend, ib_carry_df[:price_last_date]], axis=1)
                    else:
                        dfConcat = pd.concat([dfToAppend, quandl_carry_df[:price_last_date]], axis=1)
                dfConcat.columns = ["PRICE", "CARRY"]
                dfConcat["CARRY_CONTRACT"] = next_carry_maturity
                dfConcat["PRICE_CONTRACT"] = next_price_maturity
                legacy_carry_df = (legacy_carry_df).append(dfConcat)
                legacy_carry_df.index.name = 'DATETIME'
                print(legacy_carry_df.tail(4))
                legacy_carry_df.to_csv(legacy_carry_file)
                print(legacy_carry_df)
                logger.info("SPLICING  : {:<10}: Stitched CARRY saved to file {}".
                                                    format(market.CARVER, market.CARVER + '_carrydata.csv'))
        # If there are any updates to market_data, save the updates to file
        if market_data_update:
            market_data_copy.to_csv(market_data_filename)
            print(market_data_copy)


if __name__ == "__main__":

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)