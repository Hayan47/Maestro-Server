from django.shortcuts import render


def test_control(request):
    return render(request, 'control/test_control.html')