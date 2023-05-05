<?php
$CONFIG = array (
  'memcache.local' => '\\OC\\Memcache\\APCu',
  'memcache.distributed' => '\\OC\\Memcache\\Redis',
  'memcache.locking' => '\\OC\\Memcache\\Redis',
  'filelocking.enabled' => true,
  'redis' => 
  array (
    'host' => 'redis',
    'port' => 6379,
    'timeout' => 0.0,
  ),
  'datadirectory' => '/data',
  'instanceid' => 'ocpqrcj5j1t8',
  'trusted_domains' => 
  array (
    0 => 'cloud.iyer.app',
    1 => '192.168.1.61',
  ),
  'trusted_proxies' => 
  array (
    0 => '172.24.0.0/16',
  ),
  'dbtype' => 'pgsql',
  'version' => '25.0.5.1',
  'overwrite.cli.url' => 'https://cloud.iyer.app',
  'installed' => true,
  'dbname' => 'nextcloud_db',
  'dbpassword' => 'gILmZ7Q5Ve*qO0DH31jdzFUFaRQ',
  'dbuser' => 'ncadmin',
  'dbhost' => 'postgresql',
  'dbport' => '5432',
  'log_type' => 'file',
  'log_file' => 'nextcloud.log',
  'log_level' => '2',
  'dbtableprefix' => 'oc_',
  'theme' => '',
  'loglevel' => 2,
  'maintenance' => false,
  'secret' => '5WiMeN6VcEqaOBebHglIMpQE0/HJQL1dH8aKxwNScw14ANe7',
  'updater.release.channel' => 'stable',
  'updater.secret' => '$2y$10$3ofRnfDpNq33gi4o0Z.SA.PtFMyCsZmPZ.m5hxTEwVBeo9gzVMGE2',
  'passwordsalt' => 'Nfw5vX/20Fk3HhfQIY8io20Jxw5Wtd',
);
