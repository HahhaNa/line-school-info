from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, PostbackEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage

import firebase_admin
from firebase_admin import credentials, db
import os
import time

# image.py import
from message import handle_image_message, handle_text_message
import utility


# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 LineBotApi 和 WebhookHandler
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'U5q89tva8HSnVXrP91MStbXkyLoNL9qWlm1i810j46Kyp/VmgYPsvbz/Mfb//Jgu6G7kJHuYd1nXH2rVAm6NF3H4ord5OxhaXnHRjYXKPKYys4vdiVBAgtD2kF0IWIzI7MYvgfMXVIvQ8FmrvOvbrAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')

# line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 初始化 Firebase Admin SDK
cred = credentials.Certificate("line-school-info-firebase-adminsdk-74vka-d87b39d170.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://line-school-info-default-rtdb.firebaseio.com/'
})


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')

    if not signature:
        app.logger.error("Missing 'X-Line-Signature' header")
        abort(400)

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Check your channel secret.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error while handling the request: {e}")
        abort(500)

    return 'OK'

@handler.add(FollowEvent)
def handle_follow(event):
    utility.send_welcome_message(event)

@handler.add(MessageEvent, message=(TextMessage, ImageMessage))
def handle_message(event):
    user_id = event.source.user_id

    reply_message = None

    # 檢查訊息類型
    if isinstance(event.message, TextMessage):
        user_message = event.message.text

        # 處理不同的指令
        if user_message == '!查看筆記':
            notes = utility.get_user_notes(user_id)
            reply_message = f'這是您的筆記內容：\n{notes}'
        elif user_message == '!查看活動事件':
            events = utility.get_user_events(user_id)
            reply_message = f'這是您最近的活動：\n{events}'
        elif user_message == '!查看當日TODO':
            todos = utility.get_user_todos(user_id)
            reply_message = f'這是您今日的TODO：\n{todos}'
        else:
            reply_message = handle_text_message(event)

    elif isinstance(event.message, ImageMessage):
        # 如果是圖片訊息，呼叫 handle_image_message
        reply_message = handle_image_message(event)

    # 回覆用戶
    if reply_message:
        utility.send_reply_message(event, reply_message)

@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id

    # 假設您的 Rich Menu 按鈕的 postback_data 是 'open_link'
    if event.data == 'open_link':
        # 創建帶有 user_id 的 URL
        link_url = f"https://curriculum-4e9d2.web.app?user_id={user_id}"

        # 發送回覆給用戶
        reply_message = f"您可以通過以下連結訪問課表：\n{link_url}"
        utility.send_reply_message(event, reply_message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)