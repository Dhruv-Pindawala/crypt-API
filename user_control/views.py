from django.shortcuts import render
import jwt
from .models import Jwt
from datetime import datetime, timedelta
from django.conf import settings
import random
import string
from .serializers import RefreshSerializer
from .authentication import Authentication
from rest_framework.response import Response
from rest_framework.views import APIView

def get_access_token(payload):
    return jwt.encode(
        {"exp":datetime.now() + timedelta(minutes=6), **payload},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

def get_random(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_refresh_token():
    return jwt.encode(
        {"exp":datetime.now()+timedelta(days=365),"data":get_random(10)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

class RefreshView(APIView):
    serializer_class = RefreshSerializer
    
    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            active_jwt = Jwt.objects.get(refresh=serializer.validated_data["refresh"])
        except Jwt.DoesNotExist:
            return Response({"error": "refresh token not found"}, status="400")
        if not Authentication.verify_token(serializer.validated_data["refresh"]):
            return Response({"error": "Token is invalid or has expired"})
        
        access = get_access_token({"user_id": active_jwt.user.id})
        refresh = get_refresh_token()

        active_jwt.access = access.decode()
        active_jwt.refresh = refresh.decode()
        active_jwt.save()

        return Response({"access":access,"refresh":refresh})
