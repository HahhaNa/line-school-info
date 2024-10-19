import imaplib
import email
from email.policy import default
import os
from bs4 import BeautifulSoup
from email.header import decode_header
from firebase_admin import credentials, db
import base64
from ai import ai_reply
from datetime import datetime
import pytz  
from gcal import gcal
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# 設定信箱的IMAP伺服器和登入資訊
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = 'tina920921@gmail.com'
PASSWORD = 'tdwc uhlm tayu klqu'

# 設定要搜尋的寄件人
SENDER_EMAIL = 'yuting920921@gmail.com'

# Gmail API 的 OAuth 2.0 作用域
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_credentials():
    """使用OAuth 2.0 获取授权凭证"""
    creds = None
    # 如果存在token.json，表示已经完成了认证，直接加载
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # 如果没有token，或者token已经过期，需要重新认证
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 保存token用于以后使用
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def connect_to_mail(creds):
    """使用OAuth2.0登录IMAP服务器"""
    access_token = creds.token
    auth_string = f"user={EMAIL_ACCOUNT}\1auth=Bearer {access_token}\1\1"

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.authenticate('XOAUTH2', lambda x: auth_string)
    return mail

# 提取信件正文
def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == 'text/html':  # 處理 HTML 內容
                html_content = part.get_payload(decode=True).decode('utf-8')
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.get_text()
    else:
        return msg.get_payload(decode=True).decode('utf-8')
    

# 取得信件的內容，根據使用者的 Gmail 帳號
def search_and_extract_emails(credentials, user_email):
    access_token = credentials.token
    auth_string = f"user={user_email}\1auth=Bearer {access_token}\1\1"

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.authenticate('XOAUTH2', lambda x: auth_string)

    # 選擇收件匣
    mail.select('inbox')
    
    # 搜尋來自特定寄件人的郵件
    start_time = datetime.now().strftime('%d-%b-%Y')
    result, data = mail.search(None, f'(UNSEEN SINCE {start_time} FROM "yuting920921@gmail.com")')

    if result == 'OK':
        mail_ids = data[0].split()
        for num in mail_ids:
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result == 'OK':
                msg = email.message_from_bytes(msg_data[0][1], policy=default)

                msg_date = email.utils.parsedate_to_datetime(msg['Date'])
                
                loc_dt = datetime.today()
                loc_dt_format = loc_dt.strftime("%Y/%m/%d %H:%M:%S")
                
                reply = ai_reply(extract_body(msg))
                print(reply)
                event, place, time  = reply.split(",")
                print(event, place, time)

                time = time.strip()
                date_time = datetime.strptime(time, "%Y/%m/%d %H:%M:%S")

                formatted_date = date_time.strftime("%Y%m%dT%H%M%S")
                if time < loc_dt_format:
                    print("The date is in the past.")
                    gcal(event, formatted_date+"/"+formatted_date, place)
                else:
                    print("The date is in the future.")
                    gcal(event, formatted_date+"/"+formatted_date, place)

    mail.close()
    mail.logout()

if __name__ == '__main__':
    
    while True:
        search_and_extract_emails()
    
    # print(search_and_extract_emails())
