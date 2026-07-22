FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY en /usr/share/nginx/html/en
COPY assets /usr/share/nginx/html/assets
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
