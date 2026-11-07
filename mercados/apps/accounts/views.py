from django.shortcuts import render, redirect
from django.contrib import messages

from .services import autenticar_usuario

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        senha = request.POST.get("senha")

        resultado = autenticar_usuario(email, senha)

        if resultado["sucesso"]:
            request.session["access_token"]=(resultado["access_token"])
            request.session["refresh_token"]=(resultado["refresh_token"])
            request.session["perfil_id"]=(resultado["perfil"].id)
            request.session.cycle_key()

            return redirect("admin_dashboard")

    messages.error(request, resultado["erro"])
    return render(request, "accounts/login.html")
