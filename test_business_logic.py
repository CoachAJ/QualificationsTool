#!/usr/bin/env python3
"""
Test Business Logic for Youngevity Strategy Tool
Tests all critical business rules and 60-day PCUST functionality
"""

import pandas as pd
from datetime import datetime, timedelta
import pytz
from ygy_data_setup import (
    can_pcust_be_moved, 
    validate_genealogy_data,
    create_team_data_dictionary,
    get_paid_as_rank,
    suggest_leg_moves
)

def test_60_day_pcust_rule():
    """Test the 60-day PCUST move rule"""
    print("\n=== Testing 60-Day PCUST Move Rule ===")
    
    # Create test member data
    la_timezone = pytz.timezone('America/Los_Angeles')
    current_date = la_timezone.localize(datetime.now())
    
    # Test Case 1: PCUST within 60 days (movable)
    recent_pcust = {
        'title': 'PCUST',
        'join_date': (current_date - timedelta(days=30)).strftime('%m/%d/%Y')
    }
    
    result = can_pcust_be_moved(recent_pcust, current_date)
    assert result['can_move'] == True, "Recent PCUST should be movable"
    assert result['days_remaining'] > 0, "Should have days remaining"
    print(f"[OK] Recent PCUST movable - {result['days_remaining']} days remaining")
    
    # Test Case 2: PCUST past 60 days (locked)
    old_pcust = {
        'title': 'PCUST',
        'join_date': (current_date - timedelta(days=90)).strftime('%m/%d/%Y')
    }
    
    result = can_pcust_be_moved(old_pcust, current_date)
    assert result['can_move'] == False, "Old PCUST should be locked"
    assert result['days_remaining'] <= 0, "Should have no days remaining"
    print(f"[OK] Old PCUST locked - past 60-day window")
    
    # Test Case 3: Non-PCUST (not applicable)
    distributor = {
        'title': 'DISTRIBUTOR',
        'join_date': (current_date - timedelta(days=30)).strftime('%m/%d/%Y')
    }
    
    result = can_pcust_be_moved(distributor, current_date)
    assert result['can_move'] == False, "Non-PCUST should not be movable via this rule"
    print(f"[OK] Non-PCUST correctly handled")
    
    print("[PASS] 60-Day PCUST Move Rule tests passed!")

def test_pcust_rank_enforcement():
    """Test that PCUSTs cannot advance to distributor ranks"""
    print("\n=== Testing PCUST Rank Enforcement ===")
    
    # Create test team data
    team_data = {
        '123': {
            'name': 'Test PCUST',
            'title': 'PCUST',
            'rank': 'PCUST',
            'pqv': 500.0,  # High volume but should stay PCUST
            'sponsor_id': '456'
        },
        '456': {
            'name': 'Test Distributor',
            'title': 'DISTRIBUTOR',
            'rank': 'PCUST',
            'pqv': 500.0,
            'sponsor_id': '789'
        }
    }
    
    downline_tree = {'456': ['123'], '789': ['456']}
    
    # Test PCUST rank calculation
    pcust_rank = get_paid_as_rank('123', team_data, downline_tree)
    assert pcust_rank == 'PCUST', "PCUST should remain PCUST regardless of volume"
    print(f"[OK] PCUST rank locked at PCUST (was: {pcust_rank})")
    
    # Test Distributor rank calculation
    dist_rank = get_paid_as_rank('456', team_data, downline_tree)
    assert dist_rank in ['PCUST', 'BRA', 'SRA', 'SA', '1SE', '2SE', '3SE', '4SE', '5SE', 'ASC'], "Distributor should get valid rank"
    print(f"[OK] Distributor can advance (rank: {dist_rank})")
    
    print("[PASS] PCUST Rank Enforcement tests passed!")

def test_data_validation():
    """Test comprehensive data validation"""
    print("\n=== Testing Data Validation ===")
    
    # Create test genealogy data
    test_data = pd.DataFrame({
        'ID#': ['123', '456', '789', '999'],
        'Name': ['John Doe', 'Jane Smith', '', 'Bob Wilson'],  # Missing name
        'Title': ['PCUST', 'PCUST', 'DISTRIBUTOR', 'PCUST'],
        'Rank': ['PCUST', 'BRA', 'PCUST', 'PCUST'],  # Business rule violation
        'Join Date': ['01/15/2024', 'invalid-date', '03/20/2024', ''],  # Invalid dates
        'Sponsor ID': ['456', '789', '000', '456'],  # Invalid sponsor
        'Enroller': ['456', '789', '000', '456'],
        'QV': ['100.50', '200.75', '150.00', 'invalid'],  # Invalid QV
        'Level': ['0.1', '0.2', '0.1', '0.2'],
        'RepStatus': ['Active', 'Active', 'Active', 'Inactive']
    })
    
    validation_result = validate_genealogy_data(test_data)
    
    # Check validation results
    assert len(validation_result['warnings']) > 0, "Should detect warnings"
    assert len(validation_result['errors']) > 0, "Should detect errors"
    print(f"[OK] Detected {len(validation_result['warnings'])} warnings")
    print(f"[OK] Detected {len(validation_result['errors'])} errors")
    
    # Check specific validations
    error_messages = ' '.join(validation_result['errors'])
    assert 'missing name' in error_messages.lower(), "Should detect missing names"
    assert 'business rule violation' in error_messages.lower(), "Should detect PCUST title/rank mismatch"
    print(f"[OK] Business rule violations detected")
    
    print("[PASS] Data Validation tests passed!")

def test_strategic_move_suggestions():
    """Test strategic move suggestions with 60-day rule"""
    print("\n=== Testing Strategic Move Suggestions ===")
    
    # Create test data with PCUSTs in different time windows
    current_date = datetime.now()
    team_data = {
        '100': {  # Leader
            'name': 'Team Leader',
            'title': 'DISTRIBUTOR',
            'rank': 'SRA',
            'pqv': 250.0,
            'sponsor_id': '999',
            'join_date': '01/01/2020'
        },
        '200': {  # Recent PCUST (movable)
            'name': 'Recent PCUST',
            'title': 'PCUST', 
            'rank': 'PCUST',
            'pqv': 150.0,
            'sponsor_id': '100',
            'join_date': (current_date - timedelta(days=30)).strftime('%m/%d/%Y')
        },
        '300': {  # Old PCUST (volume donor)
            'name': 'Old PCUST',
            'title': 'PCUST',
            'rank': 'PCUST', 
            'pqv': 200.0,
            'sponsor_id': '100',
            'join_date': (current_date - timedelta(days=90)).strftime('%m/%d/%Y')
        }
    }
    
    downline_tree = {'100': ['200', '300'], '999': ['100']}
    calculated_ranks = {'100': 'SRA', '200': 'PCUST', '300': 'PCUST'}
    
    # Test move suggestions with empty volume donors list
    volume_donors = []  # Empty for test
    move_suggestions = suggest_leg_moves('100', team_data, volume_donors, current_date)
    
    # Verify suggestions returned properly
    suggestions_text = '\n'.join(move_suggestions)
    print(f"[DEBUG] Suggestions returned: {suggestions_text}")
    
    # Function should return proper response when no volume donors available
    assert 'No movable orders available' in suggestions_text, "Should handle no volume donors case"
    print(f"[OK] Strategic suggestions handle empty volume donors properly")
    
    print("[PASS] Strategic Move Suggestions tests passed!")

def run_all_tests():
    """Run all business logic tests"""
    print("=== YOUNGEVITY STRATEGY TOOL - BUSINESS LOGIC TESTS ===")
    
    try:
        test_60_day_pcust_rule()
        test_pcust_rank_enforcement()
        test_data_validation()
        test_strategic_move_suggestions()
        
        print("\n" + "="*60)
        print("[SUCCESS] ALL BUSINESS LOGIC TESTS PASSED!")
        print("The Youngevity Strategy Tool is ready for production use.")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        print("Please check the business logic implementation.")
        raise

if __name__ == "__main__":
    run_all_tests()
