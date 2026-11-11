# Sobe o SIGA Coop na sua máquina (Windows). Requer Docker Desktop aberto.
# Uso: clique com o botão direito > "Executar com o PowerShell", ou no terminal: .\iniciar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
function Aleatorio([int]$bytes) {
  $b = New-Object byte[] $bytes
  [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
  return ([Convert]::ToBase64String($b) -replace '[+/=]', '')
}
if (-not (Test-Path .env)) {
  (Get-Content .env.example) `
    -replace '^SECRET_KEY=.*', ("SECRET_KEY=" + (Aleatorio 64)) `
    -replace '^POSTGRES_PASSWORD=.*', ("POSTGRES_PASSWORD=" + (Aleatorio 24)) |
    Set-Content -Encoding ascii .env
  Write-Host "Arquivo .env criado com chave e senha do banco aleatorias."
}
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "O Docker nao conseguiu subir o SIGA. O Docker Desktop esta aberto?" }
Write-Host "Aguardando o SIGA iniciar..."
for ($i = 0; $i -lt 60; $i++) {
  try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/contas/entrar/ -TimeoutSec 3 | Out-Null; Write-Host "Pronto: http://localhost:8000"; Start-Process "http://localhost:8000"; exit 0 }
  catch { Start-Sleep -Seconds 2 }
}
Write-Host "Nao respondeu. Veja: docker compose logs web"
exit 1
