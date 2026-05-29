<?php
namespace Neplatic\Http\Controllers\Api;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Neplatic\Models\Database;

class DashboardController
{
    public function getKPIs(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $sql = "SELECT * FROM neplatic.v_dashboard_gerencial";
        $kpis = $db->fetchOne($sql);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $kpis
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getEvolucion(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $sql = "SELECT * FROM neplatic.v_evolucion_morosidad ORDER BY mes DESC LIMIT 12";
        $evolucion = $db->fetchAll($sql);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $evolucion
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
    
    public function getTopDeudores(Request $request, Response $response): Response
    {
        $db = Database::getInstance();
        $params = $request->getQueryParams();
        $limit = min(50, (int)($params['limit'] ?? 10));
        
        $sql = "SELECT * FROM neplatic.v_top_deudores WHERE ranking <= :limit ORDER BY ranking";
        $deudores = $db->fetchAll($sql, ['limit' => $limit]);
        
        $response->getBody()->write(json_encode([
            'success' => true,
            'data' => $deudores
        ]));
        return $response->withHeader('Content-Type', 'application/json');
    }
}