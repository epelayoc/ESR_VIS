import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página de Streamlit
st.set_page_config(page_title="ESR_VIEWER", layout="wide", page_icon="📊")

st.title("📊 Scores Evolution - Year")
st.markdown("Temporal evolution of scores in ESR reports")

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
    st.error(f"❌ File not found **'{file_path}'** in repository.")
    st.info("💡 **Solution:** Check your excel file.")
    st.stop()

# Filtrar por Métrica == 'Score' desde el inicio
df_scores = df[df['Metric'] == 'Score']

# -----------------------------------------------------------------------------
# 2. Creación de Filtros en la Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Selection filter")

# Filtro de Área (Selección única con opción de ver todas)
areas_disponibles = ["All"] + sorted(list(df_scores['Area'].dropna().unique()))
selected_area = st.sidebar.selectbox("Select Area:", areas_disponibles)

# Filtro de Bloque (Selección múltiple, por defecto todos seleccionados)
bloques_disponibles = sorted(list(df_scores['Block'].dropna().unique()))
selected_blocks = st.sidebar.multiselect(
    "Block selection:", 
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
    st.warning("⚠️ Select at least one block.")
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
    st.subheader("📈 Temporal evolution")
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
        
        ax.set_title(f"Mean scores evolution (Área: {selected_area})", fontsize=12, pad=15)
        ax.set_ylabel("Mean Score (Σ Sum / Σ Count)", fontsize=10)
        ax.set_xlabel("Año (Year)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.info("No available data.")

with col2:
    st.subheader("📌 Summary selection")
    st.write(f"**Area:** {selected_area}")
    st.write(f"**Blocks ({len(selected_blocks)}):**")
    st.write(", ".join(selected_blocks))
    
    if not df_scores_avg.empty:
        global_sum = df_scores_avg['total_sum'].sum()
        global_count = df_scores_avg['total_count'].sum()
        global_avg = global_sum / global_count if global_count > 0 else 0
        st.metric(label="Score Promedio Global Filtrado", value=f"{global_avg:.2f}")

st.subheader("📋 Calculated data")
if not df_scores_avg.empty:
    df_display = df_scores_avg.copy()
    df_display.columns = ['Año', 'Block', 'Suma Total (Sum)', 'Count', 'Mean Score']
    st.dataframe(df_display.style.format({'Mean Score': '{:.3f}'}), use_container_width=True)
