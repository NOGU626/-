###############################################
# swagger用のドキュメンとのための初期設定の部分の辞書
###############################################
template = {
    "swagger": "3.0",
    "openapi": "3.0.0",
    "info": {
        "title": "病院用アプリケーションAPI",
        "version": "1.0",
    },
    'components': {
        'securitySchemes': {
            'JWTtoken': {
                'type': "apiKey",
                'name': "Authorization",
                'description': "認証に必要なあらかじめ生成されたJWTを入力",
                'in': "header",
                'scheme': 'jwt'
            }

        },
        'security': {
            'bearerAuth': []
        }
    }
}
