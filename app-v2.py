import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Streamlit page configuration
st.set_page_config(page_title="ESR_VIEWER", layout="wide", page_icon="📊")

st.title("📊 R&D Evaluation Dashboard")
st.markdown("Comprehensive analysis of ESR reports across multiple dimensions.")

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

# Separate score metrics from non-score issues
df_scores = df[df['Metric'] == 'Score']
df_issues = df[df['Metric'] != 'Score']

# -----------------------------------------------------------------------------
# 2. Sidebar Filters (3 Filters)
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Selection Filters")

# Filter 1: Area 
available_areas = ["All"] + sorted(list(df_scores['Area'].dropna().unique()))
selected_area = st.sidebar.selectbox("Select Area:", available_areas)

# Filter 2: Type
available_types = ["All"] + sorted(list(df_scores['Type'].dropna().unique()))
selected_type = st.sidebar.selectbox("Select Type:", available_types)

# Filter 3: Block 
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
df_issues_filtered = df_issues.copy()

# Apply filters to both datasets (Scores and Issues)
if selected_area != "All":
    df_filtered = df_filtered[df_filtered['Area'] == selected_area]
    df_issues_filtered = df_issues_filtered[df_issues_filtered['Area'] == selected_area]

if selected_type != "All":
    df_filtered = df_filtered[df_filtered['Type'] == selected_type]
    df_issues_filtered = df_issues_filtered[df_issues_filtered['Type'] == selected_type]

if selected_blocks:
    df_filtered = df_filtered[df_filtered['Block'].isin(selected_blocks)]
    df_issues_filtered = df_issues_filtered[df_issues_filtered['Block'].isin(selected_blocks)]
else:
    st.warning("⚠️ Please select at least one block.")
    st.stop()

# -----------------------------------------------------------------------------
# 4. Tab Layout & Visualizations
# -----------------------------------------------------------------------------
# Create 4 tabs for different analytical perspectives
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Trend Analysis", 
    "🗺️ Strengths Map (Heatmap)", 
    "📊 Volume & Calls", 
    "⚠️ Issue Analyzer"
])

# --- TAB 1: TEMPORAL EVOLUTION (Original Line Chart) ---
with tab1:
    st.subheader("Temporal Evolution of Mean Scores")
    
    df_scores_avg = df_filtered.groupby(['Year', 'Block']).agg(
        total_sum=('Sum', 'sum'),
        total_count=('Count', 'sum')
    ).reset_index()
    
    df_scores_avg = df_scores_avg[df_scores_avg['total_count'] > 0]
    df_scores_avg['Average_Score'] = df_scores_avg['total_sum'] / df_scores_avg['total_count']
    df_scores_avg = df_scores_avg.sort_values('Year')

    if not df_scores_avg.empty:
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        sns.lineplot(
            data=df_scores_avg, x='Year', y='Average_Score', hue='Block',
            marker='o', linewidth=2, markersize=7, ax=ax1
        )
        ax1.set_ylabel("Mean Score")
        ax1.set_xlabel("Year")
        ax1.grid(True, linestyle="--", alpha=0.5)
        st.pyplot(fig1)
    else:
        st.info("No available data for the selected combination.")

# --- TAB 2: HEATMAP (Strengths & Weaknesses) ---
with tab2
