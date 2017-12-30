import pandas as pd
import time
import os
import logging

def set_logging():
    logger = logging.getLogger('Downloads')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even DEBUG messages
    file_handler = logging.FileHandler('admin/logs/update.log')
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

def update_futures_market(rowdf, new_data_path, legacy_data_path):
    # rowdf: For each market, a single row Dataframe that holds PRICE and CARRY maturities currently in the System data files
    # Determine date of last updated rows in the legacy files
    market = rowdf.iloc[0]['CARVER'] # Gives the CARVER symbol

    legacy_price_file = legacy_data_path + market + '_price.csv'
    legacy_carry_file = legacy_data_path + market + '_carrydata.csv'
    legacy_price_df = pd.read_csv(legacy_price_file, index_col=0)
    legacy_carry_df = pd.read_csv(legacy_carry_file, index_col=0, dtype={'CARRY_CONTRACT': str, 'PRICE_CONTRACT': str})
    last_price_date = legacy_price_df.iloc[-1:].index[0]
    last_carry_date = legacy_carry_df.iloc[-1:].index[0]
    last_carry_p_mat = legacy_carry_df.iloc[-1].PRICE_CONTRACT
    last_carry_c_mat = legacy_carry_df.iloc[-1].CARRY_CONTRACT

    price_maturity = rowdf.iloc[0]['PRICE']
    carry_maturity = rowdf.iloc[0]['CARRY']
    logger.debug("MATURITIES: {:<10}, PRICE: {}, CARRY: {}".format(market, price_maturity, carry_maturity))
    logger.debug("LAST DATES: {:<10}, PRICE: {}, CARRY: {}".format(market, last_price_date, last_carry_date))
    price_maturity = price_maturity[0:6]  # VIX maturity in 8 digit form but file uses 6 digits!
    carry_maturity = carry_maturity[0:6]  # VIX maturity in 8 digit form but file uses 6 digits!

    # Check that maturity in rowdf(new_marketdata.csv) match those in last row of carry file!
    #    If not, report the error and exit loop!
    if price_maturity != last_carry_p_mat:
        logger.error("MISMATCH  : {:<10}, PRICE lookup: {} & legacy carry file: {}".format(market, price_maturity, last_carry_p_mat))
        return
    if carry_maturity != last_carry_c_mat:
        logger.error("MISMATCH  : {:<10}: CARRY lookup: {} & legacy carry file: {}".format(market, carry_maturity, last_carry_c_mat))
        return

    quandl_price_file = new_data_path + "downloads/quandl/" + market + '/' + price_maturity + '.csv'
    quandl_carry_file = new_data_path + "downloads/quandl/" + market + '/' + carry_maturity + '.csv'
    ib_price_file = new_data_path + "downloads/ib/" + market + '/' + price_maturity + '.csv'
    ib_carry_file = new_data_path + "downloads/ib/" + market + '/' + carry_maturity + '.csv'
    quandl_price_updates = False
    ib_price_updates = False
    price_file = False
    if os.path.isfile(quandl_price_file):
        price_file = True
        quandl_price_df = pd.read_csv(quandl_price_file, usecols=[0, 1])
        quandl_price_df.columns = ['DATETIME', 'PRICE']
        if not quandl_price_df.empty:
            last_quandl_date = quandl_price_df.iloc[-1].DATETIME
        quandl_df = quandl_price_df.set_index('DATETIME').copy()
        quandl_df = quandl_df.loc[last_price_date:][1:]
        if quandl_df.empty:
            logger.debug("NO NU DATA: {:<10}: PRICE (Quandl) download file empty".format(market))
        else:
            logger.info("NEW DATA  : {:<10}: PRICE (Quandl) last: {}".format(market, last_quandl_date))
            quandl_price_updates = True

    if os.path.isfile(ib_price_file):
        price_file = True
        ib_price_df = pd.read_csv(ib_price_file, usecols=[0, 1])
        ib_price_df.columns = ['DATETIME', 'PRICE']
        if not ib_price_df.empty:
            last_ib_date = ib_price_df.iloc[-1].DATETIME
        ib_df = ib_price_df.set_index('DATETIME').copy()
        ib_df = ib_df.loc[last_price_date:][1:]
        if ib_df.empty:
            logger.debug("NO NU DATA: {:<10}: PRICE (IB) download file empty".format(market))
        else:
            logger.info("NEW DATA  : {:<10}: PRICE (IB) last: {}".format(market, last_ib_date))
            ib_price_updates = True

    if not price_file:
        logger.error("NO FILE   : {:<10}: No Quandl or IB PRICE files!".format(market))
        return
    else:
        #LOGIC: Warn if no new data or if Quandl and IB are different.
        #       Use the download with most data.
        if quandl_price_updates or ib_price_updates:
            if quandl_price_updates and ib_price_updates:
                if quandl_df.equals(ib_df):
                    logger.debug("NEW DATA  : {:<10}: PRICE mat IB = Quandl".format(market))
                    legacy_price_df = legacy_price_df.append(quandl_df)
                    appended_price_df = quandl_df
                else:
                    logger.warn("NEW DATA  : {:<10}: PRICE mat IB != Quandl!".format(market))
                    # Use the download with most data.
                    if quandl_df.shape[0] > ib_df.shape[0]:
                        legacy_price_df = legacy_price_df.append(quandl_df)
                        appended_price_df = quandl_df
                    else:
                        legacy_price_df = legacy_price_df.append(ib_df)
                        appended_price_df = ib_df
            if quandl_price_updates and not ib_price_updates:
                logger.info("NEW DATA  : {:<10}: PRICE mat Quandl but no IB".format(market))
                legacy_price_df = legacy_price_df.append(quandl_df)
                appended_price_df = quandl_df
            elif ib_price_updates and not quandl_price_updates:
                logger.info("NEW DATA  : {:<10}: PRICE mat IB but no Quandl".format(market))
                legacy_price_df = legacy_price_df.append(ib_df)
                appended_price_df = ib_df
            # Write the appended df bak to file
            logger.info("NEW DATA  : {:<10}: PRICE mat appended to {}".format(market, legacy_price_file))
            legacy_price_df.to_csv(legacy_price_file)
        else:
            logger.warn("NO NU DATA: {:<10}: PRICE mat. No update...".format(market))
            # No reason to continue with CARRY loads
            return
    # If here then the legacy PRICE file has been appended => append legacy CARRY file too
    quandl_carry_updates = False
    ib_carry_updates = False
    carry_file = False
    if os.path.isfile(quandl_carry_file):
        carry_file = True
        quandl_carry_df = pd.read_csv(quandl_carry_file, usecols=[0, 1])
        quandl_carry_df.columns = ['DATETIME', 'PRICE']
        if not quandl_carry_df.empty:
            last_quandl_date = quandl_carry_df.iloc[-1].DATETIME
        quandlc_df = quandl_carry_df.set_index('DATETIME').copy()
        quandlc_df = quandlc_df.loc[last_carry_date:][1:]
        if quandlc_df.empty:
            logger.debug("NO NU DATA: {:<10}: CARRY (Quandl) last: {}".format(market, last_quandl_date))
        else:
            logger.info("NEW DATA  : {:<10}: CARRY (Quandl) last: {}".format(market, last_quandl_date))
            quandl_carry_updates = True

    if os.path.isfile(ib_carry_file):
        carry_file = True
        ib_carry_df = pd.read_csv(ib_carry_file, usecols=[0, 1])
        ib_carry_df.columns = ['DATETIME', 'PRICE']
        if not ib_carry_df.empty:
            last_ib_date = ib_carry_df.iloc[-1].DATETIME
        ibc_df = ib_carry_df.set_index('DATETIME').copy()
        ibc_df = ibc_df.loc[last_carry_date:][1:]
        if ibc_df.empty:
            logger.debug("NO NU DATA: {:<10}: CARRY (IB) last: {}".format(market, last_quandl_date))
        else:
            logger.info("NO NU DATA: {:<10}: CARRY (IB) last: {}".format(market, last_quandl_date))
            ib_carry_updates = True

    # If there are no CARRY files, or no updates to both IB & Quandl files update legacy CARRY with blanks
    if not carry_file or (not ib_carry_updates and not quandl_carry_updates) :
        logger.warn("NO CARRY  : {:<10}: No updates. CARRY column values set blank".format(market))
        concat_df = appended_price_df
        concat_df.columns = ["PRICE"]
        concat_df["CARRY"] = ""
        concat_df["CARRY_CONTRACT"] = carry_maturity
        concat_df["PRICE_CONTRACT"] = price_maturity
    else:
        if ib_carry_updates and quandl_carry_updates:
            if quandlc_df.equals(ibc_df):
                logger.debug("NEW DATA  : {:<10}: CARRY mat IB=Quandl".format(market))
                toconcat_carry_df = quandlc_df
            else:
                logger.warn("EW DATA  : {:<10}: CARRY mat IB != Quandl".format(market))
                if quandlc_df.shape[0] > ibc_df.shape[0]:
                    toconcat_carry_df = quandlc_df
                else:
                    toconcat_carry_df = ibc_df
        else:
            if quandl_carry_updates and not ib_carry_updates:
                toconcat_carry_df = quandlc_df
            elif ib_carry_updates and not quandl_carry_updates:
                toconcat_carry_df = ibc_df
        concat_df = pd.concat([appended_price_df, toconcat_carry_df], axis=1)
        concat_df.columns = ["PRICE", "CARRY"]
        concat_df["CARRY_CONTRACT"] = carry_maturity
        concat_df["PRICE_CONTRACT"] = price_maturity
    legacy_carry_df = (legacy_carry_df).append(concat_df)
    legacy_carry_df.to_csv(legacy_carry_file)
    logger.info("NEW DATA  : {:<10}: CARRY mat appended to {}".format(market, legacy_carry_file))

def update_forex_market(rowdf, new_data_path, legacy_data_path):
    market = rowdf.iloc[0]['CARVER']
    legacy_fx_file = legacy_data_path + market + 'fx.csv'
    legacy_fx_df = pd.read_csv(legacy_fx_file)
    legacy_fx_df = legacy_fx_df.set_index('DATETIME').copy()
    last_fx_date = legacy_fx_df.iloc[-1:].index[0]

    logger.debug("Market: {}, last FX data: {}".format(market, last_fx_date))

# At the moment only IB downloads for FX
    ib_fx_file = new_data_path + "downloads/ib/" + market + '/' + market + '.csv'
    #print("== Checking if there is a new update for: ", ib_fx_file)
    if not (os.path.isfile(ib_fx_file)):
        logger.error("NO FILE   : {:<10}: File handling error!".format(market))
    else:
        ib_fx_df = pd.read_csv(ib_fx_file, usecols=[0, 1])
        # Doew sourceFXDF contains newer rows?
        ib_fx_df.columns = ['DATETIME', 'FX']
        fx_df = ib_fx_df.set_index('DATETIME').copy()
        fx_df = fx_df.loc[last_fx_date:][1:]
        if fx_df.empty:
            logger.debug("NO NU DATA: {:<10}: fx (IB) last: {}".format(market, last_fx_date))
        else:
            legacy_fx_df = legacy_fx_df.append(fx_df)
            legacy_fx_df.to_csv(legacy_fx_file)
            logger.info("NEW DATA  : {:<10}: fx data appended to {}".format(market, legacy_fx_file))
def main():

    from datetime import datetime
    from datetime import timedelta
    from dateutil.parser import parse

    dir_filename = "admin/directories.csv"
    if not os.path.isfile(dir_filename):
        logger.error("The file, {}, does not exist".format('directories.csv'))
    else:
        dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
        admin_path = dir_df.loc['ADMIN'][0] # /home/pete/Documents/Python Packages/sysIB/private/data/
        destination_path = dir_df.loc['DESTINATION'][0] #/home/pete/Repos/pysystemtrade/private/SystemR/data/

        market_data_filename = admin_path + 'marketdata.csv'
        market_data_df = pd.read_csv(market_data_filename,  dtype={'CARRY': str, 'PRICE': str})
        # For each market we only need most recent (by DATETIME) row where DONE == 1
        #live_market_df = market_data_df[market_data_df.DONE == 1]
        temp_df = market_data_df[market_data_df.DONE == 1].sort_values(by=['CARVER','DATEFROM'], ascending=[1,1])
        curr_markets_df = temp_df.groupby('CARVER').tail(1)
        print(curr_markets_df)
        temp_df = market_data_df[market_data_df.DONE == 0].sort_values(by=['CARVER', 'DATEFROM'], ascending=[1, 1])
        next_markets_df = temp_df.groupby('CARVER').head(1)
        #print(next_markets_df)
        #print(next_markets_df[['CARVER', 'DATEFROM']])
        for market in curr_markets_df.itertuples():
            logger.debug("")
            market_df =  curr_markets_df.loc[curr_markets_df['CARVER'] == market.CARVER]
            next_df = next_markets_df.loc[next_markets_df['CARVER'] == market.CARVER]
            # If next_market row does not exist WARN
            # If next market row exists check DATEFROM and...
            #  ...WARN of days to roll
            #  ...ERROR if roll is required
            if market_df.iloc[0]['SECTYPE'] == 'FUT':
                if len(next_df.index) == 0:
                    logger.warn("Next roll info for, {}, missing ************************************************".format(market.CARVER))
                else:


                   dt = parse(next_df.iloc[0]['DATEFROM'])
                  # print(dt)
                   curr_price_mat = str(market_df.iloc[0]['PRICE'])[:6]
                   next_price_mat = str(next_df.iloc[0]['PRICE'])[:6]
                   days_to_roll = (dt.date() - datetime.today().date())
                   if days_to_roll.days < 0:
                       #print(next_df)
                       #print()
                       logger.error("ROLL INFO : {:<10}, ({} to {}) Date Passed!        <========================= Was due: {}".
                                                          format(market.CARVER, curr_price_mat, next_price_mat, dt))
                   else:
                       ndays = days_to_roll.days
                       if ndays < 6:
                           logger.warn("ROLL INFO : {:<10}: ({} to {}) Roll soon!            <======================== Days to Roll: {:<3}".
                                                          format(market.CARVER, curr_price_mat, next_price_mat,  ndays))
                       else:
                           logger.info("ROLL INFO : {:<10}: ({} to {}) Due in (days) : {:<3}".format(market.CARVER,
                                                                                                     curr_price_mat,
                                                                                                     next_price_mat,
                                                                                                     ndays))
                update_futures_market(market_df, admin_path, destination_path)
            else:
                update_forex_market(market_df, admin_path, destination_path)

if __name__ == "__main__":

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)

