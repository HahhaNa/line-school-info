from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import firebase_admin
from firebase_admin import credentials, db
import os
import time

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
    send_welcome_message(event)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    # 檢查 reply token 是否有效
    if event.reply_token == '00000000000000000000000000000000':
        # 略過健康檢查的回覆
        return

    reply_message = None

    # 處理不同的指令
    if user_message == '!查看筆記':
        notes = get_user_notes(user_id)
        reply_message = f'這是您的筆記內容：\n{notes}'
    elif user_message == '!新增筆記':
        reply_message = '請輸入您想新增的筆記內容，格式為：\content:'
    elif user_message.startswith('content:'):
        note_content = user_message.split('content:', 1)[1].strip()
        add_user_note(user_id, note_content)
        reply_message = '筆記已新增！'
    elif user_message == '!新增活動事件':
        reply_message = '請輸入活動事件，格式為：\ntitle: ...\ndescription: ...\nstartTime: ...\nendTime: ...'
    elif user_message.startswith('title:'):
        try:
            event_details = parse_event_details(user_message)
            add_user_event(user_id, event_details)
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
            todo_details = parse_todo_details(user_message)
            add_user_todo(user_id, todo_details)
            reply_message = 'TO-DO 已新增！'
        except ValueError as ve:
            reply_message = f'格式錯誤: {ve}'
        except Exception as e:
            reply_message = f'新增 TO-DO 失敗: {e}'
    else:
        reply_message = '抱歉，我不太明白您的指令。請選擇以下其中一個操作：'

    # 回覆用戶
    if reply_message:
        send_reply_message(event, reply_message)

# 輔助函數，用於解析活動事件的細節
def parse_event_details(user_message):
    lines = user_message.split('\n')
    event_data = {}
    required_fields = ['title', 'description', 'startTime', 'endTime']

    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in required_fields:
                event_data[key] = value

    # 檢查是否所有的必需字段都存在
    if not all(field in event_data for field in required_fields):
        raise ValueError('請確保包含 title, description, startTime 和 endTime 所有字段')

    return event_data

# 輔助函數，用於解析 TO-DO 的細節
def parse_todo_details(user_message):
    if not isinstance(user_message, str):
        raise ValueError("輸入的資料不是字符串，請檢查傳入的資料類型。")
    
    lines = user_message.split('\n')
    todo_data = {}
    required_fields = ['deadline', 'description']

    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key in required_fields:
                todo_data[key] = value

    # 檢查是否所有的必需字段都存在
    if not all(field in todo_data for field in required_fields):
        raise ValueError('請確保包含 deadline 和 description 所有字段')

    return todo_data

def send_welcome_message(event):
    quick_reply_buttons = create_quick_reply_buttons()
    welcome_message = TextSendMessage(
        text='歡迎！選擇一個動作：',
        quick_reply=quick_reply_buttons
    )
    line_bot_api.reply_message(event.reply_token, welcome_message)

def send_reply_message(event, text):
    quick_reply_buttons = create_quick_reply_buttons()
    reply_message = TextSendMessage(
        text=text,
        quick_reply=quick_reply_buttons
    )
    line_bot_api.reply_message(event.reply_token, reply_message)

def create_quick_reply_buttons():
    return QuickReply(
        items=[
            QuickReplyButton(
                action=MessageAction(label='查看筆記', text='!查看筆記'),
            ),
            QuickReplyButton(
                action=MessageAction(label='查看活動事件', text='!查看活動事件'),
            ),
            QuickReplyButton(
                action=MessageAction(label='查看當日TODO', text='!查看當日TODO'),
            ),
            QuickReplyButton(
                action=MessageAction(label='新增筆記', text='!新增筆記'),
            ),
            QuickReplyButton(
                action=MessageAction(label='新增活動事件', text='!新增活動事件'),
            ),
            QuickReplyButton(
                action=MessageAction(label='新增TO-DO', text='!新增TO-DO'),
            )
        ]
    )

def add_user_note(user_id, content):
    # 獲取 notes 節點引用（所有 Notes 內容的存放位置）
    notes_ref = db.reference('notes')

    # 檢查是否已經存在相同內容的筆記
    existing_notes = notes_ref.get()
    if existing_notes:
        for note_id, value in existing_notes.items():
            if value.get('content') == content:
                # 如果已經存在相同的筆記，則直接使用其 ID，避免重複寫入
                print(f"重複的 Note: content: {content}")
                
                # 將這個筆記 ID 加入到用戶的筆記引用下
                user_notes_ref = db.reference(f'users/{user_id}/notes')
                user_notes_ref.update({note_id: True})
                return

    # 新增 Note 到 notes 節點，並生成唯一 ID
    new_note_ref = notes_ref.push()

    # 寫入 note_content，並添加 timestamp
    new_note_data = {
        'content': content,
        'timestamp': int(time.time())  # 添加時間戳來標記 Note 的創建時間
    }
    new_note_ref.set(new_note_data)

    # 獲取新的 note ID
    new_note_id = new_note_ref.key

    # 在用戶的 notes 引用下新增這個 note ID
    user_notes_ref = db.reference(f'users/{user_id}/notes')
    user_notes_ref.update({new_note_id: True})


def add_user_event(user_id, event_data):
    # 獲取 events 節點引用（所有 Events 內容的存放位置）
    events_ref = db.reference('events')

    # 檢查是否已經存在相同的 event
    existing_events = events_ref.get()
    if existing_events:
        for event_id, value in existing_events.items():
            if (value.get('title') == event_data.get('title') and
                value.get('description') == event_data.get('description') and
                value.get('startTime') == event_data.get('startTime') and
                value.get('endTime') == event_data.get('endTime')):
                # 如果已經存在相同的 event，則直接使用其 ID，避免重複寫入
                print(f"重複的 Event: title: {event_data.get('title')}, description: {event_data.get('description')}")
                
                # 將這個 event ID 加入到用戶的 events 引用下
                user_events_ref = db.reference(f'users/{user_id}/events')
                user_events_ref.update({event_id: True})
                return

    # 新增 Event 到 events 節點，並生成唯一 ID
    new_event_ref = events_ref.push()

    # 寫入 event_data，並添加 timestamp
    new_event_data = {
        'title': event_data.get('title'),
        'description': event_data.get('description'),
        'startTime': event_data.get('startTime'),
        'endTime': event_data.get('endTime'),
        'timestamp': int(time.time())  # 添加時間戳來標記 Event 的創建時間
    }
    new_event_ref.set(new_event_data)

    # 獲取新的 event ID
    new_event_id = new_event_ref.key

    # 在用戶的 events 引用下新增這個 event ID
    user_events_ref = db.reference(f'users/{user_id}/events')
    user_events_ref.update({new_event_id: True})


def add_user_todo(user_id, todo_data):
    # 獲取 todos 節點引用（所有 TO-DO 內容的存放位置）
    todos_ref = db.reference('todos')

    # 檢查是否已經存在相同的 TO-DO
    existing_todos = todos_ref.get()
    if existing_todos:
        for todo_id, value in existing_todos.items():
            if value.get('deadline') == todo_data.get('deadline') and value.get('description') == todo_data.get('description'):
                # 如果已經存在相同的 TO-DO，則直接使用其 ID，避免重複寫入
                print(f"重複的 TO-DO: deadline: {todo_data.get('deadline')}, description: {todo_data.get('description')}")
                
                # 將這個 TO-DO ID 加入到用戶的 TO-DOs 引用下
                user_todos_ref = db.reference(f'users/{user_id}/todos')
                user_todos_ref.update({todo_id: True})
                return

    # 新增 TO-DO 到 todos 節點，並生成唯一 ID
    new_todo_ref = todos_ref.push()

    # 寫入 todo_data，並添加 timestamp
    new_todo_data = {
        'deadline': todo_data.get('deadline'),
        'description': todo_data.get('description'),
        'timestamp': int(time.time())  # 添加時間戳來標記 TO-DO 的創建時間
    }
    new_todo_ref.set(new_todo_data)

    # 獲取新的 TO-DO ID
    new_todo_id = new_todo_ref.key

    # 在用戶的 TO-DOs 引用下新增這個 TO-DO ID
    user_todos_ref = db.reference(f'users/{user_id}/todos')
    user_todos_ref.update({new_todo_id: True})


def get_user_notes(user_id):
    ref = db.reference(f'users/{user_id}/notes')
    notes = ref.get()
    if notes:
        return "\n".join([f"- {note['content']}" for note in notes.values()])
    else:
        return "目前沒有任何筆記。"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
