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
