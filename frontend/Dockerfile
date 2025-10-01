FROM nginx:alpine

# Remover a configuração padrão do Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar os arquivos do frontend
COPY . /usr/share/nginx/html/

# Configuração do Nginx para SPA (Single Page Application)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]