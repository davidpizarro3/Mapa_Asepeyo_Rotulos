import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. Configuración de página ---
st.set_page_config(page_title="Mapa Rótulos Asepeyo", layout="wide")
st.title("Mapa de Estado de Rótulos Exteriores - Asepeyo")

# --- 2. Función de Mapeo de Colores ---
def get_estado_color(estado):
    """Mapea el estado del rótulo a colores para los pines del mapa"""
    estado = str(estado).strip().lower()
    if estado == 'bueno': return 'green'
    if estado == 'regular': return 'orange'
    if estado == 'malo': return 'red'
    return 'gray' # Para Pendiente o sin datos

# --- 3. Carga de Datos ---
@st.cache_data
def load_data():
    # Aquí deberás poner la URL de tu nuevo archivo CSV con los datos de rótulos
    # csv_url = "URL_DE_TU_NUEVO_CSV_EN_GITHUB_O_DRIVE"
    
    # Como ejemplo, creo un DataFrame de prueba. 
    # En tu versión final, sustituye este bloque try/except por la lectura de tu CSV real: df = pd.read_csv(csv_url)
    try:
        data = {
            'Centro': ['Vía Augusta 36', 'Vía Augusta 18', 'Coslada Hospital', 'Centro de Prueba'],
            'Latitude': [41.3985, 41.3970, 40.4259, 37.3891],
            'Longitude': [2.1524, 2.1510, -3.5643, -5.9845],
            'Comunidad': ['Cataluña', 'Cataluña', 'Madrid', 'Andalucía'],
            'Estado Rótulo': ['Bueno', 'Regular', 'Malo', 'Pendiente'],
            'Licencia Rótulo': [
                'https://drive.google.com/', # Link de ejemplo
                'https://drive.google.com/',
                '', # Sin licencia adjunta
                'https://drive.google.com/'
            ]
        }
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.warning(f"⚠️ Error al cargar los datos: {e}")
        return pd.DataFrame()

df = load_data()

# --- 4. Filtros ---
st.header("Filtrar Centros")
col1, col2 = st.columns(2)

with col1:
    comunidad_filter = st.multiselect("Comunidad", df['Comunidad'].dropna().unique() if 'Comunidad' in df.columns else [])
with col2:
    estado_filter = st.multiselect("Estado del Rótulo", df['Estado Rótulo'].dropna().unique() if 'Estado Rótulo' in df.columns else [])

# Aplicar filtros
filtered_df = df.copy()
if comunidad_filter:
    filtered_df = filtered_df[filtered_df['Comunidad'].isin(comunidad_filter)]
if estado_filter:
    filtered_df = filtered_df[filtered_df['Estado Rótulo'].isin(estado_filter)]

# --- 5. Mapa Interactivo ---
st.header("Mapa Interactivo")
# Centrar el mapa en España por defecto
m = folium.Map(location=[40.4637, -3.7492], zoom_start=6, tiles="CartoDB positron")

pins_layer = folium.FeatureGroup(name="📍 Rótulos", show=True)

for idx, row in filtered_df.iterrows():
    if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
        
        estado = row.get('Estado Rótulo', 'Pendiente')
        pin_color = get_estado_color(estado)
        
        # Enlace a Google Maps
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={row['Latitude']},{row['Longitude']}"
        
        # Enlace a la Licencia (Drive o descarga)
        licencia_link = str(row.get('Licencia Rótulo', ''))
        if pd.notna(licencia_link) and licencia_link.startswith('http'):
            licencia_html = f'<a href="{licencia_link}" target="_blank" style="color: #28a745; font-weight: bold;">📄 Ver Licencia de Rotulación</a>'
        else:
            licencia_html = '<i style="color: gray;">Sin licencia adjunta</i>'
        
        # Diseño del Popup
        popup_info = f"""
        <div style="font-family: Arial, sans-serif; min-width: 250px;">
            <h4 style="margin-bottom: 5px; color: #004b87;">{row.get('Centro', 'Desconocido')}</h4>
            <hr style="margin: 5px 0;">
            <b>Estado del Rótulo:</b> 
            <span style="background-color: {pin_color}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{estado.upper()}</span><br><br>
            
            {licencia_html}<br><br>
            
            <a href="{gmaps_link}" target="_blank" style="text-decoration: none; color: #0056b3; font-weight: bold;">📍 Abrir en Google Maps</a>
        </div>
        """
        
        # Añadir el punto al mapa
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=7,
            color="white",
            weight=1,
            fill=True,
            fill_color=pin_color,
            fill_opacity=1.0,
            popup=folium.Popup(popup_info, max_width=350),
            tooltip=row.get('Centro', 'Centro Asepeyo')
        ).add_to(pins_layer)

pins_layer.add_to(m)

# Control de capas
folium.LayerControl(position='topleft', collapsed=False).add_to(m)

# Renderizar el mapa
st_folium(m, width=1200, height=650, returned_objects=[])

# --- 6. Tabla de Datos y Exportación ---
st.header("Datos de los Centros")
# Ocultar las coordenadas para que la tabla quede más limpia
display_df = filtered_df.drop(columns=['Latitude', 'Longitude'], errors='ignore')
st.dataframe(display_df, use_container_width=True)

# Botón para descargar
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Descargar datos filtrados (CSV)",
    data=csv,
    file_name='asepeyo_rotulos_filtrado.csv',
    mime='text/csv',
)
