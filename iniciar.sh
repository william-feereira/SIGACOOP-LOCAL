#!/usr/bin/env sh
# Sobe o SIGA Coop na sua máquina (Linux/macOS). Requer Docker com o plugin "compose".
set -e
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  cp .env.example .env
  chave=$(python3 -c "import secrets;print(secrets.token_urlsafe(64))" 2>/dev/null || openssl rand -base64 64 | tr -d '\n/+=')
  senha=$(python3 -c "import secrets;print(secrets.token_urlsafe(24))" 2>/dev/null || openssl rand -hex 24)
  sed -i.bak "s|^SECRET_KEY=.*|SECRET_KEY=$chave|; s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$senha|" .env && rm -f .env.bak
  chmod 600 .env
  echo "Arquivo .env criado com chave e senha do banco aleatórias."
fi
docker compose up -d --build
echo "Aguardando o SIGA iniciar..."
i=0
until curl -fs -o /dev/null http://127.0.0.1:8000/contas/entrar/; do
  i=$((i+1)); [ $i -gt 60 ] && { echo "Não respondeu. Veja: docker compose logs web"; exit 1; }
  sleep 2
done
echo "Pronto: http://localhost:8000"
