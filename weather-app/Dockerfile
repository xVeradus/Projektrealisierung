FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build -- --configuration=production

FROM nginx:alpine

COPY --from=build /app/dist/angular19-primeng19-tailwind4/browser /usr/share/nginx/html

RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    \
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always; \
    add_header Cross-Origin-Opener-Policy "same-origin" always; \
    add_header X-Frame-Options "SAMEORIGIN" always; \
    add_header X-Content-Type-Options "nosniff" always; \
    add_header Referrer-Policy "strict-origin-when-cross-origin" always; \
    add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\''; style-src '\''self'\'' '\''unsafe-inline'\''; connect-src '\''self'\'' http://localhost:8000 http://127.0.0.1:8000; img-src '\''self'\'' data: https://*.basemaps.cartocdn.com https://*.openstreetmap.org https://tile.openstreetmap.org; font-src '\''self'\'' data:;" always; \

    \
    location / { \
    try_files $uri $uri/ /index.html; \
    } \
    \
    location ~* \.(?:ico|css|js|gif|jpe?g|png|woff2?|webp)$ { \
    expires 1y; \
    add_header Cache-Control "public, immutable"; \
    access_log off; \
    } \
    }' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
