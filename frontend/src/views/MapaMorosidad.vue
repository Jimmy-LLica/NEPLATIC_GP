<template>
  <div class="mapa-container">
    <h1>Análisis Topológico y de Rutas (ArcGIS + Google Maps)</h1>
    
    <div class="controls-panel">
      <div class="routing-box">
        <h3>Calcular Ruta Óptima (Google Maps)</h3>
        <p class="help-text">Haz clic en el mapa para establecer el Origen y luego el Destino.</p>
        <div class="route-info">
          <div><b>Origen:</b> {{ origenLatLng || 'Selecciona en el mapa' }}</div>
          <div><b>Destino:</b> {{ destinoLatLng || 'Selecciona en el mapa' }}</div>
        </div>
        <div class="route-actions">
          <button @click="calcularRuta" :disabled="!origen || !destino || calculando" class="btn">
            {{ calculando ? 'Calculando...' : 'Dibujar Ruta' }}
          </button>
          <button @click="limpiarRuta" class="btn btn-secondary">Limpiar</button>
        </div>
        <div v-if="rutaError" class="error-msg">{{ rutaError }}</div>
      </div>
    </div>

    <div v-if="cargando" class="loading">Cargando motor geográfico...</div>
    <div ref="mapContainer" class="map" :class="{ 'cursor-crosshair': modoSeleccion }"></div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'MapaMorosidad',
  data() {
    return {
      cargando: true,
      calculando: false,
      puntosCalor: [],
      
      // Routing state
      modoSeleccion: true,
      origen: null,
      destino: null,
      origenLatLng: '',
      destinoLatLng: '',
      rutaError: ''
    }
  },
  created() {
    this.view = null;
    this.routeLayer = null;
    this.markersLayer = null;
    this.directionsService = null;
  },
  async mounted() {
    // Inicializar Google Directions Service si la API cargó
    if (window.google && window.google.maps) {
      this.directionsService = new window.google.maps.DirectionsService();
    } else {
      this.rutaError = "Google Maps API Key no proporcionada o script no cargado. Verifica VITE_GOOGLE_MAPS_API_KEY en .env";
    }
    
    await this.cargarHeatmapData();
  },
  beforeUnmount() {
    if (this.view) {
      this.view.destroy()
    }
  },
  methods: {
    async cargarHeatmapData() {
      try {
        const response = await api.get('/mapa/heatmap')
        if (response.data && response.data.success && Array.isArray(response.data.data)) {
          this.puntosCalor = response.data.data
          this.inicializarMapa()
        } else {
          this.cargando = false
        }
      } catch (error) {
        console.error('Error cargando heatmap:', error)
        this.cargando = false
      }
    },
    inicializarMapa() {
      window.require([
        "esri/Map",
        "esri/views/MapView",
        "esri/Graphic",
        "esri/layers/GraphicsLayer",
        "esri/layers/FeatureLayer",
        "esri/symbols/SimpleMarkerSymbol",
        "esri/symbols/SimpleLineSymbol"
      ], (Map, MapView, Graphic, GraphicsLayer, FeatureLayer, SimpleMarkerSymbol, SimpleLineSymbol) => {
        
        const map = new Map({
          basemap: "dark-gray-vector" // Fondo oscuro para resaltar el heatmap
        });

        this.view = new MapView({
          container: this.$refs.mapContainer,
          map: map,
          center: [-70.2528, -18.0111], // Lng, Lat por defecto
          zoom: 14
        });

        this.routeLayer = new GraphicsLayer();
        this.markersLayer = new GraphicsLayer();
        
        // Convertir datos REST a Graphics de ArcGIS
        const graphics = this.puntosCalor.map(punto => {
          return new Graphic({
            geometry: {
              type: "point",
              longitude: parseFloat(punto.longitud),
              latitude: parseFloat(punto.latitud)
            },
            attributes: {
              ObjectID: punto.id_lote,
              intensidad: parseFloat(punto.intensidad),
              estado: punto.estado_predominante
            }
          });
        });

        // Configurar el HeatmapRenderer
        const heatmapRenderer = {
          type: "heatmap",
          field: "intensidad",
          colorStops: [
            { color: "rgba(63, 40, 102, 0)", ratio: 0 },
            { color: "#472b77", ratio: 0.083 },
            { color: "#4e2d87", ratio: 0.166 },
            { color: "#563098", ratio: 0.25 },
            { color: "#5d32a8", ratio: 0.333 },
            { color: "#6735be", ratio: 0.416 },
            { color: "#7139d4", ratio: 0.5 },
            { color: "#7b3ce9", ratio: 0.583 },
            { color: "#853fff", ratio: 0.666 },
            { color: "#a46fbf", ratio: 0.75 },
            { color: "#c29f80", ratio: 0.833 },
            { color: "#e0cf40", ratio: 0.916 },
            { color: "#ffff00", ratio: 1 }
          ],
          minPixelIntensity: 0,
          maxPixelIntensity: 10000 // Ajustar según los valores reales de deuda
        };

        const heatmapLayer = new FeatureLayer({
          source: graphics,
          objectIdField: "ObjectID",
          fields: [{
            name: "ObjectID",
            alias: "ObjectID",
            type: "oid"
          }, {
            name: "intensidad",
            alias: "Deuda Pendiente",
            type: "double"
          }, {
            name: "estado",
            alias: "Estado",
            type: "string"
          }],
          renderer: heatmapRenderer,
          title: "Heatmap de Morosidad"
        });

        map.addMany([heatmapLayer, this.routeLayer, this.markersLayer]);

        // Configurar el click para capturar Origen y Destino de rutas
        this.view.on("click", (event) => {
          const lat = event.mapPoint.latitude;
          const lon = event.mapPoint.longitude;
          
          if (!this.origen) {
            this.origen = { lat, lng: lon };
            this.origenLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [0, 255, 0], "Origen");
          } else if (!this.destino) {
            this.destino = { lat, lng: lon };
            this.destinoLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [255, 0, 0], "Destino");
          } else {
            // Reiniciar si ambos existen
            this.limpiarRuta();
            this.origen = { lat, lng: lon };
            this.origenLatLng = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.dibujarMarcador(lon, lat, [0, 255, 0], "Origen");
          }
        });

        // Exponer funciones necesarias al scope de Vue para creación de elementos
        this._createGraphic = Graphic;
        this._createMarker = SimpleMarkerSymbol;
        this._createLine = SimpleLineSymbol;

        this.view.when(() => {
          if (graphics.length > 0) this.view.goTo(graphics).catch(()=>{});
          this.cargando = false;
        });
      });
    },
    dibujarMarcador(lon, lat, color, titulo) {
      if (!this.markersLayer || !this._createGraphic) return;
      
      const symbol = new this._createMarker({
        color: color,
        outline: { color: [255, 255, 255], width: 2 }
      });
      
      const graphic = new this._createGraphic({
        geometry: { type: "point", longitude: lon, latitude: lat },
        symbol: symbol,
        attributes: { name: titulo },
        popupTemplate: { title: "{name}" }
      });
      
      this.markersLayer.add(graphic);
    },
    calcularRuta() {
      if (!this.directionsService || !this.origen || !this.destino) return;
      
      this.calculando = true;
      this.rutaError = '';
      this.routeLayer.removeAll();

      const request = {
        origin: this.origen,
        destination: this.destino,
        travelMode: 'DRIVING'
      };

      this.directionsService.route(request, (response, status) => {
        this.calculando = false;
        if (status === 'OK') {
          // Extraer la polyline y decodificar a [lng, lat] para ArcGIS
          const path = response.routes[0].overview_path;
          const arcgisPath = path.map(point => [point.lng(), point.lat()]);
          
          this.dibujarLineaArcGIS(arcgisPath);
        } else {
          this.rutaError = 'No se pudo calcular la ruta: ' + status;
        }
      });
    },
    dibujarLineaArcGIS(paths) {
      if (!this.routeLayer || !this._createGraphic) return;
      
      const lineSymbol = new this._createLine({
        color: [0, 200, 255, 0.9], // Azul brillante ruta Google Maps
        width: 4
      });
      
      const routeGraphic = new this._createGraphic({
        geometry: {
          type: "polyline",
          paths: [paths]
        },
        symbol: lineSymbol
      });
      
      this.routeLayer.add(routeGraphic);
      this.view.goTo(this.routeLayer.graphics);
    },
    limpiarRuta() {
      this.origen = null;
      this.destino = null;
      this.origenLatLng = '';
      this.destinoLatLng = '';
      this.rutaError = '';
      if (this.routeLayer) this.routeLayer.removeAll();
      if (this.markersLayer) this.markersLayer.removeAll();
    }
  }
}
</script>

<style scoped>
.mapa-container {
  display: flex;
  flex-direction: column;
}
.mapa-container h1 {
  margin-bottom: 1rem;
  color: #1a472a;
}
.controls-panel {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.routing-box {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
  flex: 1;
}
.routing-box h3 { margin-top: 0; margin-bottom: 0.5rem; color: #333; }
.help-text { font-size: 0.85rem; color: #666; margin-bottom: 0.5rem; }
.route-info {
  display: flex;
  gap: 2rem;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}
.route-actions { display: flex; gap: 0.5rem; }
.btn {
  background: #1a472a;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
.btn:disabled { background: #ccc; cursor: not-allowed; }
.btn-secondary { background: #6c757d; }
.error-msg { color: #dc3545; font-size: 0.85rem; margin-top: 0.5rem; font-weight: bold; }

.map {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  outline: none;
}
.cursor-crosshair { cursor: crosshair !important; }
.loading { text-align: center; padding: 2rem; color: #666; }
</style>