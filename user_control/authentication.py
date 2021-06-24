import jwt
from django.conf import settings
from datetime import datetime
from rest_framework.authentication import BaseAuthentication

class Authentication(BaseAuthentication):

    def authenticate(self,request):
        data = self.validate_request(request.headers)
        if not data:
            return None, None
        return self.get_user(data["user_id"]), None

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