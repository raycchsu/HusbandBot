from Cls_GetData import GetDataSet

test = GetDataSet('https://vipmember.tmtd.cpc.com.tw/opendata/ListPriceWebService.asmx/getCPCMainProdListPrice_XML')

#output string
content = test.get_oil_price()

#output DataFrame
#oilDataFrame = test.get_oil_price()
#content = str(oilDataFrame[['產品名稱', '計價單位', '參考牌價']][:3].to_string())
print(content)
