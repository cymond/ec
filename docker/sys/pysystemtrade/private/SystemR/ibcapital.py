import time, os, sys
import sqlalchemy
engine = sqlalchemy.create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')


def get_capital_offset():

    offset = 0
    return offset

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

def   main():
    import pandas as pd
    import numpy as np
    from matplotlib.pyplot import show, legend, matshow




    # **** Get capital from IB ****
    ib_capital = get_IB_cap()
    offset = get_capital_offset()
    notional_cap = ib_capital + offset
    print("ib capital: ", ib_capital, "offset: ", offset)

    cap_dict = {'DATE': today, 'IBCAP': ib_capital, 'CORRECTION': offset}
    update_capital(capital_file, cap_dict)

    if not os.path.isfile(dir_filename):
        logger.error("The file, {}, does not exist".format(dir_filename))
    else:
        # point to output files
        dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
        admin_path = dir_df.loc['ADMIN'][0]
        #account = get_IB_cap()
        capital_file = admin_path + 'capital/capital.csv'

    if not os.path.isfile(capital_file):
        # create a new Dataframe with one row for today
        cap_df = pd.DataFrame(columns=['IB_CAPITAL', 'OFFSET'])
        cap_df.loc[today] = [notional_cap, offset]
        cap_df.index.names = ['DATE']
        #cap_df.columns = ['IB_CAPITAL', 'OFFSET']
    else:
        # Check if file has a valid row for today's date. If not add the row to the file
        cap_df = pd.read_csv(capital_file, usecols=[0,1,2], dtype={0: int})
        cap_df.columns = ['DATE','IB_CAPITAL', 'OFFSET']
        cap_df.set_index('DATE', inplace=True)
        cap_df.ix[int(today)]=[notional_cap, offset]
        #update_df = pd.DataFrame([today, notional_cap,offset])
        #update_df.columns = ['DATE', 'IB_CAPITAL', 'OFFSET']
        #update_df.set_index('DATE', inplace=True)
        #cap_df.update(pd.DataFrame())

    print(cap_df)
    types = [type(t) for t in cap_df.index.values]
    cap_df.to_csv(capital_file)
    cap_df.to_sql('capital', con=engine, if_exists='replace', index=False)


    # Save the file to disk

if __name__ == "__main__":

    try:
        main()
    except Exception as e:
        logger.exception(e)