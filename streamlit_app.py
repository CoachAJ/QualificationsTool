#!/usr/bin/env python3
"""
Youngevity Strategy Tool - Streamlit Web Application
A user-friendly web interface for YGY strategic analysis and rank optimization.
"""

import streamlit as st
import pandas as pd
import os
import tempfile
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional

# Import functions from the main script (ImportError fix applied)
from ygy_data_setup import (
    load_csv_files,
    create_team_data_dictionary,
    build_downline_tree,
    calculate_hierarchical_levels,
    find_organizational_root,
    get_member_summary,
    calculate_all_ranks,
    analyze_member_qualifications,
    identify_strategic_assets,
    suggest_pqv_moves,
    suggest_leg_moves,
    suggest_placement_moves,
    analyze_leader_strategic_moves,
    get_current_date_la_timezone,
    get_analysis_order,
    get_strategic_analysis_summary,
    RANK_REQUIREMENTS,
    RANK_HIERARCHY
)

# Page configuration
st.set_page_config(
    page_title="Daily With Doc - Youngevity Strategy Tool",
    page_icon="🌻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Daily With Doc Brand Guidelines
st.markdown("""
<style>
    /* Daily With Doc Brand Colors */
    :root {
        --blue-fog: #71C6DB;
        --orange: #F3A234;
        --dark-blue: #0A4572;
        --medium-gray: #7D7D7D;
        --very-dark-blue: #4A4A4A;
        --white: #FFFFFF;
        --black: #000000;
    }
    
    .main-header {
        font-size: 2.5rem;
        color: var(--dark-blue);
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .section-header {
        font-size: 1.5rem;
        color: var(--orange);
        margin-top: 2rem;
        margin-bottom: 1rem;
        font-weight: 600;
        border-bottom: 2px solid var(--blue-fog);
        padding-bottom: 0.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--white) 0%, #f8f9fa 100%);
        border: 2px solid var(--blue-fog);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .success-box {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        border-left: 5px solid var(--orange);
        border-radius: 6px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff8e1 0%, #fff3cd 100%);
        border-left: 5px solid var(--dark-blue);
        border-radius: 6px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .info-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid var(--blue-fog);
        border-radius: 6px;
        padding: 1.2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .brand-accent {
        color: var(--orange);
        font-weight: 600;
    }
    
    .brand-blue {
        color: var(--dark-blue);
        font-weight: 600;
    }
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--orange) 0%, #e8941f 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #e8941f 0%, var(--orange) 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--blue-fog) 0%, #5bb8d1 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 2px solid var(--blue-fog);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--medium-gray);
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        color: var(--dark-blue) !important;
        border-bottom: 3px solid var(--orange) !important;
    }
    
    /* Priority table styling */
    .priority-1 {
        background: linear-gradient(135deg, var(--orange) 0%, #f3a234cc 100%);
        color: white;
        font-weight: bold;
    }
    
    .analysis-candidate {
        background: linear-gradient(135deg, var(--blue-fog) 0%, #71c6dbcc 100%);
        color: var(--very-dark-blue);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🌻 Daily With Doc - Youngevity Strategy Tool</h1>', unsafe_allow_html=True)
    st.markdown("**<span class='brand-accent'>Strategic Analysis & Rank Optimization</span> for <span class='brand-blue'>YGY Organizations</span>**", unsafe_allow_html=True)
    
    # Sidebar for file uploads
    st.sidebar.header("📁 Upload CSV Files")
    st.sidebar.markdown("<span class='brand-accent'>🌻 Daily With Doc</span><br>Upload your Youngevity CSV files to get started:", unsafe_allow_html=True)
    
    # File uploaders
    group_volume_file = st.sidebar.file_uploader(
        "Group Volume Details CSV",
        type=['csv'],
        help="Upload your Group Volume Details export from YGY back office"
    )
    
    genealogy_file = st.sidebar.file_uploader(
        "Advanced Genealogy Report CSV", 
        type=['csv'],
        help="Upload your Advanced Genealogy Report from YGY back office"
    )
    
    # Process files if both are uploaded
    if group_volume_file is not None and genealogy_file is not None:
        try:
            # Save uploaded files temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save files
                group_volume_path = os.path.join(temp_dir, "group_volume.csv")
                genealogy_path = os.path.join(temp_dir, "genealogy.csv")
                
                with open(group_volume_path, "wb") as f:
                    f.write(group_volume_file.getbuffer())
                
                with open(genealogy_path, "wb") as f:
                    f.write(genealogy_file.getbuffer())
                
                # Load and process data
                with st.spinner("Processing your data..."):
                    group_volume_df = pd.read_csv(group_volume_path)
                    genealogy_df = pd.read_csv(genealogy_path)
                    
                    # Process the data
                    team_data = create_team_data_dictionary(genealogy_df)
                    downline_tree = build_downline_tree(team_data)
                    hierarchical_levels = calculate_hierarchical_levels(team_data, downline_tree)
                    
                    # Store levels in team_data
                    for member_id, level in hierarchical_levels.items():
                        if member_id in team_data:
                            team_data[member_id]['hierarchical_level'] = level
                    
                    organizational_root = find_organizational_root(team_data)
                    calculated_ranks = calculate_all_ranks(team_data, downline_tree)
                    current_date = get_current_date_la_timezone()
                
                # Display results
                display_dashboard(group_volume_df, genealogy_df, team_data, downline_tree, calculated_ranks, current_date, organizational_root, hierarchical_levels)
                
        except Exception as e:
            st.error(f"Error processing files: {str(e)}")
            st.error("Please ensure your CSV files are in the correct YGY format.")
    
    else:
        # Show welcome message and instructions
        show_welcome_screen()

def show_welcome_screen():
    """Display welcome screen with instructions"""
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🚀 Get Started")
        st.markdown("""
        <div class="info-box">
        <h3 style="color: var(--dark-blue); margin-top: 0;">🌻 Welcome to Daily With Doc's Youngevity Strategy Tool!</h3>
        <p>Upload your CSV files to unlock powerful strategic insights for your YGY organization:</p>
        <ul>
        <li><span class="brand-accent">✨ Analyze</span> your team structure and rank distribution</li>
        <li><span class="brand-accent">🎯 Get strategic recommendations</span> for rank advancement</li>
        <li><span class="brand-accent">🚀 Identify optimal placement</span> and volume movement opportunities</li>
        <li><span class="brand-accent">📈 Maximize</span> your organization's growth potential</li>
        <li><span class="brand-accent">🤖 AI Strategic Advisor</span> - Get personalized advice with your own API key</li>
        </ul>
        <p><strong>Get started by uploading your CSV files in the sidebar</strong> →</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 What You'll Get")
        st.markdown("""
        **📊 Organization Analysis:**
        - Complete team structure and rank distribution
        - Volume analysis and performance metrics
        - Member summary statistics
        
        **🎯 Strategic Recommendations:**
        - PQV gap solutions with specific order moves
        - Leg development opportunities 
        - Strategic placement suggestions for new PCUSTs
        - 60-day movement window compliance
        
        **🔥 Phase 3 Features:**
        - Volume donor identification
        - Placeable asset analysis  
        - Personalized advancement strategies
        """)

def display_dashboard(group_volume_df, genealogy_df, team_data, downline_tree, calculated_ranks, current_date, organizational_root, hierarchical_levels):
    """Display the main dashboard with all analysis results"""
    
    # Organization Overview
    st.markdown('<h2 class="section-header">📊 Organization Overview</h2>', unsafe_allow_html=True)
    
    # Key metrics
    summary = get_member_summary(team_data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Members", summary['total_members'])
    
    with col2:
        st.metric("Distributors", summary['distributors'])
    
    with col3:
        st.metric("PCUSTs", summary['pcust'])
    
    with col4:
        st.metric("Active Members", summary['active_members'])
    
    # Organizational Structure
    if organizational_root:
        st.markdown("### 🌳 Organizational Structure")
        st.markdown("**Hierarchical Level Distribution:**")
        
        # Display the root
        root_info = team_data[organizational_root]
        current_rank = calculated_ranks.get(organizational_root, 'PCUST')
        
        st.markdown(f"**Level 0 (Head):** {root_info['name']} (ID: {organizational_root}) - {current_rank} - PQV: ${root_info.get('pqv', 0):.2f}")
        
        # Highlight if 102742703 is the root
        if organizational_root == '102742703':
            st.success("[SUCCESS] ID 102742703 confirmed as organizational head (Level 0)")
        
        # Count members at each level
        level_counts = {}
        for member_id, level in hierarchical_levels.items():
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Display level distribution
        st.markdown("**Team Depth Distribution:**")
        for level in sorted(level_counts.keys()):
            if level == 0:
                st.write(f"• Level 0 (Head): {level_counts[level]} member")
            else:
                distance = int(level * 10)  # Convert 0.1 to 1, 0.2 to 2, etc.
                st.write(f"• Level {level} ({distance} levels down): {level_counts[level]} members")
        
        st.markdown("---")
    
    # Rank Distribution
    st.markdown("### 🏆 Rank Distribution")
    rank_dist = {}
    for rank in calculated_ranks.values():
        rank_dist[rank] = rank_dist.get(rank, 0) + 1
    
    rank_df = pd.DataFrame(list(rank_dist.items()), columns=['Rank', 'Count'])
    rank_df = rank_df.sort_values('Count', ascending=False)
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(rank_df, use_container_width=True)
    
    with col2:
        st.bar_chart(rank_df.set_index('Rank'))
    
    # Top Performers Analysis
    st.markdown('<h2 class="section-header">🌟 Top Performers</h2>', unsafe_allow_html=True)
    
    top_performers = []
    for member_id, member_info in team_data.items():
        if member_info.get('pqv', 0) > 0:
            analysis = analyze_member_qualifications(member_id, team_data, downline_tree, calculated_ranks)
            top_performers.append({
                'ID': member_id,
                'Name': member_info['name'],
                'Current Rank': analysis['current_rank'],
                'PQV': analysis['pqv'],
                'GQV-3CL': analysis['gqv_3cl'],
                'Next Rank': analysis['next_achievable_rank'],
                'PQV Gap': analysis['gaps_to_next_rank'].get('pqv_gap', 0) if analysis['gaps_to_next_rank'] else 0
            })
    
    top_performers = sorted(top_performers, key=lambda x: x['PQV'], reverse=True)[:10]
    
    if top_performers:
        performers_df = pd.DataFrame(top_performers)
        st.dataframe(performers_df, use_container_width=True)
    
    # Strategic Analysis Section
    st.markdown('<h2 class="section-header">🎯 Strategic Move Analysis</h2>', unsafe_allow_html=True)
    
    # Leader selection
    leaders = [p for p in top_performers if p['PQV'] > 100]  # Focus on significant leaders
    
    if leaders:
        selected_leader = st.selectbox(
            "Select a leader for strategic analysis:",
            options=[f"{leader['Name']} (ID: {leader['ID']}) - {leader['Current Rank']}" for leader in leaders],
            help="Choose a team leader to analyze their strategic opportunities"
        )
        
        if selected_leader:
            # Extract leader ID
            leader_id = selected_leader.split("ID: ")[1].split(")")[0]
            
            # Run strategic analysis
            with st.spinner("Analyzing strategic opportunities..."):
                strategic_analysis = analyze_leader_strategic_moves(
                    leader_id, team_data, group_volume_df, downline_tree, calculated_ranks, current_date
                )
                
                display_strategic_analysis(strategic_analysis)
    
    else:
        st.info("No qualified leaders found for strategic analysis. Upload data with active distributors (PQV > $100).")

def display_strategic_analysis(strategic_analysis):
    """Display detailed strategic analysis results"""
    
    leader_info = strategic_analysis['leader_info']
    assets = strategic_analysis['strategic_assets']
    
    # Leader Overview
    st.markdown("### 👤 Leader Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Rank", leader_info['current_rank'])
    
    with col2:
        st.metric("Current PQV", f"${leader_info['pqv']:.2f}")
    
    with col3:
        st.metric("Next Rank", leader_info['next_achievable_rank'])
    
    with col4:
        gap = leader_info['gaps_to_next_rank'].get('pqv_gap', 0) if leader_info['gaps_to_next_rank'] else 0
        st.metric("PQV Gap", f"${gap:.2f}")
    
    # Strategic Assets
    st.markdown("### 🎯 Strategic Assets")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Frontline PCUSTs", assets['frontline_pcusts_count'])
    
    with col2:
        st.metric("Volume Donors", f"{len(assets['volume_donors'])} orders")
    
    with col3:
        st.metric("Placeable Assets", f"{len(assets['placeable_assets'])} PCUSTs")
    
    # Recommendations Tabs
    tab1, tab2, tab3 = st.tabs(["💰 PQV Solutions", "📈 Leg Development", "📍 Placement Strategy"])
    
    with tab1:
        st.markdown("### PQV Gap Solutions")
        pqv_recs = strategic_analysis['pqv_recommendations']
        if pqv_recs:
            for rec in pqv_recs:
                if "✅" in rec:
                    st.markdown(f'<div class="success-box">{rec}</div>', unsafe_allow_html=True)
                elif "❌" in rec or "⚠️" in rec:
                    st.markdown(f'<div class="warning-box">{rec}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(rec)
        else:
            st.info("No PQV recommendations available.")
    
    with tab2:
        st.markdown("### Leg Development Opportunities")
        leg_recs = strategic_analysis['leg_development_recommendations']
        if leg_recs:
            for rec in leg_recs:
                if rec.strip():  # Skip empty lines
                    if "🎯" in rec or "👤" in rec:
                        st.markdown(f"**{rec}**")
                    else:
                        st.markdown(rec)
        else:
            st.info("No leg development opportunities available.")
    
    with tab3:
        st.markdown("### Strategic Placement Opportunities")
        placement_recs = strategic_analysis['placement_recommendations']
        if placement_recs:
            for rec in placement_recs:
                if rec.strip():  # Skip empty lines
                    if "📍" in rec or "👤" in rec or "🎯" in rec:
                        st.markdown(f"**{rec}**")
                    else:
                        st.markdown(rec)
        else:
            st.info("No placement opportunities available.")
    
    # Download Results
    st.markdown("### 📥 Export Results")
    
    # Create summary report
    report_text = f"""
YOUNGEVITY STRATEGIC ANALYSIS REPORT
Generated: {strategic_analysis['analysis_date']}

LEADER: {leader_info['name']} (ID: {leader_info['member_id']})
Current Rank: {leader_info['current_rank']}
Current PQV: ${leader_info['pqv']:.2f}
Next Achievable Rank: {leader_info['next_achievable_rank']}

STRATEGIC ASSETS:
- Frontline PCUSTs: {assets['frontline_pcusts_count']}
- Volume Donors: {len(assets['volume_donors'])} orders available
- Placeable Assets: {len(assets['placeable_assets'])} PCUSTs

PQV RECOMMENDATIONS:
{chr(10).join(strategic_analysis['pqv_recommendations'])}

LEG DEVELOPMENT OPPORTUNITIES:
{chr(10).join(strategic_analysis['leg_development_recommendations'])}

PLACEMENT STRATEGIES:
{chr(10).join(strategic_analysis['placement_recommendations'])}
"""
    
    st.download_button(
        label="📄 Download Strategic Analysis Report",
        data=report_text,
        file_name=f"ygy_strategic_analysis_{leader_info['member_id']}.txt",
        mime="text/plain"
    )

if __name__ == "__main__":
    main()
