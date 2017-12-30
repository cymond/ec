from swigibpy import EWrapper
import time
import pandas as pd
from pytz import timezone
import datetime
from swigibpy import EPosixClientSocket

from IButils import autodf

MEANINGLESS_NUMBER=999



### how many seconds before we give up
MAX_WAIT=30

def return_IB_connection_info():
    """
    Returns the tuple host, port, clientID required by eConnect
   
    """
   
    host="0.0.0.0"
   
    port=7496
    clientid=1
   
    return (host, port, clientid)

class IBWrapper(EWrapper):
    """

        Callback object passed to TWS, these functions will be called directly
    by TWS.

    """

    def init_error(self):
        setattr(self, "flag_iserror", False)
        setattr(self, "error_msg", "")
        setattr(self, "error_code", 0)


    def error(self, id, errorCode, errorString):
        """
        error handling, simple for now
       
        Here are some typical IB errors
        INFO: 2107, 2106
        WARNING 326 - can't connect as already connected
        CRITICAL: 502, 504 can't connect to TWS.
            200 no security definition found
            162 no trades

        """

        ## Any errors not on this list we just treat as information
       #PK
        ERRORS_TO_TRIGGER=[201, 103, 502, 504, 509, 200, 162, 420, 2105, 1100, 478, 201, 399]
        # ERRORS_TO_TRIGGER = [201, 103, 502, 504, 509, 200,  420, 2105, 1100, 478, 201, 399]

        if errorCode in ERRORS_TO_TRIGGER:
            errormsg="IB error id %d errorcode %d string %s" %(id, errorCode, errorString)
            print(errormsg)
            setattr(self, "flag_iserror", True)
            setattr(self, "error_msg", True)
            setattr(self, "error_code", errorCode)
           
        ## Wrapper functions don't have to return anything
       

    ## The following are not used
       
    def nextValidId(self, orderId):
        pass
   
    def managedAccounts(self, openOrderEnd):
        pass

    def init_historicprices(self, tickerid):

        if "data_historicdata" not in dir(self):
            histdict=dict()
        else:
            histdict=self.data_historicdata

        EMPTY_HDATA = autodf("date", "open", "high", "low", "close", "volume")
        histdict[tickerid]=EMPTY_HDATA
        setattr(self, "data_historicdata", histdict)
        setattr(self, "flag_historicdata_finished", False)


    def historicalData(self, reqId, date, openprice, high,
                       low, close, volume,
                       barCount, WAP, hasGaps):
        

        if date[:8] == 'finished':
            setattr(self, "flag_historicdata_finished", True)

        else:
            historicdata=self.data_historicdata[reqId]
            #date=datetime.datetime.strptime(date,"%Y%m%d")
            # Comment line below to avoid errors whilst getting hourly data
            #date = datetime.datetime.strptime(date, "%Y%m%d")
            historicdata.add_row(date=date, open=openprice, high=high, low=low, close=close, volume=volume)


class IBclient(object):
    def __init__(self, callback):
        if not hasattr(self, 'tws'):
            tws = EPosixClientSocket(callback)
            (host, port, clientid)=return_IB_connection_info()
            tws.eConnect(host, port, clientid)

            self.tws=tws
            self.cb=callback

    
    def get_IB_historical_data(self, ibcontract, end_date, durationStr="1 W", barSizeSetting="1 hour", tickerid=MEANINGLESS_NUMBER, whatToShow="TRADES"):
        
        """
        Returns historical prices for a contract, up to today
        
        tws is a result of calling IBConnector()
        
        """

        today=datetime.datetime.now()

        #PK... use yesterday's date for closing prices. Otherwise IB returnes today's prices messing up the price series.
        # Neet to watch holidays too! I think IB returns OHLC even though there were no trades!
        exchange = ibcontract.exchange
        if exchange == 'KSE':
            today = datetime.datetime.now(timezone('Asia/Tokyo'))
            yesterday = datetime.datetime.now(timezone('Asia/Tokyo')) - datetime.timedelta(1)
            last_yesterday = yesterday.replace(hour=23, minute=59, second=59)
            #print("End date and time: ", last_yesterday.strftime("%Y%m%d %H:%M:%S %Z"))
        else:
            today = datetime.datetime.now(timezone('GMT'))
            yesterday = datetime.datetime.now(timezone('GMT')) - datetime.timedelta(1)
            last_yesterday = yesterday.replace(hour=23, minute=59, second=59)
            #print("End date and time: ", last_yesterday.strftime("%Y%m%d %H:%M:%S %Z"))

        self.cb.init_error()
        self.cb.init_historicprices(tickerid)
            


        self.tws.reqHistoricalData(
                tickerid,                                          # tickerId,
                ibcontract,                                   # contract,
                #last_yesterday.strftime("%Y%m%d %H:%M:%S %Z"),       # endDateTime,
                # "20160201 23:00:00 GMT",
                end_date.strftime("%Y%m%d %H:%M:%S %Z"),
                durationStr,                                      # durationStr,
                barSizeSetting,                                    # barSizeSetting,
                whatToShow,                                   # whatToShow,
                1,                                          # useRTH,
                1                                           # formatDate

            )

        start_time=time.time()
        finished=False
        iserror=False
        
        while not finished and not iserror:
            finished=self.cb.flag_historicdata_finished
            iserror=self.cb.flag_iserror
            
            if (time.time() - start_time) > MAX_WAIT:
                iserror=True
            pass
            
        if iserror:
            #print(self.cb.error_msg)
            # Handle the error so that code can continue
            #raise Exception("Problem getting Historic data")
            if (self.cb.error_code == 162) or (self.cb.error_code) == 200 or (self.cb.error_code) == 0:
                # Returns with no results dataFrame, use this to continue to next
                return
            else:
                print(self.cb.error_code)
                raise Exception("Problem getting historic data")
        
        historicdata=self.cb.data_historicdata[tickerid]

        results=historicdata.to_pandas("date")


        print("------------------------------DISCONNECTED!---------------------------------")

        return results
