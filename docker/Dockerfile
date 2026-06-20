FROM php:8.1-apache

RUN apt-get update && apt-get install -y \
    libpq-dev \
    libzip-dev \
    unzip \
    git \
    && docker-php-ext-install pdo_pgsql zip

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

COPY ../backend /var/www/html/
COPY ../frontend/dist /var/www/html/

RUN chown -R www-data:www-data /var/www/html

RUN a2enmod rewrite headers

EXPOSE 80