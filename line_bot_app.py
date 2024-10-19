from flask import Flask, request, abort
from linebot import LineBotApi
from linebot.v3.webhook import WebhookHandler  # 使用最新版本的 WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction

import os

app = Flask(__name__)

# 初始化 LineBotApi 和 WebhookHandler
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'U5q89tva8HSnVXrP91MStbXkyLoNL9qWlm1i810j46Kyp/VmgYPsvbz/Mfb//Jgu6G7kJHuYd1nXH2rVAm6NF3H4ord5OxhaXnHRjYXKPKYys4vdiVBAgtD2kF0IWIzI7MYvgfMXVIvQ8FmrvOvbrAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # 獲取請求頭部的簽名
    signature = request.headers.get('X-Line-Signature')

    if not signature:
        app.logger.error("Missing 'X-Line-Signature' header")
        abort(400)

    # 獲取請求正文
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 驗證簽名
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Check your channel secret.")
        abort(400)
    except Exception as e:
        app.logger.error(f"Error while handling the request: {e}")
        abort(500)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    app.logger.info(f"Handling message: {event.message.text}")
    if event.message.text == '!快速按鈕':
        quick_reply_buttons = QuickReply(
            items=[
                QuickReplyButton(
                    action=MessageAction(label='查看筆記', text='!查看筆記'),
                ),
                QuickReplyButton(
                    action=MessageAction(label='查看本週事件', text='!查看本週事件'),
                ),
                QuickReplyButton(
                    action=MessageAction(label='查看當日TODO', text='!查看當日TODO'),
                )
            ]
        )

        reply_message = TextSendMessage(
            text='選擇一個動作：',
            quick_reply=quick_reply_buttons
        )

        try:
            line_bot_api.reply_message(
                event.reply_token,
                reply_message
            )
            app.logger.info("Reply message sent successfully.")
        except Exception as e:
            app.logger.error(f"Failed to send reply message: {e}")
    else:
        # 其他訊息回覆原本的訊息
        try:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=event.message.text)
            )
        except Exception as e:
            app.logger.error(f"Failed to send reply message: {e}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
