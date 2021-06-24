import jwt
from django.conf import settings
from datetime import datetime

class Authentication():

    @staticmethod
    def verify_token(token):
        try:
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")
        except Exception:
            return None
        exp = decoded_data["exp"]
        if datetime.now().timestamp()>exp:
            return None
        return decoded_data