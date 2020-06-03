import traceback
import requests
import pandas as pd
import json
import xml.etree.ElementTree as etree

class OilDataSet:
    url = ''
    UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"

    def __init__(self, url, UA=UA):
        self.url = url
        self.headers = {'user-agent': UA}
    
    def get_oil_price(self):
        try:
            requests.session()
            headers = self.headers
            root = etree.fromstring(requests.get(self.url, headers=headers).text)
            columns = ["型別名稱", "產品編號", "產品名稱", "包裝", "銷售對象", "交貨地點", "計價單位", "參考牌價", "營業稅", "貨物稅", "牌價生效時間", "備註"]
            datatframe = pd.DataFrame(columns = columns)
            content = ''

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
                
                #for Line output string
                content = content + '{}:{}:{} １%0D%0A'.format(prodName, unit, ref_money)
            
            return content
            #return datatframe

        except (ValueError, EOFError, KeyboardInterrupt):
            errorMsg = '數值錯誤!請稍晚再試'
            return errorMsg

        except:
            errorMsg = '資料擷取錯誤，請稍晚再試!'
            return errorMsg
            #traceback.print_exc()

    ''' API concantenation of government public data '''

    def oil_apiConnect(self):
        headers = self.headers
        res = requests.get(self.url, headers = headers)
        res.encoding='utf-8'

        return json.loads(res.text)


if __name__ ==  '__main__':
    test = GetDataSet('')
    print(test.get_oil_price().keys)