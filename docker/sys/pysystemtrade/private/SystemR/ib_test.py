#from dbutils.capital import get_trade_capital
from dbutils.ibwrapper import get_net_liquidation
import pandas as pd

def main():
    print("Here we are !!!!!!!!!!")
    try:
        net_liquidation = get_net_liquidation()
    except Exception as e:
        print("IB read failed", e)

    print("Net Liquidation: ", net_liquidation)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
