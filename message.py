from PIL import Image
from io import BytesIO
import pytesseract
import re
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageMessage, MessageEvent, TextMessage
import os 
from classify import classify
import utility

# 設定 pytesseract 的安裝路徑
# pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# 初始化 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler_console = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler_console.setFormatter(formatter)
logger.addHandler(handler_console)


# 初始化 LineBotApi 和 WebhookHandler
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'U5q89tva8HSnVXrP91MStbXkyLoNL9qWlm1i810j46Kyp/VmgYPsvbz/Mfb//Jgu6G7kJHuYd1nXH2rVAm6NF3H4ord5OxhaXnHRjYXKPKYys4vdiVBAgtD2kF0IWIzI7MYvgfMXVIvQ8FmrvOvbrAdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', '9b39153b154382ce669ca95fb4a11305')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """
    處理文字訊息，將文字分類並回覆給用戶
    :param event: LINE bot 傳來的事件
    """
    try:
        response_type, formatted_output = classify(event.message.text)
        if response_type == "unknown":
            reply_message = "抱歉，我不太明白您的指令。請選擇以下其中一個操作："
        elif response_type == "note":
            reply_message = "筆記已新增！"
            utility.add_user_note(event.source.user_id, formatted_output)
        elif response_type == "todo":
            reply_message = "TO-DO 已新增！"
            utility.add_user_todo(event.source.user_id, formatted_output)
        elif response_type == "event":
            reply_message = "活動事件已新增！"
            utility.add_user_event(event.source.user_id, formatted_output)
        else:
            reply_message = "Sorry, I couldn't classify the content."

    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}")
        reply_message = "An error occurred while processing the text."
    return reply_message

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """
    處理圖片訊息，提取圖片中的文字並回覆給用戶
    :param event: LINE bot 傳來的事件
    """
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)
    image = Image.open(BytesIO(message_content.content))
    extracted_text = extract_text_from_image(image)

    return handle_text_message(TextMessage(id=message_id, text=extracted_text))

def extract_text_from_image(image: Image.Image):
    """
    使用 Tesseract 從圖片中提取文字
    :param image: PIL 圖片對象
    :return: 提取出的文字
    """
    try:
        text = pytesseract.image_to_string(image, lang='eng')
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # 移除非 ASCII 字符
        return text.replace('\n', ' ').strip()
    except Exception as e:
        logger.error(f"Failed to extract text from image: {str(e)}")
        return ""
