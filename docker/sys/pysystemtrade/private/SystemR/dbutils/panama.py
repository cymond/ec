from accessrights import q_access_key
import quandl
import pandas as pd


source_path = "quandl_history/"
destination_path = "data/"


def pretty_print(title, dt_frame, n_head, n_tail):
    print()
    if n_head > 0:
        print("Head --------------------------------------------------------------------------")
        print(title)
        print(dt_frame.head(n_head))

    if n_tail > 0:
        print("Tail --------------------------------------------------------------------------")
        print(title)
        print(dt_frame.tail(n_tail))
        print("-------------------------------------------------------------------------------")
    print()


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


def get_qndl_string(mkt_ser,maturity):
    """
    :param mkt_ser: Series with elements {CARVER,QUANDL,IB,SECTYPE,CURRENCY,Q_EXCHANGE,IB_EXCHANGE,MULTIPLIER}
    :param maturity:  e.g. 201803
    :return: String to sent to Quandl API
    >>> data=mysqlFuturesData()
    >>> data._get_all_cost_data()
    """
    year = str(maturity)[:4]
    month = str(maturity)[4:6]
    month_code = get_code_from_month(month)
    symbol = mkt_ser.QUANDL
    exchange = mkt_ser.Q_EXCHANGE
    api_call_head = '{}/{}{}{}'.format(exchange, symbol, month_code, year)
    return api_call_head


def get_ib_contract(mkt_ser,maturity):
    '''
    :param mkt_ser: Series with elements {CARVER,QUANDL,IB,SECTYPE,CURRENCY,Q_EXCHANGE,IB_EXCHANGE,MULTIPLIER}
    :param maturity:  e.g. 201803
    :return: Contract to send to IB API
    '''
    from swigibpy import Contract as IBcontract

    ib_multiplier = mkt_ser.MULTIPLIER
    ib_security_type = mkt_ser.SECTYPE
    ib_exchange = mkt_ser.IB_EXCHANGE
    ibcontract = IBcontract()
    ibcontract.symbol = mkt_ser.IB
    ibcontract.secType = ib_security_type # Security Type

    ibcontract.currency = mkt_ser.CURRENCY  # Currency
    ibcontract.exchange = ib_exchange  # Exchange
    if ib_multiplier > 0:
        ibcontract.multiplier = str(ib_multiplier)
    if ib_security_type == 'FUT':
        ibcontract.expiry = maturity
        ibcontract.includeExpired = True
    return ibcontract


def ib_download(client, mkt_ser, maturity, end_date, **kwargs):
    start_date = kwargs.get('start_date')
    counter = 100
    ibcontract = get_ib_contract(mkt_ser, maturity)
    if ibcontract.secType == 'CASH':
        ibcontract.primaryExchange = ibcontract.exchange
        result = client.get_IB_historical_data(ibcontract, end_date, "4 M", "1 day", counter, "MIDPOINT")
        result.rename(columns={0:'DATETIME',\
                              'close':'FX'}, inplace=True)
        result.index.names = ['DATETIME']
        result = result[['FX']]

    else:
        result = client.get_IB_historical_data(ibcontract, end_date, "5 Y", "1 day", counter)
        result.rename(columns={'Date': 'DATETIME', \
                               'Trade Date': 'DATETIME', \
                               'Prev. Day Open Interest': 'Open Interest', \
                               'Total Volume': 'Volume', \
                               'close': 'PRICE', \
                               'Current Price': 'PRICE'}, inplace=True)
        result.index.names = ['DATETIME']
        result = result[['PRICE']]
        if not isinstance(result, pd.Dataframe):
            print(mkt_ser.IB, maturity, "IB Downloads does not return a Dataframe!!!")
        else:
            print("IB Downloads!!!!")
            print(result.tail(5))
     
    return result


def qndl_download(mkt_ser, maturity, **kwargs):
    from dateutil.relativedelta import relativedelta
    start_date = kwargs.get('start_date')
    auth_token = q_access_key()
    api_call_head = get_qndl_string(mkt_ser, maturity)
    #print(maturity, ": ", api_call_head)
    result = quandl.get(api_call_head, returns="pandas", authtoken=auth_token, start_date=start_date)
    # result = quandl.get(api_call_head, returns="pandas", authtoken=auth_token)
    # re = quandl.get
    # rename to Dates to DATETIME
    # and to Settle
    # print(result)
    result.rename(columns={'Date': 'DATETIME',
                           'Trade Date': 'DATETIME',
                           'Prev. Day Open Interest': 'Open Interest',
                           'Total Volume': 'Volume',
                           'Settle': 'PRICE',
                           'Current Price': 'PRICE'}, inplace=True)
    result.index.names = ['DATETIME']
    result.reset_index(inplace=True)
    result['DATETIME'] = result['DATETIME'].apply(lambda x: x + relativedelta(hours=23))
    result.set_index(['DATETIME'],inplace=True)
    frame = result[['PRICE']].copy()
    # Divide by 1000000 for Peso and Yen!
    if mkt_ser.CARVER == 'MXP' or mkt_ser.CARVER == 'JPY':
        frame['PRICE'] = frame['PRICE'].apply(lambda x: x / 1000000)
    return frame


def q_download(engine, symbol, maturity, **kwargs):

    start_date = kwargs.get('start_date')
    auth_token = q_access_key()
    marketdata_df = pd.read_sql_table(table_name="marketdata", con=engine,index_col='CARVER')
    # market_info = marketdata_df[marketdata_df['CARVER']== symbol]
    # carver_sym = symbol
    quandl_sym = marketdata_df.loc[symbol]['QUANDL']
    quandl_exchange = marketdata_df.loc[symbol]['Q_EXCHANGE']
    month = str(maturity)[4:6]
    year = str(maturity)[:4]
    code = get_code_from_month(month)
    api_call_head = '{}/{}{}{}'.format(quandl_exchange, quandl_sym, code, year)
    result = quandl.get(api_call_head, returns="pandas", authtoken=auth_token, start_date=start_date)
    # result = quandl.get(api_call_head, returns="pandas", authtoken=auth_token)
    # re = quandl.get
    # rename to Dates to DATETIME
    # and to Settle
    result.rename(columns={'Trade Date': 'Date', \
                           'Prev. Day Open Interest': 'Open Interest', \
                           'Total Volume': 'Volume', \
                           'Current Price': 'Settle'}, inplace=True)
    result.index.names = ['Date']
    frame  = result[['Settle']]
    return frame

def get_padded_carry(app_carry, symbol, maturity):

    if not symbol in ["KR3","KR10"] or len(app_carry) == 0:
        return app_carry
    else:
        app_carry_copy = app_carry.copy()
        pad_from_year = '2017'
        if str(maturity) > pad_from_year:
            first_carry_entry = False
            # remove index first...
            app_carry_copy.reset_index(inplace=True)
            for counter, row in enumerate(app_carry_copy.itertuples(), 1):
                if not first_carry_entry:
                    if not (pd.isnull(row.CARRY) or row.CARRY == 0):
                        # 0 CARRY values allowed until first CARRY entry... then can p
                        first_carry_entry = True
                    prev_carry = row.CARRY
                else:
                    if row.PRICE > 0 and (pd.isnull(row.CARRY) or row.CARRY == 0):
                        # This 0 is not allowed IF PRICE is not 0
                        # ...extrapolate from previous CARRY value and PRICE delta
                        delta = row.PRICE - prev_price
                        print("delta: ", delta)
                        new_value = prev_carry + delta
                        print("Padded CARRY contract: ", maturity, " on date: ", row.DATETIME)
                        app_carry_copy.set_value(counter - 1, 'CARRY', new_value)
                        prev_carry = new_value
                    else:
                        prev_carry = row.CARRY

                prev_price = row.PRICE
            app_carry_copy.set_index(['DATETIME'], inplace=True)

        return app_carry_copy



def splice_price(base_df,new_df,date):
    import datetime

    # Panama splice the two dataframes together on 'date' and return the spliced df
    # First, determine delta between the 2 dfs on the splice date
    # There may be one price or several intra-day prices, BUT the splice is done on the last price of day
    '''
    next_day = date + datetime.timedelta(1)

    basedf_mask = (base_df.index >= date) & (base_df.index < next_day)
    basedf_date = base_df.index[basedf_mask][-1]
    newdf_mask = (new_df.index >= date) & (new_df.index < next_day)
    newdf_date = new_df.index[newdf_mask][-1]


    delta = new_df.loc[newdf_date][0] - base_df.loc[basedf_date][0]
    '''
    delta = new_df.resample("B").last().loc[date][0] - base_df.resample("B").last().loc[date][0]
    print("---- date: ", date, "---------- delta: ", delta)
    # print("delta: ", delta)
    # Add this delta to pan_df stream
    # and truncate both dfs at splice date...

    # print(base_df[:date][:-1].tail(5))
    base_df['PRICE'] = base_df['PRICE'] + delta
    # print(base_df[:date][:-1].tail(5))
    appended_df = new_df[date:].copy()
    price_df = base_df[:date][:-1]
    # print("price: ", len(price_df))
    price_df = price_df.append(appended_df).round({'PRICE':10})
    return price_df


def splice_carry(symbol, base_df, new_price, new_carry, price_mat, carry_mat, date):
    """
    import datetime
    next_day = date + datetime.timedelta(1)

    basedf_mask = (base_df.index >= date) & (base_df.index < next_day)
    basedf_date = base_df.index[basedf_mask][-1]
    new_price_mask = (new_price.index >= date) & (new_price.index < next_day)
    new_price_date = new_price.index[new_price_mask][-1]


    new_carry_mask = (new_carry.index >= date) & (new_carry.index < next_day)
    new_carry_date = new_carry.index[new_carry_mask][-1]
    """
    import numpy as np
    new_price = new_price[date:].copy()
    new_carry = new_carry[date:].copy()

    if len(new_carry) > 0:
        append_df = pd.concat([new_price, new_carry], axis=1)
    else:
        append_df = new_price.copy()
        append_df["CARRY"] = np.nan
    append_df.columns = ["PRICE", 'CARRY']
    append_df["CARRY_CONTRACT"] = carry_mat
    append_df["PRICE_CONTRACT"] = price_mat
    carry_df = base_df[:date][:-1]
    append_df = get_padded_carry(append_df, symbol, price_mat) # indexed !!
    # print(append_df.tail(5))
    # print(carry_df.tail(5))
    # print("price: ", len(carry_df))
    carry_df = carry_df.append(append_df)
    carry_df.index.names = ['DATETIME']
    carry_df = carry_df[pd.notnull(carry_df['PRICE'])]
    return carry_df




def prev_weekday(adate):
    from datetime import date, timedelta
    adate -= timedelta(days=1)
    while adate.weekday() > 4: # Mon-Fri are 0-4
        adate -= timedelta(days=1)
    return adate


def check_data_ok(maturity, df, start_date, end_date, match):
    # Will raise an error if splice date that's supposed to be in df is missing (for match = True)
    # Called after a call to quandl or IB
    import datetime
    if not pd.isnull(start_date):
                    #
        if start_date.hour == 23:
            start_date_alt = datetime.datetime(start_date.year, start_date.month, start_date.day, 0)
        if start_date.hour == 0:
            start_date_alt = datetime.datetime(start_date.year, start_date.month, start_date.day, 23)

    if not pd.isnull(end_date):
                    #
        if end_date.hour == 23:
            end_date_alt = datetime.datetime(end_date.year, end_date.month, end_date.day, 0)
        if end_date.hour == 0:
            end_date_alt = datetime.datetime(end_date.year, end_date.month, end_date.day, 23)
    temp_df = df.copy()
    temp_df['HOURS'] = temp_df.index.map(lambda x: x.hour)
    closing_prices = temp_df[(temp_df['HOURS'] == 0) | (temp_df['HOURS'] == 23)]
    last_settlement_date = closing_prices[-1:].index[0]

    if match:
        # Check if splice dates that should be in temp_df are... propagate an error if missing
        if start_date == start_date:
            if start_date.date() < last_settlement_date.date() and not \
                    (start_date in df.index or start_date_alt in df.index):
                print("****", maturity, start_date)
                print(df.head(40))
                assert False, maturity + ": Start splice date is missing in database data"
        if end_date  == end_date:
            if end_date.date() < last_settlement_date.date() and not \
                    (end_date in df.index or end_date_alt in df.index):
                print("****", maturity, end_date)
                assert False, maturity + ": End splice date is missing in database data"
    return True


def get_raw_legacy_data(engine, market, contract):
    '''
    1. Get both carry_contract and pric_contract entries
    2. If the contract appears in PRICE_CONTRACT check that there is a row corresponding to
        the following splice date for the contract after combining PRICE and CARRY rows.
    3. If not - compunte the splice date row from the PRICE series
    i.e
    DATE    PRICE CARRY CARRY_CONTRACT PRICE_CONTRACT
            ...   ...   201103         201106
            ...   ...   201106         201109    <- splice date   *** can use CARRY price for 201106 price

    DATE    PRICE CARRY CARRY_CONTRACT PRICE_CONTRACT
            ...   ...   201109         201106
            ...   ...   201112         201109    <- splice date   *** Must compute 201106 price (from PRICE)

    the contract may also appear in just CARRY_CONTRACT or just PRICE_CONTRACT!
    '''

    legacy_price_table = "z_" + market.lower() + "_price"
    legacy_carry_table = "z_" + market.lower() + "_carrydata"
    try:
        price_df = pd.read_sql_table(table_name=legacy_price_table, \
                                     con=engine, index_col=['DATETIME'],
                                     parse_dates=['DATETIME'])
        len_price = len(price_df)
    except Exception as e:
        # If error, announce and get data from quandl or IB
        print(legacy_price_table, e, "Error when getting table from database!")

    try:
        carry_df = pd.read_sql_table(table_name=legacy_carry_table, \
                                     con=engine, index_col=['DATETIME'],
                                     columns=['DATETIME','PRICE','PRICE_CONTRACT', 'CARRY','CARRY_CONTRACT'],
                                     parse_dates=['DATETIME'])
        carry_price_contract_df = carry_df[(carry_df['PRICE_CONTRACT'] == contract)]
        carry_carry_contract_df = carry_df[(carry_df['CARRY_CONTRACT'] == contract)]
        len_carry_price_contract = len(carry_price_contract_df)
        len_carry_carry_contract = len(carry_carry_contract_df)
        len_carry = len(carry_df)
    except Exception as e:
        # If error, announce and get data from quandl or IB
        print(legacy_carry_table, e, "Error when getting table from database!")


    if len_carry_carry_contract > 0 and len_carry_price_contract == 0:
        # df1 = carry_df[(carry_df['CARRY_CONTRACT'] == contract)]
        carry_carry_contract_df = carry_carry_contract_df[pd.notnull(carry_carry_contract_df['CARRY'])]
        df = carry_carry_contract_df[['CARRY']].copy()
        df.rename(columns={'CARRY': 'PRICE'}, inplace=True)
        df.sort_index(inplace=True)
        return df
    elif len_carry_price_contract > 0 and len_carry_carry_contract == 0:
        # df1 = carry_df[(carry_df['PRICE_CONTRACT'] == contract)]
        carry_price_contract_df = carry_price_contract_df[pd.notnull(carry_price_contract_df['PRICE'])]
        df = carry_price_contract_df[['PRICE']].copy()
        df.sort_index(inplace=True)
        # determine date of last row i.e. the date before splicing...
        pre_splice_date = df[-1:].index.values[0]
        # the next day in the carry stream is the splice date!
        # remove nulls --- they mess up finding next valid date!
        splice_date = carry_df[pd.notnull(carry_df['PRICE'])].loc[pre_splice_date:][1:2].index.values[0]
        # Get the splice delta from the <panama price> - <raw price> on pre_splice_date
        # ... get the <panama price> from in price_df and compute delta on pre_splice_date
        pre_splice_date_raw_price = carry_df.loc[pre_splice_date:][0:1]['PRICE'][0]
        pre_splice_date_adj_price = price_df.loc[pre_splice_date:][0:1]['PRICE'][0]
        splice_delta = pre_splice_date_adj_price - pre_splice_date_raw_price
        # *** the adjusted price was added to the raw price, so it must be taken away from the
        # *** splice_date price to get the splice date raw price
        splice_date_price = price_df.loc[splice_date:][0:1]['PRICE'][0]  # This was splice price
        splice_date_raw_price = splice_date_price - splice_delta


        splice_date_row_df = carry_df.loc[splice_date:][0:1].drop(['CARRY', 'CARRY_CONTRACT', 'PRICE_CONTRACT'], 1)
        splice_date_row_df['PRICE'] = round(splice_date_raw_price, 3)
        df = df.append(splice_date_row_df)
        return df
    elif len_carry_price_contract > 0 and len_carry_carry_contract > 0:

        #d_carry = carry_df[(carry_df['CARRY_CONTRACT'] == contract)]
        #df1.set_index(['DATETIME'], inplace=True)
        #d_carry = d_carry[pd.notnull(d_carry['CARRY'])]
        carry_carry_contract_df = carry_carry_contract_df[pd.notnull(carry_carry_contract_df['CARRY'])]
        #df1 = d_carry[['CARRY']].copy()
        df1 = carry_carry_contract_df[['CARRY']].copy()
        df1.rename(columns={'CARRY': 'PRICE'}, inplace=True)

        carry_price_contract_df = carry_price_contract_df[pd.notnull(carry_price_contract_df['PRICE'])]
        #df2.set_index(['DATETIME'], inplace=True)
        df2 = carry_price_contract_df[['PRICE']].copy()
        # determine pre-splice date
        pre_splice_date = df2[-1:].index.values[0]
        splice_date = carry_df[pd.notnull(carry_df['PRICE'])].loc[pre_splice_date:][1:2].index.values[0]
        if not splice_date in df1.index:
            # Must compute splice_date value and add it to df2
            # Get the splice delta from the <panama price> - <raw price> on pre_splice_date
            # ... get the <panama price> from in price_df and compute delta on pre_splice_date
            pre_splice_date_raw_price = carry_df.loc[pre_splice_date:][0:1]['PRICE'][0]
            pre_splice_date_adj_price = price_df.loc[pre_splice_date:][0:1]['PRICE'][0]
            splice_delta = pre_splice_date_adj_price - pre_splice_date_raw_price
            # *** the adjusted price was added to the raw price, so it must be taken away from the
            # *** splice_date price to get the splice date raw price
            splice_date_price = price_df.loc[splice_date:][0:1]['PRICE'][0]  # This was splice price
            splice_date_raw_price = splice_date_price - splice_delta

            # df1.drop(['CARRY', 'CARRY_CONTRACT', 'PRICE_CONTRACT'], 1, inplace=True)  # without splice date row
            # df2.drop(['CARRY', 'CARRY_CONTRACT', 'PRICE_CONTRACT'], 1, inplace=True)  # without splice date row
            splice_date_row_df = carry_df.loc[splice_date:][0:1].drop(['CARRY', 'CARRY_CONTRACT', 'PRICE_CONTRACT'], 1)
            splice_date_row_df['PRICE'] = round(splice_date_raw_price, 3)
            df1 = df1.append(df2)
            df1 = df1.append(splice_date_row_df)
        else:
            df1 = df1.append(df2)
        df1.sort_index(inplace=True)
        return df1
    else:
        assert False, market + contract + " no legacy data found for contract!"




def get_raw_data(engine, client, mkt_ser, maturity, start_date, end_date, match):
    """

    :param engine:
    :param client:
    :param mkt_ser:
    :param maturity:
    :param start_date:
    :param end_date:
    :param match:
    :return: use_df, raw data from either quandl, IB or z_legacy...

    Before current month: Get settlement history from Quandl, if suspect, before July2017 retrieve from z_legacy...
    From current month on: Get settlement prices from IB, if not from Quandl
    i.e. Always get quandl data..
    before today compare quandl with legacy ...
    after today: compare quandl with IB ...
    """


    import datetime
    today = pd.datetime.today()
    if pd.isnull(end_date):
        end_date_plus = None
    else:
        end_date_plus = end_date + datetime.timedelta(days= 1, hours=23, minutes=1)
    yesterBD = pd.datetime.today() - pd.tseries.offsets.BDay(1)
    current_contract = datetime.date.today().strftime('%Y%m')
    if not pd.isnull(start_date):
        start_date_alt = datetime.datetime(start_date.year, start_date.month, start_date.day, 23)
    if not pd.isnull(end_date):
        end_date_alt = datetime.datetime(end_date.year, end_date.month, end_date.day, 23)

    if pd.isnull(start_date):
        start_string = None
    else:
        start_string = str(start_date)
    if pd.isnull(end_date):
        end_string = None
    else:
        end_string = str(end_date_plus)

    symbol = mkt_ser.CARVER
    print("--------", symbol,maturity,"---------")
    # Get quandl
    try:
        quandl_df = qndl_download(mkt_ser, maturity)

        if isinstance(quandl_df, pd.DataFrame):
            last_quandl_date = quandl_df.index[-1:][0]
            qev_df = quandl_df[start_string:end_string].resample("B").last()
            quandl_request_frame = True
            len_quandl = len(qev_df[pd.notnull(qev_df['PRICE'])])
            print("IB maturity: ", maturity, ": Quandl_length: ", len_quandl)
            use_df = quandl_df      # default return if data is not up to date...
        else:
            quandl_request_frame = False

    except Exception as e:
        quandl_request_frame = False
        print(e, maturity, "Can not download data from quandl ")


    if int(maturity) < int(current_contract):
        # Use quandl - or alternatively legacy...
        legacy_df = get_raw_legacy_data(engine, symbol, maturity)
        if isinstance(legacy_df, pd.DataFrame):
            last_legacy_date = legacy_df.index[-1:][0]
            legacy_request_frame = True
            lev_df = legacy_df[start_string:end_string].resample("B").last()
            len_legacy = len(lev_df[pd.notnull(lev_df['PRICE'])])
            print("Legacy maturity: ", maturity, "legacy_length: ", len_legacy)
            if symbol in ['KR3', 'KR10','EUR', 'LIVECOW','GAS_US','OAT', 'SP500', 'NASDAQ', 'MXP'] :
                use_df = legacy_df.copy(); print("Using Legacy")
                return use_df
        else:
            legacy_request_frame = False

        if not quandl_request_frame and not legacy_request_frame:
            assert False, symbol + maturity + " no download data or legacy data"
        else:
            if match:
            # Check whethere start and end dates are passed.
                if yesterBD <= start_date : # No Match Necessary
                    # if both loads exist with data_start, use longest
                    if (legacy_request_frame and quandl_request_frame):
                        #if symbol in ['EUR', 'LIVECOW','GAS_US','OAT', 'SP500', 'NASDAQ', 'MXP'] or len_legacy > len_quandl:
                        if len_legacy > len_quandl:
                            use_df = legacy_df.copy(); print("Using Legacy")
                        else:
                            use_df = quandl_df.copy(); print("Using Quandl")
                    # Or use whichever exists...
                    if legacy_request_frame and not quandl_request_frame:
                        use_df = legacy_df.copy(); print("Using Legacy")
                    if quandl_request_frame and not legacy_request_frame:
                        use_df = quandl_df.copy(); print("Using Quandl")

                if start_date < yesterBD and yesterBD < end_date: # start_date must be in load or cry foul
                    if (legacy_request_frame and quandl_request_frame):
                        if (start_date in legacy_df.index or start_date_alt in legacy_df.index) and \
                                (start_date in qev_df.index or start_date_alt in qev_df.index):
                            # use legacy if it has more rows.
                            #if symbol in ['EUR', 'LIVECOW','GAS_US','OAT', 'SP500', 'NASDAQ', 'MXP'] or len_legacy > len_quandl:
                            if len_legacy > len_quandl:
                                use_df = legacy_df.copy(); print("Using Legacy")
                            else:
                                use_df = quandl_df.copy(); print("Using Quandl")
                        if (start_date in legacy_df.index or start_date_alt in legacy_df.index) and \
                                (not start_date in qev_df.index and not start_date_alt in qev_df.index):
                             use_df =  legacy_df.copy()
                        if (start_date in qev_df.index or start_date_alt in qev_df.index) and \
                                (not start_date in legacy_df.index and not start_date_alt in legacy_df.index) :
                            use_df = quandl_df.copy(); print("Using Quandl")
                        if (not start_date in legacy_df.index and not start_date_alt in legacy_df.index) and \
                                (not start_date in qev_df.index and not start_date_alt in qev_df.index):
                            if last_quandl_date > start_date or last_legacy_date > start_date:
                                assert False, symbol + maturity + str(start_date) + "missing in both legacy and quandl loads"
                    if (legacy_request_frame and not quandl_request_frame):
                        if start_date in legacy_df.index or start_date_alt in legacy_df.index:
                            use_df = legacy_df.copy(); print("Using Legacy")
                        else:
                            if last_legacy_date > start_date:
                                assert False, symbol + maturity + str(start_date) + "missing in legacy load"
                    if ( quandl_request_frame and not legacy_request_frame):
                        if start_date in quandl_df.index or start_date_alt in quandl_df.index:
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            if last_quandl_date > start_date :
                                assert False, symbol + maturity + str(start_date) + "missing in quandl load"

                if end_date < yesterBD: # Both start_date and end_date should match or CRY foul!!
                    if (legacy_request_frame and quandl_request_frame):
                        if (start_date in legacy_df.index or start_date_alt in legacy_df.index) and \
                                (start_date in qev_df.index or start_date_alt in qev_df.index) and \
                                (end_date in legacy_df.index or end_date_alt in legacy_df.index) and \
                                (end_date in qev_df.index or end_date_alt in qev_df.index):
                            # use legacy if it has more rows.
                            #if symbol in ['EUR', 'LIVECOW','GAS_US','OAT', 'SP500', 'NASDAQ', 'MXP'] or  len_legacy > len_quandl:
                            if len_legacy > len_quandl:
                                use_df = legacy_df.copy(); print("Using Legacy")
                            else:
                                use_df = quandl_df.copy(); print("Using Quandl")
                        elif (start_date in legacy_df.index or start_date_alt in legacy_df.index) and \
                                (end_date in legacy_df.index or end_date_alt in legacy_df.index) :
                            use_df = legacy_df.copy(); print("Using Legacy")
                        elif (start_date in qev_df.index or start_date_alt in qev_df.index) and \
                                (end_date in qev_df.index or end_date_alt in qev_df.index):
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            # Reject all other outcomes
                            if last_quandl_date > end_date or last_legacy_date > end_date:
                                assert False, symbol + maturity + "either start or end dates missing in both quandl and legacy loads"
                    if (legacy_request_frame and not quandl_request_frame):
                        if (start_date in legacy_df.index or start_date_alt in legacy_df.index) and \
                                (end_date in legacy_df.index or end_date_alt in legacy_df.index) :
                            use_df = legacy_df.copy(); print("Using Legacy")
                        else:
                            if  last_legacy_date > end_date:
                                assert False, symbol + maturity + str(start_date) + "missing in legacy load"
                    if (quandl_request_frame and not legacy_request_frame):
                        if (start_date in quandl_df.index or start_date_alt in quandl_df.index) and \
                                (end_date in quandl_df.index or end_date_alt in quandl_df.index):
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            if last_quandl_date > end_date :
                                assert False, symbol + maturity + str(start_date) + "missing in quandl load"

            else: # if match: ... No match necessary - Simply use quandl if it has more rows.
                if (legacy_request_frame and quandl_request_frame) :
                    if len_quandl >= len_legacy:
                    #if len_legacy > len_quandl:
                        use_df = quandl_df.copy(); print("Using Quandl")
                    else:
                        use_df = legacy_df.copy(); print("Using Legacy")
                elif legacy_request_frame and not quandl_request_frame:
                    use_df = legacy_df.copy(); print("Using Legacy")
                elif quandl_request_frame and not legacy_request_frame:
                    use_df = quandl_df.copy(); print("Using Quandl")
        return use_df
    else:           # if int(maturity) < int(current_contract)
        ib_request = False
        try:
            #ib_df = ib_download(client, mkt_ser, maturity, end_date_plus)
            from pytz import timezone
            exchange = mkt_ser.IB_EXCHANGE
            if exchange == 'KSE':
                tz = 'Asia/Tokyo'
            else:
                tz = 'GMT'
            time_now = datetime.datetime.now(timezone(tz))
            today_asdate = time_now.date()
            today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
            ib_df = ib_download(client, mkt_ser, maturity, today_asdatetime)
            # return as much raw data as possible i.e. ib_df rather than ibev_df (just used to check against quandl for gaps in data)
            if isinstance(ib_df, pd.DataFrame):

                if pd.isnull(start_date):
                    start_string = None
                else:
                    start_string = str(start_date)
                if pd.isnull(end_date):
                    end_string = None
                else:
                    end_string = str(end_date_plus)
                ib_df.set_index(pd.to_datetime(ib_df.index), inplace=True)
                last_ib_date = ib_df.index[-1:][0]
                if last_ib_date > last_quandl_date:
                    use_df = ib_df
                #ib_df[start_string:end_string].resample("B").last()
                ibev_df = ib_df[start_string:end_string].resample("B").last()
                ib_request_frame = True
                len_ib = len(ibev_df[pd.notnull(ibev_df['PRICE'])]) # to check against quandl load for splice range...
                print("IB maturity: ", maturity, " IB length: ", len_ib)
            else:
                ib_request_frame = False
        except Exception as e:
            ib_request_frame = False
            ib_request = False

        if not quandl_request_frame and not ib_request_frame:
            return pd.DataFrame([])
            print(symbol + maturity + " no download data or legacy data")
        else:
            if match:
            # Check whethere start and end dates are passed.
                if yesterBD <= start_date : # No Match Necessary
                    # if both loads exist with data_start, use longest
                    if (ib_request_frame and quandl_request_frame):
                        if len_ib >= len_quandl:
                            use_df = ib_df.copy(); print("Using IB")
                        else:
                            use_df = quandl_df.copy(); print("Using Quandl")
                    # Or use whichever exists...
                    if ib_request_frame and not quandl_request_frame:
                        use_df = ib_df.copy(); print("Using IB")
                    if quandl_request_frame and not ib_request_frame:
                        use_df = quandl_df.copy(); print("Using Quandl")

                if start_date < yesterBD and yesterBD < end_date: # start_date must be in load or cry foul
                    if (ib_request_frame and quandl_request_frame):
                        if (start_date in ibev_df.index or start_date_alt in ibev_df.index) and \
                                (start_date in qev_df.index or start_date_alt in qev_df.index):
                            # use quandl if it has more rows.
                            if len_ib >= len_quandl:
                                use_df = ib_df.copy(); print("Using IB")
                            else:
                                use_df = quandl_df.copy(); print("Using Quandl")
                        if (start_date in ibev_df.index or start_date_alt in ibev_df.index) and \
                                (not start_date in qev_df.index and not  start_date_alt in qev_df.index)  :
                             use_df =  ib_df.copy()
                        if (start_date in qev_df.index or start_date_alt in qev_df.index) and \
                                (not start_date in ibev_df.index and not start_date_alt in ibev_df.index):
                            use_df = quandl_df.copy(); print("Using Quandl")
                        if (not start_date in ibev_df.index and not start_date_alt in ibev_df.index) and \
                                    (not start_date in qev_df.index and not start_date_alt in qev_df.index):
                            if last_quandl_date > start_date or last_ib_date > start_date:
                                assert False, symbol + maturity + str(start_date) + "missing in both ib and quandl loads"
                    if (ib_request_frame and not quandl_request_frame):
                        if start_date in ibev_df.index or start_date_alt in ibev_df.index :
                            use_df = ib_df.copy(); print("Using IB")
                        else:
                            if last_ib_date > start_date:
                                assert False, symbol + maturity + str(start_date) + "missing in ib load"
                    if ( quandl_request_frame and not ib_request_frame):
                        if start_date in quandl_df.index or start_date_alt in quandl_df.index:
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            if last_quandl_date > start_date :
                                assert False, symbol + maturity + str(start_date) + "missing in quandl load"

                if end_date < yesterBD: # Both start_date and end_date should match or CRY foul!!
                    if (ib_request_frame and quandl_request_frame):
                        if (start_date in ibev_df.index or start_date_alt in ibev_df.index) and \
                                (start_date in qev_df.index or start_date_alt in qev_df.index) and \
                                        (end_date in ibev_df.index or end_date_alt in ibev_df.index) and \
                                                (end_date in qev_df.index or end_date_alt in qev_df.index):
                            # use legacy if it has more rows or if IB is more up to date.
                            if len_ib >= len_quandl or ib_df[-1:].index[0] > quandl_df[-1:].index[0]:
                                use_df = ib_df.copy(); print("Using IB")
                            else:
                                use_df = quandl_df.copy(); print("Using Quandl")
                        elif (start_date in ibev_df.index or start_date_alt in ibev_df.index) and \
                                (end_date in ibev_df.index or end_date_alt in ibev_df.index) :
                            use_df = ib_df.copy(); print("Using IB")
                        elif (start_date in quandl_df.index or start_date_alt in quandl_df.index) and \
                                (end_date in quandl_df.index or end_date_alt in quandl_df.index) :
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            # Reject all other outcomes
                            if last_quandl_date > end_date or last_ib_date > end_date:
                                assert False, symbol + maturity + "either start or end dates missing in both quandl and legacy loads"
                    if (ib_request_frame and not quandl_request_frame):
                        if (start_date in ibev_df.index or start_date_alt in ibev_df.index) and \
                                (end_date in ibev_df.index or end_date_alt in ibev_df.index):
                            use_df = ib_df.copy(); print("Using IB")
                        else:
                            if last_ib_date > start_date:
                                assert False, symbol + maturity + str(start_date) + "missing in ib load"

                    if (quandl_request_frame and not ib_request_frame ):
                        if (start_date in quandl_df.index or start_date_alt in quandl_df.index) and \
                                (end_date in quandl_df.index or end_date_alt in quandl_df.index):
                            use_df = quandl_df.copy(); print("Using Quandl")
                        else:
                            if last_quandl_date > start_date :
                                assert False, symbol + maturity + str(start_date) + "missing in quandl load"

            else:   # No match necessary - Simply use quand if it has more rows.
                if (ib_request_frame and quandl_request_frame) :
                    # Use IB if it is more up to date or it has more rows...
                    if len_ib >= len_quandl or ib_df[-1:].index[0] > quandl_df[-1:].index[0]:
                        use_df = ib_df.copy(); print("Using IB")
                    else:
                        use_df = quandl_df.copy(); print("Using Quandl")
                elif ib_request_frame and not quandl_request_frame:
                    use_df = ib_df.copy(); print("Using IB")
                elif quandl_request_frame and not ib_request_frame:
                    use_df = quandl_df.copy(); print("Using Quandl")
        return use_df


def get_raw_data_update(engine, mkt_ser, maturity, start_date, end_date, match):

    # First check whether database data is up to date with daily updates... (i.e. from quandl)
    # Must consider Business Day (ignore Holidays during processing...)

    import datetime
    if not pd.isnull(start_date):
        #
        if start_date.hour == 23:
            start_date_alt = datetime.datetime(start_date.year, start_date.month, start_date.day, 0)
        if start_date.hour == 0:
            start_date_alt = datetime.datetime(start_date.year, start_date.month, start_date.day, 23)

    if not pd.isnull(end_date):
        #
        if end_date.hour == 23:
            end_date_alt = datetime.datetime(end_date.year, end_date.month, end_date.day, 0)
        if end_date.hour == 0:
            end_date_alt = datetime.datetime(end_date.year, end_date.month, end_date.day, 23)

    db_request = False
    quandl_request = False
    ib_request = False

    # Get PRICE mat
    symbol = mkt_ser.CARVER
    table = symbol.lower() + str(maturity)

    # Check for local database storage of raw data
    try:
        table_df = pd.read_sql_table(table_name=table, \
                                     con=engine, index_col=['DATETIME'], \
                                     parse_dates=['DATETIME'])


    except Exception as e:
        # If error, announce and get data from quandl or IB
        print(table, e, "Error when getting table from database!")
    else:
        # If table exists, check whether the startdate and enddate are available in the database
        # If so no downloads required from Quandl
        # Checks that the splice dates, start_date and end_date, if in the past, are available if any later dates are contained
        # in the database or downloaded data. If not the program should skip that market

        temp_df = table_df.copy()
        temp_df['HOURS'] = temp_df.index.map(lambda x: x.hour)
        closing_prices = temp_df[(temp_df['HOURS'] == 0) | (temp_df['HOURS'] == 23) ]
        last_settlement_date = closing_prices[-1:].index[0]
        db_request = True
        if last_settlement_date >= end_date:
            if match:
                if start_date == start_date:
                    if start_date.date() < last_settlement_date.date() and not \
                            (start_date in table_df.index or start_date_alt in table_df.index):
                        assert False, str(maturity) + ": Start splice date is missing in database data"
                if end_date == end_date:
                    if end_date.date() < last_settlement_date.date() and not \
                            (end_date in table_df.index or end_date_alt in table_df.index):
                        assert False, str(maturity) + ": End splice date is missing in database data"
                return table_df
            else:
                return table_df
    finally:

        try:
            quandl_df = qndl_download(mkt_ser, maturity)
            new_df = quandl_df
            quandl_request = True
            # print(quandl_df.tail(4))
        except Exception as e:
            print(e, maturity, "Can not download data from quandl ")
            assert False, maturity
        else:
            if db_request:
                new_df = table_df.append(quandl_df[last_settlement_date:][1:])
            else:
                new_df = quandl_df
            if check_data_ok(symbol, new_df, start_date, end_date, match):
                try:
                    to_store_df = new_df.copy()
                    to_store_df.reset_index(inplace=True)
                    to_store_df.to_sql(name=table, con=engine, if_exists='replace', index=False)
                except:
                    print("Can't access database", table)
                    assert False, "Check database..."
                return new_df


def get_active_price_and_carry(engine, mkt_ser):
    symbol = mkt_ser.CARVER
    price_table = symbol.lower() + "_price"
    carrydata_table = symbol.lower() + "_carrydata"

    # Determine if the contracts to add are already in
    try:
        price_df = pd.read_sql_table(table_name=price_table, con=engine, \
                                     index_col=['DATETIME'], parse_dates=['DATETIME'], \
                                     columns=['PRICE'])
    except Exception as e:
        print("Cant access table: ", carrydata_table, ": skipping market: ",symbol)
        return(None,None)
    try:
        carry_df = pd.read_sql_table(table_name=carrydata_table, con=engine, \
                                     index_col=['DATETIME'], \
                                     columns=[ 'PRICE', 'CARRY' , 'CARRY_CONTRACT', 'PRICE_CONTRACT'], \
                                     parse_dates=['DATETIME'])
    except Exception as e:
        print("Can't access table: ", price_table, ": skipping market: ",symbol)
        return(None, None)
    # curr_price_contract = carry_df[-1:]['PRICE_CONTRACT'][0]
    return (price_df,carry_df)


def set_active_price_and_carry(engine, mkt_ser, price_df, carry_df):
    symbol = mkt_ser.CARVER
    price_table = symbol.lower() + "_price"
    carrydata_table = symbol.lower() + "_carrydata"

    price_df.reset_index(inplace=True)
    try:
        price_df.to_sql(name=price_table, con=engine, if_exists='replace', index=False)
    except:
        print("Can't access database", price_table)
        assert False, "Check database..."

    carry_df.reset_index(inplace=True)
    try:
        carry_df.to_sql(name=carrydata_table, con=engine, if_exists='replace', index=False)
    except:
        print("Can't access database", carrydata_table)
        assert False, "Check database..."


def set_raw_data(engine, table, df, append):

    if append:
        # retrieve table and add df to it... and only add rows in df that don't already exist
        new_rows = False
        try:
            current_df = pd.read_sql_table(table_name=table, \
                                         con=engine, index_col=['DATETIME'],
                                         parse_dates=['DATETIME'])

        except Exception as e:
            print(e, " Can't access table: ", table, ":: Overwriting")
            new_rows = True # will use df to overwrite
        else:
            if len(current_df) > 0:
                current_df['HOURS'] = current_df.index.map(lambda x: x.hour)
                closing_prices = current_df[(current_df['HOURS'] == 0) | (current_df['HOURS'] == 23)]
                last_settlement_date = closing_prices[-1:].index[0]
                df_toadd = df[last_settlement_date:][1:]
                if len(df_toadd) > 0:
                    df = current_df.append(df_toadd)
                    df.drop(['HOURS'],1,inplace=True)
                    new_rows = True # will add df with new rows
    if not append or new_rows:
        try:
            to_store_df = df.copy()
            to_store_df.reset_index(inplace=True)
            to_store_df.to_sql(name=table, con=engine, if_exists='replace', index=False)
        except:
            print(e, " Can't access database", table)
            assert False, "Check database..."


def get_splice_data(engine, client, mkt_ser, row, initialize):
    import datetime

    symbol = mkt_ser.CARVER

    carry_mat = str(int(row.CARRY_CONTRACT))
    carry_table = symbol.lower() + carry_mat
    price_mat = str(int(row.PRICE_CONTRACT))
    price_table = symbol.lower() + price_mat
    start_date = row.DATETIME
    end_date = row.END_DATETIME
    if pd.isnull(end_date):
        end_date = datetime.datetime(2099, 1, 1)
    today = datetime.datetime.now()
    if not "end_date" in locals():
        end_date = today

    if initialize:
        append = False          # overwrite any existing table
        price_df = get_raw_data(engine, client, mkt_ser,price_mat, start_date, end_date, True)
        if len(price_df) > 0 :
            set_raw_data(engine, price_table, price_df, append)

        carry_df = get_raw_data(engine, client, mkt_ser, carry_mat, start_date, end_date, False)
        if len(carry_df) > 0:
            set_raw_data(engine, carry_table, carry_df, append)

    else:
        # first get current db raw data and then update with download df,
        append = True
        price_df = get_raw_data(engine, client, mkt_ser, price_mat, start_date, end_date, True)
        set_raw_data(engine, price_table, price_df, append)

        carry_df = get_raw_data(engine, client, mkt_ser, carry_mat, start_date, end_date, False)
        set_raw_data(engine, carry_table, carry_df, append)


    return(price_df,carry_df)


def check_raw_data_downloads_v2(engine, client, mkt_ser, rolls, initialize):
    """
    :param engine:
    :param mkt_ser:
    :param rolls:
    :return: streams_collection of CARRY & PRICE dataframes corresponding to each splice date
    # For past maturities, only check that start and end dates are available for PRICE and CARRY
    #   Attempt to download both from Quandl
    #   Assert error if still a PRICE splice date is missing.
    # For present and future maturities
    #   Get the latest data up to yesterday
    #   For PRICE matuirty get up to the minute data
    #   Assert error if a start data in the past is missing
    #   Ignore future splice dates
    """

    import datetime
    today_asdate = datetime.date.today()
    today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
    symbol = mkt_ser.CARVER
    rolls_copy = rolls.copy()
    rolls_copy['END_DATETIME'] = rolls_copy['DATETIME']
     # Make copy to upshift END_DATETIME
    rolls_copy.END_DATETIME = rolls_copy.END_DATETIME.shift(-1)
    streams_collection = []
    for row in rolls_copy.itertuples():
        # get_splice_mats(row)
        (price_df, carry_df) = get_splice_data(engine, client, mkt_ser, row, initialize)
        if row.DATETIME <= today_asdatetime:
            streams_collection.append([row, price_df, carry_df])
    return streams_collection


def initialize_series(engine, client, mkt_ser, rolls ):
    import datetime
    initialize = True
    streams_collection = check_raw_data_downloads_v2(engine, client, mkt_ser, rolls, initialize)
    # streams_collection has list of [schedule, price_df, carry_df] where schedule is (DATETIME, CARRY_CONTRACT & PRICE_CONTRACT)
    # First row is base
    today_asdate = datetime.date.today()
    today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
    count = 0
    coll = []

    symbol = mkt_ser.CARVER
    for row in streams_collection:
        splice_date = row[0].DATETIME
        if splice_date < today_asdatetime:
            price_mat = row[0].PRICE_CONTRACT
            carry_mat = row[0].CARRY_CONTRACT
            #### **** AttributeError: 'NoneType' object has no attribute 'resample'
            #print("Price mat: ", price_mat)
            #print("Carry mat: ", carry_mat)
            price_df = row[1].resample("B").last()
            carry_df = row[2].resample("B").last()
            if count == 0:
                # initialize splice
                spliced_price = price_df
                spliced_carry = pd.concat([price_df, carry_df], axis=1)
                spliced_carry.columns = ["PRICE", 'CARRY']
                #spliced_carry = carry_df[pd.notnull(carry_df['PRICE'])]
                spliced_carry["CARRY_CONTRACT"] = carry_mat
                spliced_carry["PRICE_CONTRACT"] = price_mat
                spliced_carry.index.names = ['DATETIME']
                #print("Roll number: ", count + 1, " Splice date: ", splice_date)
                pretty_print("Roll number: " + str(count + 1) + " Splice date: " + str(splice_date) + " Price maturity: " + price_mat, spliced_price, 0, 5)
                pretty_print("Roll number: " + str(count + 1) + " Splice date: " + str(splice_date) + " Carry maturity: " + carry_mat, spliced_carry, 0, 5)
            else:
                print("----Next maturity: ", price_mat)
                spliced_price = splice_price(spliced_price, price_df, splice_date)
                spliced_carry = splice_carry(symbol, spliced_carry, price_df, carry_df, price_mat, carry_mat, splice_date)
                pretty_print("Roll number: " +  str(count + 1) +" Splice date: " + str(splice_date) + " Price maturity: " + price_mat, spliced_price, 0, 5)
                pretty_print("Roll number: " + str(count + 1) +" Splice date: " + str(splice_date) + " Carry maturity: " + carry_mat, spliced_carry, 0, 5)
            count += 1
    if count > 0:
        print("****************************************************************************")
        spliced_price.to_csv("panama_price_file.csv")
        spliced_carry.to_csv("panama_carry_file.csv")
        # Set the database table
        set_active_price_and_carry(engine, mkt_ser, spliced_price, spliced_carry)

        print("************************", count, " usable roll/s ******************************")
        pretty_print("Current price mat: " + str(price_mat), spliced_price, 0, 5)
        pretty_print("Current carry mat: " + str(carry_mat), spliced_carry, 0, 5)
        print("********************************************************************************")

        coll.append(spliced_price)
    return coll


def update_current_maturities(engine, client, mkt_ser, price_mat,carry_mat, curr_price, curr_carry):
    """

    :param engine: comms engine to database
    :param mkt_ser:
    :param price_mat: PRICE maturity
    :param carry_mat: CARRY maturity
    :param curr_price: panama stitched price strean
    :param curr_carry: stitched carry stream
    :return:
    """

    # First get the current price and carry raw data, update them with current mat
    # and return the two as a tuple...
    import datetime

    symbol = mkt_ser.CARVER
    q_price_df = get_raw_data(engine, client, mkt_ser, price_mat, None, None, False)
    q_carry_df = get_raw_data(engine, client, mkt_ser, carry_mat, None, None, False)
    # Add the latest updates... new series 'spliced..' are now ready for any splicing

    print("Price_mat: ", price_mat, "Carry_mat: ", carry_mat)
    print("Current Price series ")
    print(curr_price.tail(7))
    pretty_print("Current price mat: " + str(price_mat), curr_price, 0, 5)
    pretty_print("Current carry mat: " + str(carry_mat), curr_carry, 0, 5)

    price_df = q_price_df.resample("B").last()
    if len(q_carry_df) > 0:
        carry_df = q_carry_df.resample("B").last()
    else:
        carry_df = q_carry_df
    temp_df = curr_price.copy()
    temp_df['HOURS'] = temp_df.index.map(lambda x: x.hour)
    closing_prices = temp_df[(temp_df['HOURS'] == 0) | (temp_df['HOURS'] == 23)]
    last_settlement_date = closing_prices[-1:].index[0]
    price_toadd = price_df[last_settlement_date:][1:]
    append = True
    if len(price_toadd) > 0:
        # Add new updates...
        end_date = price_toadd[-1:].index[0]
        end_date_r1d = end_date + datetime.timedelta(days= 1, hours=23, minutes=1)
        new_price_df = curr_price.append(price_df[last_settlement_date:][1:])
        # *** update PRICE raw data
        price_table = mkt_ser.CARVER.lower() + str(int(price_mat))
        set_raw_data(engine, price_table, new_price_df, append)
        # *** create carry to add filling CARRY missing prices

        carry_toadd = carry_df[last_settlement_date:end_date_r1d][1:]
        carry_toadd = pd.concat([price_toadd, carry_toadd], axis=1)
        carry_toadd.columns = ["PRICE", 'CARRY']
        # spliced_carry = carry_df[pd.notnull(carry_df['PRICE'])]
        carry_toadd["CARRY_CONTRACT"] = carry_mat
        carry_toadd["PRICE_CONTRACT"] = price_mat
        carry_toadd.index.names = ['DATETIME']  # indexed !!!
        #carry_toadd = get_padded_carry(carry_toadd, symbol, price_mat)
        new_carry_df = curr_carry.append(carry_toadd)
        # pad last maturity carry
        base_carry = new_carry_df[(new_carry_df['PRICE_CONTRACT'] != price_mat)]
        carry_to_pad = new_carry_df[(new_carry_df['PRICE_CONTRACT'] == price_mat)]
        padded_carry = get_padded_carry(carry_to_pad, symbol, price_mat)
        new_carry_df = base_carry.append(padded_carry)
        # *** update CARRY raw data
        carry_table = mkt_ser.CARVER.lower() + str(int(carry_mat))
        set_raw_data(engine, carry_table, carry_df, append)
        return (new_price_df, new_carry_df)  # return updated series..
    return(curr_price, curr_carry) # no new updates - simply return inputs


def get_curr_rolls_and_mats(mkt_ser, rolls, curr_carry_df):

    import datetime

    curr_price_mat = curr_carry_df[-1:].iloc[0]['PRICE_CONTRACT']
    curr_carry_mat = curr_carry_df[-1:].iloc[0]['CARRY_CONTRACT']
    # date of last roll is the date curr_price_mat first appears in curr_carry_df, i.e. take that row's index
    last_splice_datetime = curr_carry_df[curr_carry_df['PRICE_CONTRACT'] == curr_price_mat][0:1].index[0]
    last_splice_date = datetime.datetime(last_splice_datetime.year, last_splice_datetime.month,
                                         last_splice_datetime.day)
    # Now check rolls for that date, if found usable rolls are all rolls after that one. if not there are NO
    # usable rolls.
    found = False
    for row in rolls.itertuples():
        if row.DATETIME == last_splice_date:
            found = True
    if found:
        usable_rolls = rolls[(rolls['DATETIME'] > last_splice_date)]
    else:
        usable_rolls = rolls[(rolls['DATETIME'] != rolls['DATETIME'])] # empty dataframe, no rolling
    return(usable_rolls, curr_price_mat, curr_carry_mat)


def update_series(engine, client, mkt_ser, rolls ):
    """
    :param engine:
    :param mkt_ser:
    :param rolls:
    :return: list of spliced PRICE and CARRY streams
    Assumes PRICE and CARRY streams are in the database engine. Use rolls to determine missing entries and perform
    updates and any required stitching
    """
    # 1. Find current price and carry mats (curr_price_mat, curr_carry_mat) - current active roll
    # 2. from active roll, determine any due rolls..
    # 3. Update raw data
    # 4. Update current roll
    # 5. Update any other due rolls

    import datetime
    from pytz import timezone
    exchange = mkt_ser.IB_EXCHANGE
    if exchange == 'KSE':
        tz = 'Asia/Tokyo'
    else:
        tz = 'GMT'
    now_asdatetime = datetime.datetime.now(timezone(tz))
    today_asdatetime = datetime.datetime(now_asdatetime.year, now_asdatetime.month, now_asdatetime.day)

    # Check the current PRICE and CARRY... if none exist, skip the symbol
    (curr_price_df, curr_carry_df) = get_active_price_and_carry(engine, mkt_ser)
    if not isinstance(curr_price_df, pd.DataFrame) or not isinstance(curr_carry_df, pd.DataFrame):
        return

    # From CARRY stream determine the current PRICE and CARRY contracts and the usable_rolls
    (usable_rolls, curr_price_mat, curr_carry_mat) = get_curr_rolls_and_mats(mkt_ser, rolls, curr_carry_df)

    # UPDATE Current maturities
    #  Get all raw data for PRICE and CARRY contracts and then update current maturities
    # **** This corresponds to raw data for DAILY UPDATES!!!!
    (spliced_price, spliced_carry) = update_current_maturities(engine, client, mkt_ser, curr_price_mat, curr_carry_mat, curr_price_df, curr_carry_df)

    # PERFORM any due rolls
    # 1. Update any data not up to date in database. Return a list of all
    # 2.
    initialize = False
    list = check_raw_data_downloads_v2(engine, client, mkt_ser, usable_rolls, initialize)
    count = 0
    #today_asdate = datetime.date.today()
    #today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
    symbol = mkt_ser.CARVER
    for row in list:
        splice_date = row[0].DATETIME


        price_mat = row[0].PRICE_CONTRACT
        carry_mat = row[0].CARRY_CONTRACT
        price_df = row[1].resample("B").last()
        if len(row[2]) > 0:
            carry_df = row[2].resample("B").last()
        else:
            carry_df = row[2]
        #if count == 0 :
        #    (spliced_price, spliced_carry) = update_current_mat(row , curr_price_df, curr_carry_df)
        # Check if there are entries later than splice date!
        last_price_date = price_df[-1:].index[0]
        if splice_date < today_asdatetime and last_price_date >= splice_date:
            print("----Next maturity: ", price_mat)
            spliced_price = splice_price(spliced_price, price_df, splice_date)
            spliced_carry = splice_carry(symbol, spliced_carry, price_df, carry_df, price_mat, carry_mat, splice_date)
            pretty_print("Roll number: "+ str(count + 1) +" Splice date: " + str(splice_date) +" Price maturity: " + str(curr_price_mat), spliced_price, 0, 5)
            pretty_print("Roll number: "+ str(count + 1) +" Splice date: " + str(splice_date) +" Carry maturity: " + str(curr_carry_mat), spliced_carry, 0, 5)
            count += 1

    print("****************************************************************************")
    if count > 0:
        print("*************************",count," usable roll/s *************************")
        pretty_print("Current price mat: " + str(curr_price_mat), spliced_price, 0, 5)
        pretty_print("Current carry mat: " + str(curr_carry_mat), spliced_carry, 0, 5)
        print("****************************************************************************")
    else:
        print("************************ NO usable rolls! ********************************")
        print("Price mat:", curr_price_mat)
        pretty_print("Current price mat: " + str(curr_price_mat), spliced_price, 0, 5)
        pretty_print("Current carry mat: " + str(curr_carry_mat), spliced_carry, 0, 5)
        print("****************************************************************************")

    # Set the database table
    set_active_price_and_carry(engine, mkt_ser, spliced_price, spliced_carry)


def update_fx(engine, ib_client, market_series):
    # update forex data in the database
    import datetime
    today = datetime.datetime.now()
    maturity = ""
    df_fx = ib_download(ib_client, market_series, maturity, today)
    print(df_fx)
    append = True
    symbol = market_series.CARVER
    table = symbol + "fx"
    df_fx.set_index(pd.to_datetime(df_fx.index), inplace=True)
    set_raw_data(engine, table, df_fx, append)



































































































"""




def getIBContract(engine, market, curr_contract):

    :param engine:
    :param market:
    :param contract:
    :return:
    IB should return latest intra-day data plus settlement price from yesterday if not available
    1. retrieve database raw data...
    2. Check if newer rows in quandl
    3. Update database with newer rows
    4. return the entire current raw data
    2. Update database table.

    price_string = 'Settle'
    to_save = False
    table = market.lower() + str(curr_contract)
    try:
        contract_df = pd.read_sql_table(table_name=table, \
                                        con=engine, index_col=['Date'], \
                                        parse_dates=['Date'])
    except Exception as e:
        print(table, "is not in the database!")
        contract_df = ib_download(engine, market, curr_contract)



"""





















