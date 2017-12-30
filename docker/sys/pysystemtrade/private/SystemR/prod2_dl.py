import pandas as pd
import quandl
from wrapper_v2 import IBWrapper, IBclient
from swigibpy import Contract as IBcontract
from accessrights import q_access_key
import os
import time
import logging

def set_logging():
    logger = logging.getLogger('Downloads')
    logger.setLevel(logging.DEBUG)

    # create file han dler which logs even DEBUG messages
    file_handler = logging.FileHandler('admin/logs/download.log')
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

def download_quandl_data(marketdata_df, mats_df, path):

    auth_token = q_access_key()
    #print(market_df)
    for tuple in mats_df.itertuples() : # .itertuples():

        carver_symbol = tuple.Index
        contract = tuple.CONTRACT
        # Look up marketdata_df to get quandl attributes

        quandl_symbol = marketdata_df.loc[carver_symbol]['QUANDL']
        quandl_exchange = marketdata_df.loc[carver_symbol]['Q_EXCHANGE']
        if quandl_exchange == 'KRX':
            close = 'Current Price'
        else:
            close = 'Settle'

        if not len(quandl_symbol) > 0:
            logger.warn('MKT DATA : {:<10}: No Quandl state data for symbol'.format(carver_symbol))

        else:
            month = str(contract)[4:6]

            year = str(contract)[:4]
            code = get_code_from_month(month)
            logger.info('DOWNLOAD : {:<10}: {:<6}: Starting Quandl download...'.format( carver_symbol, str(contract)))
            api_call_head = '{}/{}{}{}'.format(quandl_exchange, quandl_symbol, code, year)
            #print(api_call_head)
            try:
                result = quandl.get(api_call_head, returns="pandas", authtoken=auth_token)
            except:
                logger.error('DOWNLOAD : {:<10}: {:<6}: Quandl symbol: {:<5} download Error! ** String: {}**'.
                                           format(carver_symbol, str(contract)[:6], quandl_symbol, api_call_head))
            else:
                cols = list(result)
                cols.insert(0, cols.pop(cols.index(close)))
                result = result.ix[:, cols]
                # Divide by 1000000 for Peso and Yen!
                if str(carver_symbol) == 'MXP' or str(carver_symbol) == 'JPY':
                    result['Settle'] = result['Settle'].apply(lambda x: x / 1000000)
                file_name = path + "downloads/quandl/" + str(carver_symbol) + "/" + str(contract)[:6] + ".csv"
                short_file_name = str(carver_symbol) + "/" + str(contract)[:6] + ".csv"
                logger.info('DOWNLOAD : {:<10}: {:<6}: Saving maturity to disk'.format(carver_symbol, str(contract)[:6]))
                #print(result.tail(3))
                result.to_csv(file_name)


def download_ib_data(marketdata_df, mats_df, path):

    callback = IBWrapper()
    client = IBclient(callback)
    counter = 100

    for row in mats_df.itertuples():
        counter = counter + 1
        carver_symbol = row[0]
        contract = str(row[1])

        #if carver_symbol == 'KR10' or carver_symbol == 'KR3':

        ib_symbol = marketdata_df.loc[carver_symbol]['IB']
        ib_exchange = marketdata_df.loc[carver_symbol]['IB_EXCHANGE']
        ib_sec_type = marketdata_df.loc[carver_symbol]['SECTYPE']
        ib_currency = marketdata_df.loc[carver_symbol]['CURRENCY']
        ib_multiplier = marketdata_df.loc[carver_symbol]['MULTIPLIER']

        ibcontract = IBcontract()
        ibcontract.symbol = ib_symbol
        ibcontract.secType = ib_sec_type  # Security Type
        ibcontract.currency = ib_currency  # Currency
        ibcontract.exchange = ib_exchange  # Exchange
        if ib_multiplier > 0:
            ibcontract.multiplier = str(ib_multiplier)
        ibcontract.expiry = contract
        if not len(ib_symbol) > 0:
            logger.warn('MKT DATA : {:<10}: No IB state data for symbol'.format(carver_symbol))
        else:
            logger.info('DOWNLOAD : {:<10}: {:<6}: Starting IB download...'.format(carver_symbol, str(contract)))
            if ib_sec_type == 'CASH':
                ibcontract.primaryExchange = ib_exchange
                result = client.get_IB_historical_data(ibcontract, "3 M", "1 day", counter, "MIDPOINT")
            else:
                result = client.get_IB_historical_data(ibcontract, "3 M", "1 day", counter)
            if not isinstance(result, pd.DataFrame):
                logger.error('DOWNLOAD : {:<10}: {:<6}: IB symbol: {:<5}  download Error!   ******'.
                             format(carver_symbol, str(contract), ib_symbol))
            else:
                if ib_sec_type == 'CASH':
                    file_name = path + "downloads/ib/" + carver_symbol + "/" + ib_symbol + ib_currency + ".csv"
                    short_file_name = carver_symbol + "/" + ib_symbol + ib_currency + ".csv"
                else:
                    file_name = path + "downloads/ib/" + carver_symbol + "/" + str(contract)[:6] + ".csv"
                    short_file_name = carver_symbol + "/" + str(contract)[:6] + ".csv"
                result.to_csv(file_name)
                logger.info('DOWNLOAD : {:<10}: {:<6}: Saving IB maturity to disk'.format( carver_symbol, str(contract) ))
                #print(result.tail(3))

def get_month_from_code(code):

    return {
        'F': '01',
        'G': '02',
        'H': '03',
        'J': '04',
        'K': '05',
        'M': '06',
        'N': '07',
        'Q': '08',
        'U': '09',
        'V': '10',
        'X': '11',
        'Z': '12'
    }[code]


def get_code_from_month(m):

    return {
        '01': 'F',
        '02': 'G',
        '03': 'H',
        '04': 'J',
        '05': 'K',
        '06': 'M',
        '07': 'N',
        '08': 'Q',
        '09': 'U',
        '10': 'V',
        '11': 'X',
        '12': 'Z'
    }[m]


def main():
    # Author: Pete K
    # Date:   12 Oct 2016
    # Desc:   Downloads data from Quandl and from Quandl and from IB
    #         The file 'downloads_info.csv' specifies each market and associated maturities to be downloaded.
    #           CARVER
    #           QUANDL      Quandl symbol
    #           IB          IB symbol
    #           SECTYPE     {FUT or CASH}
    #           CURRENCY    Required for IB downloads
    #           Q_EXCHANGE  Exchange used to cosntruct download string
    #           IB_EXCHANGE Exchange used to construct download string
    #           MANTURITY   Maturity
    #           MULTIPLIER  Used for some IB markets

    today = time.strftime("%Y%m%d")
    time_now = time.strftime("%Y%m%d %H:%M:%S")
    dir_filename = "admin/directories.csv"

    try:
        df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
    except IOError as e:
        logger.error("FILE ERROR: {:<10}, Error opening file!".format('directories.csv', e))
    else:
        sourc_path = df.loc['SOURCE'][0]
        admin_path = df.loc['ADMIN'][0]
        market_data_filename = admin_path + 'marketdata.csv'

        if not os.path.isfile(market_data_filename):
            logger.error("FILE ERROR: {:<10}, Error opening file!".format(market_data_filename))
        else:
            market_data_df = pd.read_csv(market_data_filename,
                                         dtype={'CARVER': str, 'QUANDL': str, 'IB': str, 'PRICE': str, 'CARRY': str})
            market_data_df.fillna('', inplace=True)
            market_data_df = market_data_df.set_index(['CARVER']).copy()
            market_data_df.sort_index(ascending=True, inplace=True)
            marketdatadf = market_data_df[['QUANDL', 'IB', 'SECTYPE', 'CURRENCY', 'Q_EXCHANGE', 'IB_EXCHANGE', 'MULTIPLIER']]
            marketdatadf = marketdatadf.reset_index().drop_duplicates().set_index('CARVER')
            temp1_df = market_data_df['PRICE']
            temp2_df = market_data_df['CARRY']
            temp1_df = temp1_df.append(temp2_df)

            matsdf = temp1_df.reset_index().drop_duplicates().set_index('CARVER')
            matsdf.columns = ['CONTRACT']
            matsdf.sort_index(ascending=True, inplace=True)
            #print("Matsdf ----------------------------")
            #print(type(matsdf))
            #print(matsdf)
            #print(market_data_df)

            download_ib_data(marketdatadf, matsdf, admin_path)
            download_quandl_data(marketdatadf,matsdf, admin_path)



if __name__ == "__main__":

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)





