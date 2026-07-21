# 🚀 Guía de Despliegue — NEPLATIC Sistema Web

Guía completa para desplegar el sistema web **NEPLATIC** desde cero en un VPS nuevo con Ubuntu.

---

## 📋 Requisitos Previos

### Lo que necesitas ANTES de empezar:
- **VPS con Ubuntu 22.04+** (mínimo 1 GB RAM, 20 GB disco)
- **Dominio** apuntando a la IP del VPS (ej: `neplatic.online` → `TU_IP_VPS`)
- **Acceso SSH** al VPS (usuario + contraseña o clave SSH)
- **El código fuente** de este proyecto (`NEPLATIC_GP/`) en tu computadora local

### Tecnologías que se instalarán automáticamente:
| Componente | Versión | Rol |
|---|---|---|
| Docker + Docker Compose | Última | Contenedores |
| PHP | 8.1 | Backend API (Slim 4) |
| Apache | 2.4 | Servidor web + Reverse Proxy |
| Node.js | 18+ | Compilar el frontend (Vue 3 + Vite) |
| PostgreSQL/PostGIS | 15+ | Base de datos (en la nube o local) |
| Redis | 7 | Caché + Eventos en tiempo real |
| Certbot | Última | Certificado SSL gratuito (HTTPS) |

---

## 📁 Estructura del Proyecto

```
NEPLATIC_GP/
├── backend/                    # API REST (PHP 8.1 + Slim 4)
│   ├── .env                    # Variables de entorno (BD, Redis, JWT)
│   ├── .htaccess               # Reglas de Apache (SPA + API routing)
│   ├── index.php               # Punto de entrada de la API
│   ├── composer.json           # Dependencias PHP
│   ├── app/
│   │   ├── Http/Controllers/   # Controladores (Auth, Ruta, Dashboard, etc.)
│   │   ├── Models/             # Database.php (conexión PDO)
│   │   ├── Middleware/         # Autenticación JWT
│   │   ├── Services/           # RedisService.php
│   │   └── Utils/              # JwtHelper.php
│   └── routes/api.php          # Definición de endpoints
├── frontend/                   # SPA (Vue 3 + Vite)
│   ├── package.json            # Dependencias JS
│   ├── vite.config.js          # Configuración de Vite
│   ├── index.html              # Punto de entrada HTML
│   └── src/
│       ├── views/              # Vistas (Login, Dashboard, MisRutas, etc.)
│       ├── api/index.js        # Cliente Axios configurado
│       └── router/index.js     # Rutas del SPA
└── docker/
    ├── Dockerfile              # Imagen PHP 8.1 + Apache
    └── docker-compose.yml      # Orquestación de servicios
```

---

## 🔧 PASO 1: Preparar el VPS

Conéctate a tu VPS nuevo por SSH:
```bash
ssh usuario@TU_IP_VPS
```

### 1.1 Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Instalar Docker y Docker Compose
```bash
# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh

# Agregar tu usuario al grupo docker (para no usar sudo)
sudo usermod -aG docker $USER

# Cerrar sesión y volver a conectarse para que tome efecto
exit
```
Vuelve a conectarte por SSH y verifica:
```bash
docker --version
docker compose version
```

### 1.3 Instalar Node.js (para compilar el frontend)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # Debe mostrar v18.x o superior
npm --version
```

### 1.4 Instalar Apache (Reverse Proxy principal)
```bash
sudo apt install -y apache2
sudo a2enmod proxy proxy_http proxy_wstunnel ssl rewrite headers
sudo systemctl enable apache2
```

### 1.5 Instalar Certbot (SSL gratuito con Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-apache
```

---

## 🗄️ PASO 2: Configurar la Base de Datos

> **IMPORTANTE:** Si ya tienes PostgreSQL en la nube (otro servidor), salta al paso 2.2.
> Si necesitas instalar PostgreSQL localmente en el mismo VPS, sigue el paso 2.1.

### 2.1 (OPCIONAL) Instalar PostgreSQL localmente en el VPS
```bash
sudo apt install -y postgresql postgresql-contrib postgis

# Entrar a PostgreSQL
sudo -u postgres psql

# Crear la base de datos y el usuario
CREATE DATABASE neplatic;
CREATE USER neplatic_app WITH ENCRYPTED PASSWORD 'Upt2026';
GRANT ALL PRIVILEGES ON DATABASE neplatic TO neplatic_app;

# Habilitar PostGIS
\c neplatic
CREATE EXTENSION postgis;

# Crear el schema
CREATE SCHEMA neplatic AUTHORIZATION neplatic_app;
ALTER ROLE neplatic_app SET search_path TO neplatic, public;

\q
```

Editar `pg_hba.conf` para permitir conexiones desde Docker:
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```
Agregar esta línea al final:
```
host    neplatic    neplatic_app    172.16.0.0/12    md5
```
Y en `postgresql.conf`, permitir escuchar en todas las interfaces:
```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
```
Descomentar/cambiar:
```
listen_addresses = '*'
```
Reiniciar PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 2.2 Restaurar los datos
Si tienes un backup SQL de tu base de datos anterior:
```bash
psql -h TU_HOST_DB -U neplatic_app -d neplatic < backup_neplatic.sql
```

> **💡 Tip:** Antes de cancelar tu VPS actual, exporta tu base de datos:
> ```bash
> pg_dump -h 178.238.228.92 -U neplatic_app -d neplatic > backup_neplatic.sql
> ```

---

## 📦 PASO 3: Subir el Código al VPS

Desde tu **computadora local** (PowerShell), sube todo el proyecto:
```powershell
scp -r C:\Users\Usuario\Desktop\NEPLATIC_GP usuario@TU_IP_VPS:~/NEPLATIC_GP-web
```

> **Nota:** Si usas un puerto SSH distinto al 22, agrega `-P PUERTO` (ej: `scp -P 12453 -r ...`)

---

## ⚙️ PASO 4: Configurar Variables de Entorno

### 4.1 Editar el archivo `.env` del backend
```bash
nano ~/NEPLATIC_GP-web/backend/.env
```

Actualiza con los datos de tu **nuevo VPS**:
```env
# PostgreSQL
DB_HOST=TU_IP_BASE_DE_DATOS      # Si es local: 172.17.0.1 (IP del host Docker)
DB_PORT=5432
DB_NAME=neplatic
DB_USER=neplatic_app
DB_PASS=Upt2026
DB_SCHEMA=neplatic

# Redis (se conecta al contenedor Docker interno)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=Upt2026
REDIS_PREFIX=neplatic:

# Canales de eventos
REDIS_CHANNEL_RUTAS=neplatic.rutas

# JWT (cambia el secreto por uno propio en producción)
JWT_SECRET=TuClaveSecretaAquiCambialaPorFavor2026
JWT_EXPIRES=86400

# CORS
ALLOWED_ORIGINS=https://TU_DOMINIO.com
```

### 4.2 Editar `docker-compose.yml`
```bash
nano ~/NEPLATIC_GP-web/docker/docker-compose.yml
```

Actualiza las variables de entorno con los datos correctos:
```yaml
services:
  web:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: neplatic-web
    restart: always                      # <-- Auto-arranque tras reinicios
    ports:
      - "8085:80"
      - "8443:443"
    environment:
      - DB_HOST=TU_IP_BASE_DE_DATOS     # Si es local: 172.17.0.1
      - DB_PORT=5432
      - DB_NAME=neplatic
      - DB_USER=neplatic_app            # <-- IMPORTANTE: usar neplatic_app, NO readonly
      - DB_PASS=Upt2026
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    networks:
      - neplatic-network

  redis:
    image: redis:7-alpine
    container_name: neplatic-redis
    restart: always                      # <-- Auto-arranque tras reinicios
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --requirepass Upt2026
    networks:
      - neplatic-network

networks:
  neplatic-network:
    driver: bridge
```

> ⚠️ **CUIDADO:** El `DB_USER` DEBE ser `neplatic_app` (con permisos de escritura), **NO** `neplatic_readonly`.

---

## 🏗️ PASO 5: Compilar el Frontend

El frontend (Vue 3) necesita ser compilado antes de construir Docker:

```bash
cd ~/NEPLATIC_GP-web/frontend

# Instalar dependencias
npm install

# Compilar para producción (genera la carpeta dist/)
npm run build
```

Verifica que se haya creado la carpeta `dist/`:
```bash
ls dist/
# Debes ver: index.html, assets/ (con archivos .js y .css)
```

---

## 🐳 PASO 6: Construir y Levantar Docker

```bash
cd ~/NEPLATIC_GP-web/docker

# Construir la imagen (descarga PHP, copia archivos, instala dependencias)
docker compose build web --no-cache

# Levantar todos los servicios (web + Redis)
docker compose up -d

# Verificar que están corriendo
docker compose ps
```

Debes ver algo como:
```
NAME             STATUS          PORTS
neplatic-redis   Up              0.0.0.0:6379->6379/tcp
neplatic-web     Up              0.0.0.0:8085->80/tcp, 0.0.0.0:8443->443/tcp
```

### Verificar que la API responde:
```bash
curl http://localhost:8085/api
```
Debe devolver:
```json
{"name":"Neplatic Web API","version":"2.0.0","status":"running"}
```

---

## 🌐 PASO 7: Configurar Apache como Reverse Proxy

Apache actúa como la "puerta principal" que recibe las peticiones HTTPS del dominio y las redirige al contenedor Docker.

### 7.1 Crear el VirtualHost
```bash
sudo nano /etc/apache2/sites-available/neplatic.conf
```

Pega este contenido (cambia `TU_DOMINIO` por tu dominio real):
```apache
<VirtualHost *:80>
    ServerName TU_DOMINIO.com
    
    # Redirigir todo HTTP a HTTPS
    RewriteEngine On
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName TU_DOMINIO.com
    
    SSLEngine on
    SSLProxyEngine on
    
    # Los certificados se configurarán con Certbot (paso 8)
    # SSLCertificateFile    /etc/letsencrypt/live/TU_DOMINIO.com/fullchain.pem
    # SSLCertificateKeyFile /etc/letsencrypt/live/TU_DOMINIO.com/privkey.pem

    # Proxy hacia el contenedor Docker
    ProxyPreserveHost On
    ProxyPass / https://localhost:8443/
    ProxyPassReverse / https://localhost:8443/
    
    # Cabeceras de seguridad
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-Port "443"
    
    # Desactivar verificación SSL del backend (usa certificado auto-firmado)
    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off
</VirtualHost>
```

### 7.2 Activar el sitio
```bash
sudo a2ensite neplatic.conf
sudo a2dissite 000-default.conf    # Desactivar el sitio por defecto
sudo systemctl reload apache2
```

---

## 🔒 PASO 8: Obtener Certificado SSL (HTTPS gratuito)

> **Requisito:** Tu dominio ya debe estar apuntando a la IP del VPS (registro DNS tipo A).

```bash
sudo certbot --apache -d TU_DOMINIO.com
```

Certbot te pedirá tu correo electrónico y aceptar los términos. Después configurará automáticamente el SSL en tu VirtualHost.

Verifica que la renovación automática funciona:
```bash
sudo certbot renew --dry-run
```

---

## ✅ PASO 9: Verificación Final

### 9.1 Verificar desde el navegador
1. Abre `https://TU_DOMINIO.com` → Debe cargar la pantalla de Login.
2. Inicia sesión con un usuario válido.
3. Navega por Dashboard, Mis Rutas, Monitoreo, Mapa de Morosidad.
4. Prueba registrar una visita de notificación.

### 9.2 Verificar desde la terminal
```bash
# Estado de los contenedores
docker compose -f ~/NEPLATIC_GP-web/docker/docker-compose.yml ps

# Logs en tiempo real (Ctrl+C para salir)
docker compose -f ~/NEPLATIC_GP-web/docker/docker-compose.yml logs -f web

# Probar conexión a la BD desde el contenedor
docker exec neplatic-web php -r "
\$pdo = new PDO('pgsql:host=TU_IP_BD;port=5432;dbname=neplatic', 'neplatic_app', 'Upt2026');
echo 'Conexión a BD: OK';
"

# Probar Redis
docker exec neplatic-redis redis-cli -a Upt2026 PING
# Debe devolver: PONG
```

---

## 🔄 Comandos de Mantenimiento

### Actualizar código después de hacer cambios:
```bash
cd ~/NEPLATIC_GP-web

# 1. Recompilar frontend (si cambiaste archivos .vue o .js)
cd frontend && npm run build && cd ..

# 2. Reconstruir y reiniciar Docker
cd docker
docker compose build web --no-cache
docker compose up -d
```

### Actualizar SOLO el backend (sin recompilar frontend):
```bash
# Copiar el archivo modificado directamente al contenedor
docker cp ~/NEPLATIC_GP-web/backend/app/Http/Controllers/Api/RutaController.php \
  neplatic-web:/var/www/html/app/Http/Controllers/Api/RutaController.php

# Recargar Apache sin downtime
docker exec neplatic-web apachectl graceful
```

### Limpiar caché de Redis:
```bash
docker exec neplatic-redis redis-cli -a Upt2026 FLUSHALL
```

### Ver logs de errores:
```bash
docker compose -f ~/NEPLATIC_GP-web/docker/docker-compose.yml logs web --tail 50
```

### Reiniciar todo el sistema:
```bash
cd ~/NEPLATIC_GP-web/docker
docker compose down
docker compose up -d
```

### Backup de la base de datos:
```bash
pg_dump -h TU_IP_BD -U neplatic_app -d neplatic > ~/backup_neplatic_$(date +%Y%m%d).sql
```

### Restaurar un backup:
```bash
psql -h TU_IP_BD -U neplatic_app -d neplatic < ~/backup_neplatic_20260720.sql
```

---

## ⚠️ Errores Comunes y Soluciones

| Error | Causa | Solución |
|---|---|---|
| `503 Service Unavailable` | Contenedor Docker apagado | `cd ~/NEPLATIC_GP-web/docker && docker compose up -d` |
| `ERR_CONNECTION_REFUSED` | Apache apagado | `sudo systemctl start apache2` |
| `Port already allocated` | Puerto ocupado por proceso fantasma | `sudo kill -9 $(sudo lsof -t -i :8443)` luego `docker compose up -d` |
| `Hubo un error al guardar` | Columnas de BD no coinciden con el código | Verificar que el backend usa los nombres exactos de columna |
| `NOAUTH Authentication required` (Redis) | Falta contraseña de Redis | Agregar `-a Upt2026` al comando redis-cli |
| El frontend no se actualiza | Caché del navegador | `Ctrl + F5` o abrir en modo incógnito |
| Cambios en .vue no se reflejan | Frontend no recompilado | `cd frontend && npm run build` luego rebuild Docker |

---

## 🔑 Credenciales por Defecto

> ⚠️ **Cambia todas las contraseñas en producción.**

| Servicio | Usuario | Contraseña |
|---|---|---|
| PostgreSQL | `neplatic_app` | `Upt2026` |
| Redis | — | `Upt2026` |
| JWT Secret | — | `Neplatic2026SecureKey...` |

---

## 📊 Resumen de Puertos

| Puerto | Servicio | Descripción |
|---|---|---|
| 22 (o custom) | SSH | Acceso remoto al VPS |
| 80 | Apache | HTTP (redirige a 443) |
| 443 | Apache + SSL | HTTPS (punto de entrada público) |
| 5432 | PostgreSQL | Base de datos |
| 6379 | Redis | Caché y eventos |
| 8085 | Docker (HTTP) | Contenedor web interno |
| 8443 | Docker (HTTPS) | Contenedor web interno (SSL) |

---

*Última actualización: Julio 2026*
*Versión del Sistema: 2.0.0*
*Arquitectura: Event-Driven Architecture (EDA)*
