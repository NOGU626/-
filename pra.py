from flask import Flask
from flask_jwt import JWT, jwt_required, current_identity
from datetime import datetime, timedelta
from werkzeug.security import safe_str_cmp

# JWTのユーザ認証に関する処理
class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
        

    def __str__(self):
        return "User(id='%s')" % self.id

users = [
    User(1, 'user1', 'abcxyz'),
    User(2, 'user2', 'abcxyz'),
]

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user

def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_ALGORITHM'] = 'HS256'                       # 暗号化署名のアルゴリズム
app.config['JWT_AUTH_URL_RULE'] = '/auth'                   # 認証エンドポイントURL
app.config['JWT_NOT_BEFORE_DELTA'] = timedelta(seconds=10)
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=50)

jwt = JWT(app, authenticate, identity)

# JWTペイロードのカスタマイズを行う関数を追加
@jwt.jwt_payload_handler
def make_payload(identity):
    iat = datetime.utcnow() # トークン発行日
    exp = iat + app.config.get('JWT_EXPIRATION_DELTA') # トークン有効期限
    nbf = iat + app.config.get('JWT_NOT_BEFORE_DELTA') # トークンが有効になる日時
    identity = getattr(identity, 'username')
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': 1}

@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity

if __name__ == '__main__':
    app.run()