import base64
import requests
import os

# Credenciais (recomendado armazenar no .env)
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Monta o header de autenticação em Base64
auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
b64_auth = base64.b64encode(auth_str.encode()).decode()

# Monta os dados da requisição
url = "https://accounts.spotify.com/api/token"
headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "client_credentials"
}

# Faz a requisição POST
response = requests.post(url, headers=headers, data=data)

# Verifica a resposta
if response.status_code == 200:
    token = response.json().get("access_token")
    print("✅ Token obtido com sucesso:")
    print(token)
else:
    print(f"❌ Erro ao obter token: {response.status_code}")
    print(response.text)
