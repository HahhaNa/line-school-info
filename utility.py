from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, ImageMessage

import firebase_admin
from firebase_admin import credentials, db
import os
import time

LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'U5q89tva8HSnVXrP91MStbXkyLoNL9qWlm1i810j46Kyp/VmgYPsvbz/Mfb//Jgu6G7kJHuYd1nXH2rVAm6NF3H4ord5OxhaXnHRjYXKPKYys4vdiVBAgtD2kF0IWIzI7MYvgfMXVIvQ8FmrvOvbrAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
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

    # 檢查是否所有的必需欄位都存在
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

    # 檢查是否所有的必需欄位都存在
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
    # 獲取 notes 節點參考（所有 Notes 內容的存放位置）
    notes_ref = db.reference('notes')

    # 檢查是否已經存在相同內容的筆記，避免重複新增
    existing_notes = notes_ref.get()
    if existing_notes:
        for note_id, value in existing_notes.items():
            if value.get('content') == content:
                # 如果已經存在相同的筆記，則直接使用其 ID，避免重複寫入
                print(f"重複的 Note: content: {content}")
                
                # 將這個筆記 ID 加入到用戶的筆記參考下
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

    # 在用戶的 notes 參考下新增這個 note ID
    user_notes_ref = db.reference(f'users/{user_id}/notes')
    user_notes_ref.update({new_note_id: True})


def add_user_event(user_id, event_data):
    # 獲取 events 節點參考（所有 Events 內容的存放位置）
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
                
                # 將這個 event ID 加入到用戶的 events 參考下
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

    # 在用戶的 events 參考下新增這個 event ID
    user_events_ref = db.reference(f'users/{user_id}/events')
    user_events_ref.update({new_event_id: True})


def add_user_todo(user_id, todo_data):
    # 獲取 todos 節點參考（所有 TO-DO 內容的存放位置）
    todos_ref = db.reference('todos')

    # 檢查是否已經存在相同的 TO-DO
    existing_todos = todos_ref.get()
    if existing_todos:
        for todo_id, value in existing_todos.items():
            if value.get('deadline') == todo_data.get('deadline') and value.get('description') == todo_data.get('description'):
                # 如果已經存在相同的 TO-DO，則直接使用其 ID，避免重複寫入
                print(f"重複的 TO-DO: deadline: {todo_data.get('deadline')}, description: {todo_data.get('description')}")
                
                # 將這個 TO-DO ID 加入到用戶的 TO-DOs 參考下
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

    # 在用戶的 TO-DOs 參考下新增這個 TO-DO ID
    user_todos_ref = db.reference(f'users/{user_id}/todos')
    user_todos_ref.update({new_todo_id: True})


# 更新後的筆記、活動事件和 TO-DO 的檢索函數
def get_user_notes(user_id):
    user_notes_ref = db.reference(f'users/{user_id}/notes')
    user_notes = user_notes_ref.get()
    if user_notes:
        notes_ref = db.reference('notes')
        note_contents = []
        for note_id in user_notes.keys():  # 修正這裡，使用 keys() 以獲取所有 note 的 ID
            note = notes_ref.child(note_id).get()
            if note:
                note_contents.append(f"- {note['content']}")
        return "\n".join(note_contents)
    else:
        return "目前沒有任何筆記。"

def get_user_events(user_id):
    user_events_ref = db.reference(f'users/{user_id}/events')
    user_events = user_events_ref.get()
    if user_events:
        events_ref = db.reference('events')
        event_contents = []
        for event_id in user_events.keys():  # 修正這裡，使用 keys() 以獲取所有 event 的 ID
            event = events_ref.child(event_id).get()
            if event:
                event_contents.append(f"- {event['title']} ({event['startTime']} - {event['endTime']}): {event['description']}")
        return "\n".join(event_contents)
    else:
        return "目前沒有任何活動事件。"

def get_user_todos(user_id):
    user_todos_ref = db.reference(f'users/{user_id}/todos')
    user_todos = user_todos_ref.get()
    if user_todos:
        todos_ref = db.reference('todos')
        todo_contents = []
        for todo_id in user_todos.keys():  # 修正這裡，使用 keys() 以獲取所有 TO-DO 的 ID
            todo = todos_ref.child(todo_id).get()
            if todo:
                todo_contents.append(f"- {todo['deadline']}: {todo['description']}")
        return "\n".join(todo_contents)
    else:
        return "目前沒有任何 TO-DO。"