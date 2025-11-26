
import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from pathlib import Path

# Configure the page
st.set_page_config(
    page_title="FAB Financial Analyzer",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with your color scheme
st.markdown("""
<style>
    /* Main background and text colors */
    .main {
        background-color: #ffffff;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 0px;
        margin-bottom: 2rem;
        color: white;
    }
    .header-content {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    .header-text {
        flex: 1;
    }
    .logo-container {
        flex-shrink: 0;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        color: white;
    }
    .header-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        line-height: 1.5;
        color: white;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Metric boxes */
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        border-left: 4px solid #dc3545;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .metric-change {
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    /* Result boxes */
    .result-box {
        background-color: #f0f8ff;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #1e3c72;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #c82333 0%, #a71e2a 100%);
        color: white;
    }
    
    /* Example query buttons */
    .example-query {
        background: linear-gradient(135deg, #87CEEB 0%, #a8d8f0 100%);
        border: none;
        color: #1e3c72;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        width: 100%;
        text-align: left;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .example-query:hover {
        background: linear-gradient(135deg, #76b4d6 0%, #95c8e8 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem;
        text-align: center;
        margin-top: 3rem;
        border-radius: 0px;
    }
    
    /* Capabilities section */
    .capability-item {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo and text
def render_header():
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Try to load the logo image
        try:
            logo_path = Path("logo.png")
            if logo_path.exists():
                st.image(str(logo_path), width=120)
            else:
                st.markdown("🏦")  # Fallback emoji
        except:
            st.markdown("🏦")  # Fallback emoji
    
    with col2:
        st.markdown(
            """
            <div class="header-text">
                <div class="header-title">First Abu Dhabi Bank</div>
                <div class="header-subtitle">
                    First Abu Dhabi Bank (FAB) is the UAE's largest bank and one of the world's largest 
                    and safest financial institutions. Our AI-powered financial analyzer provides deep 
                    insights into FAB's financial performance and strategic direction.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# Footer
def render_footer():
    st.markdown(
        """
        <div class="footer">
            <h4>FAB Financial Analysis Multi-Agent System</h4>
            <p>Built with advanced AI technology to deliver comprehensive financial insights</p>
            <p><strong>Developed by Abhijeet Dhulekar</strong></p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Sample metrics display
def render_sample_metrics():
    st.markdown("### 📈 Live Financial Metrics")
    
    sample_metrics = [
        {"metric": "Net Profit Q1 2022", "value": "AED 5,120M", "change": "+107% YoY", "icon": "💰"},
        {"metric": "Total Assets 2023", "value": "AED 981,163M", "change": "+4% YoY", "icon": "🏦"},
        {"metric": "Return on Equity", "value": "25.0%", "change": "Record High", "icon": "📊"},
        {"metric": "Loan-to-Deposit Ratio", "value": "72.3%", "change": "Stable", "icon": "⚖️"},
        {"metric": "Customer Deposits", "value": "AED 368,700M", "change": "+5% Growth", "icon": "💳"},
        {"metric": "Shareholder Equity", "value": "AED 110,992M", "change": "Strong", "icon": "👥"}
    ]
    
    cols = st.columns(3)
    for i, metric in enumerate(sample_metrics):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-value">{metric['icon']} {metric['value']}</div>
                    <div class="metric-label">{metric['metric']}</div>
                    <div class="metric-change" style="color: {'#28a745' if 'Growth' in metric['change'] or 'High' in metric['change'] or 'Strong' in metric['change'] else '#17a2b8'}">
                        {metric['change']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# Main application
def main():
    # Render header
    render_header()
    
    # Sidebar
    st.sidebar.title("⚙️ Configuration")
    api_url = st.sidebar.text_input("API URL", "http://localhost:8000")
    
    # Health check
    with st.sidebar:
        st.markdown("### 🔍 System Status")
        try:
            health_response = requests.get(f"{api_url}/health", timeout=5)
            if health_response.status_code == 200:
                health_data = health_response.json()
                if health_data.get("status") == "healthy":
                    st.success("✅ API Connected")
                    st.metric("Documents in DB", health_data.get("documents_in_db", "N/A"))
                else:
                    st.warning("⚠️ API Degraded")
            else:
                st.error("❌ API Connection Failed")
        except:
            st.error("❌ Cannot reach API")
    
    # Main content layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🤖 Financial Analysis Query")
        
        # Example queries
        with st.expander("💡 Example Queries", expanded=True):
            examples = [
                "How has FAB's Return on Equity (ROE) trended over the last 6 quarters? Calculate the ROE for each quarter and identify the best and worst performing quarters.",
                "Compare FAB's loan-to-deposit ratio between Q4 2022 and Q4 2023. Has the bank's lending activity increased or decreased relative to its deposit base?",
                "What were the top 3 risk factors mentioned in the 2023 annual report, and how did management address them in subsequent quarters?",
                "Calculate the net interest margin for Q1 2022 and Q1 2023. What factors contributed to the change?",
                "Analyze the trend in total assets over the last 8 quarters and identify any significant growth patterns."
            ]
            
            for example in examples:
                if st.button(example, key=example):
                    st.session_state.query = example
        
        # Query input
        query = st.text_area(
            "Enter your financial analysis question:",
            height=120,
            placeholder="e.g., What was the year-over-year percentage change in Net Profit between Q3 2022 and Q3 2023? Calculate the growth rate and explain the key factors driving this change.",
            value=st.session_state.get("query", "")
        )
        
        # Analysis options
        col1a, col1b = st.columns(2)
        with col1a:
            include_calculations = st.checkbox("Include Detailed Calculations", value=True)
        with col1b:
            include_sources = st.checkbox("Include Sources", value=True)
        
        # Analyze button
        if st.button("🚀 Analyze", type="primary", use_container_width=True):
            if query:
                with st.spinner("🔍 Analyzing financial data with AI agents..."):
                    try:
                        # Call the API
                        response = requests.post(
                            f"{api_url}/analyze",
                            json={
                                "query": query,
                                "include_calculations": include_calculations,
                                "include_sources": include_sources
                            },
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Display results
                            st.success("✅ Analysis Complete!")
                            
                            # Main answer
                            st.markdown("### 📋 Analysis Results")
                            st.markdown(f'<div class="result-box">{result["answer"]}</div>', unsafe_allow_html=True)
                            
                            # Confidence indicator
                            confidence = result["confidence"]
                            st.progress(confidence)
                            st.caption(f"Confidence Level: {confidence:.0%}")
                            
                            # Calculations section
                            if include_calculations and result["calculations"]:
                                st.markdown("### 🧮 Detailed Calculations")
                                
                                for calc in result["calculations"]:
                                    calc_type = calc.get('calculation_type', 'unknown')
                                    
                                    if calc_type == 'percentage_change':
                                        st.metric(
                                            label="Percentage Change",
                                            value=f"{calc['percentage_change']:+.1f}%",
                                            delta=f"AED {calc['absolute_change']:,.0f}M",
                                            delta_color="normal"
                                        )
                                    elif calc_type == 'roe':
                                        st.metric(
                                            label="Return on Equity",
                                            value=f"{calc['roe_percentage']:.1f}%"
                                        )
                                    elif calc_type == 'trend_analysis':
                                        # Create trend visualization
                                        df = pd.DataFrame({
                                            'Period': calc['periods'],
                                            'Value': calc['values']
                                        })
                                        
                                        fig = px.line(
                                            df, 
                                            x='Period', 
                                            y='Value',
                                            title=f"{calc.get('metric', 'Metric').replace('_', ' ').title()} Trend",
                                            markers=True,
                                            color_discrete_sequence=['#1e3c72']
                                        )
                                        fig.update_layout(
                                            plot_bgcolor='rgba(0,0,0,0)',
                                            paper_bgcolor='rgba(0,0,0,0)',
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                            
                            # Data points
                            if result["data_points"]:
                                st.markdown("### 📊 Extracted Financial Data")
                                df_data = pd.DataFrame([
                                    {
                                        'Metric': dp['metric'].replace('_', ' ').title(),
                                        'Value (AED M)': f"{dp['value']:,.0f}",
                                        'Period': dp['period'],
                                        'Source': f"{dp['metadata']['document_type']} {dp['metadata']['year']} {dp['metadata']['quarter']}"
                                    }
                                    for dp in result["data_points"]
                                ])
                                st.dataframe(df_data, use_container_width=True)
                            
                            # Processing time
                            st.caption(f"⏱️ Processing time: {result['processing_time']:.2f} seconds")
                        
                        else:
                            st.error(f"❌ API Error: {response.status_code} - {response.text}")
                    
                    except requests.exceptions.Timeout:
                        st.error("⏰ Request timed out. The analysis is taking longer than expected.")
                    except Exception as e:
                        st.error(f"❌ Error calling analysis API: {str(e)}")
            else:
                st.warning("⚠️ Please enter a query to analyze.")
    
    with col2:
        # Sample Metrics
        render_sample_metrics()
        
        # Capabilities
        st.markdown("### 🛠️ System Capabilities")
        
        capabilities = [
            "Temporal analysis and comparisons",
            "Financial ratio calculations", 
            "Trend analysis and pattern recognition",
            "Risk factor identification and assessment",
            "Management commentary synthesis",
            "Multi-document cross-referencing",
            "Real-time financial metric extraction"
        ]
        
        for capability in capabilities:
            st.markdown(
                f"""
                <div class="capability-item">
                    ✅ {capability}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        if st.button("🔄 Test Connection", use_container_width=True):
            try:
                response = requests.get(f"{api_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ Connection successful!")
                else:
                    st.error("❌ Connection failed")
            except:
                st.error("❌ Cannot connect to API")
        
        if st.button("📊 View API Docs", use_container_width=True):
            st.info(f"Open [API Documentation]({api_url}/docs) in your browser")

# Initialize session state
if 'query' not in st.session_state:
    st.session_state.query = ""

if __name__ == "__main__":
    main()
    render_footer()