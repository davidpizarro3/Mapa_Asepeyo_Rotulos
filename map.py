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
    if estado in ['bueno', 'good']: return 'green'
    if estado in ['regular', 'fair', 'medio']: return 'orange'
    if estado in ['malo', 'bad', 'poor']: return 'red'
    return 'gray' # Para Pendiente o sin datos

# Función auxiliar para comprobar si hay licencia
def tiene_licencia(val):
    if pd.isna(val): return False
    return str(val).strip() != ''

# --- 3. Carga de Datos (Desde tu GitHub) ---
@st.cache_data
def load_data():
    # URL raw de tu repositorio público en GitHub
    csv_url = "https://raw.githubusercontent.com/davidpizarro3/Mapa_Asepeyo_Rotulos/refs/heads/main/data.csv"
    
    try:
        df = pd.read_csv(csv_url)
        
        # Limpiar espacios extra en los nombres de las columnas por si acaso
        df.columns = df.columns.str.strip()
        
        # Separar la columna 'Geo-Loaction' en Latitude y Longitude
        if 'Geo-Loaction' in df.columns:
            coords = df['Geo-Loaction'].astype(str).str.split(',', expand=True)
            if coords.shape[1] >= 2:
                df['Latitude'] = pd.to_numeric(coords[0], errors='coerce')
                df['Longitude'] = pd.to_numeric(coords[1], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"⚠️ Error al cargar los datos desde GitHub. Revisa la URL o el archivo. Detalle: {e}")
        return pd.DataFrame()

df = load_data()

# --- 4. Filtros ---
st.header("Filtrar Centros")
col1, col2, col3, col4 = st.columns(4)

if not df.empty:
    with col1:
        comunidad_filter = st.multiselect("Comunidad", df['Comunidad'].dropna().unique() if 'Comunidad' in df.columns else [])
    with col2:
        provincia_filter = st.multiselect("Provincia", df['Provincia'].dropna().unique() if 'Provincia' in df.columns else [])
    with col3:
        estado_filter = st.multiselect("Estado del Rótulo", df['Estado Rótulo'].dropna().unique() if 'Estado Rótulo' in df.columns else [])
    with col4:
        # Nuevo filtro de Licencia
        licencia_filter = st.selectbox("Licencia de Rotulación", ["Todos", "Con Licencia", "Sin Licencia"])

    # Aplicar filtros
    filtered_df = df.copy()
    if comunidad_filter:
        filtered_df = filtered_df[filtered_df['Comunidad'].isin(comunidad_filter)]
    if provincia_filter:
        filtered_df = filtered_df[filtered_df['Provincia'].isin(provincia_filter)]
    if estado_filter:
        filtered_df = filtered_df[filtered_df['Estado Rótulo'].isin(estado_filter)]
        
    # Aplicar filtro de Licencia
    if licencia_filter == "Con Licencia":
        filtered_df = filtered_df[filtered_df['Licencia Rótulo'].apply(tiene_licencia)]
    elif licencia_filter == "Sin Licencia":
        filtered_df = filtered_df[~filtered_df['Licencia Rótulo'].apply(tiene_licencia)]
else:
    filtered_df = pd.DataFrame()
    st.warning("No se han podido cargar los datos para aplicar filtros.")

# --- 5. Mapa Interactivo ---
st.header("Mapa Interactivo")
# Centrar el mapa en España por defecto
m = folium.Map(location=[40.4637, -3.7492], zoom_start=6, tiles="OpenStreetMap")

pins_layer = folium.FeatureGroup(name="📍 Rótulos", show=True)

if not filtered_df.empty:
    for idx, row in filtered_df.iterrows():
        # Verificamos que tengamos latitud y longitud válidas
        if 'Latitude' in row and 'Longitude' in row and pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
            
            estado = str(row.get('Estado Rótulo', 'Pendiente'))
            pin_color = get_estado_color(estado)
            
            # Enlace a Google Maps
            gmaps_link = f"https://www.google.com/maps/search/?api=1&query={row['Latitude']},{row['Longitude']}"
            
            # Enlace a la Licencia (Drive o descarga)
            licencia_link = str(row.get('Licencia Rótulo', ''))
            if pd.notna(licencia_link) and licencia_link.startswith('http'):
                licencia_html = f'<a href="{licencia_link}" target="_blank" style="color: #28a745; font-weight: bold;">📄 Ver Licencia de Rotulación</a>'
            else:
                licencia_html = '<i style="color: gray;">Sin licencia adjunta</i>'
                
            # Extraer las Observaciones (si existen y no están vacías)
            observaciones_texto = row.get('Observaciones')
            obs_html = ""
            if pd.notna(observaciones_texto) and str(observaciones_texto).strip() != '':
                obs_html = f"""
                <div style='margin-top: 10px; padding: 8px; background-color: #fff9e6; border-left: 4px solid #ffc107; font-size: 13px; color: #333;'>
                    <b>Observaciones:</b><br>{str(observaciones_texto)}
                </div>
                """
            
            # Diseño del Popup
            popup_info = f"""
            <div style="font-family: Arial, sans-serif; min-width: 250px;">
                <h4 style="margin-bottom: 5px; color: #004b87;">{row.get('Centre', 'Desconocido')}</h4>
                <hr style="margin: 5px 0;">
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #555;">
                    {row.get('Dirección Suministro', 'Dirección no disponible')}<br>
                    {row.get('Provincia', '')}
                </p>
                <b>Estado del Rótulo:</b> 
                <span style="background-color: {pin_color}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold;">{estado.upper()}</span><br><br>
                
                {licencia_html}
                
                {obs_html}
                
                <br><br>
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
                tooltip=row.get('Centre', 'Centro Asepeyo')
            ).add_to(pins_layer)

pins_layer.add_to(m)

# Control de capas
folium.LayerControl(position='topleft', collapsed=False).add_to(m)

# Renderizar el mapa
st_folium(m, width=1200, height=650, returned_objects=[])

# --- 6. Tabla de Datos y Exportación ---
st.header("Datos de los Centros")
if not filtered_df.empty:
    # Ocultar las columnas generadas internamente para que la tabla sea fiel al CSV
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
else:
    st.info("No hay datos para mostrar en la tabla.")
