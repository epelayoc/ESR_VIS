import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    "🗺️ Strengths Map (Heatmap)", 
    "📊 Volume & Calls", 
    "⚠️ Issue Analyzer",
    "🔄 Score vs Critique"
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
with tab2:
    st.subheader("Global Strengths & Weaknesses Matrix")
    st.markdown("Compares performance across all Areas (ignoring the Area filter) for context.")
    
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
        
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot_heat, annot=True, cmap="RdYlGn", fmt=".2f", linewidths=.5, ax=ax2)
        ax2.set_ylabel("R&D Area")
        ax2.set_xlabel("Evaluation Block")
        st.pyplot(fig2)
    else:
        st.info("No data available to generate heatmap.")

# --- TAB 3: VOLUME & CALLS (Stacked Bar) ---
with tab3:
    st.subheader("Project Volume & Call Distribution")
    st.markdown("Shows the total volume of evaluations based on your active filters.")
    
    df_vol = df_filtered.groupby(['Year', 'Call'])['Count'].sum().reset_index()
    
    if not df_vol.empty:
        fig3 = px.bar(
            df_vol, x='Year', y='Count', color='Call', 
            title="Total Evaluations per Year", text_auto=True
        )
        fig3.update_layout(barmode='stack', yaxis_title="Number of Evaluations (Count)")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No data available.")

# --- TAB 4: ISSUE ANALYZER (Non-Score Metrics) ---
with tab4:
    st.subheader("Non-Score Issue & Observation Bottlenecks")
    st.markdown("Visualizes other metrics (e.g., Minor Issues, Weaknesses) present in the reports.")
    
    if not df_issues_filtered.empty:
        df_iss_agg = df_issues_filtered.groupby(['Block', 'Metric'])['Sum'].sum().reset_index()
        
        fig4 = px.bar(
            df_iss_agg, x='Block', y='Sum', color='Metric', barmode='group',
            title="Volume of Non-Score Remarks by Block", text_auto=True
        )
        fig4.update_layout(yaxis_title="Total Occurrences (Sum)")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.success("✅ No non-score issues found for this specific filter combination!")

# --- TAB 5: SCORE VS CRITIQUE FREQUENCY (DYNAMIC METRIC FIX) ---
with tab5:
    st.subheader("⚖️ Critique Density vs. Evaluation Scores Dynamics")
    st.markdown("Analyze metrics and scores together to identify trends and negative correlations.")
    
    # 1. Calculate Average Score per Year
    df_score_trend = df_filtered.groupby('Year').agg(
        score_sum=('Sum', 'sum'), score_count=('Count', 'sum')
    ).reset_index()
    df_score_trend = df_score_trend[df_score_trend['score_count'] > 0]
    df_score_trend['Average Score'] = df_score_trend['score_sum'] / df_score_trend['score_count']
    
    # 2. Calculate Mean Appearance of Critique Keywords per Year (Sum / Count)
    df_issue_trend = df_issues_filtered.groupby(['Year', 'Metric']).agg(
        issue_sum=('Sum', 'sum'), issue_count=('Count', 'sum')
    ).reset_index()
    df_issue_trend = df_issue_trend[df_issue_trend['issue_count'] > 0]
    df_issue_trend['Mean Appearance'] = df_issue_trend['issue_sum'] / df_issue_trend['issue_count']
    
    if not df_score_trend.empty and not df_issue_trend.empty:
        # Prepare and merge consolidated data
        df_issue_pivot = df_issue_trend.pivot(index='Year', columns='Metric', values='Mean Appearance').reset_index()
        df_combined = pd.merge(df_score_trend[['Year', 'Average Score']], df_issue_pivot, on='Year', how='outer').sort_values('Year')
        critique_metrics = [col for col in df_issue_pivot.columns if col != 'Year']
        
        # ---------------------------------------------------------------------
        # NEW: Dynamic Dropdown Selector to prevent string matching errors
        # ---------------------------------------------------------------------
        st.markdown("### 🎯 Interactive Focus Target")
        selected_target_metric = st.selectbox(
            "Select which critique metric to plot on the right-hand bar chart:",
            options=critique_metrics,
            index=0 if critique_metrics else None,
            key="tab5_metric_selector"
        )
        st.markdown("---")
        
        # Display side-by-side updated graphs
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("##### 1. Unified Temporal Chart (Dual Y-Axis)")
            fig_combined = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Primary axis: Average Score (Vibrant Green)
            fig_combined.add_trace(
                go.Scatter(
                    x=df_combined['Year'], y=df_combined['Average Score'], 
                    name="Average Score (Left Axis)", mode='lines+markers',
                    line=dict(color="#2ca02c", width=4)
                ),
                secondary_y=False,
            )
            
            # Secondary axis: All Critique Metrics
            for metric in critique_metrics:
                fig_combined.add_trace(
                    go.Scatter(
                        x=df_combined['Year'], y=df_combined[metric], 
                        name=f"Critique: {metric} (Right Axis)", mode='lines+markers'
                    ),
                    secondary_y=True,
                )
                
            fig_combined.update_layout(
                title_text="Scores & Critiques Over Time",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_combined.update_yaxes(title_text="<b>Average Score</b> (Green)", secondary_y=False)
            fig_combined.update_yaxes(title_text="<b>Critique Mean Appearance</b> (Others)", secondary_y=True)
            st.plotly_chart(fig_combined, use_container_width=True)
            
        with col_right:
            st.markdown(f"##### 2. Direct Correlation Chart (X: Score, Y: {selected_target_metric})")
            
            if selected_target_metric:
                # To make the relationship readable, sort by Average Score ascending
                df_sorted_by_score = df_combined.sort_values('Average Score')
                
                # Convert X-axis to string temporarily so Plotly treats the scores as distinct ranked groups
                df_sorted_by_score['Score_Label'] = df_sorted_by_score['Average Score'].round(3).astype(str)
                
                fig_corr = px.bar(
                    df_sorted_by_score, 
                    x='Score_Label', 
                    y=selected_target_metric, 
                    hover_data=['Year', 'Average Score'],
                    title=f"Distribution of '{selected_target_metric}' across Ranked Average Scores",
                    labels={'Score_Label': 'Average Score (X Axis - Ranked)', selected_target_metric: f'{selected_target_metric} Mean Appearance'}
                )
                fig_corr.update_traces(marker_color='#d62728', marker_line_color='DarkSlateGrey', marker_line_width=1)
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("No text critique metrics available to map in this view.")
            
        # 3. Dynamic Correlation Data Table
        st.markdown("##### 📋 Consolidated Correlation Matrix")
        float_cols = [col for col in df_combined.columns if col != 'Year']
        st.dataframe(
            df_combined.style.format({col: '{:.3f}' for col in float_cols}), 
            use_container_width=True
        )
    else:
        st.info("Insufficient data available to compile a comparative trend line.")
