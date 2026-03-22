#!/bin/sh
echo "<?php \$config['session_storage'] = 'redis'; \$config['redis_hosts'] = ['redis:6379']; ?>" > /var/www/html/config/redis-session.php
echo "include(__DIR__ . '/redis-session.php');" >> /var/www/html/config/config.inc.php
