<template>
  <div class="mapa-container">
    <h1>Mapa de Calor - Morosidad por Sector</h1>
    <div class="legend">
      <div class="legend-item"><span class="color coactiva"></span> Coactiva (Rojo)</div>
      <div class="legend-item"><span class="color ordinaria"></span> Ordinaria (Guinda)</div>
      <div class="legend-item"><span class="color sin-proceso"></span> Sin Proceso (Azul)</div>
    </div>
    <div v-if="cargando" class="loading">Cargando mapa...</div>
    <div ref="mapContainer" class="map"></div>
  </div>
</template>

<script>
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import api from '../api'

export default {
  name: 'MapaMorosidad',
  data() {
    return {
      cargando: true,
      map: null,
      sectores: []
    }
  },
  async mounted() {
    await this.cargarSectores()
  },
  methods: {
    async cargarSectores() {
      try {
        const response = await api.get('/mapa/sectores')
        // La respuesta ya viene en response.data (axios lo decodifica)
        if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.sectores = response.data.data
          if (this.sectores.length === 0) {
            console.warn('No se encontraron sectores')
            this.cargando = false
            return
          }
          this.inicializarMapa()
        } else {
          console.error('Respuesta inesperada:', response.data)
          this.cargando = false
        }
      } catch (error) {
        console.error('Error cargando sectores:', error)
        this.cargando = false
      }
    },
    inicializarMapa() {
      // Crear el mapa si no existe
      if (!this.map) {
        this.map = L.map(this.$refs.mapContainer).setView([-18.0111, -70.2528], 13)
        // Usamos una capa base gratuita y sin necesidad de API key
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
          subdomains: 'abcd',
          maxZoom: 19,
          minZoom: 3
        }).addTo(this.map)
      }

      // Agregar cada sector como capa GeoJSON
      this.sectores.forEach(sector => {
        if (sector.geojson) {
          const color = sector.color_predominante || '#CCCCCC'
          const layer = L.geoJSON(sector.geojson, {
            style: {
              color: color,
              weight: 2,
              fillColor: color,
              fillOpacity: 0.6
            },
            onEachFeature: (feature, layer) => {
              // Popup con información del sector
              layer.bindPopup(`
                <b>${sector.nombre_sector}</b><br>
                Deuda Total: S/ ${Number(sector.monto_total_pendiente).toLocaleString()}<br>
                Deuda Coactiva: S/ ${Number(sector.monto_coactiva).toLocaleString()}<br>
                Contribuyentes Morosos: ${sector.total_contribuyentes_morosos}<br>
                Efectividad: ${sector.tasa_efectividad_notificacion}%
              `)
            }
          }).addTo(this.map)
        } else {
          console.warn('Sector sin geojson:', sector)
        }
      })

      // Ajustar el zoom para que se vean todos los sectores (opcional)
      if (this.sectores.length > 0 && this.map) {
        const bounds = []
        this.sectores.forEach(sector => {
          if (sector.geojson && sector.geojson.coordinates) {
            // Extraer coordenadas del polígono para calcular el límite
            const coords = sector.geojson.coordinates[0]
            coords.forEach(coord => bounds.push(L.latLng(coord[1], coord[0])))
          }
        })
        if (bounds.length) {
          this.map.fitBounds(bounds)
        }
      }

      this.cargando = false
    }
  }
}
</script>

<style scoped>
.mapa-container h1 {
  margin-bottom: 1rem;
  color: #1a472a;
}
.legend {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
  padding: 0.5rem 1rem;
  background: white;
  border-radius: 5px;
  display: inline-block;
}
.legend-item {
  display: inline-block;
  margin-right: 1.5rem;
}
.legend-item .color {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 3px;
  margin-right: 0.5rem;
  vertical-align: middle;
}
.color.coactiva { background-color: #ff0000; }
.color.ordinaria { background-color: #800020; }
.color.sin-proceso { background-color: #0000ff; }
.map {
  width: 100%;
  height: 600px;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  margin-top: 1rem;
}
.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>