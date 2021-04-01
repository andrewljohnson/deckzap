from django.shortcuts import render, redirect
from django.http import Http404

def index(request):
    if request.method == "POST":
        room_code = request.POST.get("room_code")
        char_choice = request.POST.get("username")
        return redirect(
            '/play/%s?&username=%s' 
            %(room_code, char_choice)
        )
    return render(request, "index.html", {})


def game(request, room_code):
    context = {
        "username": request.GET.get("username"), 
        "room_code": room_code
    }
    return render(request, "game.html", context)