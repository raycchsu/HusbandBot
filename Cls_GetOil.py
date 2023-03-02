import traceback
import requests
from bs4 import BeautifulSoup
import json

__version__ = '1.0'

class OilDataSet:
    url = 'https://www.cpc.com.tw/'
    oilprice_url = 'https://www.cpc.com.tw/GetOilPriceJson.aspx'
    params = {'type': 'TodayOilPriceString'}
    headers = {
        'content-type': 'text/html; charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36'
    }

    def __init__(self, url, oilprice_url, params, headers=headers):
        self.url = url
        self.oilprice_url = oilprice_url
        self.headers = headers
        self.params = params
    
    def get_oil_price(self):
        try:
            results = {}
            response = requests.get(self.url, headers=self.headers)
            response_oilprice = requests.get(self.seloilprice_url, headers=self.headers, params=self.params)
            soup = BeautifulSoup(response.content, 'html.parser')
            if response.status_code == 200 and response_oilprice.status_code == 200:
               
                data = json.loads(response_oilprice.text)
                for row in soup.find_all("b", {"class": "name"})[:6]:
                    results[row.text] = ''
                
                results['實施日'] = data['PriceUpdate']
                results['92無鉛'] = data['sPrice1']
                results['95無鉛'] = data['sPrice2']
                results['98無鉛'] = data['sPrice3']
                results['酒精汽油'] = data['sPrice4']
                results['超級柴油'] = data['sPrice5']
                results['液化石油氣'] = data['sPrice6']   
            else:
                print('Error: failed to retrieve oil data.')

            return results
            #return datatframe

        except (ValueError, EOFError, KeyboardInterrupt):
            errorMsg = '數值錯誤!請稍晚再試'
            return errorMsg

        except:
            errorMsg = '資料擷取錯誤，請稍晚再試!'
            return errorMsg
            #traceback.print_exc()



if __name__ ==  '__main__':
    OilDataSet.get_oil_price