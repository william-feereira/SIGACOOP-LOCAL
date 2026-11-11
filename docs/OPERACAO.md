# Operação na VM Ubuntu

## Instalação (uma vez)

1. Pacotes: `sudo apt install python3.13-venv postgresql nginx` e Node.js 22 LTS (só para gerar o build das telas).
2. Usuário e pasta: `sudo useradd --system --home /opt/siga-coop siga` e clone o repositório em `/opt/siga-coop`.
3. Banco: `sudo -u postgres createuser siga_app --pwprompt` e `sudo -u postgres createdb -O siga_app siga_coop`.
4. Ambiente: `python3 -m venv /opt/siga-coop/.venv && /opt/siga-coop/.venv/bin/pip install -r requirements.txt`.
   Telas: `cd /opt/siga-coop/frontend && npm ci && npm run build` (gera `frontend/dist`, que o `collectstatic` publica).
5. Segredos em `/etc/siga-coop/siga.env` (dono root, modo 640, grupo siga), a partir de `.env.example`:
   `SECRET_KEY` com 50+ caracteres aleatórios (`python -c "import secrets;print(secrets.token_urlsafe(64))"`),
   `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS=https://...`, `TRUST_PROXY=True` e as variáveis `POSTGRES_*`.
6. Pastas: `sudo mkdir -p /opt/siga-coop/private_media /opt/siga-coop/staticfiles && sudo chown siga: ...`.
7. Copie `deploy/ubuntu/siga-web.service`, `siga-backup.service` e `siga-backup.timer` para `/etc/systemd/system/`,
   `siga-nginx.conf` para `/etc/nginx/sites-available/siga` e `siga-proxy.conf` para `/etc/nginx/`.
8. `sudo systemctl daemon-reload && sudo systemctl enable --now siga-web siga-backup.timer && sudo systemctl reload nginx`.
9. Primeiro administrador: `sudo -u siga /opt/siga-coop/.venv/bin/python manage.py createsuperuser`.
   No primeiro acesso ele cadastra o aplicativo autenticador (MFA).

## Atualização

`git pull`, `pip install -r requirements.txt`, `cd frontend && npm ci && npm run build` e `sudo systemctl restart siga-web` (as migrações rodam no start).
**Rollback:** `git checkout <versão anterior>` e restart. Se a versão nova tinha migração, antes rode
`python manage.py migrate <app> <migração anterior>` ou restaure o backup do dia.

## Backup e restauração

- Backup diário às 02:30 em `/var/backups/siga` (30 dias), com verificação do arquivo.
- Copie a pasta para outro servidor ou disco (fora da VM).
- **Teste mensal de restauração:**
  `createdb siga_restauracao && pg_restore --no-owner -d siga_restauracao /var/backups/siga/<arquivo>.dump`,
  confira algumas contagens e apague o banco de teste.
- Arquivos anexos ficam em `/opt/siga-coop/private_media`: inclua essa pasta no backup de arquivos da VM.

## Bloqueio de login

Após 5 senhas erradas (usuário + IP) o acesso fica bloqueado por 15 minutos.
Para liberar antes: `python manage.py axes_reset_username <usuario>`.
