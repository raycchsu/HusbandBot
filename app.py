import requests
import re
import configparser
import json
import random
from bs4 import BeautifulSoup
import psycopg2
import config
import datetime
from gevent.pywsgi import WSGIServer
import realtime_stock

from flask import Flask, request, abort

# ＤataClass
from Cls_GetData import GetDataSet

# LineBot
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi('hyMMOPQMt8aJg0JFMTxAcBJXT7BByqSQsxkeKIoXx9sxOwlj1NCA6dKjWfLHGXBxmZp8YE+SJxrq/IutRQpubeZKg5+Lxaz2CNn3yc7zj5YX5ypMaXtC+IeGhg1hQt6X7ual1LtyznPn+nCFFa7h5gdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('522121ef546e53b52e77236213baf5db')

husband_bot_id = 'U358bc616907dc55b5c5b31738997c68c'

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text = True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def pattern_mega(event):
    patterns = [
        'mega', 'mg', 'mu', 'ＭＥＧＡ', 'ＭＥ', 'ＭＵ',
        'ｍｅ', 'ｍｕ', 'ｍｅｇａ', 'GD', 'MG', 'google',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

# 查詢伊莉電影
def eyny_movie():
    target_url = 'http://www.eyny.com/forum-205-1.html'
    print('Start parsing eynyMovie....')
    rs = requests.session()
    res = rs.get(target_url, verify = False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ''
    for titleURL in soup.select('.bm_c tbody .xst'):
        if pattern_mega(titleURL.text):
            title = titleURL.text
            if '11379780-1-3' in titleURL['href']:
                continue
            link = 'http://www.eyny.com/' + titleURL['href']
            data = '{}\n{}\n\n'.format(title, link)
            content += data
    return content

# 查詢蘋果新聞
def apple_news():
    target_url = 'https://tw.appledaily.com/new/realtime'
    print('Start parsing appleNews....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('.rtddt a'), 0):
        if index == 5:
            return content
        link = data['href']
        content += '{}\n\n'.format(link)
    return content

# 查詢PTT頁面數量
def get_page_number(content):
    start_index = content.find('index')
    end_index = content.find('.html')
    page_number = content[start_index + 5: end_index]
    return int(page_number) + 1

# 查詢PTT頁面內容
def craw_page(res):
    soup_ = BeautifulSoup(res.text, 'html.parser')
    article_seq = []
    push_rate = 10  # 設定最低推文數
    for r_ent in soup_.find_all(class_="r-ent"):
        try:
            # 先得到每篇文章的篇url
            link = r_ent.find('a')['href']
            if link:
                # 確定得到url再去抓 標題 以及 推文數
                title = r_ent.find(class_="title").text.strip()
                rate = r_ent.find(class_="nrec").text
                url = 'https://www.ptt.cc' + link
                #print(title,rate,url,type(rate))
                push_type = ["爆","X",""]
                if rate not in push_type:
                    rate = int(rate)
                else:
                    if rate == "爆":
                        rate = 100
                    elif  "X" in rate:
                        rate = -1
                    else:
                        rate = 0
                # 比對推文數
                if int(rate) >= push_rate and "公告" not in title:
                    article_seq.append({
                        'title': title,
                        'url': url,
                        'rate': rate,
                    })
        except Exception as e:
            # print('crawPage function error:',r_ent.find(class_="title").text.strip())
            print('本文已被刪除', e)
    return article_seq

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

# 查詢PTT熱門
def ptt_hot():
    target_url = 'http://disp.cc/b/PttHot'
    print('Start parsing pttHot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('#list div.row2 div span.listTitle'):
        title = data.text
        link = "http://disp.cc/b/" + data.find('a')['href']
        if data.find('a')['href'] == "796-59l9":
            break
        content += '{}\n{}\n\n'.format(title, link)
    return content

# 查詢電影
def movie():
    target_url = 'http://www.atmovies.com.tw/movie/next/0/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for index, data in enumerate(soup.select('ul.filmNextListAll a')):
        if index == 20:
            return content
        title = data.text.replace('\t', '').replace('\r', '')
        link = "http://www.atmovies.com.tw" + data['href']
        content += '{}\n{}\n'.format(title, link)
    return content

# 查詢科技新知
def technews():
    target_url = 'https://technews.tw/'
    print('Start parsing movie ...')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""

    for index, data in enumerate(soup.select('article div h1.entry-title a')):
        if index == 20:
            return content
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content

# 查詢科技新知
def panx():
    target_url = 'https://panx.asia/'
    print('Start parsing ptt hot....')
    rs = requests.session()
    res = rs.get(target_url, verify=False)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ""
    for data in soup.select('div.container div.row div.desc_wrap h2 a'):
        title = data.text
        link = data['href']
        content += '{}\n{}\n\n'.format(title, link)
    return content

# 查詢油價(new)
def oil_price():
    test = GetDataSet('https://vipmember.tmtd.cpc.com.tw/opendata/ListPriceWebService.asmx/getCPCMainProdListPrice_XML')
    
    #output Line string
    content = test.get_oil_price()

    #output DataFrame
    #oilDataFrame = test.get_oil_price()
    #content = str(oilDataFrame[['產品名稱', '計價單位', '參考牌價']][:3].to_string())
    return content

#確認句子中地點
def getLocation(sentence):
        taiwan_countynm =['雲林縣', '新竹市', '臺東縣', '嘉義縣', '花蓮縣', '彰化縣', '臺中市', '金門縣',
                       '桃園市', '屏東縣', '臺北市', '澎湖縣', '新竹縣', '南投縣', '基隆市', '高雄市',
                       '新北市', '宜蘭縣', '苗栗縣', '嘉義市', '連江縣', '臺南市']
        taiwnan_sitenm =['恆春', '臺南', '復興', '線西', '萬里', '古亭', '三重', '花蓮', '基隆', '松山',
                         '左營', '宜蘭', '富貴角', '桃園', '竹東', '彰化', '大園', '萬華', '前鎮', '豐原',
                         '龍潭', '仁武', '麥寮', '忠明', '汐止', '苗栗(後龍)', '大里', '嘉義', '平鎮', '小港',
                         '永和', '觀音', '竹山', '中壢', '林園', '苗栗', '臺東', '林口', '士林', '新港', '關山',
                         '中山', '西屯', '善化', '彰化(大城)', '臺南(北門)', '朴子', '新莊', '南投', '沙鹿', '二林',
                         '安南', '三義', '崙背', '新店', '冬山', '前金', '楠梓', '埔里', '大同', '土城', '菜寮', '新竹',
                         '屏東', '鳳山', '馬祖', '大寮', '臺西', '屏東(琉球)', '淡水', '新營', '馬公', '美濃', '橋頭',
                         '陽明', '潮州', '板橋', '頭份', '斗六', '金門', '湖口']

        for city in taiwan_countynm:
            if city in sentence:
                return ("County",city)

        for site in taiwnan_sitenm:
            if site in sentence:
                return ("SiteName",site)
#查詢空氣品質
def air_quality(area_type,search_area):
    rs = requests.session()
    res = rs.get('http://opendata2.epa.gov.tw/AQI.json')
    res_text = res.text
    # convert 'str' to Json
    air_data = json.loads(res_text)
    air_sit = ""
    if area_type == "County":
        for area in air_data:
            if area['County'] == search_area:
                air_sit = (area['County'] + ' ' + search_area +
                                '\n---------------\nPM2.5指數：'+ area["PM2.5_AVG"] +
                                '\n狀態：' + area['Status'] +
                                '\n調查時間：' + area['PublishTime'])

    elif area_type == "SiteName":
        for area in air_data:
                if area['SiteName'] == search_area:
                    air_sit = (area['County'] + ' ' + search_area +
                                    '\n---------------\nPM2.5指數：'+ area["PM2.5_AVG"] +
                                    '\n狀態：' + area['Status'] +
                                    '\n調查時間：' + area['PublishTime'])
    else :
        air_sit = "找不到此地區空氣品質資訊"

    return air_sit
#查詢天氣狀況
def weather_query(area):
    taiwan_list={'臺北市':'Taipei_City.htm','新北市':'New_Taipei_City.htm','桃園市':'Taoyuan_City.htm','臺中市':'Taichung_City.htm',
                 '臺南市':'Tainan_City.htm','高雄市':'Kaohsiung_City.htm','基隆縣':'Keelung_City.htm','新竹市':'Hsinchu_City.htm','新竹縣':'Hsinchu_County.htm',
                 '苗栗縣':'Miaoli_County.htm','彰化縣':'Changhua_County.htm','南投縣':'Nantou_County.htm','雲林縣':'Yunlin_County.htm',
                 '嘉義市':'Chiayi_City.htm','嘉義縣':'Chiayi_County.htm','屏東縣':'Pingtung_County.htm','宜蘭縣':'Yilan_County.htm','花蓮縣':'Hualien_County.htm',
                 '臺東縣':'Taitung_County.htm','澎湖縣':'Penghu_County.htm','金門縣':'Kinmen_County.htm','連江縣':'Lienchiang_County.htm'}
    rs = requests.session()
    res = rs.get('https://www.cwb.gov.tw/V7/forecast/taiwan/'+ taiwan_list[area])
    res.encoding=('utf8')
    soup = BeautifulSoup(res.text, 'html.parser')
    content=area+'天氣\n================\n'

    weather = soup.select('table tbody')[0].text.split('\n')
    while '' in weather:
        weather.remove('')

    for i in range(0,len(weather)+1,1):
        if i in [0,4,8]:
            content +=(weather[i])
        elif i in [1,5,9]:
            content +=('\n溫度：'+weather[i])
        elif i in [2,6,10]:
            content +=('\n舒適度：'+ weather[i])
        elif i in [3,7,11]:
            content +=('\n降雨機率：'+weather[i] + '\n')
    return content
#寫入回應規則
def insert_learn(key_words,reply):
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    insert_SQL = ("insert into how_data.learn_rule VALUES(%s,%s,%s) "+
                  "ON CONFLICT (key_words) DO UPDATE SET (reply_message, add_time)"+
                  "= ( EXCLUDED.reply_message, EXCLUDED.add_time) ")
    conn = None
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(insert_SQL,(key_words,reply,now_time))
        conn.commit()
        cursor.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return "宣皓很聰明的，我已經記住！"


#查詢DB是否有回應規則
def db_find(key_word):
    key_word = key_word.lower()
    select_SQL = ("select reply_message from how_data.learn_rule where lower(key_words) = '" + key_word+"';")
    conn = None
    all_rows = ""
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(select_SQL)
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else :
            print("資料庫找不到此回應規則")
        conn.commit()
        cursor.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

#寫入LINE使用者
def check_USER_ID(USER_ID):
    select_SQL = ("select line_code from how_data.line_list where line_code = '" + USER_ID +"';")
    conn = None
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(select_SQL)
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        return result

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_USER_ID(USER_ID):
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    insert_SQL = ("insert into how_data.line_list VALUES(%s,%s)" )
    conn = None
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        if check_USER_ID(USER_ID) is None:
            cursor.execute(insert_SQL,(USER_ID,now_time))
            conn.commit()
            cursor.close()
            return "已經存入您的USER_ID！"
        else:
            print("已紀錄此USER_ID")

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
#寫入user user_table
def inser_user_table(user_id,push_type):
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    insert_user_table = ("insert into how_data.push_main VALUES(%s,%s,%s)"+
                        "ON CONFLICT DO NOTHING")
    conn = None
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(insert_user_table,(user_id,push_type,now_time))
        conn.commit()
        cursor.close()
        print("成功寫入user_table")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            return "done"

#讀取wheather table 資料
def weather_push_query(user_id):
    query_sql = ("select * from how_data.weather where user_id ='"+ user_id +"'")
    conn = None
    content=""
    result =[]
    push_weather_detail = []
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(query_sql,(user_id))
        result = cursor.fetchall()
        conn.commit()
        cursor.close()
        for i in range (0,len(result),1):
            content = result[i][0] +":" +str(result[i][1].hour)+"點"
            push_weather_detail.append(content)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            return push_weather_detail

#寫入推播地點與時間
def weather_push_insert(location,push_time,user_id):
    insert_weather = ("insert into how_data.weather VALUES(%s,%s,%s)"+
                      "ON CONFLICT DO NOTHING")
    conn = None
    try:
        db_conn = config.db_config
        conn = psycopg2.connect(**db_conn)
        cursor = conn.cursor()
        cursor.execute(insert_weather,(location,push_time,user_id))
        conn.commit()
        cursor.close()
        print("成功寫入weather_table")
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            return "done"



# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):


    print(event)
    # get user id when reply
    user_id = event.source.user_id
    insert_USER_ID(user_id)
    print("user_id =", user_id)
    text = event.message.text
    ptt_hot = ["八卦","廢文","鄉民"]
    ptt_joke = ["joke","笑話","Joke"]
    ptt_stock = ["Stock","stock","股票討論","ptt股票","股票"]
    ptt_finance = ["finance","Finance","金融討論","金融"]
    oil = ["油價查詢","油價"]


    if db_find(text) is not None :
        reply_text = db_find(text)
    elif text[0:5] =="寶包我教你":
        text_list =text.split(" ")
        if len(text_list)==3:
            if text.split(" ")[1] !=" " and text.split(" ")[2] !=" ":
                key_words = text.split(" ")[1]
                reply = text.split(" ")[2]
                reply_text = insert_learn(key_words,reply)
            else:
                reply_text = "正確寫入規則方式為 寶包我教你 [輸入關鍵字] [回應文字]"
        else:
            reply_text = "正確寫入規則方式為 寶包我教你 [輸入關鍵字] [回應文字]"
    elif "推播" in text and "天氣" in text and "查詢" not in text:
        if getLocation(text.replace("台","臺")) != None:
            location = list(getLocation(text.replace("台","臺")))[1]
            push_type = "weather"
            puh_time = text.split(" ")[2]
            if inser_user_table(user_id,push_type) == "done":
                if weather_push_insert(location,puh_time,user_id) == "done":
                    print("成功寫入推播規則")
                else: print("寫入失敗")
        else: print("請輸入欲推播天氣之地點")
        reply_text ="成功加入推播設定"
    elif "推播" in text and "天氣" in text and "查詢" in text:
        reply_text =""
        content_data = weather_push_query(user_id)
        for i in range(0,len(content_data),1):
            reply_text += content_data[i]+"\n"
    elif text.lower() == "eyny":
        reply_text = eyny_movie()
    elif "股票查詢" in text:
        if len(text.split(" ")) > 1:
            stock_list=text.split(" ")[1]
            reply_text = str(realtime_stock.get(stock_list))
        else: reply_text="請提供股票代號"
    elif "股票名稱查詢" in text:
        if len(text.split(" ")) > 1:
            stock_code=text.split(" ")[1]
            reply_text = stock_code +"股票名稱為:"+ str(realtime_stock.stock_map_search("code",stock_code))
    elif "股票代號查詢" in text:
        if len(text.split(" ")) > 1:
            stock_name=text.split(" ")[1]
            reply_text = stock_name +"股票代號為:"+ str(realtime_stock.stock_map_search("name",stock_name))
    elif "幫我跟媽媽說" in text and user_id =="Uf1da20918c33cdbc433ae540e19bd3e2":
        message = text.split(" ")[1]
        push_message = TextSendMessage(message)
        line_bot_api.push_message("U899a0164b04ce74d0ac8e1c158736948", push_message)
        reply_text = "已推播給媽媽"
    elif text == "蘋果即時新聞":
        reply_text = apple_news()
    elif text == "表特":
        reply_text = ptt_board("beauty")
    elif text == "熱門廢文":
        reply_text = ptt_hot()
    elif text in ptt_hot:
        reply_text = ptt_board("Gossiping")
    elif text == "近期上映電影":
        reply_text = movie()
    elif text == "科技新報":
        reply_text = technews()
    elif text == "PanX泛科技":
        reply_text = panx()
    elif text in oil:
        #reply_text = oil_price()
         reply_text = 'v1.5'
    elif text in ptt_stock:
        reply_text = ptt_board("Stock")
    elif text == "電影":
        reply_text =  movie()
    elif text == "PTT電影":
        reply_text =  ptt_board("movie")
    elif text == "科技":
        reply_text = panx() + technews()
    elif text == "棒球":
         reply_text = ptt_board("Baseball")
    elif "mlb" in text.lower():
         reply_text = ptt_board("mlb")
    elif text in ptt_joke:
        reply_text = ptt_board("joke")
    elif "PTT" in text.upper():
        if len(text)>3 and "+" in text:
            reply_text = ptt_board(text.split("+")[1])
        else :
            reply_text = "輸入PTT+「版名(英文)」可取得最近推文前幾高文章"
    elif "USERID" in text.upper():
        reply_text = "您的LINE USER_ID:[" + user_id + "]"
    elif text == "ptt查詢":
        buttons_template = TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                thumbnail_image_url='https://3.bp.blogspot.com/-ySeeBKsmDWs/VrHG-rLxY0I/AAAAAAAB550/7PRntaXLEgU/s600/ptt0203.png',
                title='Menu',
                text='請選擇',
                actions=[
                    MessageTemplateAction(
                        label='棒球',
                        text='棒球'
                    ),
                    MessageTemplateAction(
                        label='廢文',
                        text='廢文'
                    ),
                    MessageTemplateAction(
                        label='科技',
                        text='科技'
                    ),
                    MessageTemplateAction(
                        label='電影',
                        text='PTT電影'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, buttons_template)
    elif getLocation(text.replace("台","臺")) != None and "空氣" in text and "推播" not in text:
        reply_text = air_quality(list(getLocation(text.replace("台","臺")))[0],list(getLocation(text.replace("台","臺")))[1])
    elif getLocation(text.replace("台","臺")) != None and "天氣" in text and "推播" not in text:
        reply_text=weather_query(list(getLocation(text.replace("台","臺")))[1])
    else:
        reply_text = text

    message = TextSendMessage(reply_text)
    line_bot_api.reply_message(event.reply_token, message)

#處理來自貼圖訊息
@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    sticker_list = list(range(52114110,52114149))
    message = StickerSendMessage(
    package_id='11539',
    sticker_id=random.choice(sticker_list)
    )
    line_bot_api.reply_message(event.reply_token, message)

# Other Message Type
@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        message = ImageSendMessage(
        original_content_url='https://i.imgur.com/WWo5bU5.jpg',
        preview_image_url='https://i.imgur.com/WWo5bU5.jpg'
        )
    elif isinstance(event.message, VideoMessage):
        message = VideoSendMessage(
        original_content_url='https://example.com/original.mp4',
        preview_image_url='https://i.imgur.com/WWo5bU5.jpg'
        )
    elif isinstance(event.message, AudioMessage):
        message = AudioSendMessage(
        original_content_url='https://example.com/original.m4a',
        duration=240000
        )
    else:
        message = "我看不懂唷～"

    line_bot_api.reply_message(event.reply_token, message)

import os

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
