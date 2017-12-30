from private.SystemR.dbutils.panama import ib_download
import pandas as pd
import datetime
from pytz import timezone
from private.SystemR.wrapper_v2 import IBWrapper, IBclient

    #engine = create_engine('mysql+pymysql://root:admin@0.0.0.0/pkdemo')
callback = IBWrapper()

client = IBclient(callback)
end_date = datetime.datetime.now()
maturity = '201709'
#mkt_ser = resource_marketdata_setup
'''
CARVER,QUANDL,IB,SECTYPE,CURRENCY,Q_EXCHANGE,IB_EXCHANGE,MULTIPLIER,PRICE,CARRY
KR10,KRDRVFUBMA,FLKTB,FUT,KRW,KRX,KSE,0,201706,201709

mkt_ser  = pd.Series({"QUANDL": "ED", "IB": "GE", "SECTYPE": "FUT", "CURRENCY": "USD",
                       "Q_EXCHANGE": "CME", "IB_EXCHANGE": "GLOBEX", "MULTIPLIER": 0})

mkt_ser  = pd.Series({"QUANDL": "KRDRVFUBMA", "IB": "FLKTB", "SECTYPE": "FUT", "CURRENCY": "KRW",
                       "Q_EXCHANGE": "KRX", "IB_EXCHANGE": "KSE", "MULTIPLIER": 0})
'''

mkt_ser  = pd.Series({"QUANDL": "KRDRVFUBMA", "IB": "FLKTB", "SECTYPE": "FUT", "CURRENCY": "KRW",
                       "Q_EXCHANGE": "KRX", "IB_EXCHANGE": "KSE", "MULTIPLIER": 0})

print("Japanese Time Zone")
tz = 'Asia/Tokyo'
time_now = datetime.datetime.now(timezone(tz))
print("Time now Japan: ", time_now)
result = ib_download(client, mkt_ser, maturity, end_date=time_now )
print(result.tail(5))
print("------------------------")
today_asdate = time_now.date()
print("Today as Date Japan: ", today_asdate)
today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
print("Today as Datetime: ", today_asdatetime)
result = ib_download(client, mkt_ser, maturity, end_date=today_asdatetime )
print(result.tail(5))
print()
print("================================================================================")
print()
print("GMT Zone")
mkt_ser  = pd.Series({"QUANDL": "ED", "IB": "GE", "SECTYPE": "FUT", "CURRENCY": "USD",
                       "Q_EXCHANGE": "CME", "IB_EXCHANGE": "GLOBEX", "MULTIPLIER": 0})

tz = 'GMT'
time_now = datetime.datetime.now(timezone(tz))
print("Time now GMT: ", time_now)
result = ib_download(client, mkt_ser, maturity, end_date=time_now )
print(result.tail(5))
print("------------------------")
today_asdate = time_now.date()
print("Today as Date GMT: ", today_asdate)
today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
print("Today as Datetime: ", today_asdatetime)
result = ib_download(client, mkt_ser, maturity, end_date=today_asdatetime )
print(result.tail(5))


'''
exchange = mkt_ser.IB_EXCHANGE
if exchange == 'KSE':
    tz = 'Asia/Tokyo'
else:
    tz = 'GMT'
time_now = datetime.datetime.now(timezone(tz))
today_asdate = time_now.date()
today_asdatetime = datetime.datetime(today_asdate.year, today_asdate.month, today_asdate.day)
'''