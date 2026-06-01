import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página de Streamlit
st.set_page_config(page_title="Visualizador de Informes I+D", layout="wide", page_icon="📊")

st.title("📊 Evolución de Scores - Informes de Evaluación de I+D")
st.markdown("Esta aplicación web interactiva permite filtrar y analizar la evolución temporal de los scores promedio de los proyectos de I+D.")

# -----------------------------------------------------------------------------
# 1. Carga de datos de forma dinámica
# -----------------------------------------------------------------------------
# En Streamlit Cloud, si subes el archivo 'esr_data_long.xlsx' a la raíz de tu 
# repositorio de GitHub junto a este script, se leerá automáticamente.
file_path = "esr_data_long.xlsx"

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df['Year'] = df['Year'].astype(str) # Asegurar tipo string para el año
    return df

try:
    df = load_data(file_path)
except FileNotFoundError:
    st.error(f"❌ No se encontró el archivo **'{file_path}'** en el repositorio.")
    st.info("💡 **Solución:** Asegúrate de subir tu archivo Excel con ese nombre exacto a la raíz de tu repositorio de GitHub junto a este script python.")
    st.stop()

# Filtrar por Métrica == 'Score' desde el inicio
df_scores = df[df['Metric'] == 'Score']

# -----------------------------------------------------------------------------
# 2. Creación de Filtros en la Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Filtros de Selección")

# Filtro de Área (Selección única con opción de ver todas)
areas_disponibles = ["Todas"] + sorted(list(df_scores['Area'].dropna().unique()))
selected_area = st.sidebar.selectbox("Selecciona el Área:", areas_disponibles)

# Filtro de Bloque (Selección múltiple, por defecto todos seleccionados)
bloques_disponibles = sorted(list(df_scores['Block'].dropna().unique()))
selected_blocks = st.sidebar.multiselect(
    "Selecciona los Bloques:", 
    options=bloques_disponibles, 
    default=bloques_disponibles
)

# -----------------------------------------------------------------------------
# 3. Aplicación de Filtros Dinámicos
# -----------------------------------------------------------------------------
df_filtered = df_scores.copy()

if selected_area != "Todas":
    df_filtered = df_filtered[df_filtered['Area'] == selected_area]

if selected_blocks:
    df_filtered = df_filtered[df_filtered['Block'].isin(selected_blocks)]
else:
    st.warning("⚠️ Por favor, selecciona al menos un **Bloque** en la barra lateral para visualizar los resultados.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. Agrupación y Cálculo de Totales (Suma / Count)
# -----------------------------------------------------------------------------
df_scores_avg = df_filtered.groupby(['Year', 'Block']).agg(
    total_sum=('Sum', 'sum'),
    total_count=('Count', 'sum')
).reset_index()

# Filtrar para evitar la división por cero si total_count fuera 0
df_scores_avg = df_scores_avg[df_scores_avg['total_count'] > 0]

# Calcular el Score Promedio Ponderado
df_scores_avg['Average_Score'] = df_scores_avg['total_sum'] / df_scores_avg['total_count']

# Ordenar cronológicamente por año para la gráfica de líneas
df_scores_avg = df_scores_avg.sort_values('Year')

# -----------------------------------------------------------------------------
# 5. Visualizaciones y Reporte en Pantalla
# -----------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Gráfico de Evolución Temporal")
    if not df_scores_avg.empty:
        fig, ax = plt.subplots(figsize=(10, 5.5))
        
        sns.lineplot(
            data=df_scores_avg,
            x='Year',
            y='Average_Score',
            hue='Block',
            marker='o',
            linewidth=2,
            markersize=7,
            ax=ax
        )
        
        ax.set_title(f"Evolución de Scores Promedio (Área: {selected_area})", fontsize=12, pad=15)
        ax.set_ylabel("Score Promedio (Σ Sum / Σ Count)", fontsize=10)
        ax.set_xlabel("Año (Year)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.info("No hay datos que coincidan con la combinación de filtros seleccionada.")

with col2:
    st.subheader("📌 Resumen de Filtros")
    st.write(f"**Área Seleccionada:** {selected_area}")
    st.write(f"**Bloques Seleccionados ({len(selected_blocks)}):**")
    st.write(", ".join(selected_blocks))
    
    if not df_scores_avg.empty:
        global_sum = df_scores_avg['total_sum'].sum()
        global_count = df_scores_avg['total_count'].sum()
        global_avg = global_sum / global_count if global_count > 0 else 0
        st.metric(label="Score Promedio Global Filtrado", value=f"{global_avg:.2f}")

st.subheader("📋 Tabla de Datos Calculados")
if not df_scores_avg.empty:
    df_display = df_scores_avg.copy()
    df_display.columns = ['Año', 'Bloque', 'Suma Total (Sum)', 'Conteo Total (Count)', 'Score Promedio (Ponderado)']
    st.dataframe(df_display.style.format({'Score Promedio (Ponderado)': '{:.3f}'}), use_container_width=True)
