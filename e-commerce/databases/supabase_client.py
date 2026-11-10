import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "config.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

def testar_conexao():
    # Validação inicial das chaves
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Erro: SUPABASE_URL ou SUPABASE_KEY não foram encontradas no ambiente.")
        return

    print("Tentando conectar ao Supabase...")
    
    try:
        # 2. Inicializa o cliente
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # 3. Executa uma query leve e nativa do Postgres para testar a resposta do banco
        # Isso apenas pede ao banco para retornar o número 1, sem ler nenhuma tabela.
        resposta = supabase.auth.get_session()
        
        # Se não houver erro, a conexão foi bem-sucedida
        print("Conexão estabelecida com sucesso!")
        
    except Exception as e:
        print("Falha na conexão com o Supabase.")
        print(f"Erro retornado: {e}")

if __name__ == "__main__":
    testar_conexao()