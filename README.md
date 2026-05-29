# Portugues

# Insta Tracker

Aplicação Flask para comparar seguidores e seguindo de uma conta do Instagram usando o cookie `sessionid`.

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

## Instalação

```powershell
pip install -r requirements.txt
```

## Como pegar o sessionid do Instagram

1. Entre no Instagram pelo navegador: `https://www.instagram.com`.
2. Com o Instagram aberto, pressione `F12`.
   - Se nao abrir, tente `Ctrl + Shift + I`.
3. Nas ferramentas de desenvolvedor, abra a area de armazenamento:
   - Chrome/Edge: aba `Application`.
   - Firefox: aba `Storage` ou `Armazenamento`.
4. No menu lateral, abra `Cookies`.
5. Clique em `https://www.instagram.com`.
6. Na tabela de cookies, procure a linha chamada `sessionid`.
7. Copie o conteudo da coluna `Value` ou `Valor`.
8. Cole esse valor no campo `Sessionid` da tela de login do Insta Tracker.

Voce tambem pode colar a linha completa de cookies no app, desde que ela contenha `sessionid=...`.

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

# English

# Insta Tracker

Flask application to compare followers and following of an Instagram account using the `sessionid` cookie.

The app shows:

- Total followers
- Total following
- Who you follow but doesn't follow you back
- Who follows you but you don't follow back
- Profile picture, name, and @handle of found profiles
- CSV export

## Requirements

- Python 3.10+
- An Instagram account logged in via browser

## Installation

```powershell
pip install -r requirements.txt
```

## How to get the Instagram sessionid

1. Go to Instagram in your browser: `https://www.instagram.com`.
2. With Instagram open, press `F12`.
   - If it doesn't open, try `Ctrl + Shift + I`.
3. In developer tools, open the storage area:
   - Chrome/Edge: `Application` tab.
   - Firefox: `Storage` tab.
4. In the sidebar, expand `Cookies`.
5. Click on `https://www.instagram.com`.
6. In the cookie table, find the row named `sessionid`.
7. Copy the content of the `Value` column.
8. Paste this value into the `Sessionid` field on the Insta Tracker login screen.

You can also paste the full cookie string into the app, as long as it contains `sessionid=...`.

## How to run

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Paste the `sessionid` on the login screen and sign in.

## Notes

- The app does not save passwords.
- The app does not use `instaloader`.
- The app depends on the `sessionid` being valid.
- If Instagram expires or blocks the session, log out in the app, copy a new `sessionid`, and log in again.
- Profile pictures are served through the local `/avatar` endpoint to avoid blocking issues from Instagram's CDN.

## Structure

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
