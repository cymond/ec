
from private.SystemR.mysqldata import mysqlFuturesData
data=mysqlFuturesData()
df = data.get_raw_price("EDOLLAR")
print(df)

'''

from sysdata.csvdata import csvFuturesData
data = csvFuturesData()
data.get_raw_price("EDOLLAR")
'''