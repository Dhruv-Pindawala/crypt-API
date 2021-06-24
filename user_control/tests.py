from rest_framework.test import APITestCase
from .views import get_refresh_token, get_access_token, get_random

class TestGenericFunctions(APITestCase):
    def test_get_random(self):
        r1 = get_random(10)
        r2 = get_random(10)
        r3 = get_random(15)

        self.assertTrue(r1)
        self.assertNotEqual(r1,r2)
        self.assertEqual(len(r1),10)
        self.assertEqual(len(r3),15)
    
    def test_get_access_token(self):
        p = {"id":1}
        token = get_access_token(p)
        self.assertTrue(token)
    
    def test_get_refresh_tooken(self):
        token = get_refresh_token()
        self.assertTrue(token)

class TestAuth(APITestCase):
    login = "/user/login"
    register = "/user/register"
    refreshurl = "/user/refresh"

    def test_register(self):
        p = {"username":'testuser',"password":'password'}

        response = self.client.post(self.register,data=p)

        self.assertEqual(response.status_code,201)

    def test_login(self):
        p = {"username":'testuser',"password":'password'}
        self.client.post(self.register,data=p)

        response = self.client.post(self.login,data=p)
        result = response.json()

        self.assertEqual(response.status_code,200)
        self.assertTrue(result['access'])
        self.assertTrue(result['refresh'])
    
    def test_refresh(self):
        p = {"username":'testuser',"password":'password'}
        self.client.post(self.register,data=p)

        response = self.client.post(self.login,data=p)
        refresh = response.json()['refresh']

        response = self.client.post(self.refreshurl,data={'refresh':refresh})
        result = response.json()

        self.assertEqual(response.status_code,200)

        self.assertTrue(result['access'])
        self.assertTrue(result["refresh"])
