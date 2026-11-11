# SIGA Coop: versão para rodar na sua máquina

Esta é uma cópia do SIGA Coop pronta para rodar **no seu computador**, sem servidor. Ela serve para conhecer, testar e demonstrar o sistema. Hoje o destaque é o **Kanban de reformas dos PAs**: o quadro mostra o que já foi feito, onde a obra parou e quem continua, com checklist, diário e passagem de bastão entre terceiros.

> Esta versão roda só em `http://localhost` e só a própria máquina acessa. Ela **não é** a instalação de produção. A de produção (VM Linux com Nginx, HTTPS e backup) está em [docs/OPERACAO.md](docs/OPERACAO.md).

## Jeito mais fácil: com Docker (Windows, Linux ou Mac)

**O que você precisa:** o [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e aberto. No Linux, o Docker Engine com o plugin `compose` resolve.

1. Baixe este repositório: no GitHub, clique em **Code > Download ZIP** e descompacte. Se preferir, use `git clone`.
2. Rode o script de início dentro da pasta:
   - **Windows:** clique com o botão direito em `iniciar.ps1` e escolha **Executar com o PowerShell**. Se o Windows bloquear o script, abra o PowerShell na pasta e rode:
     `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1`
   - **Linux/Mac:** `./iniciar.sh`

   Na primeira vez, o script cria o arquivo `.env` com uma chave secreta e uma senha do banco aleatórias. Depois ele monta tudo, o que leva alguns minutos, e avisa quando estiver pronto.
3. Crie os dados de demonstração. Eles são fictícios: um PA de exemplo, empresas "(exemplo)" e uma reforma em andamento.
   ```sh
   docker compose exec web python manage.py carregar_demo
   ```
   O comando pede uma senha com no mínimo 12 caracteres para os usuários de teste.
4. Abra **http://localhost:8000** e entre com o usuário `gestora.demo` e a senha que você escolheu. Também existe o usuário `tecnico.demo`, com a mesma senha.

### Criar o seu próprio administrador

```sh
docker compose exec web python manage.py createsuperuser
```

No primeiro acesso, o administrador precisa cadastrar um aplicativo autenticador (Microsoft Authenticator, Google Authenticator etc.) lendo um QR code. É a verificação em duas etapas (MFA), obrigatória para administradores mesmo na versão local.

### Comandos do dia a dia

| Para... | Rode |
|---|---|
| Parar | `docker compose stop` |
| Ligar de novo | `docker compose start` |
| Ver erros | `docker compose logs web` |
| Atualizar depois de baixar uma versão nova | `docker compose up -d --build` |
| Apagar tudo, inclusive os dados | `docker compose down -v` |

## Sem Docker (para quem desenvolve)

Precisa de Python 3.13, PostgreSQL 16 ou mais novo e Node.js 22.

```sh
# 1) banco: crie um usuário e um banco no PostgreSQL
sudo -u postgres createuser siga_app --pwprompt
sudo -u postgres createdb -O siga_app siga_coop

# 2) configuração: copie e ajuste (SECRET_KEY longa e a senha do banco)
cp .env.example .env

# 3) telas (React)
cd frontend && npm ci && npm run build && cd ..

# 4) sistema (Django)
python3 -m venv .venv && . .venv/bin/activate      # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_units
python manage.py carregar_demo
python manage.py runserver
```

O `manage.py` lê o `.env` sozinho. Abra http://localhost:8000.

Para mexer nas telas com recarga automática, deixe o `runserver` rodando e, em outro terminal, rode `cd frontend && npm run dev`. Depois abra http://localhost:5173.

## Testes

```sh
pytest                                         # backend (usa o PostgreSQL do .env)
cd frontend && npm run typecheck && npm test   # telas
```

## O que tem dentro

| Pasta | O que é |
|---|---|
| `apps/` | Módulos em Django: `reformas` (Kanban), `requests_center` (solicitações), `assets`, `fleet`, `travels`, `contracts`, `analytics`, `accounts` (login, perfis, MFA), `audit` |
| `frontend/` | Telas novas em React + TypeScript (quadro de reformas e visão geral) |
| `templates/`, `static/` | Telas em HTML do Django e o design system |
| `config/settings/local.py` | Configuração desta versão local (sem HTTPS, só localhost) |
| `compose.yaml`, `Dockerfile` | PostgreSQL + aplicação em containers |
| `deploy/ubuntu/`, `docs/OPERACAO.md` | Instalação de produção na VM Linux |

## Segurança, mesmo sendo local

- O `.env` guarda a chave e a senha do banco e **nunca** vai para o Git (está no `.gitignore`).
- A aplicação escuta só em `127.0.0.1`. Outras máquinas da rede não acessam.
- Continuam ligados: senha forte (12+ caracteres), bloqueio após 5 tentativas erradas, MFA para administradores, CSP sem scripts de fora, filtro por unidade e auditoria.
