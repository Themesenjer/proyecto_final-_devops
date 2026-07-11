FROM nginx:1.25-alpine

# Eliminar los archivos por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar el código fuente estático del frontend al contenedor
COPY index.html /usr/share/nginx/html/
COPY styles.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/

# Exponer el puerto 80 estándar de Nginx
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]