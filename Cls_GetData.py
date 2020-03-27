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
            errorMsg = '資料擷取錯誤，請稍晚再試!'
            return errorMsg
            #traceback.print_exc()
    # 查詢PTT
    def ptt_board(board_name):
        rs = requests.session()
        # 先檢查網址是否包含'over18'字串 ,如有則為18禁網站
        if (rs.get('https://www.ptt.cc/bbs/'+ board_name +'/index.html', verify=False).url.find('over18') > -1):
            print("18禁網頁")
            load = {
                'from': '/bbs/' + board_name + '/index.html',
                'yes': 'yes'
            }
            res = rs.post('https://www.ptt.cc/ask/over18', verify=False, data=load)
        else:
            res = rs.get('https://www.ptt.cc/bbs/'+ board_name +'/index.html', verify=False)
        soup = BeautifulSoup(res.text, 'html.parser')
        all_page_url = soup.select('.btn.wide')[1]['href']
        start_page = get_page_number(all_page_url)
        page_term = 5# crawler count
        index_list = []
        article_list = []
        for page in range(start_page, start_page - page_term, -1):
            page_url = 'https://www.ptt.cc/bbs/'+ board_name +'/index{}.html'.format(page)
            index_list.append(page_url)

        # 抓取 文章標題 網址 推文數
        while index_list:
            index = index_list.pop(0)
            res = rs.get(index, verify=False)
            # 如網頁忙線中,則先將網頁加入 index_list 並休息1秒後再連接
            if res.status_code != 200:
                index_list.append(index)
                # print u'error_URL:',index
                # time.sleep(1)
            else:
                article_list += craw_page(res)

                # print u'OK_URL:', index
                # time.sleep(0.05)
        content = ''
        #以推文數排序
        article_list.sort(key= lambda x : x['rate'], reverse = True)
        #因line無法傳送過多資訊，只取前15筆
        for article in article_list[0:15]:
            data = '[{} push] {}\n{}\n\n'.format(article.get('rate', None), article.get('title', None),
                                                 article.get('url', None))
            content += data
        return content

if __name__ ==  '__main__':
    test = GetDataSet('https://vipmember.tmtd.cpc.com.tw/opendata/ListPriceWebService.asmx/getCPCMainProdListPrice_XML')
    print(test.get_oil_price().keys)