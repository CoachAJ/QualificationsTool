#!/usr/bin/env python3
"""
Test script to demonstrate get_paid_as_rank function for specific members
"""

# Import the main module
from ygy_data_setup import (
    load_csv_files, create_team_data_dictionary, build_downline_tree,
    get_paid_as_rank, analyze_member_qualifications, calculate_gqv_3cl
)

def test_specific_members():
    print("=== Testing get_paid_as_rank for Specific Members ===")
    print()
    
    # Load data
    print("Loading data...")
    group_volume_df, genealogy_df = load_csv_files()
    team_data = create_team_data_dictionary(genealogy_df)
    downline_tree = build_downline_tree(team_data)
    
    # Target members (found from previous output)
    target_members = {
        "102807573": "Ariali PTL Properties LLC",
        "102801189": "Siplin Law PA"
    }
    
    print("Testing get_paid_as_rank function...")
    print()
    
    for member_id, member_name in target_members.items():
        print(f"=== {member_name} (ID: {member_id}) ===")
        
        # Calculate rank
        calculated_rank = get_paid_as_rank(member_id, team_data, downline_tree)
        print(f"Calculated Paid-As Rank: {calculated_rank}")
        
        # Get detailed analysis
        analysis = analyze_member_qualifications(member_id, team_data, downline_tree, {member_id: calculated_rank})
        
        print(f"PQV: ${analysis['pqv']:.2f}")
        print(f"GQV-3CL: ${analysis['gqv_3cl']:.2f}")
        print(f"Direct Sponsees: {analysis['direct_sponsees_count']}")
        
        if analysis['next_achievable_rank']:
            gaps = analysis['gaps_to_next_rank']
            print(f"Next Rank: {analysis['next_achievable_rank']}")
            print(f"Gaps - PQV: ${gaps['pqv_gap']:.2f}, GQV: ${gaps['gqv_gap']:.2f}, Legs: {gaps['leg_gap']}")
        
        # Show downline details
        sponsees = downline_tree.get(member_id, [])
        print(f"Direct Sponsees ({len(sponsees)}):")
        for sponsee_id in sponsees[:5]:  # Show first 5
            if sponsee_id in team_data:
                sponsee_name = team_data[sponsee_id]['name']
                sponsee_pqv = team_data[sponsee_id]['pqv']
                sponsee_rank = get_paid_as_rank(sponsee_id, team_data, downline_tree)
                print(f"  - {sponsee_name} (PQV: ${sponsee_pqv:.2f}, Rank: {sponsee_rank})")
        
        if len(sponsees) > 5:
            print(f"  ... and {len(sponsees) - 5} more")
        
        print()

if __name__ == "__main__":
    test_specific_members()
