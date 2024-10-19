import imaplib
import email
from email.policy import default
import os
from bs4 import BeautifulSoup
from email.header import decode_header
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

def extract_body(msg):
    """從郵件中提取郵件內容，無論是純文本還是HTML"""
    if msg.is_multipart():
        # 如果郵件是多部分的
        for part in msg.walk():
            content_type = part.get_content_type()

            if content_type == 'text/html':  # 如果是HTML部分
                html_content = part.get_payload(decode=True).decode('utf-8')
                # 使用BeautifulSoup來解析HTML並擷取純文本
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.get_text()
    else:
        # 單一部分的郵件，直接提取純文本
        return msg.get_payload(decode=True).decode('utf-8')
    

def search_and_extract_emails():
    start_time = datetime.now().strftime('%d-%b-%Y')
    # 連接到IMAP伺服器
    # mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    # mail.login(EMAIL_ACCOUNT, PASSWORD)
    creds = get_credentials()
    mail = connect_to_mail(creds)
    # 選擇收件匣
    mail.select('inbox')
    
    # 搜尋來自特定寄件人的郵件
    result, data = mail.search(None, f'(UNSEEN SINCE {start_time} FROM "{SENDER_EMAIL}")')

    if result == 'OK':
        mail_ids = data[0].split()
        latest_10_mail_ids = mail_ids[-10:]
        for num in latest_10_mail_ids:
            result, msg_data = mail.fetch(num, '(RFC822)')
            if result == 'OK':
                # 解析郵件內容
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
            
    # 關閉連線
    mail.close()
    mail.logout()
def check_emails_for_all_users():
    # 取得 Firebase Database 中所有 users 的資料
    users_ref = db.reference('/users')
    users = users_ref.get()

    # 遍歷每個 user 的資料
    for user_id, user_data in users.items():
        if 'email' in user_data and 'token' in user_data:
            user_email = user_data['email']
            token_info = user_data['token']
            
            # 建立 credentials 物件
            creds = Credentials(
                token=token_info['token'],
                refresh_token=token_info.get('refresh_token'),
                token_uri=token_info['token_uri'],
                client_id=token_info['client_id'],
                client_secret=token_info['client_secret'],
                scopes=token_info['scopes']
            )

            # 執行 search_and_extract_emails 函數
            search_and_extract_emails(creds, user_email)
if __name__ == '__main__':
    
    while True:
        search_and_extract_emails()
    
    # print(search_and_extract_emails())
