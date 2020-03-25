import requests
import re
import configparser
import json
import random
from bs4 import BeautifulSoup
from flask import Flask, request, abort
import psycopg2
import config
import datetime
import time
import app

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
# Channel Access Token
line_bot_api = LineBotApi('hyMMOPQMt8aJg0JFMTxAcBJXT7BByqSQsxkeKIoXx9sxOwlj1NCA6dKjWfLHGXBxmZp8YE+SJxrq/IutRQpubeZKg5+Lxaz2CNn3yc7zj5YX5ypMaXtC+IeGhg1hQt6X7ual1LtyznPn+nCFFa7h5gdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('522121ef546e53b52e77236213baf5db')


class push_message():
    def __init__ (self,push_type):
        self.push_type = push_type
        self.db_config = config.db_config

    #讀取推播用戶
    def get_push_list(self):
        select_push_list = ("select user_id from how_data.push_main where push_type = %(type_name)s;")
        conn = None
        result = []
        id_list= []
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute(select_push_list,{'type_name' : self.push_type})
            result = cursor.fetchall()
            if result is not None:
                for row in result:
                    id_list += row
                return  id_list
            else: print("沒有推播用戶")
            conn.commit()
            cursor.close()

        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()

    #讀取推播詳細設定
    def get_push_detail(self,id_list):
        now_hour = str(time.localtime()[3])
        select_push_detail = ("select user_id,location from how_data.weather where user_id = ANY(%s)"+
                             " and extract(hour from push_time) = " + now_hour +";")
        conn = None
        push_list =[]
        try:
                conn = psycopg2.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute(select_push_detail,(id_list,))
                push_list = cursor.fetchall()
                if push_list is not None:
                    return  push_list
                else: print("沒有推播清單")

                conn.commit()
                cursor.close()

        except (Exception, psycopg2.DatabaseError) as error:
                print(error)
        finally:
                if conn is not None:
                    conn.close()


    #設定推播訊息內容
    def push_line_message(self,push_id,message):
        try:
            push_message = TextSendMessage(message)
            line_bot_api.push_message(push_id, push_message)
        except LineBotApiError as e:
            # error handle
            raise e
    #推播主要功能
    def active_push_message(self):
        push = push_message(self.push_type)
        id_list = push.get_push_list()
        push_list = push.get_push_detail(id_list)

        if push_list is not None:
            for i in range(len(push_list)):
                push_content = app.weather_query(push_list[i][1])
                push.push_line_message(push_list[i][0],push_content)
        else: print("沒有推播項目")
