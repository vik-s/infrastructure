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
  'instanceid' => 'oc7aklgzcr2c',                                 
  'passwordsalt' => 'RuedhZsHowTadiIbmdDUb1MGKBNMlm',             
  'secret' => 'VtIIclZA4c/AbujUNRiLpid8AzFzew9GWk1WpOhebOHeWAGm', 
  'trusted_domains' =>                                            
  array (                                                         
    0 => 'cloud.iyer.app',                                        
    1 => '192.168.1.61',                                          
  ),                                                              
  'dbtype' => 'pgsql',                                            
  'version' => '23.0.0.10',                                       
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
  'updater.secret' => '$2y$10$AwlMl97QDe6W0uyb24MJYOwsiHFWuX9YSBS7
);
