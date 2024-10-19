from PIL import Image
from io import BytesIO
import pytesseract
import re
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, ImageMessage
import os 

# 設定 pytesseract 的安裝路徑
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

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

def handle_image_message(event):
    """
    處理圖片訊息，提取圖片中的文字並回覆給用戶
    :param event: LINE bot 傳來的事件
    """
    try:
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        image = Image.open(BytesIO(message_content.content))
        extracted_text = extract_text_from_image(image)

        if extracted_text:
            reply_message = TextSendMessage(text=extracted_text)
        else:
            reply_message = TextSendMessage(text="Sorry, I couldn't extract any text from the image.")

        line_bot_api.reply_message(event.reply_token, reply_message)
    except Exception as e:
        logger.error(f"Error handling image message: {str(e)}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="An error occurred while processing the image."))

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