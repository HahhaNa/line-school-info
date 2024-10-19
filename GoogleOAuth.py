from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)
app.secret_key = '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'
flow = None

# 初始化 Firebase Admin SDK
firebase_admin.initialize_app(credentials.Certificate('adminsdk.json'), {
    'databaseURL': 'https://curriculum-4e9d2-default-rtdb.firebaseio.com/'
})

# Google OAuth 2.0 認證
@app.route('/login')
def login():
    print("login")
    global flow
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri=url_for('callback', _external=True)
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

# Google OAuth 2.0 回調
@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # 將 token.json 儲存到 Firebase
    user_id = session.get('user_id')
    ref = db.reference(f'/users/{user_id}')
    ref.update({
        'token': credentials_to_dict(credentials)
    })
    return 'Token 已儲存！'

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run('localhost', 8080, debug=True)
