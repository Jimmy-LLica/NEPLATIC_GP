-- ================================================================
-- Vista para centralizar la consulta de las rutas y sus deudas
-- Ejecutar en la base de datos "neplatic"
-- ================================================================

CREATE OR REPLACE VIEW neplatic.v_ruta_asignada AS
SELECT 
    r.id_usuario,
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
        )
        FROM neplatic.ruta_detalle rd2 
        LEFT JOIN neplatic.deuda d2 ON rd2.id_deuda = d2.id_deuda
        LEFT JOIN neplatic.estado_cobranza ec2 ON d2.id_estado_cobranza = ec2.id_estado
        LEFT JOIN neplatic.lote l2 ON d2.id_lote = l2.id_lote
        LEFT JOIN neplatic.contribuyente c2 ON d2.id_contribuyente = c2.id_contribuyente
        LEFT JOIN neplatic.notificacion n2 ON rd2.id_notificacion = n2.id_notificacion
        LEFT JOIN neplatic.estado_notificacion en2 ON n2.id_estado_notif = en2.id_estado_notif
        WHERE rd2.id_ruta = r.id_ruta), '[]'::json) as deudas
FROM neplatic.ruta_notificacion r;

COMMENT ON VIEW neplatic.v_ruta_asignada IS 'Vista que consolida la ruta de notificación con sus deudas en formato JSON';
