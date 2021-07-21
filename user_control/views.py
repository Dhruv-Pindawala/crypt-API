from django.db.models import query
import jwt
from .models import CustomUser, Jwt
from .models import CustomUser
from datetime import datetime, timedelta
from django.conf import settings
import random
import string
from .serializers import RefreshSerializer, RegisterSerializer, LoginSerializer, UserProfileSerializer, UserProfile
from .authentication import Authentication
from rest_framework.response import Response
from rest_framework.views import APIView
from chatapi.custom_methods import IsAuthenticatedCustom
from django.contrib.auth import authenticate
from rest_framework.viewsets import ModelViewSet
import re
from django.db.models import Q

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

def decodeJWT(bearer):
    if not bearer:
        return None
    token = bearer[7:]
    decoded = jwt.decode(token, key=settings.SECRET_KEY)
    if decoded:
        try:
            return CustomUser.objects.get(id=decoded['user_id'])
        except Exception:
            return None

class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if not user:
            return Response({"error":"Invalid username or password"},status="400")
        
        Jwt.objects.filter(user_id=user.id).delete()
        access = get_access_token({"user_id":user.id})
        refresh = get_refresh_token()

        # change from access.decode and refresh.decode after testing
        Jwt.objects.create(
            user_id=user.id, access=access, refresh=refresh
        )

        return Response({"access":access,"refresh":refresh})

class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        CustomUser.objects._create_user(**serializer.validated_data)

        return Response({"success":"User successfully created."}, status=201)

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

        # change from access.decode and refresh.decode after testing
        active_jwt.access = access
        active_jwt.refresh = refresh
        active_jwt.save()

        return Response({"access":access,"refresh":refresh})

class UserProfileView(ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedCustom,) # access to profile only when logged in

    def get_queryset(self):
        
        if self.request.method.lower() != 'get':
            return self.queryset

        data = self.request.query_params.dict()
        keyword = data.pop('keyword', None)

        if keyword:
            search_fields = (
                "user__username", "first_name", "last_name", "user__email"
            )
            query = self.get_query(keyword, search_fields)
            try:
                return self.queryset.filter(query).filter(**data).exclude(Q(user_id=self.request.user.id) | Q(user__is_superuser=True)).distinct()
            except Exception as e:
                raise Exception(e)

        return self.queryset.filter(**data).exclude(Q(user_id=self.request.user.id) | Q(user__is_superuser=True)).distinct()

    @staticmethod
    def get_query(query_string, search_fields):
        """
        Returns a query, that is a combination of Q objects. Thar combination aims to search keywords within a model by testing the given search fields
        """

        query = None # query to search for every term
        terms = UserProfileView.normalize_query(query_string)
        for term in terms:
            or_query = None # query to search for a given term in each field
            for field_name in search_fields:
                q = Q(**{'%s__icontains'%field_name: term})
                if or_query is None:
                    or_query=q
                else:
                    or_query = or_query | q
            if query is None:
                query = or_query
            else:
                query = query & or_query
        return query

    @staticmethod
    def normalize_query(query_string, findterms=re.compile(r'"([^"]+)"|(\S+)').findall, normspace=re.compile(r'\s{2,}').sub):

        return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

class MeView(APIView):
    permission_classes = (IsAuthenticatedCustom,)
    serializer_class = UserProfileSerializer

    def get(self, request):
        data = {}
        try:
            data = self.serializer_class(request.user.user_profile).data
        except Exception:
            data = {
                "user": {
                    "id": request.user.id
                }
            }
        return Response(data, status=200)

class LogoutView(APIView):
    permission_classes = (IsAuthenticatedCustom,)

    def get(self, request):
        user_id = request.user.id

        Jwt.objects.filter(user_id=user_id).delete()

        return Response('Logged out successfully', status=200)
