from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

class LoginView(View):
    def get(self, request):
        print("SSSSS")
        return render(request, 'authentication/test_login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            response = redirect('/control/')
            response.set_cookie('access', str(refresh.access_token))
            response.set_cookie('refresh', str(refresh))
            return response
        return render(request, 'login.html', {'error': 'Invalid credentials'})


