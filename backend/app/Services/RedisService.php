<?php
namespace Neplatic\Services;

use Predis\Client;

class RedisService
{
    private static $instance = null;
    private $client;
    
    private function __construct()
    {
        $this->client = new Client([
            'scheme' => 'tcp',
            'host'   => $_ENV['REDIS_HOST'],
            'port'   => (int)$_ENV['REDIS_PORT'],
            'password' => $_ENV['REDIS_PASSWORD'] ?: null,
        ], [
            'parameters' => [
                'read_write_timeout' => -1,   // ← AQUÍ está el cambio
            ]
        ]);
    }
    
    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new RedisService();
        }
        return self::$instance;
    }
    
    public function getClient()
    {
        return $this->client;
    }
    
    public function publish($channel, $event)
    {
        $data = json_encode($event);
        return $this->client->publish($channel, $data);
    }
    
    public function set($key, $value, $ttl = 3600)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $this->client->setex($fullKey, $ttl, json_encode($value));
    }
    
    public function get($key)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $data = $this->client->get($fullKey);
        return $data ? json_decode($data, true) : null;
    }
    
    public function delete($key)
    {
        $fullKey = $_ENV['REDIS_PREFIX'] . $key;
        $this->client->del([$fullKey]);
    }
    
    public function deleteByPattern($pattern)
    {
        $fullPattern = $_ENV['REDIS_PREFIX'] . $pattern;
        $keys = $this->client->keys($fullPattern);
        if (!empty($keys)) {
            $this->client->del($keys);
        }
    }
}