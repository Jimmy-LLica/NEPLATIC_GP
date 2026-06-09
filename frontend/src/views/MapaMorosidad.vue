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
import api from '../api'

export default {
  name: 'MapaMorosidad',
  data() {
    return {
      cargando: true,
      sectores: []
    }
  },
  created() {
    // Definimos view como propiedad no reactiva para evitar que Vue 3
    // envuelva los objetos de ArcGIS en Proxies, lo cual causa errores graves.
    this.view = null;
  },
  async mounted() {
    await this.cargarSectores()
  },
  beforeUnmount() {
    if (this.view) {
      this.view.destroy()
    }
  },
  methods: {
    async cargarSectores() {
      try {
        const response = await api.get('/mapa/sectores')
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
      // Usar require global de ArcGIS CDN
      window.require([
        "esri/Map",
        "esri/views/MapView",
        "esri/Graphic",
        "esri/layers/GraphicsLayer",
        "esri/symbols/SimpleFillSymbol"
      ], (Map, MapView, Graphic, GraphicsLayer, SimpleFillSymbol) => {
        
        const map = new Map({
          basemap: "osm" // Basemap gratuito de OSM a través de ArcGIS
        });

        this.view = new MapView({
          container: this.$refs.mapContainer,
          map: map,
          center: [-70.2528, -18.0111], // Lng, Lat para ArcGIS
          zoom: 13
        });

        const graphicsLayer = new GraphicsLayer();
        map.add(graphicsLayer);

        const graphics = [];

        this.sectores.forEach(sector => {
          if (sector.geojson) {
            const color = sector.color_predominante || '#CCCCCC';
            
            // ArcGIS Graphic requiere anillos (rings) para polígonos
            let rings = [];
            if (sector.geojson.type === 'Polygon') {
              rings = sector.geojson.coordinates;
            } else if (sector.geojson.type === 'MultiPolygon') {
              sector.geojson.coordinates.forEach(poly => {
                poly.forEach(ring => {
                   rings.push(ring);
                });
              });
            }

            const fillSymbol = new SimpleFillSymbol({
              color: [...this.hexToRgb(color), 0.6], // color con opacidad
              outline: {
                color: [255, 255, 255, 0.8],
                width: 1
              }
            });

            const polygon = {
              type: "polygon",
              rings: rings
            };

            const popupTemplate = {
              title: "{nombre_sector}",
              content: `
                <b>Deuda Total:</b> S/ {monto_total_pendiente}<br>
                <b>Deuda Coactiva:</b> S/ {monto_coactiva}<br>
                <b>Contribuyentes Morosos:</b> {total_contribuyentes_morosos}<br>
                <b>Efectividad:</b> {tasa_efectividad_notificacion}%
              `
            };

            const graphic = new Graphic({
              geometry: polygon,
              symbol: fillSymbol,
              attributes: {
                nombre_sector: sector.nombre_sector,
                monto_total_pendiente: Number(sector.monto_total_pendiente).toLocaleString('es-PE', { minimumFractionDigits: 2 }),
                monto_coactiva: Number(sector.monto_coactiva).toLocaleString('es-PE', { minimumFractionDigits: 2 }),
                total_contribuyentes_morosos: sector.total_contribuyentes_morosos,
                tasa_efectividad_notificacion: sector.tasa_efectividad_notificacion
              },
              popupTemplate: popupTemplate
            });

            graphics.push(graphic);
            graphicsLayer.add(graphic);
          }
        });

        this.view.when(() => {
          if (graphics.length > 0) {
            this.view.goTo(graphics).catch(err => {
              if (err.name !== "AbortError") {
                console.error("Error navigating to graphics: ", err);
              }
            });
          }
          this.cargando = false;
        });

      });
    },
    hexToRgb(hex) {
      hex = hex.replace(/^#/, '');
      if (hex.length === 3) {
          hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
      }
      var bigint = parseInt(hex, 16);
      var r = (bigint >> 16) & 255;
      var g = (bigint >> 8) & 255;
      var b = bigint & 255;
      return [r, g, b];
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
  outline: none; /* ArcGIS focus outline removal */
  overflow: hidden; /* Ensure radius applies to inner canvas */
}
.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>