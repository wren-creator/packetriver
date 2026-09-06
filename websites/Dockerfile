# websites: the vulnerable Main Street storefronts (Apache + PHP 8). Phase 1
# ships one, the General Store, behind its login portal. Later phases add the
# other seven plus Town Hall, Police, and Fire as extra vhosts in this image.
FROM php:8.2-apache

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl default-mysql-client \
 && rm -rf /var/lib/apt/lists/*

RUN docker-php-ext-install pdo_mysql && a2enmod headers

COPY php/packetriver.ini    /usr/local/etc/php/conf.d/packetriver.ini
COPY apache/000-default.conf /etc/apache2/sites-available/000-default.conf
COPY site/ /var/www/generalstore/

RUN chown -R www-data:www-data /var/www/generalstore

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["apache2-foreground"]
