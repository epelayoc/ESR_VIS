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
# Create 5 tabs for different analytical perspectives
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trend Analysis", 
    "🕸️ R&D Profile (Radar)", 
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

# --- TAB 2: RADAR CHART (R&D Profile) ---
with tab2:
    st.subheader("R&D Profile Fingerprint")
    st.markdown("Shows the balance of performance across the selected evaluation blocks.")
    
    # Aggregate data across all selected years to get a global profile
    df_radar = df_filtered.groupby('Block').agg(
        total_sum=('Sum', 'sum'), total_count=('Count', 'sum')
    ).reset_index()
    
    df_radar = df_radar[df_radar['total_count'] > 0]
    df_radar['Average_Score'] = df_radar['total_sum'] / df_radar['total_count']
    
    if not df_radar.empty and len(df_radar) > 2:
        # Plotly Radar Chart
        fig2 = px.line_polar(
            df_radar, r='Average_Score', theta='Block', line_close=True,
            markers=True, text='Average_Score'
        )
        fig2.update_traces(fill='toself', textposition="top center")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ The radar chart requires at least 3 blocks to be displayed properly.")

# --- TAB 3: HEATMAP (Strengths & Weaknesses) ---
with tab3:
    st.subheader("Global Strengths & Weaknesses Matrix")
    st.markdown("Compares performance across all Areas (ignoring the Area filter) for context.")
    
    # Use the base df_scores (only applying Type and Block filters) to show all Areas
    df_heat_base = df_scores.copy()
    if selected_type != "All":
        df_heat_base = df_heat_base[df_heat_base['Type'] == selected_type]
    df_heat_base = df_heat_base[df_heat_base['Block'].isin(selected_blocks)]
    
    df_heat = df_heat_base.groupby(['Area', 'Block']).agg(
        total_sum=('Sum', 'sum'), total_count=('Count', 'sum')
    ).reset_index()
    
    df_heat = df_heat[df_heat['total_count'] > 0]
    df_heat['Average_Score'] = df_heat['total_sum'] / df_heat['total_count']
    
    if not df_heat.empty:
        pivot_heat = df_heat.pivot(index='Area', columns='Block', values='Average_Score')
        
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        # RdYlGn gives a Red-Yellow-Green color scale (Red=Low, Green=High)
        sns.heatmap(pivot_heat, annot=True, cmap="RdYlGn", fmt=".2f", linewidths=.5, ax=ax3)
        ax3.set_ylabel("R&D Area")
        ax3.set_xlabel("Evaluation Block")
        st.pyplot(fig3)
    else:
        st.info("No data available to generate heatmap.")

# --- TAB 4: VOLUME & CALLS (Stacked Bar) ---
with tab4:
    st.subheader("Project Volume & Call Distribution")
    st.markdown("Shows the total volume of evaluations based on your active filters.")
    
    # Group by Year and Call, summing the 'Count' column
    df_vol = df_filtered.groupby(['Year', 'Call'])['Count'].sum().reset_index()
    
    if not df_vol.empty:
        fig4 = px.bar(
            df_vol, x='Year', y='Count', color='Call', 
            title="Total Evaluations per Year", text_auto=True
        )
        fig4.update_layout(barmode='stack', yaxis_title="Number of Evaluations (Count)")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No data available.")

# --- TAB 5: ISSUE ANALYZER (Non-Score Metrics) ---
with tab5:
    st.subheader("Non-Score Issue & Observation Bottlenecks")
    st.markdown("Visualizes other metrics (e.g., Minor Issues, Weaknesses) present in the reports.")
    
    if not df_issues_filtered.empty:
        # Group by Block and the specific Metric type
        df_iss_agg = df_issues_filtered.groupby(['Block', 'Metric'])['Sum'].sum().reset_index()
        
        fig5 = px.bar(
            df_iss_agg, x='Block', y='Sum', color='Metric', barmode='group',
            title="Volume of Non-Score Remarks by Block", text_auto=True
        )
        fig5.update_layout(yaxis_title="Total Occurrences (Sum)")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.success("✅ No non-score issues found for this specific filter combination!")
