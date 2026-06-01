import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit page configuration
st.set_page_config(page_title="ESR_VIEWER", layout="wide", page_icon="📊")

st.title("📊 Scores Evolution - Year")
st.markdown("Temporal evolution of scores in ESR reports")

# -----------------------------------------------------------------------------
# 1. Data Loading
# -----------------------------------------------------------------------------
file_path = "esr_data_long.xlsx"

@st.cache_data
def load_data(path):
    df = pd.read_excel(path)
    df['Year'] = df['Year'].astype(str) # Ensure string type for year
    return df

try:
    df = load_data(file_path)
except FileNotFoundError:
    st.error(f"❌ File not found: **'{file_path}'** in repository.")
    st.info("💡 **Solution:** Please ensure your Excel file is uploaded to the repository.")
    st.stop()

# Filter by Metric == 'Score' from the start
df_scores = df[df['Metric'] == 'Score']

# -----------------------------------------------------------------------------
# 2. Sidebar Filters (3 Filters Total)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Selection Filters")

# Filter 1: Area (Single selection with "All" option)
available_areas = ["All"] + sorted(list(df_scores['Area'].dropna().unique()))
selected_area = st.sidebar.selectbox("Select Area:", available_areas)

# Filter 2: Type (NEW - Single selection with "All" option)
available_types = ["All"] + sorted(list(df_scores['Type'].dropna().unique()))
selected_type = st.sidebar.selectbox("Select Type:", available_types)

# Filter 3: Block (Multi-select, all selected by default)
available_blocks = sorted(list(df_scores['Block'].dropna().unique()))
selected_blocks = st.sidebar.multiselect(
    "Block Selection:", 
    options=available_blocks, 
    default=available_blocks
)

# -----------------------------------------------------------------------------
# 3. Dynamic Filtering Application
# -----------------------------------------------------------------------------
df_filtered = df_scores.copy()

# Apply Area filter if a specific one is chosen
if selected_area != "All":
    df_filtered = df_filtered[df_filtered['Area'] == selected_area]

# Apply Type filter if a specific one is chosen
if selected_type != "All":
    df_filtered = df_filtered[df_filtered['Type'] == selected_type]

# Apply Block filter
if selected_blocks:
    df_filtered = df_filtered[df_filtered['Block'].isin(selected_blocks)]
else:
    st.warning("⚠️ Please select at least one block.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. Aggregation and Total Calculations (Sum / Count)
# -----------------------------------------------------------------------------
# Data is aggregated by Year and Block based on the active row filters above
df_scores_avg = df_filtered.groupby(['Year', 'Block']).agg(
    total_sum=('Sum', 'sum'),
    total_count=('Count', 'sum')
).reset_index()

# Filter out rows to prevent division by zero if total_count is 0
df_scores_avg = df_scores_avg[df_scores_avg['total_count'] > 0]

# Calculate the weighted Mean Score
df_scores_avg['Average_Score'] = df_scores_avg['total_sum'] / df_scores_avg['total_count']

# Sort chronologically by year for line plotting
df_scores_avg = df_scores_avg.sort_values('Year')

# -----------------------------------------------------------------------------
# 5. Visualizations and Layout Reports
# -----------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Temporal Evolution")
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
        
        # Updated chart title to display both selected Area and Type
        ax.set_title(f"Mean Scores Evolution (Area: {selected_area} | Type: {selected_type})", fontsize=12, pad=15)
        ax.set_ylabel("Mean Score (Σ Sum / Σ Count)", fontsize=10)
        ax.set_xlabel("Year", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.info("No available data for the selected combination.")

with col2:
    st.subheader("
