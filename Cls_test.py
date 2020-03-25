from Cls_GetData import GetDataSet

test = GetDataSet('https://vipmember.tmtd.cpc.com.tw/opendata/ListPriceWebService.asmx/getCPCMainProdListPrice_XML')
oilData = test.get_oil_price()

