<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;
use Neplatic\Services\RedisService;

class RutaController
{
    public function getMisRutas(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        $params = $request->getQueryParams();
        $fecha = $params['fecha'] ?? date('Y-m-d');
        
        // Solo usuarios con rol NORMAL pueden ver rutas
        if ($usuario['rol_codigo'] !== 'NORMAL') {
            $response->getBody()->write(json_encode([
                'success' => false,
                'error' => 'Solo notificadores pueden acceder a sus rutas'
            ]));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        // Intentar obtener de caché Redis
        $redis = RedisService::getInstance();
        $cacheKey = "rutas_usuario_{$usuarioId}_{$fecha}";
        $cachedData = $redis->get($cacheKey);
        
        if ($cachedData) {
            $response->getBody()->write(json_encode([
                'success' => true,
                'data' => $cachedData,
                'cached' => true
            ]));
            return $response->withHeader('Content-Type', 'application/json');
        }
        
        // Consultar base de datos
        $db = Database::getInstance();
        
        $sql = "SELECT * FROM neplatic.v_ruta_asignada 
                WHERE id_usuario = :usuario_id AND fecha_ruta = :fecha";
        
        $ruta = $db->fetchOne($sql, ['usuario_id' => $usuarioId, 'fecha' => $fecha]);
        
        if (!$ruta) {
            $ruta = [
                'id_ruta' => null,
                'fecha_ruta' => $fecha,
                'estado_ruta' => 'SIN_RUTA',
                'total_deudas' => 0,
                'deudas_atendidas' => 0,
                'deudas_efectivas' => 0,
                'distancia_estimada_km' => 0,
                'deudas' => []
            ];
        } else {
            $ruta['deudas'] = json_decode($ruta['deudas'], true);
        }
        
        // Guardar en caché (TTL 1 hora)
        $redis->set($cacheKey, $ruta, 3600);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $ruta,
            'cached' => false
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getRutasFuturas(Request $request, Response $response): Response
    {
        $usuario = $request->getAttribute('usuario');
        $usuarioId = $usuario['id_usuario'];
        
        if ($usuario['rol_codigo'] !== 'NORMAL') {
            $response->getBody()->write(json_encode([
                'success' => false,
                'error' => 'Solo notificadores pueden acceder a sus rutas'
            ]));
            return $response->withStatus(403)->withHeader('Content-Type', 'application/json');
        }
        
        $db = Database::getInstance();
        
        $sql = "SELECT 
                    r.id_ruta,
                    r.fecha_ruta,
                    r.estado_ruta,
                    r.total_deudas,
                    r.deudas_atendidas,
                    r.deudas_efectivas,
                    r.distancia_estimada_km,
                    r.hora_inicio,
                    r.hora_fin,
                    CASE 
                        WHEN r.fecha_ruta = CURRENT_DATE THEN 'HOY'
                        WHEN r.fecha_ruta > CURRENT_DATE THEN 'FUTURA'
                        ELSE 'PASADA'
                    END as tipo
                FROM neplatic.ruta_notificacion r
                WHERE r.id_usuario = :usuario_id 
                AND r.fecha_ruta >= CURRENT_DATE
                AND r.estado_ruta IN ('PLANIFICADA', 'EN_CURSO')
                ORDER BY r.fecha_ruta ASC";
        
        $rutas = $db->fetchAll($sql, ['usuario_id' => $usuarioId]);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $rutas
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}