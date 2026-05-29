<?php

use Slim\Routing\RouteCollectorProxy;
use Neplatic\Http\Middleware\AuthMiddleware;

return function ($app) {
    
    // Rutas públicas
    $app->post('/api/login', [Neplatic\Http\Controllers\Api\AuthController::class, 'login']);
    
    // Rutas protegidas
    $app->group('/api', function (RouteCollectorProxy $group) {
        
        // Auth
        $group->get('/me', [Neplatic\Http\Controllers\Api\AuthController::class, 'me']);
        
        // Dashboard
        $group->get('/dashboard/kpis', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getKPIs']);
        $group->get('/dashboard/evolucion', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getEvolucion']);
        $group->get('/dashboard/top-deudores', [Neplatic\Http\Controllers\Api\DashboardController::class, 'getTopDeudores']);
        
        // Mapa
        $group->get('/mapa/sectores', [Neplatic\Http\Controllers\Api\MapaController::class, 'getSectores']);
        $group->get('/mapa/manzanas', [Neplatic\Http\Controllers\Api\MapaController::class, 'getManzanas']);
        $group->get('/mapa/lotes', [Neplatic\Http\Controllers\Api\MapaController::class, 'getLotes']);
        $group->get('/mapa/heatmap', [Neplatic\Http\Controllers\Api\MapaController::class, 'getHeatmapData']);
        
        // Rutas (solo lectura para notificadores)
        $group->get('/rutas/mis-rutas', [Neplatic\Http\Controllers\Api\RutaController::class, 'getMisRutas']);
        $group->get('/rutas/futuras', [Neplatic\Http\Controllers\Api\RutaController::class, 'getRutasFuturas']);
        
    })->add(new AuthMiddleware());
};