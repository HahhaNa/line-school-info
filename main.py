from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import FollowEvent, MessageEvent, TextMessage, ImageMessage

import firebase_admin
from firebase_admin import credentials
import os

# image.py import
from image import handle_image_message
import utility

# Initialize FastAPI application
app = FastAPI()

# Initialize LineBotApi and WebhookHandler
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("line-school-info-firebase-adminsdk-74vka-d87b39d170.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://line-school-info-default-rtdb.firebaseio.com/'
})

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        return HTTPException(status_code=400, detail="Missing 'X-Line-Signature' header")

    body = await request.body()
    body = body.decode('utf-8')

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return HTTPException(status_code=400, detail="Invalid signature. Check your channel secret.")
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Error while handling the request: {e}")

    return PlainTextResponse('OK')

@handler.add(FollowEvent)
def handle_follow(event):
    utility.send_welcome_message(event)

@handler.add(MessageEvent, message=(TextMessage, ImageMessage))
def handle_message(event):
    user_id = event.source.user_id

    # Check if reply token is valid
    if event.reply_token == '00000000000000000000000000000000':
        # Skip health check reply
        return

    reply_message = None

    # Handle different commands
    if isinstance(event.message, TextMessage):
        user_message = event.message.text

        if user_message == '!查看筆記':
            notes = utility.get_user_notes(user_id)
            reply_message = f'這是您的筆記內容：\n{notes}'
        elif user_message == '!查看活動事件':
            events = utility.get_user_events(user_id)
            reply_message = f'這是您最近的活動：\n{events}'
        elif user_message == '!查看當日TODO':
            todos = utility.get_user_todos(user_id)
            reply_message = f'這是您今日的TODO：\n{todos}'
        elif user_message == '!新增筆記':
            reply_message = '請輸入您想新增的筆記內容，格式為：\ncontent:'
        elif user_message.startswith('content:'):
            note_content = user_message.split('content:', 1)[1].strip()
            utility.add_user_note(user_id, note_content)
            reply_message = '筆記已新增！'
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
        else:
            reply_message = '抱歉，我不太明白您的指令。請選擇以下其中一個操作：'

        if reply_message:
            utility.send_reply_message(event, reply_message)

    elif isinstance(event.message, ImageMessage):
        handle_image_message(event)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", default=8080))
    debug = True if os.environ.get("API_ENV", default="develop") == "develop" else False
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)