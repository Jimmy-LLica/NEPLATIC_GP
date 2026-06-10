<?php
namespace Neplatic\Models;

use PDO;
use PDOException;

class Database
{
    private static $instance = null;
    private $connection;
    
    private function __construct()
    {
        $host = $_ENV['DB_HOST'];
        $port = $_ENV['DB_PORT'];
        $dbname = $_ENV['DB_NAME'];
        $user = $_ENV['DB_USER'];
        $pass = $_ENV['DB_PASS'];
        $schema = $_ENV['DB_SCHEMA'];
        
        try {
            $dsn = "pgsql:host=$host;port=$port;dbname=$dbname";
            $options = [
                PDO::ATTR_PERSISTENT => true,
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ];
            $this->connection = new PDO($dsn, $user, $pass, $options);
            $this->connection->exec("SET search_path TO $schema, public");
        } catch (PDOException $e) {
            throw new \Exception("Error de conexión PostgreSQL: " . $e->getMessage());
        }
    }
    
    public static function getInstance()
    {
        if (self::$instance === null) {
            self::$instance = new Database();
        }
        return self::$instance;
    }
    
    public function getConnection()
    {
        return $this->connection;
    }
    
    public function query($sql, $params = [])
    {
        $stmt = $this->connection->prepare($sql);
        $stmt->execute($params);
        return $stmt;
    }
    
    public function fetchAll($sql, $params = [])
    {
        return $this->query($sql, $params)->fetchAll(PDO::FETCH_ASSOC);
    }
    
    public function fetchOne($sql, $params = [])
    {
        return $this->query($sql, $params)->fetch(PDO::FETCH_ASSOC);
    }
}