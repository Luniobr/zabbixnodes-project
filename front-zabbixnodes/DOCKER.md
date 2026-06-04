# Guia Docker - Front-end ZabbixNodes

## 📋 Visão Geral

O projeto Vue.js foi configurado com Docker multi-stage para otimizar:
- **Build**: Compila o projeto com Node.js
- **Production**: Executa com Nginx em Alpine Linux

## 🏗️ Arquivos Criados

### Dockerfile
- **Multi-stage**: reduz o tamanho final da imagem (~50MB)
- **Build stage**: Node.js 22 Alpine (compila o projeto)
- **Production stage**: Nginx Alpine (serve a aplicação)

### nginx.conf
- Configuração otimizada para SPA Vue.js
- Compressão Gzip habilitada
- Cache inteligente (assets versionados com 1 ano, HTML sem cache)
- Health check endpoint

### docker-entrypoint.sh
- Permite injetar a URL da API em tempo de execução
- Suporta variável de ambiente `VITE_API_BASE_URL`

### docker-compose.yml
- Orquestra a execução local com variáveis de ambiente
- Mapeamento de porta 3000 → 80

## 🚀 Como Usar

### 1. Build da Imagem

```bash
# Build padrão
docker build -t zabbixnodes-frontend:latest .

# Build com tag de versão
docker build -t zabbixnodes-frontend:v1.0.0 .
```

### 2. Executar com Docker

#### Usando docker-compose (recomendado)
```bash
docker-compose up -d
```

Acesse em: `http://localhost:3000`

#### Usando docker run
```bash
# Com URL padrão (http://142.93.116.237:8001/api/v1)
docker run -d -p 3000:80 \
  --name zabbixnodes-frontend \
  zabbixnodes-frontend:latest

# Com URL customizada
docker run -d -p 3000:80 \
  -e VITE_API_BASE_URL="http://seu-api-url:8001/api/v1" \
  --name zabbixnodes-frontend \
  zabbixnodes-frontend:latest

# Ambiente de desenvolvimento
docker run -d -p 3000:80 \
  -e VITE_API_BASE_URL="http://localhost:8001/api/v1" \
  --name zabbixnodes-frontend \
  zabbixnodes-frontend:latest
```

### 3. Verificar Logs

```bash
# Com docker-compose
docker-compose logs -f frontend

# Com docker run
docker logs -f zabbixnodes-frontend
```

### 4. Parar o Container

```bash
# Com docker-compose
docker-compose down

# Com docker run
docker stop zabbixnodes-frontend
docker rm zabbixnodes-frontend
```

## 🔧 Variáveis de Ambiente

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `VITE_API_BASE_URL` | `http://142.93.116.237:8001/api/v1` | URL base da API |

### Exemplos de Uso

**Produção (Brasil)**:
```bash
VITE_API_BASE_URL=http://142.93.116.237:8001/api/v1
```

**Staging**:
```bash
VITE_API_BASE_URL=http://staging-api.example.com/api/v1
```

**Desenvolvimento Local**:
```bash
VITE_API_BASE_URL=http://localhost:8001/api/v1
```

## 📊 Tamanho da Imagem

```
Comparação:
- node:22-alpine (builder):    400MB
- nginx:alpine (final):        ~50MB
- Imagem final zabbixnodes:   ~60-70MB
```

## 🏥 Health Check

O container inclui um health check automático:

```bash
# Verificar status
docker inspect --format='{{.State.Health.Status}}' zabbixnodes-frontend

# Teste manual
curl http://localhost:3000/health
# Resposta: OK
```

## 🔍 Troubleshooting

### Erro: "Cannot GET /"
- Verifique se o container está rodando: `docker ps`
- Confirme a porta mapeada: `docker port zabbixnodes-frontend`

### API retorna erro de CORS
- Verifique se `VITE_API_BASE_URL` está correto
- Confirme que a API está acessível do container

### Container não inicia
```bash
# Ver logs de erro
docker logs zabbixnodes-frontend

# Verificar configuração
docker inspect zabbixnodes-frontend
```

### Performance lenta
- Aumente recursos: `--memory 512m --cpus 0.5`
- Verifique gzip comprimindo: `curl -H "Accept-Encoding: gzip" -I http://localhost:3000`

## 📦 Pushing para Registry

### Docker Hub
```bash
docker tag zabbixnodes-frontend:latest seu-usuario/zabbixnodes-frontend:latest
docker push seu-usuario/zabbixnodes-frontend:latest
```

### Registry Privado
```bash
docker tag zabbixnodes-frontend:latest registry.example.com/zabbixnodes-frontend:v1.0.0
docker push registry.example.com/zabbixnodes-frontend:v1.0.0
```

## 📝 Ambiente de Build

O projeto usa as seguintes variáveis durante o build:

- `.env.production` - Variáveis padrão para produção
- `.env.local` - Variáveis locais (não commitar)
- `.env.example` - Template de variáveis

**Nota**: As variáveis do Vite são substituídas durante o build, não em runtime (exceto via script de entrypoint).

## 🚢 Deploy em Produção

### Kubernetes (exemplo)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zabbixnodes-frontend
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: frontend
        image: zabbixnodes-frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: VITE_API_BASE_URL
          value: "http://142.93.116.237:8001/api/v1"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 30
```

### Docker Swarm
```bash
docker service create \
  --name zabbixnodes-frontend \
  -p 3000:80 \
  -e VITE_API_BASE_URL="http://142.93.116.237:8001/api/v1" \
  zabbixnodes-frontend:latest
```

## ❓ Dúvidas Frequentes

**P: Posso mudar a URL da API sem rebuild?**
R: Sim! Use a variável `VITE_API_BASE_URL` ao executar o container.

**P: Como atualizar para uma nova versão?**
R: Faça rebuild (`docker build`) e reinicie com `docker-compose up -d`.

**P: Preciso de HTTPS?**
R: Configure um reverse proxy (nginx/traefik) na frente do container.

**P: Como escalar para múltiplas instâncias?**
R: Use Docker Compose com múltiplos serviços ou Kubernetes com replicas.
