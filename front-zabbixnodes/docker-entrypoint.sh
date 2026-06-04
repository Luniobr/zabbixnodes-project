#!/bin/sh
set -e

# Script de entrypoint para injetar variáveis de ambiente em tempo de execução
# Isso permite que a URL da API seja alterada sem fazer rebuild da imagem

API_URL="${VITE_API_BASE_URL:-http://142.93.116.237:8001/api/v1}"

# Encontra todos os arquivos .js no dist e substitui o placeholder pela URL real
echo "Configurando API URL: $API_URL"

# Se o arquivo main*.js existir, substitui a URL padrão pela variável de ambiente
if [ -d "/app/dist" ]; then
  find /app/dist -name "*.js" -type f -exec sed -i "s|__VITE_API_BASE_URL__|${API_URL}|g" {} +
  echo "URL da API configurada com sucesso"
fi

# Inicia o nginx
exec nginx -g "daemon off;"
