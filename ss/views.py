from django.shortcuts import render, redirect

def hangman(request):
    return render(request, "hangman.html", {})