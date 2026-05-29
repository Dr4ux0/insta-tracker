# Insta Tracker

Aplicacao Flask para comparar seguidores e seguindo de uma conta do Instagram usando o cookie `sessionid`.

O app mostra:

- total de seguidores
- total de perfis seguidos
- quem voce segue e nao te segue de volta
- quem te segue e voce nao segue de volta
- foto, nome e @ dos perfis encontrados
- exportacao CSV

## Requisitos

- Python 3.10+
- Uma conta logada no Instagram pelo navegador

## Instalacao

```powershell
pip install -r requirements.txt
```

## Como pegar o sessionid

1. Entre no Instagram pelo navegador.
2. Abra as ferramentas de desenvolvedor.
3. Va em `Application` ou `Storage`.
4. Abra `Cookies`.
5. Selecione `https://www.instagram.com`.
6. Copie o valor do cookie `sessionid`.

Voce tambem pode colar a linha completa de cookies se ela contiver `sessionid`.

## Como rodar

```powershell
python app.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

Cole o `sessionid` na tela de login e entre.

## Observacoes

- O app nao salva senha.
- O app nao usa `instaloader`.
- O app depende do `sessionid` estar valido.
- Se o Instagram expirar ou bloquear a sessao, faca logout no app, copie um `sessionid` novo e entre novamente.
- As fotos de perfil passam pelo endpoint local `/avatar` para evitar bloqueios de imagem da CDN do Instagram.

## Estrutura

```text
app.py
requirements.txt
static/
  dashboard.js
  login.js
  css/
    style.css
templates/
  index.html
  login.html
```
