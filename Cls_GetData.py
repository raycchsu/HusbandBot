import traceback
import requests
import pandas as pd
import xml.etree.ElementTree as etree

class GetDataSet:
    url = ''

    def __init__(self, url):
        self.url = url

    def get_oil_price(self):
        try:
            root = etree.fromstring(requests.get(self.url).text)
            columns = ["型別名稱", "產品編號", "產品名稱", "包裝", "銷售對象", "交貨地點", "計價單位", "參考牌價", "營業稅", "貨物稅", "牌價生效時間", "備註"]
            datatframe = pd.DataFrame(columns = columns)

            for node in root:
                typeName = node.find("型別名稱").text if node is not None else None
                idNum = node.find("產品編號").text if node is not None else None
                prodName = node.find("產品名稱").text if node is not None else None
                package = node.find("包裝").text if node is not None else None
                target = node.find("銷售對象").text if node is not None else None
                local = node.find("交貨地點").text if node is not None else None
                unit = node.find("計價單位").text if node is not None else None
                ref_money = node.find("參考牌價").text if node is not None else None
                tax_1 = node.find("營業稅").text if node is not None else None
                tax_2 = node.find("貨物稅").text if node is not None else None
                time = node.find("牌價生效時間").text if node is not None else None
                note= node.find("備註").text if node is not None else None
                datatframe = datatframe.append(pd.Series([typeName, idNum, prodName, package, target, local,unit,ref_money,tax_1, tax_2, time, note], index = columns), ignore_index = True)
            return datatframe

        except (ValueError, EOFError, KeyboardInterrupt):
            errorMsg = '資料擷取錯誤，請稍晚再試!'
            return errorMsg

        except:
            print('不明原因中斷:')
            traceback.print_exc()


if __name__ ==  '__main__':
    test = GetDataSet('https://vipmember.tmtd.cpc.com.tw/opendata/ListPriceWebService.asmx/getCPCMainProdListPrice_XML')
    print(test.get_oil_price().keys)