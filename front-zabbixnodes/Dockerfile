# docker build -t registry.lunioit.com/zabbixnodes-frontend:vue-dev . && docker push registry.lunioit.com/zabbixnodes-frontend:vue-dev
# Stage 1: Build
FROM node:22-alpine AS builder

WORKDIR /build

# Copiar package files
COPY package*.json ./

# Instalar dependências
RUN npm ci 

# Copiar código fonte
COPY . .

# Build do projeto Vue.js
# Por padrão, usa .env.production se existir
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Definir diretório de trabalho
WORKDIR /app

# Copiar os arquivos buildados do stage anterior
COPY --from=builder /build/dist /app/dist

# Copiar configuração do nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Copiar script de entrypoint
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Variáveis de ambiente padrão
ENV VITE_API_BASE_URL=http://142.93.116.237:8001/api/v1

# Expor porta
EXPOSE 80

# Executar entrypoint
ENTRYPOINT ["/entrypoint.sh"]
