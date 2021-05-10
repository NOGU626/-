from flask import Flask, request, abort, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from datetime import datetime, timedelta
from werkzeug.security import safe_str_cmp
from orignalmodules import initialize
import configparser

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from flasgger import Swagger , swag_from

import os

config = configparser.ConfigParser()
inifile = os.path.join(os.path.dirname(__file__),'orignalmodules/config.ini')
config.read(inifile)

app = Flask(__name__)

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


app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_ALGORITHM'] = 'HS256'  # 暗号化署名のアルゴリズム
app.config['JWT_AUTH_URL_RULE'] = '/auth'  # 認証エンドポイントURL
app.config['JWT_NOT_BEFORE_DELTA'] = timedelta(seconds=10)
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=50)

jwt = JWT(app, authenticate, identity)


# JWTペイロードのカスタマイズを行う関数を追加
@jwt.jwt_payload_handler
def make_payload(identity):
    iat = datetime.utcnow()  # トークン発行日
    exp = iat + app.config.get('JWT_EXPIRATION_DELTA')  # トークン有効期限
    nbf = iat + app.config.get('JWT_NOT_BEFORE_DELTA')  # トークンが有効になる日時
    identity = getattr(identity, 'username')
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': 1}


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# swaggerによるタイトルとapiバージョンに関する設定
swagger = Swagger(app,
                  template= initialize.template
                  )

# LINE Developersで設定されているアクセストークンとChannel Secretをを取得し、設定します。
YOUR_CHANNEL_ACCESS_TOKEN = config["BussinesLINE"]["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = config["BussinesLINE"]["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


###############################################
# Webhookからのリクエストをチェック。(LINE BOT用)
###############################################
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得します。
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得します。
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す。
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す。
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'


###############################################
# LINEのメッセージの取得と返信内容の設定(オウム返し)
###############################################

# LINEでMessageEvent（普通のメッセージを送信された場合）が起こった場合に、
# def以下の関数を実行します。
# reply_messageの第一引数のevent.reply_tokenは、イベントの応答に用いるトークンです。
# 第二引数には、linebot.modelsに定義されている返信用のTextSendMessageオブジェクトを渡しています。

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))  # ここでオウム返しのメッセージを返します。



@app.route('/colors/<palette>/')
def colors(palette):
    """
        post user
        ---
        tags:
          - user
        produces:
          - application/json
        parameters:
          - in: body
            name: user
            schema:
              $ref: '#/definitions/UserSchema'
        responses:
          200:
            description: Successful operation
            schema:
              $ref: "#/definitions/UserSchema"
        """
    all_colors = {
        'cmyk': ['cian', 'magenta', 'yellow', 'black'],
        'rgb': ['red', 'green', 'blue']
    }
    if palette == 'all':
        result = all_colors
    else:
        result = {palette: all_colors.get(palette)}

    return jsonify(result)

# ポート番号の設定
if __name__ == "__main__":
    # app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
