# Estágio 1: Build (se você tivesse um passo de build, como em React/Vue)
# FROM node:18-alpine as builder
# WORKDIR /app
# COPY package.json yarn.lock ./
# RUN yarn install
# COPY . .
# RUN yarn build

# Estágio 2: Servir os arquivos estáticos com Nginx
FROM nginx:stable-alpine

# Copia os arquivos estáticos do seu frontend
# Se você tivesse um estágio de build, a linha seria:
# COPY --from=builder /app/build /usr/share/nginx/html
COPY . /usr/share/nginx/html

# Copia uma configuração customizada do Nginx, se necessário
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta 80 (padrão do Nginx)
EXPOSE 80

# Comando para iniciar o Nginx em primeiro plano
CMD ["nginx", "-g", "daemon off;"]
