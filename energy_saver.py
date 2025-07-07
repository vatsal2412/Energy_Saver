import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Page configuration
st.set_page_config(
    page_title="Daily Energy Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    .energy-tip {
        background: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'energy_data' not in st.session_state:
        st.session_state.energy_data = []
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {}

def calculate_base_energy(facility):
    """Calculate base energy consumption based on apartment type"""
    energy_map = {
        "1bhk": 2 * 0.4 + 2 * 0.8,  # 2.4 kWh
        "2bhk": 3 * 0.4 + 3 * 0.8,  # 3.6 kWh
        "3bhk": 4 * 0.4 + 4 * 0.8   # 4.8 kWh
    }
    return energy_map.get(facility.lower(), 0)

def calculate_appliance_energy(appliances):
    """Calculate energy consumption from appliances"""
    appliance_consumption = {
        'AC': 3.0,
        'Refrigerator': 3.0,
        'Washing Machine': 3.0,
        'TV': 0.5,
        'Microwave': 1.5,
        'Water Heater': 2.0,
        'Dishwasher': 2.5,
        'Ceiling Fan': 0.3
    }
    
    total = 0
    for appliance in appliances:
        total += appliance_consumption.get(appliance, 0)
    return total

def save_daily_consumption(date, base_energy, appliance_energy, total_energy, appliances, notes=""):
    """Save daily energy consumption data"""
    entry = {
        'date': date.strftime('%Y-%m-%d'),
        'base_energy': base_energy,
        'appliance_energy': appliance_energy,
        'total_energy': total_energy,
        'appliances': appliances,
        'notes': notes,
        'timestamp': datetime.now().isoformat()
    }
    
    # Check if entry for this date already exists
    existing_index = None
    for i, record in enumerate(st.session_state.energy_data):
        if record['date'] == date.strftime('%Y-%m-%d'):
            existing_index = i
            break
    
    if existing_index is not None:
        st.session_state.energy_data[existing_index] = entry
    else:
        st.session_state.energy_data.append(entry)

def get_energy_dataframe():
    """Convert energy data to DataFrame for analysis"""
    if not st.session_state.energy_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(st.session_state.energy_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    return df

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>⚡ Daily Energy Consumption Tracker</h1>
        <p>Monitor and analyze your household energy usage patterns</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for user profile
    with st.sidebar:
        st.header("👤 User Profile")
        
        name = st.text_input("Name", value=st.session_state.user_profile.get('name', ''))
        age = st.number_input("Age", min_value=1, max_value=120, 
                             value=st.session_state.user_profile.get('age', 25))
        city = st.text_input("City", value=st.session_state.user_profile.get('city', ''))
        area = st.text_input("Area", value=st.session_state.user_profile.get('area', ''))
        
        flat_type = st.selectbox("Housing Type", 
                                ["Flat", "Tenement"],
                                index=0 if st.session_state.user_profile.get('flat_type') != 'Tenement' else 1)
        
        facility = st.selectbox("Apartment Size", 
                               ["1BHK", "2BHK", "3BHK"],
                               index=["1BHK", "2BHK", "3BHK"].index(st.session_state.user_profile.get('facility', '1BHK')))
        
        if st.button("💾 Save Profile"):
            st.session_state.user_profile = {
                'name': name, 'age': age, 'city': city, 'area': area,
                'flat_type': flat_type, 'facility': facility
            }
            st.success("Profile saved!")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Daily Entry", "📈 Analytics", "🏆 Insights", "📋 History"])
    
    with tab1:
        st.header("Daily Energy Consumption Entry")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Date selection
            selected_date = st.date_input("Select Date", datetime.now())
            
            # Appliances selection
            st.subheader("🔌 Appliances Used Today")
            appliances = st.multiselect(
                "Select appliances used:",
                ["AC", "Refrigerator", "Washing Machine", "TV", "Microwave", 
                 "Water Heater", "Dishwasher", "Ceiling Fan"],
                default=["Refrigerator"]
            )
            
            # Usage hours for major appliances
            usage_hours = {}
            if appliances:
                st.subheader("⏱️ Usage Hours")
                for appliance in appliances:
                    if appliance in ["AC", "TV", "Microwave", "Water Heater"]:
                        usage_hours[appliance] = st.slider(
                            f"{appliance} hours", 0.0, 24.0, 8.0 if appliance == "AC" else 2.0, 0.5
                        )
            
            # Additional notes
            notes = st.text_area("📝 Notes (optional)", 
                               placeholder="Any special circumstances, power outages, etc.")
            
        with col2:
            if st.session_state.user_profile:
                # Calculate energy consumption
                base_energy = calculate_base_energy(st.session_state.user_profile.get('facility', '1BHK'))
                appliance_energy = calculate_appliance_energy(appliances)
                
                # Adjust for usage hours
                adjusted_appliance_energy = appliance_energy
                for appliance, hours in usage_hours.items():
                    if appliance in ["AC", "TV", "Microwave", "Water Heater"]:
                        base_consumption = {"AC": 3.0, "TV": 0.5, "Microwave": 1.5, "Water Heater": 2.0}
                        adjusted_appliance_energy += (base_consumption[appliance] * hours / 8) - base_consumption[appliance]
                
                total_energy = base_energy + adjusted_appliance_energy
                
                # Display energy breakdown
                st.subheader("⚡ Energy Breakdown")
                
                # Create metrics
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Base Energy", f"{base_energy:.1f} kWh", 
                             help="Energy from lighting and basic electrical needs")
                with col_m2:
                    st.metric("Appliance Energy", f"{adjusted_appliance_energy:.1f} kWh",
                             help="Energy from selected appliances")
                with col_m3:
                    st.metric("Total Energy", f"{total_energy:.1f} kWh",
                             help="Total daily energy consumption")
                
                # Energy cost estimation (assuming ₹5 per kWh)
                estimated_cost = total_energy * 5
                st.info(f"💰 Estimated daily cost: ₹{estimated_cost:.2f}")
                
                # Save data button
                if st.button("💾 Save Today's Consumption", type="primary"):
                    save_daily_consumption(selected_date, base_energy, adjusted_appliance_energy, 
                                         total_energy, appliances, notes)
                    st.success(f"✅ Energy data saved for {selected_date}")
                    st.rerun()
            else:
                st.warning("Please complete your profile in the sidebar first!")
    
    with tab2:
        st.header("📈 Energy Consumption Analytics")
        
        df = get_energy_dataframe()
        
        if not df.empty:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Days Tracked", len(df))
            with col2:
                st.metric("Avg Daily Consumption", f"{df['total_energy'].mean():.1f} kWh")
            with col3:
                st.metric("Highest Consumption", f"{df['total_energy'].max():.1f} kWh")
            with col4:
                st.metric("Monthly Estimate", f"{df['total_energy'].mean() * 30:.1f} kWh")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Daily consumption trend
                fig_line = px.line(df, x='date', y='total_energy', 
                                 title="Daily Energy Consumption Trend",
                                 labels={'total_energy': 'Energy (kWh)', 'date': 'Date'})
                fig_line.update_layout(height=400)
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col2:
                # Energy breakdown pie chart
                avg_base = df['base_energy'].mean()
                avg_appliance = df['appliance_energy'].mean()
                
                fig_pie = px.pie(values=[avg_base, avg_appliance], 
                               names=['Base Energy', 'Appliance Energy'],
                               title="Average Energy Breakdown")
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Weekly comparison
            if len(df) >= 7:
                df['week'] = df['date'].dt.isocalendar().week
                weekly_avg = df.groupby('week')['total_energy'].mean().reset_index()
                
                fig_bar = px.bar(weekly_avg, x='week', y='total_energy',
                               title="Weekly Average Energy Consumption")
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No data available yet. Start tracking your daily energy consumption!")
    
    with tab3:
        st.header("🏆 Energy Insights & Recommendations")
        
        df = get_energy_dataframe()
        
        if not df.empty:
            # Energy efficiency score
            avg_consumption = df['total_energy'].mean()
            if avg_consumption < 5:
                efficiency_score = "Excellent ⭐⭐⭐⭐⭐"
                score_color = "green"
            elif avg_consumption < 8:
                efficiency_score = "Good ⭐⭐⭐⭐"
                score_color = "blue"
            elif avg_consumption < 12:
                efficiency_score = "Average ⭐⭐⭐"
                score_color = "orange"
            else:
                efficiency_score = "Needs Improvement ⭐⭐"
                score_color = "red"
            
            st.markdown(f"""
            <div style="background: {score_color}; color: white; padding: 1rem; border-radius: 10px; text-align: center;">
                <h3>Energy Efficiency Score: {efficiency_score}</h3>
                <p>Average Daily Consumption: {avg_consumption:.1f} kWh</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Insights and recommendations
            st.subheader("💡 Personalized Recommendations")
            
            recommendations = []
            
            if df['appliance_energy'].mean() > df['base_energy'].mean() * 2:
                recommendations.append("Consider upgrading to energy-efficient appliances")
            
            if avg_consumption > 10:
                recommendations.append("Your consumption is above average. Try to reduce AC usage during peak hours")
            
            if len(df) >= 7:
                recent_week = df.tail(7)['total_energy'].mean()
                previous_week = df.head(7)['total_energy'].mean() if len(df) >= 14 else recent_week
                
                if recent_week > previous_week * 1.1:
                    recommendations.append("Your energy consumption has increased recently. Check for any new appliances or increased usage")
                elif recent_week < previous_week * 0.9:
                    recommendations.append("Great job! Your energy consumption has decreased recently")
            
            recommendations.extend([
                "Use natural light during daytime to reduce electricity usage",
                "Set your AC to 24-26°C for optimal efficiency",
                "Unplug devices when not in use to avoid phantom loads",
                "Consider using LED bulbs if you haven't already"
            ])
            
            for i, rec in enumerate(recommendations[:5]):
                st.markdown(f"""
                <div class="energy-tip">
                    <strong>Tip {i+1}:</strong> {rec}
                </div>
                """, unsafe_allow_html=True)
            
            # Monthly projection
            st.subheader("📊 Monthly Projection")
            monthly_kwh = avg_consumption * 30
            monthly_cost = monthly_kwh * 5  # ₹5 per kWh
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Projected Monthly Usage", f"{monthly_kwh:.1f} kWh")
            with col2:
                st.metric("Projected Monthly Cost", f"₹{monthly_cost:.2f}")
        else:
            st.info("Start tracking your energy consumption to get personalized insights!")
    
    with tab4:
        st.header("📋 Energy Consumption History")
        
        df = get_energy_dataframe()
        
        if not df.empty:
            # Display data table
            display_df = df.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df = display_df[['date', 'total_energy', 'base_energy', 'appliance_energy', 'appliances', 'notes']]
            display_df.columns = ['Date', 'Total Energy (kWh)', 'Base Energy (kWh)', 'Appliance Energy (kWh)', 'Appliances', 'Notes']
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export data
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"energy_consumption_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # Clear data option
            st.subheader("🗑️ Data Management")
            if st.button("Clear All Data", type="secondary"):
                if st.checkbox("I understand this will delete all my data"):
                    st.session_state.energy_data = []
                    st.success("All data cleared!")
                    st.rerun()
        else:
            st.info("No energy consumption data available yet.")

if __name__ == "__main__":
    main()