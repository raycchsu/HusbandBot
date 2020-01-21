import datetime
import json
import time
import requests
import config
import psycopg2

SESSION_URL = 'http://mis.twse.com.tw/stock/index.jsp'
STOCKINFO_URL = 'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}&_={time}'

# Mock data
mock = False
twse = {}

def stock_map_search(type,param):
    select_SQL =""
    if type == "code":
        select_SQL = ("select name from how_data.stock_info where lower(code) = '" + param +"';")
    else:select_SQL = ("select code from how_data.stock_info where name = '" + param +"';")

    conn = None
    result = ""
    try:
        conn = psycopg2.connect(**config.db_config)
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

def _format_stock_info(data) :
    result = {
        'timestamp': 0.0,
        'info': {},
        'realtime': {}
    }

    # Timestamp
    result['timestamp'] = int(data['tlong']) / 1000

    # Information
    result['info']['code'] = data['c']
    result['info']['channel'] = data['ch']
    result['info']['name'] = data['n']
    result['info']['fullname'] = data['nf']
    result['info']['time'] = datetime.datetime.fromtimestamp(
        int(data['tlong']) / 1000).strftime('%Y-%m-%d %H:%M:%S')

    # Process best result
    def _split_best(d):
        if d:
            return d.strip('_').split('_')
        return d
    # Realtime information
    result['realtime']['latest_trade_price'] = data.get('z', None)
    result['realtime']['trade_volume'] = data.get('tv', None)
    result['realtime']['accumulate_trade_volume'] = data.get('v', None)
    result['realtime']['best_bid_price'] = _split_best(data.get('b', None))
    result['realtime']['best_bid_volume'] = _split_best(data.get('g', None))
    result['realtime']['best_ask_price'] = _split_best(data.get('a', None))
    result['realtime']['best_ask_volume'] = _split_best(data.get('f', None))
    result['realtime']['open'] = data.get('o', None)
    result['realtime']['high'] = data.get('h', None)
    result['realtime']['low'] = data.get('l', None)
    # Success fetching
    result['success'] = True
    message =str("最近成交價:"+ result['realtime']['latest_trade_price']+"\n交易量:"
                 + result['realtime']['trade_volume'] +"\n累積成交量:"
                 + result['realtime']['accumulate_trade_volume'] +"\n買價:"
                 + str(result['realtime']['best_bid_price']) + "\n買量:"
                 + str(result['realtime']['best_bid_volume']) + "\n賣價:"
                 + str(result['realtime']['best_ask_price']) + "\n賣量:"
                 + str(result['realtime']['best_ask_volume']) +"\n開盤價:"
                 + str(result['realtime']['open']) +"\n最高價:"
                 + str(result['realtime']['high']) +"\n最低價:"
                 + str(result['realtime']['low']))
    return message


#def _join_stock_id(stocks) :
#    if isinstance(stocks, list):
#        return '|'.join(['{}_{}.tw'.format(
#            'tse' if s in twse else 'otc', s) for s in stocks])
#    return '{}_{stock_id}.tw'.format(
#        'tse' if stocks in twse else 'otc', stock_id=stocks)


def get_raw(stocks):
    req = requests.Session()
    req.get(SESSION_URL)

    r = req.get(
        STOCKINFO_URL.format(
            stock_id='{}_{stock_id}.tw'.format(
                   'tse', stock_id=stocks),
            time=int(time.time()) * 1000))
    return r.json()

def get(stocks, retry=3):
    # Prepare data
    data = get_raw(stocks)
    message = ""
    # Set success
    data['success'] = False

    # JSONdecode error, could be too fast, retry
    if data['rtcode'] == '5000':
        # XXX: Stupit retry, you will dead here
        if retry:
            return get(stocks, retry - 1)
        return data

    # No msgArray, dead
    if 'msgArray' not in data:
        return data

    # Check have data
    if not len(data['msgArray']):
        data['rtmessage'] = 'Empty Query.'
        data['rtcode'] = '5001'
        return data

    # Return multiple stock data
    if isinstance(stocks, list):
        result = {
            data['info']['code']: data for data in map(_format_stock_info, data['msgArray'])
        }
        result['success'] = True

        return result

    return _format_stock_info(data['msgArray'][0])
