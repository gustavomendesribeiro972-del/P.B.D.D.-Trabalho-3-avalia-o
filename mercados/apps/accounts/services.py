from integrations.supabase_client import supabase

def autenticar_usuario(email, senha):
    try:
        resposta = supabase.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })
        return{
            "sucesso": True,
            "usuario": resposta.user,
            "access_token": resposta.session.access_token,
            "refresh_token": resposta.session.refresh_token
        }
    
    except Exception:
        return {"sucesso":False, "erro": "Email ou senha inválidos, tente novamente..."}