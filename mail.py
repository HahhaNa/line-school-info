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
# 設定信箱的IMAP伺服器和登入資訊
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = 'tina920921@gmail.com'
PASSWORD = 'tdwc uhlm tayu klqu'

# 設定要搜尋的寄件人
SENDER_EMAIL = 'eeclass@my.nthu.edu.tw'

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
    messages = []
    # 連接到IMAP伺服器
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    
    # 選擇收件匣
    mail.select('inbox')
    
    # 搜尋來自特定寄件人的郵件
    result, data = mail.search(None, f'(FROM "{SENDER_EMAIL}")')
    # TODO: if time is before now, break and return 
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
                print(loc_dt_format)
                
                print(extract_body(msg))
                reply = ai_reply(extract_body(msg))
                print(reply)
                place, event, time  = reply.split(",")
                print(place, event, time)
                # 解析成 datetime 物件
                time = time.strip()
                date_time = datetime.strptime(time, "%Y/%m/%d %H:%M:%S")

                formatted_date = date_time.strftime("%Y%m%dT%H%M%S")
                if time < loc_dt_format:
                    print("The date is in the past.")
                else:
                    print("The date is in the future.")
                    print(reply)
                    gcal(event, formatted_date, place)
                messages.append(extract_body(msg))
            
    # 關閉連線
    mail.close()
    mail.logout()
    return messages

if __name__ == '__main__':
    messages = search_and_extract_emails()
    
    # print(search_and_extract_emails())
