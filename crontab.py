from apscheduler.schedulers.blocking import BlockingScheduler
import push_message
import code
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes = 60)
def scheduled_push_job():
    print('This job is run every hour.')
    push_type = "weather"
    push = push_message.push_message(push_type)
    push.active_push_message()

@sched.scheduled_job('cron',hour=17, minute=30)
def schedual_push_mom():
    message = "媽咪早點下班唷～😘"
    push_message = TextSendMessage(message)
    line_bot_api.push_message("U899a0164b04ce74d0ac8e1c158736948", push_message)


@sched.scheduled_job('interval', days=1)
def stock_update_job():
    print('This job is run every day at 1 am.')
    code.fetch_all_stock_info('Uf1da20918c33cdbc433ae540e19bd3e2','http://isin.twse.com.tw/isin/C_public.jsp?strMode=2')


sched.start()
