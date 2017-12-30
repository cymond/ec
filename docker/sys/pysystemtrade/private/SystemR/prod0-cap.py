import time, os, sys

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
    console_formatter = logging.Formatter('{asctime} {name} {levelname:8s} {message}', datefmt='%Y%m%d %I:%M:%S%p',  style='{')
    file_formatter = logging.Formatter('{asctime},{name},{levelname:8s},{message}', datefmt='%Y%m%d %I:%M:%S%p',style='{')
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

    today = time.strftime("%Y%m")
    year = int(today[:4])
    month = int(today[4:])

    if year == 2017 and month < 7:
        offset = (7 - month) * 10000
    else:
        offset = 0
    print("Offset: ", offset)
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
    '''
    print("sys.executable: ", sys.executable)
    print("os.get_cwd(): ", os.getcwd())
    print("sys.version: ", sys.version)
    print("sys.path")
    print(sys.path)
    print("--------------------------")
    print(os.path.join(os.path.dirname(__file__), '..'))
    print("--------------------------")
    '''
    try:
        user_paths = os.environ['PYTHONPATH'].split(os.pathsep)
    except KeyError:
        user_paths = []
    print(user_paths)

    print("--------------------------")

    today = time.strftime("%Y%m%d")
    dir_filename = "../SystemR/admin/directories.csv"
    # point to output files
    dir_df = pd.read_csv(dir_filename, index_col=['DIRECTION'], dtype={'PATH': str})
    admin_path = dir_df.loc['ADMIN'][0]
    positions_file = admin_path + 'positions_test/system.csv'
    history_file = admin_path + 'positions_test/history/' + today + "system.csv"
    capital_file = admin_path + 'capital/capital.csv'
    print("In main....")


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
    print("The End")
    print(cap_df.index.values)
    types = [type(t) for t in cap_df.index.values]
    print(types)
    cap_df.to_csv(capital_file)

    # Save the file to disk

if __name__ == "__main__":

    logger = set_logging()
    try:
        main()
    except Exception as e:
        logger.exception(e)