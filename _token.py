import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# 使用你下載的 serviceAccountKey.json 檔案來初始化應用程式
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-name.firebaseio.com'
})
def get_user_tokens():
    # 參考 users 資料夾
    ref = db.reference('users')
    
    # 獲取 users 底下所有的 user 資料
    users = ref.get()
    
    # 用來儲存 user id 和 token 的字典
    user_tokens = {}

    # 遍歷每個使用者的資料
    if users:
        for user_id, user_info in users.items():
            # 假設每個 user 資訊內有 token 欄位
            token = user_info.get('token', None)
            if token:
                user_tokens[user_id] = token

    return user_tokens

# 調用這個函數
user_tokens = get_user_tokens()
print(user_tokens)