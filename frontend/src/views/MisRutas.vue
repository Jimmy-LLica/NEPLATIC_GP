<template>
  <div class="rutas-container">
    <h1>Mis Rutas de Notificación</h1>
    
    <div class="fecha-selector">
      <label>Fecha:</label>
      <input type="date" v-model="fecha" @change="cargarRuta" />
    </div>
    
    <div v-if="loading" class="loading">Cargando...</div>
    
    <div v-else-if="ruta && ruta.estado_ruta !== 'SIN_RUTA'" class="ruta-card">
      <div class="ruta-header">
        <h2>Ruta del {{ formatFecha(ruta.fecha_ruta) }}</h2>
        <span :class="['estado', ruta.estado_ruta.toLowerCase()]">{{ ruta.estado_ruta }}</span>
      </div>
      
      <div class="ruta-stats">
        <div class="stat">
          <span class="label">Total Deudas:</span>
          <span class="value">{{ ruta.total_deudas }}</span>
        </div>
        <div class="stat">
          <span class="label">Atendidas:</span>
          <span class="value">{{ ruta.deudas_atendidas }}</span>
        </div>
        <div class="stat">
          <span class="label">Efectivas:</span>
          <span class="value">{{ ruta.deudas_efectivas }}</span>
        </div>
        <div class="stat">
          <span class="label">Distancia estimada:</span>
          <span class="value">{{ ruta.distancia_estimada_km }} km</span>
        </div>
      </div>
      
      <div class="deudas-list">
        <h3>Deudas a notificar</h3>
        <div v-for="deuda in ruta.deudas" :key="deuda.id_deuda" class="deuda-item">
          <div class="deuda-orden">{{ deuda.orden }}</div>
          <div class="deuda-info">
            <div class="contribuyente">{{ deuda.nombres_contribuyente }} {{ deuda.apellidos_contribuyente }}</div>
            <div class="direccion">{{ deuda.direccion }}</div>
            <div class="monto">Monto: S/ {{ formatNumber(deuda.monto_pendiente) }}</div>
          </div>
          <div :class="['estado-badge', deuda.estado_cobranza.toLowerCase()]">
            {{ deuda.estado_cobranza }}
          </div>
          <div v-if="deuda.fue_visitado" class="visitado-badge">
            ✅ {{ deuda.resultado_notificacion || 'Visitado' }}
          </div>
        </div>
      </div>
    </div>
    
    <div v-else class="sin-ruta">
      <p>No tienes ruta asignada para la fecha seleccionada</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const loading = ref(false)
const ruta = ref(null)
const fecha = ref(new Date().toISOString().split('T')[0])

const formatNumber = (num) => {
  return num?.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

const formatFecha = (fechaStr) => {
  return new Date(fechaStr).toLocaleDateString('es-PE')
}

const cargarRuta = async () => {
  loading.value = true
  try {
    const response = await api.get(`/rutas/mis-rutas?fecha=${fecha.value}`)
    ruta.value = response.data.data
  } catch (error) {
    console.error('Error cargando ruta:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  cargarRuta()
})
</script>

<style scoped>
.rutas-container h1 {
  margin-bottom: 1.5rem;
  color: #1a472a;
}
.fecha-selector {
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.fecha-selector label {
  font-weight: bold;
}
.fecha-selector input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 5px;
}
.ruta-card {
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}
.ruta-header {
  background: #1a472a;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ruta-header .estado {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: bold;
}
.estado.planificada { background: #ffc107; color: #333; }
.estado.en_curso { background: #17a2b8; color: white; }
.estado.completada { background: #28a745; color: white; }
.ruta-stats {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}
.stat .label {
  font-size: 0.8rem;
  color: #666;
}
.stat .value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #1a472a;
}
.deudas-list {
  padding: 1rem;
}
.deudas-list h3 {
  margin-bottom: 1rem;
  color: #333;
}
.deuda-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #eee;
}
.deuda-orden {
  width: 30px;
  height: 30px;
  background: #1a472a;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}
.deuda-info {
  flex: 1;
}
.contribuyente {
  font-weight: bold;
  color: #333;
}
.direccion {
  font-size: 0.8rem;
  color: #666;
}
.monto {
  font-size: 0.8rem;
  color: #1a472a;
  font-weight: bold;
}
.estado-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: bold;
}
.estado-badge.coactiva { background: #ff0000; color: white; }
.estado-badge.ordinaria { background: #800020; color: white; }
.estado-badge.sin_proceso { background: #0000ff; color: white; }
.visitado-badge {
  background: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
}
.sin-ruta {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 10px;
  color: #666;
}
.loading {
  text-align: center;
  padding: 2rem;
}
</style>