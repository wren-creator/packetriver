# websites: the vulnerable Main Street storefronts (Apache + PHP 8). One
# container, one docroot, one subdirectory per shop (/generalstore/, /hardware/
# ...), each its own MariaDB schema. Later phases add Town Hall / Police / Fire
# here too.
FROM php:8.2-apache

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl default-mysql-client git \
 && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-install pdo_mysql && a2enmod headers rewrite

COPY php/packetriver.ini    /usr/local/etc/php/conf.d/packetriver.ini
COPY apache/000-default.conf /etc/apache2/sites-available/000-default.conf
COPY site/ /var/www/site/

RUN chown -R www-data:www-data /var/www/site

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["apache2-foreground"]
