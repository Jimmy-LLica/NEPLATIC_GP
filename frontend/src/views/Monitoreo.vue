<template>
  <div class="monitoreo-container">
    <h1>Monitoreo de Notificadores</h1>
    <p>Ubicación en tiempo real de los notificadores en campo.</p>
    
    <div v-if="loading" class="loading">Cargando ubicaciones...</div>
    <div v-else class="map-wrapper">
      <div id="monitoreo-map" ref="mapRef" style="height: 600px; width: 100%; border-radius: 8px;"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '../api'

const loading = ref(true)
const mapRef = ref(null)
let map = null
let markers = {}
let intervalId = null

const initMap = () => {
  if (window.google && window.google.maps) {
    // Coordenadas base en Ciudad Nueva, Tacna
    map = new window.google.maps.Map(mapRef.value, {
      center: { lat: -17.9700, lng: -70.2300 },
      zoom: 14,
      mapTypeId: 'roadmap'
    });
    fetchUbicaciones();
    // Actualizar cada 10 segundos
    intervalId = setInterval(fetchUbicaciones, 10000);
  } else {
    setTimeout(initMap, 500); // Reintentar si Google Maps no cargó
  }
}

const fetchUbicaciones = async () => {
  try {
    const res = await api.get('/rutas/ubicaciones-activas')
    loading.value = false
    if (res.data.success && res.data.data) {
      actualizarMarcadores(res.data.data);
    }
  } catch (error) {
    console.error('Error fetching ubicaciones:', error)
  }
}

const actualizarMarcadores = (ubicaciones) => {
  if (!map || !window.google) return;
  
  // Track cuáles actualizamos para borrar los desconectados
  const actualizados = new Set();

  ubicaciones.forEach(ub => {
    const key = ub.nombres + ub.apellidos;
    actualizados.add(key);
    
    const latlng = new window.google.maps.LatLng(ub.lat, ub.lng);
    
    if (markers[key]) {
      markers[key].setPosition(latlng);
    } else {
      markers[key] = new window.google.maps.Marker({
        position: latlng,
        map: map,
        title: `${ub.nombres} ${ub.apellidos}`,
        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' // Icono azul para notificadores
      });
      
      const infoWindow = new window.google.maps.InfoWindow({
        content: `<b>${ub.nombres} ${ub.apellidos}</b><br>Última act: ${new Date(ub.timestamp * 1000).toLocaleTimeString()}`
      });
      
      markers[key].addListener('click', () => {
        infoWindow.open(map, markers[key]);
      });
    }
  });

  // Borrar los que ya no vienen del backend (desconectados o TTL expirado)
  Object.keys(markers).forEach(key => {
    if (!actualizados.has(key)) {
      markers[key].setMap(null);
      delete markers[key];
    }
  });
}

onMounted(() => {
  initMap()
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId);
})
</script>

<style scoped>
.monitoreo-container {
  padding: 2rem;
}
.monitoreo-container h1 {
  margin-bottom: 0.5rem;
  color: #1a472a;
}
.monitoreo-container p {
  margin-bottom: 1.5rem;
  color: #666;
}
.map-wrapper {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
</style>
