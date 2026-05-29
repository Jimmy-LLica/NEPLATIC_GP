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
                    r.comentario,
                    COALESCE(
                        (SELECT json_agg(
                            json_build_object(
                                'orden', rd2.orden_visita,
                                'id_deuda', d2.id_deuda,
                                'monto_pendiente', d2.saldo_pendiente,
                                'id_estado_cobranza', d2.id_estado_cobranza,
                                'estado_cobranza', ec2.nombre,
                                'color_estado', ec2.color_hex,
                                'id_lote', l2.id_lote,
                                'codigo_lote', l2.codigo,
                                'direccion', l2.direccion,
                                'latitud', l2.latitud,
                                'longitud', l2.longitud,
                                'nombres_contribuyente', c2.nombres,
                                'apellidos_contribuyente', 
                                    COALESCE(c2.apellido_paterno, '') || ' ' || COALESCE(c2.apellido_materno, ''),
                                'fue_visitado', rd2.visitado,
                                'resultado_notificacion', en2.nombre,
                                'fecha_notificacion', n2.fecha_notificacion
                            )
                            ORDER BY rd2.orden_visita
                        ), '[]'::json)
                    , '[]'::json) as deudas
                FROM neplatic.ruta_notificacion r
                LEFT JOIN neplatic.ruta_detalle rd2 ON r.id_ruta = rd2.id_ruta
                LEFT JOIN neplatic.deuda d2 ON rd2.id_deuda = d2.id_deuda
                LEFT JOIN neplatic.estado_cobranza ec2 ON d2.id_estado_cobranza = ec2.id_estado
                LEFT JOIN neplatic.lote l2 ON d2.id_lote = l2.id_lote
                LEFT JOIN neplatic.contribuyente c2 ON d2.id_contribuyente = c2.id_contribuyente
                LEFT JOIN neplatic.notificacion n2 ON rd2.id_notificacion = n2.id_notificacion
                LEFT JOIN neplatic.estado_notificacion en2 ON n2.id_estado_notif = en2.id_estado_notif
                WHERE r.id_usuario = :usuario_id AND r.fecha_ruta = :fecha
                GROUP BY r.id_ruta, r.fecha_ruta, r.estado_ruta, r.total_deudas, 
                         r.deudas_atendidas, r.deudas_efectivas, r.distancia_estimada_km,
                         r.hora_inicio, r.hora_fin, r.comentario";
        
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