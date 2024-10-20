from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage, FlexSendMessage
import json
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
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'U5q89tva8HSnVXrP91MStbXkyLoNL9qWlm1i810j46Kyp/VmgYPsvbz/Mfb//Jgu6G7kJHuYd1nXH2rVAm6NF3H4ord5OxhaXnHRjYXKPKYys4vdiVBAgtD2kF0IWIzI7MYvgfMXVIvQ8FmrvOvbrAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
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

        if user_message == '!查看筆記':
            notes_flex = utility.get_user_notes(user_id)
            utility.send_flex_message_with_quick_reply(event, notes_flex)
        elif user_message == '!查看活動事件':
            events_flex = utility.get_user_events(user_id)
            utility.send_flex_message_with_quick_reply(event, events_flex)
        elif user_message == '!查看當日TODO':
            todos_flex = utility.get_user_todos(user_id)
            utility.send_flex_message_with_quick_reply(event, todos_flex)
        elif user_message == '!新增筆記':
            reply_message = '請輸入您想新增的筆記內容，格式為：\ncontent:'
            utility.send_reply_message(event, reply_message)
        elif user_message.startswith('content:'):
            note_content = user_message.split('content:', 1)[1].strip()
            utility.add_user_note(user_id, note_content)
            reply_message = '筆記已新增！'
            utility.send_reply_message(event, reply_message)

        elif user_message == '!新增活動事件':
            reply_message = '請輸入活動事件，格式為：\ntitle: ...\ndescription: ...\nstartTime: ...\nendTime: ...'
        elif user_message.startswith('title:'):
            try:
                event_details = utility.parse_event_details(user_message)
                utility.add_user_event(user_id, event_details)
                reply_message = '活動事件已新增！'
            except ValueError as ve:
                reply_message = f'格式錯誤: {ve}'
            except Exception as e:
                reply_message = f'新增活動事件失敗: {e}'
        elif user_message == '!新增TO-DO':
            # 單純提供格式，而不進行任何資料庫操作
            reply_message = '請輸入TO-DO，格式為：\ndeadline: ...\ndescription: ...'
        elif user_message.startswith('deadline:'):
            try:
                todo_details = utility.parse_todo_details(user_message)
                utility.add_user_todo(user_id, todo_details)
                reply_message = 'TO-DO 已新增！'
            except ValueError as ve:
                reply_message = f'格式錯誤: {ve}'
            except Exception as e:
                reply_message = f'新增 TO-DO 失敗: {e}'
        elif user_message == '!我的課表':
            reply_message = '請輸入您的姓名，格式為：\nname:'
            utility.send_reply_message(event, reply_message)
        elif user_message.startswith('name:'):
            note_content = user_message.split('name:', 1)[1].strip()
            utility.get_user_class(note_content)
            reply_message = '您的課表如下！'
            utility.send_reply_message(event, reply_message)
        else:
            reply_message = handle_text_message(event)

    elif isinstance(event.message, ImageMessage):
        # 如果是圖片訊息，呼叫 handle_image_message
        reply_message = handle_image_message(event)

    # 回覆用戶
    if reply_message:
        utility.send_reply_message(event, reply_message)
    else:
        quick_reply_buttons = utility.create_quick_reply_buttons()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)