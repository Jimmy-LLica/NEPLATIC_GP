<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;
use Neplatic\Utils\JwtHelper;

class AuthController
{
    public function login(Request $request, Response $response): Response
    {
        $data = json_decode($request->getBody()->getContents(), true);
        $username = $data['username'] ?? '';
        $password = $data['password'] ?? '';
        
        if (empty($username) || empty($password)) {
            return $this->jsonError($response, 'Usuario y contraseña son requeridos', 400);
        }
        
        $db = Database::getInstance();
        
        $sql = "SELECT u.id_usuario, u.username, u.password_hash, u.nombres, u.apellidos, 
                       u.id_rol, r.codigo as rol_codigo, r.nombre as rol_nombre,
                       u.activo, u.bloqueado
                FROM neplatic.usuario u
                JOIN neplatic.rol_usuario r ON u.id_rol = r.id_rol
                WHERE u.username = :username";
        
        $user = $db->fetchOne($sql, ['username' => $username]);
        
        if (!$user) {
            return $this->jsonError($response, 'Usuario no existe', 401);
        }
        
        if (!$user['activo']) {
            return $this->jsonError($response, 'Usuario inactivo', 401);
        }
        
        if ($user['bloqueado']) {
            return $this->jsonError($response, 'Usuario bloqueado', 401);
        }
        
        if (!password_verify($password, $user['password_hash'])) {
            return $this->jsonError($response, 'Contraseña incorrecta', 401);
        }
        
        $tokenData = [
            'id_usuario' => $user['id_usuario'],
            'username' => $user['username'],
            'nombres' => $user['nombres'],
            'apellidos' => $user['apellidos'],
            'id_rol' => $user['id_rol'],
            'rol_codigo' => $user['rol_codigo']
        ];
        
        $token = JwtHelper::encode($tokenData);
        
        $result = [
            'success' => true,
            'token' => $token,
            'usuario' => [
                'id' => $user['id_usuario'],
                'username' => $user['username'],
                'nombres' => $user['nombres'],
                'apellidos' => $user['apellidos'],
                'rol' => $user['rol_codigo'],
                'rol_nombre' => $user['rol_nombre']
            ]
        ];
        
        $response->getBody()->write(json_encode($result));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function me(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'usuario' => $usuario
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    private function jsonError(Response $response, string $message, int $code): Response
    {
        $response->getBody()->write(json_encode(['error' => $message]));
        return $response->withStatus($code)->withHeader('Content-Type', 'application/json');
    }
}