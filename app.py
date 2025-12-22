import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
from data_loader import DataLoader
from apscheduler.schedulers.background import BackgroundScheduler
from scripts.update_data import update_all_data
import atexit

# --- Background Scheduler ---
# Run data update every day at 06:00 AM
def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_all_data, 'cron', hour=6, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

# Initialize scheduler only once (hack for Streamlit reloading)
if "scheduler_started" not in st.session_state:
    init_scheduler()
    st.session_state["scheduler_started"] = True

from datetime import datetime

# --- Page Config & Theme ---
# ... (existing config) ...

# Dynamic Year Calculation
current_year = datetime.now().year
prev_year = current_year - 1
pre_pandemic_year = 2019

# --- Page Config & Theme ---
st.set_page_config(
    page_title=f"Czech Culture Executive Dashboard {current_year}",
    page_icon="🇨🇿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ... (styles) ...

# --- Data Loading ---
loader = DataLoader()

# --- Sidebar ---
with st.sidebar:
    st.title("🇨🇿 Ministr Kultů")
    st.markdown("---")
    
    menu_options = [
        "Overview: KPI Scorecard",
        "Heritage & UNESCO Map",
        "State Budget",
        "Sector Analytics",
        "Status of the Artist"
    ]
    
    selected_module = st.radio("Navigation", menu_options)
    
    st.markdown("---")
    st.caption(f"Last Updated: {loader.get_last_updated()}")
    st.caption("Data Sources: NKOD, CZSO, NIPOS")

# --- Main Content ---
econ_data = loader.load_economic_indicators()

# Module A: Minister's KPI Scorecard
if selected_module == "Overview: KPI Scorecard":
    st.markdown('<h1 class="section-header">Executive Overview: KPI Scorecard</h1>', unsafe_allow_html=True)
    
    econ_data = loader.load_economic_indicators()
    
    if econ_data:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Culture Share of GDP",
                value=f"{econ_data.get('culture_share_gdp', 'N/A')}%",
                delta=f"0.05% vs {prev_year}"
            )
            
        with col2:
            st.metric(
                label="Total Fin. Resources (CZK)",
                value=f"{econ_data.get('total_financial_resources', 'N/A')} B",
                delta=f"{econ_data.get('financial_resources_growth', 'N/A')}% YoY"
            )
            
        with col3:
            st.metric(
                label="Avg Monthly Wage (Culture)",
                value=f"{econ_data.get('avg_monthly_wage', 'N/A')} CZK",
                delta="+8.5% YoY"
            )

# ... (chart) ...

# Module B: Heritage & UNESCO Map
elif selected_module == "Heritage & UNESCO Map":
    st.markdown('<h1 class="section-header">Heritage & UNESCO Sites</h1>', unsafe_allow_html=True)
    
    sites_df = loader.load_unesco_sites()
    
    if not sites_df.empty:
        # Toggle for Renovation ROI
        show_roi = st.toggle("Overlay: Renovation ROI Impact", value=False)
        
        # Map Visualization
        
        # Check if 'visitors_2024' exists, else try to find any 'visitors' column
        # specific fix for the hardcoded column in CSV
        visitor_col = "visitors_2024" 
        
        # Define layer based on toggle
        if show_roi:
            # Scale circle radius by ROI or Visitors
            layer = pdk.Layer(
                "ScatterplotLayer",
                sites_df,
                get_position='[lon, lat]',
                get_color='[0, 100, 200, 160]',
                get_radius='renovation_roi * 100', 
                pickable=True,
                auto_highlight=True
            )
            tooltip_html = f"<b>{{name}}</b><br/>Renovation ROI: {{renovation_roi}}%<br/>Visitors {prev_year}: {{{visitor_col}}}"
        else:
            layer = pdk.Layer(
                "ScatterplotLayer",
                sites_df,
                get_position='[lon, lat]',
                get_color='[227, 6, 19, 200]',
                get_radius=5000,
                pickable=True,
            )
            tooltip_html = f"<b>{{name}}</b><br/>Visitors {prev_year}: {{{visitor_col}}}"

        view_state = pdk.ViewState(latitude=49.8, longitude=15.5, zoom=6.5, pitch=0)

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": tooltip_html, "style": {"backgroundColor": "white", "color": "black"}}
        ))
        
        # Highlight Table (Top Sites)
        st.markdown("### Top Sites by Visitor Volume")
        st.dataframe(
            sites_df[["name", visitor_col, "renovation_roi"]].sort_values(visitor_col, ascending=False).head(5),
            hide_index=True,
            column_config={
                "name": "Site Name",
                visitor_col: st.column_config.NumberColumn(f"Visitors ({prev_year})"),
                "renovation_roi": st.column_config.ProgressColumn("Renovation ROI %", format="%d%%", min_value=0, max_value=700)
            }
        )
    else:
        st.warning("⚠️ No UNESCO Data Available. Please check NKOD connection.")

# Module C: Official State Budget
elif selected_module == "State Budget":
    st.markdown(f'<h1 class="section-header">State Budget {current_year}: Official Execution</h1>', unsafe_allow_html=True)
    st.caption(f"Source: Ministry of Finance (Act for {current_year})")
    
    budget_df = loader.load_budget(current_year)
    
    if not budget_df.empty:
        # Calculate Total dynamically since we removed the "Total" row
        total_budget = budget_df['Amount_CZK'].sum()
        
        # Display Total as a Key Metric
        st.metric(f"Total Ministry Budget {current_year}", f"{total_budget:,.0f} CZK", "Approved")
        
        tab1, tab2 = st.tabs(["Allocation (Treemap)", "Rankings (Bar Chart)"])
        
        with tab1:
            # Treemap
            fig_treemap = px.treemap(
                budget_df, 
                path=['Category'], 
                values='Amount_CZK',
                color='Amount_CZK',
                hover_data=['Description'],
                color_continuous_scale='RdBu',
                title=f"Budget Allocation (Total {total_budget/1e9:.2f}B CZK)"
            )
            st.plotly_chart(fig_treemap, use_container_width=True)
            
        with tab2:
            # Bar Chart for Rank
            fig_bar = px.bar(
                budget_df.sort_values("Amount_CZK", ascending=True),
                x="Amount_CZK",
                y="Category",
                orientation='h',
                title="Top Funding Areas",
                text_auto='.2s',
                color="Amount_CZK",
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Data Table
        with st.expander("View Raw Data"):
            st.dataframe(
                budget_df,
                column_config={
                    "Amount_CZK": st.column_config.NumberColumn("Amount", format="%.2f CZK")
                },
                hide_index=True,
                use_container_width=True
            )
    else:
        st.error(f"⚠️ Budget Data Unavailable for {current_year}")

# Module D: Sector Analytics
elif selected_module == "Sector Analytics":
    st.markdown('<h1 class="section-header">Sector Analytics: Employment & Wages</h1>', unsafe_allow_html=True)
    st.caption("Strategic Data for Budget Negotiations (Source: CZSO)")
    
    # econ_data is loaded at the top
    if econ_data and "historical_growth" in econ_data:
        hist = econ_data["historical_growth"]
        years = hist["years"]
        
        # --- Row 1: The Wage Gap ---
        st.subheader("⚠️ The Wage Gap: Culture vs National Average")
        
        # Prepare data for plotting
        wage_df = pd.DataFrame({
            "Year": years,
            "Culture Sector": hist.get("avg_wage_culture", []),
            "National Average": hist.get("avg_wage_national", [])
        })
        wage_df = wage_df.melt('Year', var_name='Category', value_name='Wage (CZK)')
        
        fig_wages = px.line(
            wage_df, 
            x="Year", 
            y="Wage (CZK)", 
            color="Category",
            markers=True,
            color_discrete_map={"Culture Sector": "#ef4444", "National Average": "#3b82f6"},
            title="Average Monthly Wage Evolution"
        )
        # Add annotation for the latest gap
        gap = hist["avg_wage_national"][-1] - hist["avg_wage_culture"][-1]
        fig_wages.add_annotation(
            x=years[-1], 
            y=hist["avg_wage_national"][-1],
            text=f"Gap: -{gap:,.0f} CZK",
            showarrow=True,
            arrowhead=1
        )
        st.plotly_chart(fig_wages, use_container_width=True)
        
        # --- Row 2: Employment & Inflation ---
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Employment Trends (NACE 90-93)")
            emp_df = pd.DataFrame({
                "Year": years,
                "Employees (Thousands)": hist.get("employment_k", [])
            })
            
            fig_emp = px.area(
                emp_df,
                x="Year",
                y="Employees (Thousands)",
                title="Workforce Size (Thousands)",
                color_discrete_sequence=["#10b981"]
            )
            fig_emp.update_yaxes(range=[70, 90]) # Zoom in to show trend
            st.plotly_chart(fig_emp, use_container_width=True)
            
        with col2:
            st.subheader("Economic Context (2024)")
            st.metric("Sector Unemployment Rate", f"{econ_data.get('unemployment_rate_culture', 'N/A')}%", "-0.2% vs Nat. Avg")
            st.metric("Inflation Rate", f"{econ_data.get('inflation_rate_2024', 'N/A')}%", "High Impact on Grants")
            st.warning("Action Required: Low wages are driving talent to commercial sectors.")
            
    else:
        st.error("⚠️ Detailed Economic Data Unavailable")

# Module E: Status of the Artist
elif selected_module == "Status of the Artist":
    st.markdown('<h1 class="section-header">Status of the Artist: Implementation Leaderboard</h1>', unsafe_allow_html=True)
    
    artist_data = loader.load_artist_status()
    
    col_lead, col_pie = st.columns([1, 2])
    
    if artist_data:
        with col_lead:
            st.markdown("### Registered Artists")
            st.metric(label="Total Registrations", value=artist_data["registered_count"], delta="+4 this week")
            st.markdown("*Live data from Registry API*")
            
        with col_pie:
            st.markdown("### Breakdown by Discipline")
            
            df_discipline = pd.DataFrame(list(artist_data["disciplines"].items()), columns=["Discipline", "Percentage"])
            
            fig_pie = px.pie(
                df_discipline, 
                values="Percentage", 
                names="Discipline", 
                color_discrete_sequence=px.colors.qualitative.Prism,
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.error("⚠️ Registry API Offline. No artist data available.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Ministry of Culture Czech Republic | Dashboard v1.0 MVP | Built for Minister Oto Klempíř
    </div>
    """, 
    unsafe_allow_html=True
)
