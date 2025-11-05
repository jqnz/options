from options.ib_app import IBApp
from options.util import make_option_contract
import time

def main():
    ib_app = IBApp()
    ib_app.start()
    ib_app.reqMarketDataType(1)

    reqId = 9001
    contract = make_option_contract("JPM", "20251107", 290, "P")
    ib_app.reqMktData(reqId, contract, "", True, False, [])


    time.sleep(3)
    print(ib_app.option_quotes[reqId])


if __name__ == "__main__":
    main()
