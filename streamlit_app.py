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
import json

# Import functions from the main script (ImportError fix applied)
from ygy_data_setup import (
    load_csv_files, create_team_data_dictionary, validate_genealogy_data,
    build_downline_tree, calculate_all_ranks, analyze_member_qualifications,
    identify_strategic_assets, analyze_leader_strategic_moves,
    calculate_hierarchical_levels, find_organizational_root,
    get_member_summary, get_current_date_la_timezone, RANK_HIERARCHY
)
from individual_rank_planner import (
    analyze_individual_rank_advancement, get_available_ranks_for_member
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
    
    # LLM Integration Section
    st.sidebar.markdown("---")
    st.sidebar.header("🤖 AI Strategic Advisor")
    st.sidebar.markdown("<span class='brand-accent'>✨ Expert Data Scientist Advisor</span>", unsafe_allow_html=True)
    
    # LLM Model selection (moved up to determine API key type)
    llm_model = st.sidebar.selectbox(
        "🤖 AI Model",
        options=[
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-flash-preview-04-17",
            "gemini-2.5-flash-lite-preview-06-17"
        ],
        index=1,  # Default to gpt-4o-mini for cost efficiency
        help="Choose AI model for strategic analysis - OpenAI, Anthropic Claude, or Google Gemini"
    )
    
    # API Key input based on selected model
    if llm_model.startswith('gpt'):
        api_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key for GPT models",
            placeholder="sk-proj-..."
        )
    elif llm_model.startswith('claude'):
        api_key = st.sidebar.text_input(
            "Anthropic API Key",
            type="password", 
            help="Enter your Anthropic API key for Claude models",
            placeholder="sk-ant-..."
        )
    elif llm_model.startswith('gemini'):
        api_key = st.sidebar.text_input(
            "Google AI API Key",
            type="password",
            help="Enter your Google AI API key for Gemini models",
            placeholder="AIza..."
        )
    else:
        api_key = st.sidebar.text_input(
            "API Key",
            type="password",
            help="Enter your API key for the selected model",
            placeholder="API key..."
        )
    
    # Store API key in session state
    if api_key:
        st.session_state.openai_api_key = api_key
        st.session_state.llm_model = llm_model
        st.sidebar.success("✅ AI Advisor Ready!")
    else:
        st.sidebar.info("🔑 Add API key to unlock AI advisor")
    
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
                    
                    if genealogy_df is not None:
                        st.success(f"Genealogy report uploaded successfully! ({len(genealogy_df)} records)")
                        st.session_state.genealogy_df = genealogy_df
                        
                        # Validate the data first
                        with st.spinner("Validating data quality..."):
                            try:
                                validation_result = validate_genealogy_data(genealogy_df)
                                # Ensure all required keys exist
                                if not isinstance(validation_result, dict):
                                    raise ValueError("Validation function returned invalid format")
                                
                                # Add missing keys with defaults
                                validation_result.setdefault('warnings', [])
                                validation_result.setdefault('errors', [])
                                validation_result.setdefault('has_issues', False)
                                validation_result.setdefault('summary', 'Validation completed')
                                validation_result.setdefault('total_members', len(genealogy_df))
                                
                            except Exception as e:
                                st.error(f"Error during validation: {str(e)}")
                                # Fallback validation result
                                validation_result = {
                                    'warnings': [],
                                    'errors': [f"Validation error: {str(e)}"],
                                    'has_issues': True,
                                    'summary': f"Validation failed: {str(e)}",
                                    'total_members': len(genealogy_df)
                                }
                        
                        with st.expander("Data Quality Report", expanded=validation_result.get('has_issues', True)):
                            st.info(validation_result.get('summary', 'Data validation completed'))
                            
                            # Display errors first
                            if validation_result['errors']:
                                st.subheader("[ALERT] Critical Issues")
                                for error in validation_result['errors']:
                                    st.error(error)
                            
                            # Display warnings
                            if validation_result['warnings']:
                                st.subheader("[WARNING] Data Quality Issues")
                                for warning in validation_result['warnings']:
                                    st.warning(warning)
                            
                            if not validation_result['has_issues']:
                                st.success("[OK] Data validation passed - no issues found")
                        
                        # Process the genealogy data and store results
                        with st.spinner("Processing genealogy data..."):
                            try:
                                team_data = create_team_data_dictionary(genealogy_df)
                                downline_tree = build_downline_tree(team_data)
                                calculated_ranks = calculate_all_ranks(team_data, downline_tree)
                                hierarchical_levels = calculate_hierarchical_levels(team_data, downline_tree)
                                
                                # Store in session state
                                st.session_state.team_data = team_data
                                st.session_state.downline_tree = downline_tree
                                st.session_state.calculated_ranks = calculated_ranks
                                st.session_state.hierarchical_levels = hierarchical_levels
                                
                                st.success("Data processed successfully!")
                                
                            except Exception as e:
                                st.error(f"Error processing genealogy data: {str(e)}")
                                st.stop()
                    
                    try:
                        organizational_root = find_organizational_root(team_data)
                        calculated_ranks = calculate_all_ranks(team_data, downline_tree)
                        current_date = get_current_date_la_timezone()
                        
                        # Display results
                        display_dashboard(group_volume_df, genealogy_df, team_data, downline_tree, calculated_ranks, current_date, organizational_root, hierarchical_levels)
                        
                        # Display Individual Rank Planner
                        display_individual_rank_planner(team_data, group_volume_df, current_date)
                        
                    except Exception as e:
                        st.error(f"Error displaying dashboard: {str(e)}")
                        st.error("Please check your CSV format and try again.")
                
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
    
    # Always include organizational root (sheet owner) as priority
    analysis_candidates = []
    
    # Add organizational root first (PRIORITY)
    if organizational_root:
        root_info = team_data[organizational_root]
        root_analysis = analyze_member_qualifications(organizational_root, team_data, downline_tree, calculated_ranks)
        analysis_candidates.append({
            'ID': organizational_root,
            'Name': root_info['name'],
            'Current Rank': root_analysis['current_rank'],
            'PQV': root_analysis['pqv'],
            'GQV-3CL': root_analysis['gqv_3cl'],
            'Next Rank': root_analysis['next_achievable_rank'],
            'PQV Gap': root_analysis['gaps_to_next_rank'].get('pqv_gap', 0) if root_analysis['gaps_to_next_rank'] else 0,
            'Priority': '🌟 SHEET OWNER (Level 0)'
        })
    
    # Add other qualified leaders (PQV > 50 to be more inclusive)
    qualified_leaders = [p for p in top_performers if p['PQV'] > 50 and p['ID'] != organizational_root]
    for leader in qualified_leaders:
        leader['Priority'] = f"Level {hierarchical_levels.get(leader['ID'], 'Unknown')}"
        analysis_candidates.append(leader)
    
    # Member Search Section
    st.markdown("### [SEARCH] Find Any Member")
    col1, col2 = st.columns(2)
    
    with col1:
        search_term = st.text_input(
            "Search by Name or ID:",
            placeholder="Enter member name or ID (e.g., 'nutrientshelp')",
            help="Search for any member in the organization"
        )
    
    with col2:
        if search_term:
            search_results = []
            for member_id, member_info in team_data.items():
                if (search_term.lower() in member_info['name'].lower() or 
                    search_term in member_id):
                    member_analysis = analyze_member_qualifications(member_id, team_data, downline_tree, calculated_ranks)
                    search_results.append({
                        'ID': member_id,
                        'Name': member_info['name'],
                        'Current Rank': member_analysis['current_rank'],
                        'PQV': member_analysis['pqv'],
                        'Level': hierarchical_levels.get(member_id, 'Unknown'),
                        'Priority': '[SEARCH] RESULT'
                    })
            
            if search_results:
                st.success(f"Found {len(search_results)} member(s)")
                # Add search results to analysis candidates
                for result in search_results:
                    if result['ID'] not in [c['ID'] for c in analysis_candidates]:
                        analysis_candidates.append(result)
            else:
                st.warning(f"No members found matching '{search_term}'")
    
    # Leader Selection
    if analysis_candidates:
        st.markdown("### [ANALYSIS] Select Member for Strategic Analysis")
        
        # Create dropdown options with priority indicators
        options = []
        for candidate in analysis_candidates:
            priority = candidate.get('Priority', 'Standard')
            options.append(f"{priority} - {candidate['Name']} (ID: {candidate['ID']}) - {candidate['Current Rank']} - PQV: ${candidate['PQV']:.2f}")
        
        selected_member = st.selectbox(
            "Choose a member for detailed strategic analysis:",
            options=options,
            help="The sheet owner (Level 0) is always available first, followed by other qualified leaders"
        )
        
        if selected_member:
            # Extract member ID
            member_id = selected_member.split("ID: ")[1].split(")")[0]
            
            # Show member context
            selected_info = next(c for c in analysis_candidates if c['ID'] == member_id)
            st.info(f"**Analyzing:** {selected_info['Name']} - {selected_info.get('Priority', 'Member')}")
            
            # Run strategic analysis
            with st.spinner("Analyzing strategic opportunities..."):
                strategic_analysis = analyze_leader_strategic_moves(
                    member_id, team_data, group_volume_df, downline_tree, calculated_ranks, current_date
                )
                
                display_strategic_analysis(strategic_analysis)
    
    else:
        st.error("❌ No organizational root found. Please check your data upload.")

def display_strategic_analysis(strategic_analysis):
    """Display detailed strategic analysis results"""
    
    leader_info = strategic_analysis['leader_info']
    assets = strategic_analysis['strategic_assets']
    
    # Leader Overview
    st.markdown("### [LEADER] Overview")
    
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
    st.markdown("### [ASSETS] Strategic Assets")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Frontline PCUSTs", assets['frontline_pcusts_count'])
    
    with col2:
        st.metric("Volume Donors", f"{len(assets['volume_donors'])} orders")
    
    with col3:
        st.metric("Placeable Assets", f"{len(assets['placeable_assets'])} PCUSTs")
    
    # Recommendations Tabs
    tab1, tab2, tab3 = st.tabs(["[PQV] Solutions", "[LEG] Development", "[PLACE] Strategy"])
    
    with tab1:
        st.markdown("### PQV Gap Solutions")
        pqv_recs = strategic_analysis['pqv_recommendations']
        if pqv_recs:
            for rec in pqv_recs:
                if "[OK]" in rec:
                    st.markdown(f'<div class="success-box">{rec}</div>', unsafe_allow_html=True)
                elif "[ALERT]" in rec or "[WARNING]" in rec:
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
                    if "[TARGET]" in rec or "[LEG]" in rec:
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
                    if "[PLACE]" in rec or "[LEG]" in rec or "[TARGET]" in rec:
                        st.markdown(f"**{rec}**")
                    else:
                        st.markdown(rec)
        else:
            st.info("No placement opportunities available.")
    
    # Download Results
    st.markdown("### [EXPORT] Results")
    
    # Create CSV data for export
    import pandas as pd
    import io
    
    # Prepare CSV export data
    export_data = []
    
    # Add leader info
    export_data.append({
        'Category': 'LEADER',
        'ID': leader_info['member_id'],
        'Name': leader_info['name'],
        'Current_Rank': leader_info['current_rank'],
        'Current_PQV': leader_info['pqv'],
        'Next_Rank': leader_info['next_achievable_rank'],
        'Action_Type': 'OVERVIEW',
        'Recommendation': f"Current: {leader_info['current_rank']} | Target: {leader_info['next_achievable_rank']}",
        'Priority': 'HIGH'
    })
    
    # Add PQV recommendations
    for i, rec in enumerate(strategic_analysis['pqv_recommendations']):
        if rec.strip() and not rec.startswith('['):
            export_data.append({
                'Category': 'PQV_SOLUTION',
                'ID': leader_info['member_id'],
                'Name': leader_info['name'],
                'Current_Rank': leader_info['current_rank'],
                'Current_PQV': leader_info['pqv'],
                'Next_Rank': leader_info['next_achievable_rank'],
                'Action_Type': 'PQV_MOVE',
                'Recommendation': rec.strip(),
                'Priority': 'HIGH' if 'SOLUTION' in rec else 'MEDIUM'
            })
    
    # Add leg development recommendations
    for i, rec in enumerate(strategic_analysis['leg_development_recommendations']):
        if rec.strip() and '[LEG]' in rec:
            # Extract member info from recommendation
            parts = rec.split(')')
            if len(parts) >= 2:
                export_data.append({
                    'Category': 'LEG_DEVELOPMENT',
                    'ID': 'EXTRACT_FROM_REC',
                    'Name': 'EXTRACT_FROM_REC', 
                    'Current_Rank': 'EXTRACT_FROM_REC',
                    'Current_PQV': 'EXTRACT_FROM_REC',
                    'Next_Rank': 'EXTRACT_FROM_REC',
                    'Action_Type': 'VOLUME_MOVE',
                    'Recommendation': rec.strip(),
                    'Priority': 'HIGH'
                })
    
    # Add volume donor data
    for donor in assets['volume_donors']:
        export_data.append({
            'Category': 'VOLUME_DONOR',
            'ID': donor.get('pcust_id', 'N/A'),
            'Name': donor.get('pcust_name', 'N/A'),
            'Current_Rank': 'PCUST',
            'Current_PQV': donor.get('volume', 0),
            'Next_Rank': 'LOCKED',
            'Action_Type': 'VOLUME_AVAILABLE',
            'Recommendation': f"Order #{donor.get('order_number', 'N/A')}: ${donor.get('volume', 0):.2f} available to move",
            'Priority': 'MEDIUM'
        })
    
    # Convert to DataFrame and CSV
    df_export = pd.DataFrame(export_data)
    
    # Create CSV string
    csv_buffer = io.StringIO()
    df_export.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()
    
    # Create detailed text report
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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.download_button(
            label="[DOWNLOAD] CSV Export",
            data=csv_data,
            file_name=f"ygy_strategic_analysis_{leader_info['member_id']}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.download_button(
            label="[DOWNLOAD] Text Report",
            data=report_text,
            file_name=f"ygy_strategic_analysis_{leader_info['member_id']}.txt",
            mime="text/plain"
        )

def get_helpful_info_context() -> str:
    """Load context from helpful info folder for AI advisor"""
    helpful_info_path = "helpful info"
    context = ""
    
    if os.path.exists(helpful_info_path):
        context += "\n=== YOUNGEVITY BUSINESS RESOURCES AVAILABLE ===\n"
        context += "- CompensationPlan_022723.pdf: Full YGY compensation structure\n"
        context += "- YGY-Policies-Procedures_0625.pdf: Business rules and compliance guidelines\n"
        context += "- GLOSSARY OF TERMS.pdf: Youngevity terminology reference\n"
        context += "- rank Qualifications report.pdf: Detailed rank requirements and qualifications\n"
        context += "- Sample genealogy and volume data for pattern analysis\n"
        context += "=== END RESOURCES ===\n\n"
    
    return context

def get_ai_strategic_advice(analysis_data: Dict, api_key: str, model: str = "gpt-4o-mini") -> str:
    """Get AI-powered strategic advice for rank advancement with expert data scientist capabilities"""
    try:
        # Determine AI provider based on model
        if model.startswith('gpt'):
            return get_openai_advice(analysis_data, api_key, model)
        elif model.startswith('claude'):
            return get_claude_advice(analysis_data, api_key, model)
        elif model.startswith('gemini'):
            return get_gemini_advice(analysis_data, api_key, model)
        else:
            return get_openai_advice(analysis_data, api_key, model)  # Default to OpenAI
            
    except Exception as e:
        return f"❌ AI Advisor Error: {str(e)}"

def get_openai_advice(analysis_data: Dict, api_key: str, model: str) -> str:
    """Get OpenAI-powered strategic advice"""
    try:
        import openai
        openai.api_key = api_key
        
        # Prepare context for AI
        member_name = analysis_data['member_name']
        current_rank = analysis_data['current_rank']
        desired_rank = analysis_data['desired_rank']
        gaps = analysis_data['gaps']
        move_recommendations = analysis_data['move_recommendations']
        helpful_context = get_helpful_info_context()
        
        system_prompt = f"""
You are an EXPERT DATA SCIENTIST specializing in MLM/Network Marketing business structure optimization for MAXIMUM COMPENSATION.

EXPERTISE AREAS:
- Data Science & Analytics: Advanced statistical analysis of genealogy and volume data
- MLM Business Architecture: Deep understanding of downline structure optimization  
- Youngevity Compensation Expert: Master knowledge of YGY rank requirements, bonuses, and advancement strategies
- Strategic Planning: ROI-focused move recommendations for maximum earning potential

YOUR MISSION: Structure business for MAXIMUM COMPENSATION based on Youngevity compensation plan rules.

{helpful_context}

APPROACH:
1. Data-Driven Decisions: Use statistical analysis to identify highest ROI moves
2. Rule Compliance: Ensure all strategies follow YGY policies and procedures
3. Maximum Compensation Focus: Prioritize moves that generate highest income potential
4. Scalable Strategies: Build sustainable long-term business architecture
5. Risk Mitigation: Identify potential compliance or business risks
"""
        
        user_prompt = f"""
DISTRIBUTOR ANALYSIS:
Name: {member_name}
Current Rank: {current_rank}
Desired Rank: {desired_rank}

DATA ANALYSIS - CURRENT GAPS:
- PQV Gap: ${gaps['pqv_gap']:.2f}
- GQV Gap: ${gaps['gqv_gap']:.2f} 
- Qualifying Legs Gap: {gaps['legs_gap']}

SYSTEM RECOMMENDATIONS:
{chr(10).join(move_recommendations[:12])}

As an EXPERT DATA SCIENTIST, provide:
1. 📊 DATA INSIGHTS - Statistical analysis of advancement probability
2. 💰 COMPENSATION OPTIMIZATION - Highest ROI strategic moves
3. 🏁 BUSINESS ARCHITECTURE - Optimal structure for maximum earnings
4. ⏰ TIMELINE & MILESTONES - Data-driven achievement projections
5. ⚠️ RISK ANALYSIS - Compliance and business risk assessment
6. 🚀 NEXT ACTIONS - Specific implementable steps

Focus on MAXIMUM COMPENSATION and provide data-backed strategic insights. Keep response under 350 words.
"""
        
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except ImportError:
        return "❌ OpenAI library not installed. Run: pip install openai"
    except Exception as e:
        return f"❌ OpenAI Error: {str(e)}"

def get_claude_advice(analysis_data: Dict, api_key: str, model: str) -> str:
    """Get Claude-powered strategic advice"""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        member_name = analysis_data['member_name']
        current_rank = analysis_data['current_rank']
        desired_rank = analysis_data['desired_rank']
        gaps = analysis_data['gaps']
        move_recommendations = analysis_data['move_recommendations']
        helpful_context = get_helpful_info_context()
        
        prompt = f"""
You are an EXPERT DATA SCIENTIST specializing in MLM business optimization for MAXIMUM COMPENSATION.

{helpful_context}

DISTRIBUTOR: {member_name} | {current_rank} → {desired_rank}
GAPS: PQV ${gaps['pqv_gap']:.2f} | GQV ${gaps['gqv_gap']:.2f} | Legs {gaps['legs_gap']}

SYSTEM MOVES:
{chr(10).join(move_recommendations[:10])}

Provide expert data scientist analysis for MAXIMUM COMPENSATION optimization:
1. DATA INSIGHTS & ROI ANALYSIS
2. COMPENSATION OPTIMIZATION STRATEGY  
3. BUSINESS ARCHITECTURE RECOMMENDATIONS
4. TIMELINE & RISK ASSESSMENT
5. ACTIONABLE NEXT STEPS

Focus on highest earning potential moves. Max 300 words.
"""
        
        response = client.messages.create(
            model=model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
        
    except ImportError:
        return "❌ Anthropic library not installed. Run: pip install anthropic"
    except Exception as e:
        return f"❌ Claude Error: {str(e)}"

def get_gemini_advice(analysis_data: Dict, api_key: str, model: str) -> str:
    """Get Gemini-powered strategic advice"""
    try:
        import google.genai as genai
        genai.configure(api_key=api_key)
        model_instance = genai.GenerativeModel(model)
        
        member_name = analysis_data['member_name']
        current_rank = analysis_data['current_rank']
        desired_rank = analysis_data['desired_rank']
        gaps = analysis_data['gaps']
        move_recommendations = analysis_data['move_recommendations']
        helpful_context = get_helpful_info_context()
        
        prompt = f"""
EXPERT DATA SCIENTIST - MLM COMPENSATION OPTIMIZATION

{helpful_context}

ANALYSIS TARGET: {member_name} ({current_rank} → {desired_rank})
DATA GAPS: PQV ${gaps['pqv_gap']:.2f}, GQV ${gaps['gqv_gap']:.2f}, Legs {gaps['legs_gap']}

SYSTEM RECOMMENDATIONS:
{chr(10).join(move_recommendations[:10])}

As expert data scientist, optimize for MAXIMUM COMPENSATION:
1. Statistical ROI analysis
2. Compensation optimization strategy
3. Business structure recommendations  
4. Risk/timeline assessment
5. Priority action items

Data-driven, compensation-focused. Max 300 words.
"""
        
        response = model_instance.generate_content(prompt)
        return response.text
        
    except ImportError:
        return "❌ Google AI library not installed. Run: pip install google-genai"
    except Exception as e:
        return f"❌ Gemini Error: {str(e)}"

def display_individual_rank_planner(team_data, group_volume_df, current_date):
    """Display Individual Rank Advancement Planner"""
    
    st.markdown("---")
    st.markdown("## 🎯 Individual Rank Advancement Planner")
    st.markdown("*Select a specific member and target rank for detailed advancement strategy*")
    
    # Get list of all members for dropdown (EXCLUDE PCUSTs - they cannot advance ranks)
    member_options = [(member_id, f"{info['name']} (ID: {member_id}) - {info.get('calculated_rank', 'DIS')}")
                     for member_id, info in team_data.items()
                     if info.get('name', '').strip() and 
                        info.get('calculated_rank', '').upper() != 'PCUST' and
                        info.get('title', '').upper() != 'PCUST']
    member_options.sort(key=lambda x: x[1])  # Sort by name
    
    if not member_options:
        st.warning("No members found in the team data.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Member selection dropdown
        selected_member = st.selectbox(
            "🔍 Select Member to Analyze:",
            options=[opt[0] for opt in member_options],
            format_func=lambda x: next(opt[1] for opt in member_options if opt[0] == x),
            key="individual_member_select"
        )
    
    with col2:
        # Get available ranks for selected member
        if selected_member:
            member_info = team_data[selected_member]
            current_rank = member_info.get('calculated_rank', 'DIS')
            available_ranks = get_available_ranks_for_member(current_rank)
            
            if available_ranks:
                target_rank = st.selectbox(
                    "🎯 Target Rank:",
                    options=available_ranks,
                    key="target_rank_select"
                )
            else:
                st.info(f"Member {member_info['name']} is already at maximum rank ({current_rank})")
                return
    
    if selected_member and target_rank:
        st.markdown(f"### 📋 Advancement Plan: {team_data[selected_member]['name']} → {target_rank}")
        
        # Prepare volume donors data
        volume_donors = []
        if group_volume_df is not None and not group_volume_df.empty:
            for _, row in group_volume_df.iterrows():
                if pd.notna(row.get('Order Number')) and pd.notna(row.get('Volume')):
                    volume_donors.append({
                        'order_number': str(row['Order Number']),
                        'volume': float(row['Volume']),
                        'donor_name': str(row.get('Name', 'Unknown')),
                        'donor_id': str(row.get('ID#', 'Unknown'))
                    })
        
        # Analyze advancement strategy
        with st.spinner(f"Analyzing advancement strategy for {target_rank}..."):
            try:
                analysis = analyze_individual_rank_advancement(
                    selected_member, target_rank, team_data, volume_donors, current_date
                )
                
                if 'error' in analysis:
                    st.error(analysis['error'])
                    return
                
                # Display current status
                st.markdown("#### 📊 Current Status")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Current Rank",
                        analysis['current_rank'],
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "Current PQV",
                        f"${analysis['current_pqv']:.2f}",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Current GQV",
                        f"${analysis['current_gqv']:.2f}",
                        delta=None
                    )
                
                # Display requirements and gaps
                st.markdown("#### 🎯 Target Requirements & Gaps")
                requirements = analysis['target_requirements']
                gaps = analysis['gaps']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    pqv_color = "normal" if gaps['pqv_gap'] == 0 else "inverse"
                    st.metric(
                        f"PQV Need (${requirements['min_pqv']:.2f})",
                        f"${gaps['pqv_gap']:.2f} gap",
                        delta=None,
                        delta_color=pqv_color
                    )
                
                with col2:
                    if requirements.get('min_gqv_3cl', 0) > 0:
                        gqv_color = "normal" if gaps['gqv_gap'] == 0 else "inverse"
                        st.metric(
                            f"GQV-3CL Need (${requirements['min_gqv_3cl']:.2f})",
                            f"${gaps['gqv_gap']:.2f} gap",
                            delta=None,
                            delta_color=gqv_color
                        )
                    else:
                        st.metric("GQV-3CL", "Not Required", delta=None)
                
                with col3:
                    if requirements.get('min_qualified_legs', 0) > 0:
                        legs_color = "normal" if gaps['legs_gap'] == 0 else "inverse"
                        leg_req_rank = requirements.get('leg_rank_requirement', 'SA')
                        st.metric(
                            f"Qualifying Legs ({leg_req_rank}+)",
                            f"{gaps['legs_gap']} needed",
                            delta=None,
                            delta_color=legs_color
                        )
                    else:
                        st.metric("Qualifying Legs", "Not Required", delta=None)
                
                # Display move recommendations
                if analysis['move_recommendations']:
                    st.markdown("#### 🚀 Strategic Move Recommendations")
                    
                    # Create text area with recommendations
                    recommendations_text = "\n".join(analysis['move_recommendations'])
                    st.text_area(
                        "Detailed Move Strategy:",
                        value=recommendations_text,
                        height=400,
                        key="individual_recommendations"
                    )
                    
                    # Download button for recommendations
                    st.download_button(
                        label="[DOWNLOAD] Individual Strategy Plan",
                        data=recommendations_text,
                        file_name=f"advancement_plan_{selected_member}_{target_rank}.txt",
                        mime="text/plain"
                    )
                    
                    # AI Strategic Advisor Integration
                    if hasattr(st.session_state, 'openai_api_key') and st.session_state.openai_api_key:
                        st.markdown("---")
                        st.markdown("#### 🤖 AI Strategic Advisor")
                        
                        if st.button("✨ Get AI Strategic Advice", key="ai_advice_btn", type="primary"):
                            with st.spinner("💭 AI analyzing your strategy..."):
                                ai_advice = get_ai_strategic_advice(
                                    analysis, 
                                    st.session_state.openai_api_key,
                                    st.session_state.get('llm_model', 'gpt-4o-mini')
                                )
                            
                            st.markdown("##### 🎯 AI Strategic Insights:")
                            st.markdown(ai_advice)
                            
                            # Download AI advice
                            combined_report = f"""INDIVIDUAL ADVANCEMENT PLAN
================================
Member: {analysis['member_name']}
Current Rank: {analysis['current_rank']}
Target Rank: {analysis['desired_rank']}

SYSTEM RECOMMENDATIONS:
{recommendations_text}

================================
AI STRATEGIC ADVISOR INSIGHTS:
================================
{ai_advice}
"""
                            
                            st.download_button(
                                label="[DOWNLOAD] Complete AI-Enhanced Strategy Plan",
                                data=combined_report,
                                file_name=f"ai_strategy_plan_{selected_member}_{target_rank}.txt",
                                mime="text/plain"
                            )
                    else:
                        st.info("🔑 Add OpenAI API key in sidebar to unlock AI Strategic Advisor")
                
                # Achievement status
                if analysis['is_achievable']:
                    st.success(f"✅ {target_rank} rank is achievable with the recommended moves!")
                else:
                    st.warning(f"⚠️ {target_rank} rank may require additional volume or team building.")
                    
            except Exception as e:
                st.error(f"Error analyzing advancement strategy: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()
