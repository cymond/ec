from syscore.accounting import account_test

from syscore.pdutils import turnover
from sysdata.configdata import Config
from sysdata.csvdata import csvFuturesData
from systems.provided.futures_chapter15.estimatedsystem import futures_system
from systems.provided.moretradingrules.morerules import breakout

import pandas as pd
import numpy as np
from matplotlib.pyplot import show, legend, matshow
import time

#path = '/home/pete/Repos/pysystemtrade/private/SystemR/'
path = '/home/pete/Repos/test/quality/private/SystemR/'
today = time.strftime("%Y%m%d")
positions_file = path  + 'positions/system.csv'
history_file = path + 'positions/history/' + today + "system.csv"


## new system has all trading rules
new_config = Config("private.SystemR.production01.yaml")
# pointer to data
data=csvFuturesData("private.SystemR.data")


system = futures_system(data=data, config=new_config, log_level="on")

instruments = pd.DataFrame(system.get_instrument_list() )
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

report_path = path  + 'reports/' +  today

system.accounts.portfolio().resample("B").sum().to_csv(report_path + "_daily.csv")
system.accounts.portfolio().resample("M").sum().to_csv(report_path + "_monthly.csv")
system.accounts.portfolio().resample("A").sum().to_csv(report_path + "_annual.csv")
system.accounts.portfolio().cumsum().to_csv(report_path + "_cum.csv")
print("Now writing to Documents folder...")


