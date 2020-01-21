import psycopg2
import datetime
import time
import config
from collections import namedtuple
import os
import requests
from lxml import etree
ROW = namedtuple('Row', ['type', 'code', 'name', 'isin_name', 'start',
                         'market', 'group_name', 'cfi_type','update_time'])

def make_row_tuple(typ, row):
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    code, name = row[1].split('\u3000')
    return ROW(typ, code, name, *row[2: -1],now_time)


def fetch_data(url):
    rs = requests.session()
    res = rs.get(url)
    root = etree.HTML(res.text)
    trs = root.xpath('//tr')[1:]
    result = []
    typ = ''
    for tr in trs:
        tr = list(map(lambda x: x.text, tr.iter()))
        if len(tr) == 4:
            # This is type
            typ = tr[2].strip(' ')
        else:
            # This is the row data
            result.append(make_row_tuple(typ, tr))
    return result

def fetch_all_stock_info(user_id,url):
  conn=None
  list_link=[]
  now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  if user_id == "Uf1da20918c33cdbc433ae540e19bd3e2":
    list_link = fetch_data(url)
    conn = psycopg2.connect(**config.db_config)
    cursor = conn.cursor()
    for i in range(0,len(list_link),1):
        cursor.execute("INSERT into how_data.stock_info(type, code, name, isin_code, start, market, group_name, cfi_type, update_time) "+
                      "VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s) ON CONFLICT DO NOTHING",
                       (list_link[i][0],list_link[i][1],list_link[i][2],list_link[i][3],list_link[i][4],list_link[i][5],list_link[i][6],list_link[i][7],list_link[i][8]))

        conn.commit()
    cursor.close()
    conn.close()
    return "已完成更新"
