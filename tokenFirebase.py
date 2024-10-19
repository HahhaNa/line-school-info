from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import firebase_admin
from firebase_admin import credentials, db
import os
import imaplib
import email
from email.policy import default
from bs4 import BeautifulSoup
from datetime import datetime
import google.auth
from google.auth.transport.requests import Request
from gcal import gcal
from ai import ai_reply
import requests
import os
import threading
import time
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Flask 初始化
app = Flask(__name__)
app.secret_key = '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'
flow = None

# Firebase 初始化
firebase_admin.initialize_app(credentials.Certificate('adminsdk.json'), {
    'databaseURL': os.getenv('DATABASEURL')
})

# Google OAuth 2.0 授權
@app.route('/login')
def login():
    global flow
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'https://www.googleapis.com/auth/userinfo.email'],
        # scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri=url_for('callback', _external=True)
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

# 授權後回調
@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    # 使用 access_token 請求 userinfo API 來獲取 email
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {'Authorization': f'Bearer {credentials.token}'}
    response = requests.get(userinfo_url, headers=headers)

    if response.status_code == 200:
        user_info = response.json()
        session['user_email'] = user_info.get('email')  # 取得使用者的 email
        user_email = user_info.get('email')
        # 儲存 token 到 Firebase
        user_id = session.get('user_id')
        ref = db.reference(f'/users/{user_id}')
        ref.update({
            'token': credentials_to_dict(credentials),
            'email': user_email 
        })
        return 'Token 已儲存！'
    else:
        return '無法獲取使用者資訊', 400
# 轉換憑證為字典格式
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

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
# 在背景中定期運行的函數
def background_task(credentials, user_email, interval=60):
    while True:
        print("Checking for new emails...")
        search_and_extract_emails(credentials, user_email)
        time.sleep(interval)  # 每隔 60 秒檢查一次
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
    credentials = None  # 根據實際情況，初始化這些變數
    user_email = None
    threading.Thread(target=background_task, args=(credentials, user_email)).start()
    app.run('localhost', 8080, debug=True)
