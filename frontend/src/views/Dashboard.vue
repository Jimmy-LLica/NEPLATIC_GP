<template>
  <div class="dashboard">
    <h1>Dashboard Gerencial</h1>
    
    <div class="kpi-grid" v-if="kpis">
      <div class="kpi-card">
        <h3>Deuda Total Pendiente</h3>
        <p class="value">S/ {{ formatNumber(kpis.deuda_total_pendiente) }}</p>
      </div>
      <div class="kpi-card coactiva">
        <h3>Deuda Coactiva</h3>
        <p class="value">S/ {{ formatNumber(kpis.deuda_coactiva) }}</p>
        <span class="percentage">{{ kpis.pct_deuda_coactiva }}%</span>
      </div>
      <div class="kpi-card">
        <h3>Total Contribuyentes Morosos</h3>
        <p class="value">{{ formatNumber(kpis.total_contribuyentes_morosos) }}</p>
      </div>
      <div class="kpi-card">
        <h3>Tasa de Efectividad</h3>
        <p class="value">{{ kpis.tasa_efectividad_global }}%</p>
      </div>
    </div>

    <div class="charts">
      <div class="chart-container">
        <h3>Evolución de Morosidad</h3>
        <canvas ref="evolucionChart"></canvas>
      </div>
      <div class="chart-container">
        <h3>Top 10 Deudores</h3>
        <table class="top-deudores">
          <thead>
            <tr><th>Ranking</th><th>Contribuyente</th><th>Deuda Total</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in topDeudores" :key="d.ranking">
              <td>{{ d.ranking }}</td>
              <td>{{ d.nombres }} {{ d.apellido_paterno }}</td>
              <td>S/ {{ formatNumber(d.deuda_total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const kpis = ref(null)
const topDeudores = ref([])

const formatNumber = (num) => {
  return num?.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'
}

onMounted(async () => {
  const [kpisRes, topRes] = await Promise.all([
    api.get('/dashboard/kpis'),
    api.get('/dashboard/top-deudores?limit=10')
  ])
  kpis.value = kpisRes.data.data
  topDeudores.value = topRes.data.data
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 2rem;
  color: #1a472a;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.kpi-card {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  text-align: center;
}
.kpi-card.coactiva {
  border-left: 4px solid #ff0000;
}
.kpi-card h3 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}
.kpi-card .value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #1a472a;
}
.kpi-card .percentage {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #ff0000;
}
.charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}
.chart-container {
  background: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}
.top-deudores {
  width: 100%;
  border-collapse: collapse;
}
.top-deudores th, .top-deudores td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}
.top-deudores th {
  background: #f5f5f5;
}
</style>