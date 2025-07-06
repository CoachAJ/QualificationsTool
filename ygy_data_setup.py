#!/usr/bin/env python3
"""
Youngevity Strategy Tool - Phase 1: Data Setup
This script handles the data import and processing for YGY business analysis.
"""

import pandas as pd
import glob
import os
from datetime import datetime
import pytz
from typing import Dict, List, Any, Optional

def get_current_date_la_timezone() -> datetime:
    """
    Get the current date and time in the 'America/Los_Angeles' timezone.
    
    Returns:
        datetime.datetime: Current date/time in LA timezone
    """
    la_timezone = pytz.timezone('America/Los_Angeles')
    current_time = datetime.now(la_timezone)
    return current_time

def load_csv_files(data_folder: str = "helpful info") -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load both Group Volume Details and AdvancedGenealogyReport CSV files.
    Uses glob pattern matching to find files with date suffixes.
    
    Args:
        data_folder (str): Folder containing the CSV files
        
    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: (group_volume_df, genealogy_df)
    """
    # Find Group Volume Details CSV file
    group_volume_pattern = os.path.join(data_folder, "Group Volume Details*.csv")
    group_volume_files = glob.glob(group_volume_pattern)
    
    if not group_volume_files:
        raise FileNotFoundError(f"No Group Volume Details CSV file found in {data_folder}")
    
    # Use the most recent file if multiple exist
    group_volume_file = max(group_volume_files, key=os.path.getmtime)
    print(f"Loading Group Volume Details from: {group_volume_file}")
    
    # Find AdvancedGenealogyReport CSV file
    genealogy_pattern = os.path.join(data_folder, "AdvancedGenealogyReport*.csv")
    genealogy_files = glob.glob(genealogy_pattern)
    
    if not genealogy_files:
        raise FileNotFoundError(f"No AdvancedGenealogyReport CSV file found in {data_folder}")
    
    # Use the most recent file if multiple exist
    genealogy_file = max(genealogy_files, key=os.path.getmtime)
    print(f"Loading AdvancedGenealogyReport from: {genealogy_file}")
    
    # Load the CSV files
    try:
        group_volume_df = pd.read_csv(group_volume_file)
        genealogy_df = pd.read_csv(genealogy_file)
        
        print(f"Group Volume Details loaded: {len(group_volume_df)} rows")
        print(f"AdvancedGenealogyReport loaded: {len(genealogy_df)} rows")
        
        return group_volume_df, genealogy_df
        
    except Exception as e:
        raise Exception(f"Error loading CSV files: {str(e)}")

def create_team_data_dictionary(genealogy_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Create a central team_data dictionary from the AdvancedGenealogyReport DataFrame.
    
    Args:
        genealogy_df (pd.DataFrame): The genealogy DataFrame
        
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary with ID# as keys and member info as values
    """
    team_data = {}
    
    for index, row in genealogy_df.iterrows():
        member_id = str(row['ID#']).strip()
        
        # Handle potential missing or NaN values
        def safe_get(field, default=''):
            value = row.get(field, default)
            if pd.isna(value):
                return default
            return str(value).strip() if isinstance(value, str) else value
        
        # Parse QV field (remove spaces, handle formatting)
        qv_raw = safe_get('QV', '0.00')
        try:
            # Remove spaces and convert to float
            qv_clean = str(qv_raw).replace(' ', '').replace(',', '')
            pqv = float(qv_clean) if qv_clean else 0.0
        except (ValueError, TypeError):
            pqv = 0.0
        
        # Create member info dictionary
        member_info = {
            'name': safe_get('Name'),
            'title': safe_get('Title'),
            'rank': safe_get('Rank', 'PCUST').upper().strip(),  # Extract rank from column D
            'join_date': safe_get('Join Date'),
            'sponsor_id': safe_get('Sponsor ID'),
            'enroller_id': safe_get('Enroller'),
            'pqv': pqv,
            'level': safe_get('Level'),
            'rep_status': safe_get('RepStatus'),
            'renewal_date': safe_get('Renewal Date'),
            'enroller_name': safe_get('Enroller Name'),
            'sponsor_name': safe_get('Sponsor Name'),
            'last_ordered': safe_get('Date Last Ordered'),
            'autoship': safe_get('Active on AutoShip'),
            'active': safe_get('Active')
        }
        
        team_data[member_id] = member_info
    
    print(f"Created team_data dictionary with {len(team_data)} members")
    return team_data

def validate_genealogy_data(genealogy_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate genealogy data for common issues and business rule compliance.
    
    Args:
        genealogy_df (pd.DataFrame): The genealogy DataFrame to validate
        
    Returns:
        Dict[str, Any]: Dictionary containing warnings, errors, and summary
    """
    from datetime import datetime
    warnings = []
    errors = []
    
    # Check for required columns - Title column contains rank information
    required_columns = ['ID#', 'Name', 'Title', 'Join Date', 'Sponsor ID']
    missing_columns = [col for col in required_columns if col not in genealogy_df.columns]
    
    if missing_columns:
        errors.append(f"[ALERT] Missing required columns: {', '.join(missing_columns)}")
        return {
            'warnings': warnings, 
            'errors': errors, 
            'total_members': len(genealogy_df),
            'has_issues': True,
            'summary': f"Critical error: Missing required columns - {', '.join(missing_columns)}"
        }
    
    # Check for duplicate IDs
    duplicate_ids = genealogy_df[genealogy_df['ID#'].duplicated()]['ID#'].tolist()
    if duplicate_ids:
        errors.append(f"[ALERT] Duplicate member IDs found: {', '.join(map(str, duplicate_ids))}")
    
    # Check for missing critical data
    missing_names = genealogy_df[genealogy_df['Name'].isna() | (genealogy_df['Name'] == '')]
    if not missing_names.empty:
        errors.append(f"[ALERT] {len(missing_names)} members have missing names")
    
    missing_titles = genealogy_df[genealogy_df['Title'].isna() | (genealogy_df['Title'] == '')]
    if not missing_titles.empty:
        warnings.append(f"[WARNING] {len(missing_titles)} members have missing titles (enrollment status unclear)")
    
    # Check for invalid titles/ranks - Title column contains rank information
    valid_ranks = list(RANK_HIERARCHY) + ['PCUST']
    if 'Title' in genealogy_df.columns:
        invalid_titles = genealogy_df[~genealogy_df['Title'].str.upper().str.strip().isin([r.upper() for r in valid_ranks]) & genealogy_df['Title'].notna()]
        if not invalid_titles.empty:
            unique_invalid = invalid_titles['Title'].unique()
            warnings.append(f"[WARNING] Unrecognized titles/ranks found: {', '.join(unique_invalid)}")
    
    # Business rule validation: Title column contains valid YGY ranks
    # Note: Title column contains both enrollment status (PCUST) and distributor ranks (BRA, SRA, etc.)
    # Rank calculation logic will handle PCUST business rules automatically
    
    # Check for orphaned members (no valid sponsor)
    total_members = len(genealogy_df)
    all_ids = set(genealogy_df['ID#'].astype(str))
    orphaned_members = genealogy_df[
        ~genealogy_df['Sponsor ID'].astype(str).isin(all_ids) & 
        genealogy_df['Sponsor ID'].notna() & 
        (genealogy_df['Sponsor ID'] != '')
    ]
    if not orphaned_members.empty:
        warnings.append(f"[WARNING] {len(orphaned_members)} members have sponsors not in dataset")
    
    # Check date format issues
    invalid_dates = 0
    for index, row in genealogy_df.iterrows():
        join_date_str = str(row.get('Join Date', '')).strip()
        if join_date_str and join_date_str != 'nan':
            try:
                # Try parsing with common formats
                for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
                    try:
                        datetime.strptime(join_date_str, date_format)
                        break
                    except ValueError:
                        continue
                else:
                    invalid_dates += 1
            except:
                invalid_dates += 1
    
    if invalid_dates > 0:
        warnings.append(f"[WARNING] {invalid_dates} members have unparseable join dates (affects 60-day rule compliance)")
    
    # Return validation results
    return {
        'warnings': warnings,
        'errors': errors,
        'total_members': total_members,
        'has_issues': len(warnings) > 0 or len(errors) > 0,
        'summary': f"Validated {total_members} members - {len(warnings)} warnings, {len(errors)} errors"
    }

def can_pcust_be_moved(member_info: Dict[str, Any], current_date: datetime) -> Dict[str, Any]:
    """
    Check if a PCUST can be moved to a different upline based on the 60-day rule.
    
    YGY Business Rule: PCUSTs can only be moved within 60 days of their enrollment date.
    
    Args:
        member_info (Dict): Member information dictionary
        current_date (datetime): Current date for comparison
        
    Returns:
        Dict[str, Any]: Dictionary with movable status and details
    """
    result = {
        'can_move': False,
        'days_since_enrollment': None,
        'days_remaining': 0,
        'enrollment_date': None,
        'reason': 'Unknown'
    }
    
    # Check if member is PCUST
    member_title = member_info.get('title', '').upper().strip()
    if member_title != 'PCUST':
        result['reason'] = 'Not a PCUST - move rules do not apply'
        return result
    
    # Get join date
    join_date_str = member_info.get('join_date', '')
    if not join_date_str or join_date_str in ['', 'nan', None]:
        result['reason'] = 'No enrollment date available'
        return result
    
    try:
        # Parse join date - handle multiple formats
        if isinstance(join_date_str, str):
            # Try common date formats
            for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
                try:
                    enrollment_date = datetime.strptime(join_date_str.strip(), date_format)
                    break
                except ValueError:
                    continue
            else:
                result['reason'] = f'Cannot parse enrollment date: {join_date_str}'
                return result
        else:
            # Handle pandas datetime
            enrollment_date = pd.to_datetime(join_date_str)
            if pd.isna(enrollment_date):
                result['reason'] = 'Invalid enrollment date'
                return result
            enrollment_date = enrollment_date.to_pydatetime()
        
        # Calculate days since enrollment
        days_since = (current_date.date() - enrollment_date.date()).days
        days_remaining = max(0, 60 - days_since)
        
        result['enrollment_date'] = enrollment_date.strftime('%m/%d/%Y')
        result['days_since_enrollment'] = days_since
        result['days_remaining'] = days_remaining
        
        if days_since <= 60:
            result['can_move'] = True
            result['reason'] = f'Within 60-day window ({days_remaining} days remaining)'
        else:
            result['can_move'] = False
            result['reason'] = f'Enrollment date exceeded 60-day window by {days_since - 60} days'
        
        return result
        
    except Exception as e:
        result['reason'] = f'Error processing enrollment date: {str(e)}'
        return result

def build_downline_tree(team_data: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build a downline tree dictionary based on Sponsor ID relationships.
    
    Args:
        team_data (Dict[str, Dict[str, Any]]): The team data dictionary
        
    Returns:
        Dict[str, List[str]]: Dictionary where keys are Sponsor IDs and values are lists of their direct sponsees
    """
    downline_tree = {}
    
    for member_id, member_info in team_data.items():
        sponsor_id = str(member_info.get('sponsor_id', '')).strip()
        
        # Skip if no sponsor ID or if sponsor ID is empty
        if not sponsor_id or sponsor_id == '' or sponsor_id == 'nan':
            continue
        
        # Initialize sponsor's downline list if it doesn't exist
        if sponsor_id not in downline_tree:
            downline_tree[sponsor_id] = []
        
        # Add this member to their sponsor's downline
        if member_id not in downline_tree[sponsor_id]:
            downline_tree[sponsor_id].append(member_id)
    
    # Sort each downline list for consistency
    for sponsor_id in downline_tree:
        downline_tree[sponsor_id].sort()
    
    print(f"Built downline tree with {len(downline_tree)} sponsors")
    
    # Display some statistics
    total_sponsees = sum(len(sponsees) for sponsees in downline_tree.values())
    max_downline = max(len(sponsees) for sponsees in downline_tree.values()) if downline_tree else 0
    
    print(f"Total sponsees tracked: {total_sponsees}")
    print(f"Largest downline size: {max_downline}")
    
    return downline_tree

def calculate_hierarchical_levels(team_data: Dict[str, Dict[str, Any]], downline_tree: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Calculate hierarchical levels for all members based on distance from the organizational root.
    Level 0 = organizational head, Level 0.1 = one level down, Level 0.2 = two levels down, etc.
    
    Args:
        team_data (Dict[str, Dict[str, Any]]): The team data dictionary
        downline_tree (Dict[str, List[str]]): The downline tree mapping sponsors to sponsees
        
    Returns:
        Dict[str, float]: Dictionary mapping member IDs to their hierarchical levels
    """
    # First, find the organizational root (member with no sponsor or external sponsor)
    root_id = None
    for member_id, member_info in team_data.items():
        sponsor_id = str(member_info.get('sponsor_id', '')).strip()
        
        if (not sponsor_id or 
            sponsor_id == '' or 
            sponsor_id == 'nan' or 
            sponsor_id not in team_data):
            root_id = member_id
            break
    
    if not root_id:
        print("[WARNING] No organizational root found!")
        return {}
    
    # Calculate levels using breadth-first search from the root
    levels = {}
    queue = [(root_id, 0)]  # (member_id, level)
    
    while queue:
        current_id, current_level = queue.pop(0)
        levels[current_id] = current_level
        
        # Add all direct sponsees to the queue with level + 0.1
        if current_id in downline_tree:
            for sponsee_id in downline_tree[current_id]:
                if sponsee_id not in levels:  # Avoid cycles
                    next_level = current_level + 0.1
                    queue.append((sponsee_id, round(next_level, 1)))
    
    # Display the organizational structure
    root_info = team_data[root_id]
    print(f"Organizational Structure - Root: {root_info['name']} (ID: {root_id})")
    print(f"  Level 0 (Head): {root_info['name']} - Rank: {root_info.get('calculated_rank', 'N/A')}")
    
    # Count members at each level
    level_counts = {}
    for member_id, level in levels.items():
        level_counts[level] = level_counts.get(level, 0) + 1
    
    for level in sorted(level_counts.keys()):
        if level > 0:
            distance = int(level * 10)  # Convert 0.1 to 1, 0.2 to 2, etc.
            print(f"  Level {level} ({distance} levels down): {level_counts[level]} members")
    
    return levels


def find_organizational_root(team_data: Dict[str, Dict[str, Any]]) -> str:
    """
    Find the single organizational root (Level 0 member).
    
    Args:
        team_data (Dict[str, Dict[str, Any]]): The team data dictionary
        
    Returns:
        str: Member ID of the organizational root, or None if not found
    """
    for member_id, member_info in team_data.items():
        sponsor_id = str(member_info.get('sponsor_id', '')).strip()
        
        if (not sponsor_id or 
            sponsor_id == '' or 
            sponsor_id == 'nan' or 
            sponsor_id not in team_data):
            return member_id
    
    return None

def get_member_summary(team_data: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """
    Get summary statistics about team members.
    
    Args:
        team_data (Dict[str, Dict[str, Any]]): The team data dictionary
        
    Returns:
        Dict[str, int]: Summary statistics
    """
    summary = {
        'total_members': len(team_data),
        'distributors': 0,
        'pcust': 0,
        'active_members': 0,
        'autoship_members': 0,
        'members_with_volume': 0
    }
    
    for member_info in team_data.values():
        # Count by title/status
        title = member_info.get('title', '').upper()
        if title == 'PCUST':
            summary['pcust'] += 1
        else:
            summary['distributors'] += 1
        
        # Count active members
        if member_info.get('active', '').upper() == 'Y':
            summary['active_members'] += 1
        
        # Count autoship members
        if member_info.get('autoship', '').upper() == 'Y':
            summary['autoship_members'] += 1
        
        # Count members with volume
        if member_info.get('pqv', 0) > 0:
            summary['members_with_volume'] += 1
    
    return summary

# ============================================================================
# PHASE 2: CALCULATION ENGINE
# ============================================================================

# Rank Requirements Dictionary - YGY Compensation Plan Rules
RANK_REQUIREMENTS = {
    'PCUST': {
        'min_pqv': 0,
        'min_gqv_3cl': 0,
        'min_qualified_legs': 0,
        'leg_rank_requirement': None,
        'description': 'Preferred Customer'
    },
    'ASC': {
        'min_pqv': 50,
        'min_gqv_3cl': 0,
        'min_qualified_legs': 0,
        'leg_rank_requirement': None,
        'description': 'Associate'
    },
    'BRA': {
        'min_pqv': 100,
        'min_gqv_3cl': 0,
        'min_qualified_legs': 0,
        'leg_rank_requirement': None,
        'description': 'Brand Associate'
    },
    'SA': {
        'min_pqv': 150,
        'min_gqv_3cl': 0,
        'min_qualified_legs': 3,
        'leg_rank_requirement': 'ASC',
        'description': 'Sales Associate'
    },
    'SRA': {
        'min_pqv': 200,
        'min_gqv_3cl': 1000,
        'min_qualified_legs': 3,
        'leg_rank_requirement': 'BRA',
        'description': 'Senior Associate'
    },
    '1SE': {
        'min_pqv': 250,
        'min_gqv_3cl': 5400,
        'min_qualified_legs': 3,
        'leg_rank_requirement': 'SA',
        'description': '1 Star Executive'
    },
    '2SE': {
        'min_pqv': 300,
        'min_gqv_3cl': 7500,
        'min_qualified_legs': 3,
        'leg_rank_requirement': '1SE',
        'description': '2 Star Executive'
    },
    '3SE': {
        'min_pqv': 300,
        'min_gqv_3cl': 10500,
        'min_qualified_legs': 5,
        'leg_rank_requirement': '1SE',
        'description': '3 Star Executive'
    },
    '4SE': {
        'min_pqv': 300,
        'min_gqv_3cl': 27000,
        'min_qualified_legs': 6,
        'leg_rank_requirement': '1SE',
        'description': '4 Star Executive'
    },
    '5SE': {
        'min_pqv': 300,
        'min_gqv_3cl': 43200,
        'min_qualified_legs': 9,
        'leg_rank_requirement': '1SE',
        'description': '5 Star Executive'
    },
    'EA': {
        'min_pqv': 300,
        'min_gqv_3cl': 75000,
        'min_qualified_legs': 12,
        'leg_rank_requirement': '1SE',
        'description': 'Emerald Ambassador'
    },
    'RA': {
        'min_pqv': 300,
        'min_gqv_3cl': 150000,
        'min_qualified_legs': 15,
        'leg_rank_requirement': '1SE',
        'description': 'Ruby Ambassador'
    },
    'DA': {
        'min_pqv': 300,
        'min_gqv_3cl': 300000,
        'min_qualified_legs': 18,
        'leg_rank_requirement': '1SE',
        'description': 'Diamond Ambassador'
    },
    'BDA': {
        'min_pqv': 300,
        'min_gqv_3cl': 600000,
        'min_qualified_legs': 21,
        'leg_rank_requirement': '1SE',
        'description': 'Black Diamond Ambassador'
    }
}

# Rank hierarchy for comparison purposes
RANK_HIERARCHY = ['PCUST', 'ASC', 'BRA', 'SA', 'SRA', '1SE', '2SE', '3SE', '4SE', '5SE', 'EA', 'RA', 'DA', 'BDA']

def calculate_gqv_3cl(member_id: str, team_data: Dict[str, Dict[str, Any]], 
                      downline_tree: Dict[str, List[str]]) -> float:
    """
    Calculate Group Qualifying Volume within 3 Compressed Levels (GQV-3CL).
    
    This implements YGY's compression logic:
    - Traverse first 3 levels of downline
    - If someone has less than 50 PQV, skip that level and process their downline instead
    - Continue until we've processed 3 compressed levels
    
    Args:
        member_id (str): The member whose GQV-3CL to calculate
        team_data (Dict): The team data dictionary
        downline_tree (Dict): The downline tree dictionary
        
    Returns:
        float: Total GQV within 3 compressed levels
    """
    def traverse_compressed_levels(current_id: str, current_level: int, max_levels: int = 3) -> float:
        """
        Recursive helper function to traverse compressed levels.
        """
        if current_level > max_levels:
            return 0.0
        
        total_gqv = 0.0
        direct_sponsees = downline_tree.get(current_id, [])
        
        for sponsee_id in direct_sponsees:
            if sponsee_id not in team_data:
                continue
                
            sponsee_pqv = team_data[sponsee_id].get('pqv', 0.0)
            
            # If sponsee has >= 50 PQV, count them at this level
            if sponsee_pqv >= 50.0:
                total_gqv += sponsee_pqv
                # Continue to next level for their downline
                total_gqv += traverse_compressed_levels(sponsee_id, current_level + 1, max_levels)
            else:
                # Skip this person and process their downline at current level (compression)
                total_gqv += traverse_compressed_levels(sponsee_id, current_level, max_levels)
        
        return total_gqv
    
    # Start traversal from level 1 (member's direct downline)
    return traverse_compressed_levels(member_id, 1)

def get_rank_level(rank: str) -> int:
    """
    Get numeric level of a rank for comparison.
    
    Args:
        rank (str): The rank to get level for
        
    Returns:
        int: Numeric level (higher = better rank)
    """
    try:
        return RANK_HIERARCHY.index(rank)
    except ValueError:
        return 0  # Default to lowest level if rank not found

def meets_rank_requirements(member_id: str, target_rank: str, team_data: Dict[str, Dict[str, Any]], 
                          downline_tree: Dict[str, List[str]], 
                          calculated_ranks: Dict[str, str]) -> bool:
    """
    Check if a member meets the requirements for a specific rank.
    
    Args:
        member_id (str): The member to check
        target_rank (str): The rank to check requirements for
        team_data (Dict): The team data dictionary
        downline_tree (Dict): The downline tree dictionary
        calculated_ranks (Dict): Previously calculated ranks
        
    Returns:
        bool: True if member meets all requirements for target rank
    """
    if target_rank not in RANK_REQUIREMENTS:
        return False
    
    requirements = RANK_REQUIREMENTS[target_rank]
    member_info = team_data.get(member_id, {})
    
    # Check PQV requirement
    member_pqv = member_info.get('pqv', 0.0)
    if member_pqv < requirements['min_pqv']:
        return False
    
    # Check GQV-3CL requirement
    member_gqv_3cl = calculate_gqv_3cl(member_id, team_data, downline_tree)
    if member_gqv_3cl < requirements['min_gqv_3cl']:
        return False
    
    # Check qualified legs requirement
    if requirements['min_qualified_legs'] > 0:
        required_leg_rank = requirements['leg_rank_requirement']
        required_leg_level = get_rank_level(required_leg_rank) if required_leg_rank else 0
        
        qualified_legs = 0
        direct_sponsees = downline_tree.get(member_id, [])
        
        for sponsee_id in direct_sponsees:
            sponsee_rank = calculated_ranks.get(sponsee_id, 'PCUST')
            sponsee_level = get_rank_level(sponsee_rank)
            
            if sponsee_level >= required_leg_level:
                qualified_legs += 1
        
        if qualified_legs < requirements['min_qualified_legs']:
            return False
    
    return True

def get_paid_as_rank(member_id: str, team_data: Dict[str, Dict[str, Any]], 
                    downline_tree: Dict[str, List[str]], 
                    calculated_ranks: Optional[Dict[str, str]] = None) -> str:
    """
    Calculate the Paid-As Rank for a member using recursive bottom-up calculation.
    
    This function works recursively:
    1. First calculates ranks for all downline members (bottom-up approach)
    2. Then determines this member's rank based on their qualifications and downline ranks
    3. Uses memoization to avoid recalculating ranks
    
    Args:
        member_id (str): The member whose rank to calculate
        team_data (Dict): The team data dictionary
        downline_tree (Dict): The downline tree dictionary
        calculated_ranks (Dict): Memoization cache for calculated ranks
        
    Returns:
        str: The member's Paid-As Rank
    """
    # Initialize calculated_ranks cache if not provided
    if calculated_ranks is None:
        calculated_ranks = {}
    
    # Return cached result if already calculated
    if member_id in calculated_ranks:
        return calculated_ranks[member_id]
    
    # If member doesn't exist in team_data, default to PCUST
    if member_id not in team_data:
        calculated_ranks[member_id] = 'PCUST'
        return 'PCUST'
    
    # First, recursively calculate ranks for all direct sponsees (bottom-up)
    direct_sponsees = downline_tree.get(member_id, [])
    for sponsee_id in direct_sponsees:
        get_paid_as_rank(sponsee_id, team_data, downline_tree, calculated_ranks)
    
    # Check member type first - PCUSTs cannot become distributors regardless of volume
    member_info = team_data[member_id]
    member_title = member_info.get('title', '').upper().strip()
    
    # If member is enrolled as PCUST, they remain PCUST regardless of volume
    if member_title == 'PCUST':
        member_rank = 'PCUST'
    else:
        # For distributors, determine rank by checking requirements from highest to lowest
        member_rank = 'PCUST'  # Default to lowest rank
        
        # Check each rank from highest to lowest to find the highest qualifying rank
        for rank in reversed(RANK_HIERARCHY):
            if meets_rank_requirements(member_id, rank, team_data, downline_tree, calculated_ranks):
                member_rank = rank
                break
    
    # Cache and return the result
    calculated_ranks[member_id] = member_rank
    return member_rank

def calculate_all_ranks(team_data: Dict[str, Dict[str, Any]], 
                       downline_tree: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Calculate Paid-As Ranks for all members in the organization.
    
    Args:
        team_data (Dict): The team data dictionary
        downline_tree (Dict): The downline tree dictionary
        
    Returns:
        Dict[str, str]: Dictionary mapping member IDs to their Paid-As Ranks
    """
    calculated_ranks = {}
    
    # Calculate ranks for all members
    for member_id in team_data.keys():
        get_paid_as_rank(member_id, team_data, downline_tree, calculated_ranks)
    
    return calculated_ranks

def analyze_member_qualifications(member_id: str, team_data: Dict[str, Dict[str, Any]], 
                                downline_tree: Dict[str, List[str]], 
                                calculated_ranks: Dict[str, str]) -> Dict[str, Any]:
    """
    Provide detailed qualification analysis for a member.
    
    Args:
        member_id (str): The member to analyze
        team_data (Dict): The team data dictionary
        downline_tree (Dict): The downline tree dictionary
        calculated_ranks (Dict): Dictionary of calculated ranks
        
    Returns:
        Dict[str, Any]: Detailed qualification analysis
    """
    if member_id not in team_data:
        return {'error': 'Member not found'}
    
    member_info = team_data[member_id]
    current_rank = calculated_ranks.get(member_id, 'PCUST')
    
    # Calculate current qualifications
    member_pqv = member_info.get('pqv', 0.0)
    member_gqv_3cl = calculate_gqv_3cl(member_id, team_data, downline_tree)
    
    # Count qualified legs by rank
    direct_sponsees = downline_tree.get(member_id, [])
    leg_analysis = {}
    
    for rank in RANK_HIERARCHY[1:]:  # Skip PCUST
        required_level = get_rank_level(rank)
        qualified_count = sum(1 for sponsee_id in direct_sponsees 
                            if get_rank_level(calculated_ranks.get(sponsee_id, 'PCUST')) >= required_level)
        leg_analysis[rank] = qualified_count
    
    # Determine next achievable rank
    next_rank = None
    next_rank_gaps = {}
    
    current_level = get_rank_level(current_rank)
    for rank in RANK_HIERARCHY[current_level + 1:]:
        requirements = RANK_REQUIREMENTS[rank]
        
        pqv_gap = max(0, requirements['min_pqv'] - member_pqv)
        gqv_gap = max(0, requirements['min_gqv_3cl'] - member_gqv_3cl)
        
        if requirements['min_qualified_legs'] > 0:
            required_leg_rank = requirements['leg_rank_requirement']
            current_qualified_legs = leg_analysis.get(required_leg_rank, 0)
            leg_gap = max(0, requirements['min_qualified_legs'] - current_qualified_legs)
        else:
            leg_gap = 0
        
        if next_rank is None and (pqv_gap > 0 or gqv_gap > 0 or leg_gap > 0):
            next_rank = rank
            next_rank_gaps = {
                'pqv_gap': pqv_gap,
                'gqv_gap': gqv_gap,
                'leg_gap': leg_gap
            }
            break
    
    return {
        'member_id': member_id,
        'name': member_info.get('name', ''),
        'current_rank': current_rank,
        'pqv': member_pqv,
        'gqv_3cl': member_gqv_3cl,
        'direct_sponsees_count': len(direct_sponsees),
        'qualified_legs_by_rank': leg_analysis,
        'next_achievable_rank': next_rank,
        'gaps_to_next_rank': next_rank_gaps
    }

# ============================================================================
# PHASE 3: STRATEGIC MOVE IDENTIFIER
# ============================================================================

def identify_strategic_assets(leader_id: str, team_data: Dict[str, Dict[str, Any]], 
                             volume_details_df: pd.DataFrame, today_date: datetime) -> Dict[str, Any]:
    """
    Identify strategic assets for a team leader based on YGY 60-day rule.
    
    Args:
        leader_id (str): The team leader's ID
        team_data (Dict): The team data dictionary
        volume_details_df (pd.DataFrame): Group volume details DataFrame
        today_date (datetime): Current date for 60-day calculations
        
    Returns:
        Dict[str, Any]: Dictionary containing volume donors and placeable assets
    """
    from datetime import timedelta
    
    if leader_id not in team_data:
        return {'error': 'Leader not found'}
    
    # Get leader's frontline PCUSTs (direct sponsees who are PCUST)
    frontline_pcusts = []
    calculated_ranks = calculate_all_ranks(team_data, build_downline_tree(team_data))
    
    # Find all direct sponsees of the leader
    downline_tree = build_downline_tree(team_data)
    direct_sponsees = downline_tree.get(leader_id, [])
    
    for sponsee_id in direct_sponsees:
        if sponsee_id in calculated_ranks and calculated_ranks[sponsee_id] == 'PCUST':
            frontline_pcusts.append(sponsee_id)
    
    # Calculate 60-day cutoff date
    cutoff_date = today_date - timedelta(days=60)
    
    volume_donors = []
    placeable_assets = []
    
    for pcust_id in frontline_pcusts:
        if pcust_id not in team_data:
            continue
            
        pcust_info = team_data[pcust_id]
        
        # Use consistent 60-day move validation
        move_status = can_pcust_be_moved(pcust_info, today_date)
        
        # Check if PCUST can be moved (within 60 days) or is locked (past 60 days)
        if not move_status['can_move']:
            # This is a Volume Donor - find their movable orders
            pcust_orders = volume_details_df[
                (volume_details_df['Associate #'] == int(pcust_id)) & 
                (volume_details_df['Autoship'] == 'N')
            ]
            
            for _, order in pcust_orders.iterrows():
                volume_donors.append({
                    'pcust_id': pcust_id,
                    'pcust_name': pcust_info['name'],
                    'order_number': order['Order #'],
                    'volume': order['Volume'],
                    'order_date': order['Order Date']
                })
        else:
            # This is a Placeable Asset (within 60-day window)
            # Check if personally enrolled by leader
            if pcust_info.get('enroller_id') == leader_id:
                placeable_assets.append({
                    'pcust_id': pcust_id,
                    'pcust_name': pcust_info['name'],
                    'join_date': move_status['enrollment_date'],
                    'days_since_join': move_status['days_since_enrollment'],
                    'days_remaining': move_status['days_remaining']
                })
    
    return {
        'leader_id': leader_id,
        'leader_name': team_data[leader_id]['name'],
        'frontline_pcusts_count': len(frontline_pcusts),
        'volume_donors': volume_donors,
        'placeable_assets': placeable_assets,
        'analysis_date': today_date.strftime('%Y-%m-%d')
    }

def suggest_pqv_moves(pqv_gap: float, volume_donors: List[Dict[str, Any]], leader_info: Dict[str, Any] = None) -> List[str]:
    """
    Suggest the best combination of movable orders to meet the PQV gap.
    Format suggestions like successful 1SE achievement moves.
    
    Args:
        pqv_gap (float): The amount of PQV needed
        volume_donors (List[Dict]): List of movable orders from volume donors
        leader_info (Dict): Information about the leader for personalized suggestions
        
    Returns:
        List[str]: List of text suggestions for PQV moves
    """
    suggestions = []
    
    if pqv_gap <= 0:
        suggestions.append("[OK] No personal PQV needed - meets rank requirement")
        return suggestions
    
    leader_name = leader_info.get('name', 'LEADER') if leader_info else 'LEADER'
    leader_id = leader_info.get('member_id', 'YOUR_ID') if leader_info else 'YOUR_ID'
    
    if not volume_donors:
        suggestions.append(f"[PERSONAL] {leader_name} ({leader_id}): Add ${pqv_gap:.2f} in personal volume to meet PQV requirement")
        return suggestions
    
    # Sort orders by volume descending to optimize suggestions
    sorted_orders = sorted(volume_donors, key=lambda x: x.get('volume', 0), reverse=True)
    
    suggestions.append(f"[TARGET] {leader_name} needs ${pqv_gap:.2f} in personal PQV - Strategic Order Moves:")
    
    # Find best combination of orders - format like 1SE success example
    total_suggested = 0
    move_count = 0
    
    for order in sorted_orders:
        if total_suggested >= pqv_gap:
            break
            
        order_volume = order.get('volume', 0)
        if order_volume <= 0:
            continue
            
        move_count += 1
        total_suggested += order_volume
        
        # Format exactly like user's successful 1SE moves:
        # "Wells, Carole 33884292 → 102773173 Coronado, David"
        donor_name = order.get('pcust_name', 'Unknown')
        donor_id = order.get('pcust_id', 'N/A')
        order_num = order.get('order_number', 'N/A')
        
        suggestions.append(f"[MOVE {move_count}] {donor_name} {order_num} → {leader_id} {leader_name}: ${order_volume:.2f}")
        
        if move_count >= 5:  # Allow up to 5 moves like user's example
            break
    
    # Add personal PQV component like user's "41+ personal PQV"
    remaining_gap = max(0, pqv_gap - total_suggested)
    if remaining_gap > 0:
        suggestions.append(f"[PERSONAL] Add ${remaining_gap:.2f}+ personal PQV (new orders)")
    
    # Success summary
    total_solution = total_suggested + remaining_gap
    suggestions.append(f"[SOLUTION] Total Strategy: ${total_solution:.2f} (${total_suggested:.2f} moves + ${remaining_gap:.2f} personal)")
    
    return suggestions

def suggest_leg_moves(leader_id: str, team_data: Dict[str, Dict[str, Any]], 
                     volume_donors: List[Dict[str, Any]], current_date: datetime) -> List[str]:
    """
    Identify underperforming legs and suggest movable orders to fix their PQV gaps.
    
    Args:
        leader_id (str): The team leader's ID
        team_data (Dict): The team data dictionary
        volume_donors (List): List of movable orders from volume donors
        current_date (datetime): Current date for 60-day PCUST move rule validation
        
    Returns:
        List[str]: List of text suggestions for leg development moves
    """
    suggestions = []
    
    if not volume_donors:
        suggestions.append("[ALERT] No movable orders available for leg development.")
        return suggestions
    
    # Get leader's direct sponsees and their ranks
    downline_tree = build_downline_tree(team_data)
    calculated_ranks = calculate_all_ranks(team_data, downline_tree)
    direct_sponsees = downline_tree.get(leader_id, [])
    
    # Analyze each leg's potential for rank advancement
    underperforming_legs = []
    pcust_legs = []
    
    for sponsee_id in direct_sponsees:
        if sponsee_id not in team_data:
            continue
            
        sponsee_info = team_data[sponsee_id]
        current_rank = calculated_ranks.get(sponsee_id, 'PCUST')
        current_pqv = sponsee_info.get('pqv', 0.0)
        member_title = sponsee_info.get('title', '').upper().strip()
        
        # BUSINESS RULE: PCUSTs cannot advance to distributor ranks
        # They can only be moved (within 60 days) or donate volume
        if member_title == 'PCUST' or current_rank == 'PCUST':
            # Check 60-day move eligibility
            move_status = can_pcust_be_moved(sponsee_info, current_date)
            
            # Track PCUSTs separately for volume donation or placement suggestions
            pcust_legs.append({
                'sponsee_id': sponsee_id,
                'name': sponsee_info['name'],
                'current_pqv': current_pqv,
                'title': member_title,
                'move_status': move_status
            })
            continue  # Skip rank advancement analysis for PCUSTs
        
        # Only analyze distributors for rank advancement - check ALL requirements
        next_rank_gap = None
        for rank in RANK_HIERARCHY:
            if get_rank_level(rank) > get_rank_level(current_rank):
                requirements = RANK_REQUIREMENTS[rank]
                
                # Calculate all requirement gaps
                pqv_gap = max(0, requirements['min_pqv'] - current_pqv)
                
                # Calculate GQV-3CL if needed
                current_gqv = calculate_gqv_3cl(sponsee_id, team_data, build_downline_tree(team_data))
                gqv_gap = max(0, requirements['min_gqv_3cl'] - current_gqv)
                
                # Check qualifying legs
                qualifying_legs_needed = requirements.get('min_qualified_legs', 0)
                leg_requirement_rank = requirements.get('leg_rank_requirement')
                current_qualifying_legs = 0
                
                if qualifying_legs_needed > 0 and leg_requirement_rank:
                    # Count legs that meet the rank requirement
                    for leg_id in downline_tree.get(sponsee_id, []):
                        leg_rank = calculated_ranks.get(leg_id, 'PCUST')
                        if get_rank_level(leg_rank) >= get_rank_level(leg_requirement_rank):
                            current_qualifying_legs += 1
                
                legs_gap = max(0, qualifying_legs_needed - current_qualifying_legs)
                
                # Consider advancement opportunity if ANY gap exists and PQV gap is reasonable
                total_strategic_gap = pqv_gap + (gqv_gap * 0.1) + (legs_gap * 50)  # Weighted scoring
                
                if (pqv_gap > 0 and pqv_gap <= 500) or (legs_gap > 0 and legs_gap <= 2) or (gqv_gap > 0 and gqv_gap <= 2000):
                    next_rank_gap = {
                        'sponsee_id': sponsee_id,
                        'name': sponsee_info['name'],
                        'current_rank': current_rank,
                        'current_pqv': current_pqv,
                        'current_gqv': current_gqv,
                        'current_qualifying_legs': current_qualifying_legs,
                        'target_rank': rank,
                        'pqv_gap': pqv_gap,
                        'gqv_gap': gqv_gap,
                        'legs_gap': legs_gap,
                        'total_strategic_gap': total_strategic_gap
                    }
                    break
        
        if next_rank_gap:
            underperforming_legs.append(next_rank_gap)
    
    # Provide PCUST business rule information
    if pcust_legs:
        # Categorize PCUSTs by move eligibility
        movable_pcusts = [p for p in pcust_legs if p['move_status']['can_move']]
        locked_pcusts = [p for p in pcust_legs if not p['move_status']['can_move']]
        
        suggestions.append(f"[PCUST INFO] Found {len(pcust_legs)} PCUST legs:")
        suggestions.append("[ALERT] BUSINESS RULE: PCUSTs cannot advance to distributor ranks.")
        suggestions.append("[OPTIONS] PCUST Strategic Options:")
        suggestions.append("   • Move to different upline (ONLY within 60 days of enrollment)")
        suggestions.append("   • Use their volume to help build qualifying legs")
        suggestions.append("   • Focus on personal volume contribution")
        suggestions.append("")
        
        # Show movable PCUSTs first
        if movable_pcusts:
            suggestions.append(f"[MOVABLE] PCUSTs ({len(movable_pcusts)} within 60-day window):")
            for pcust in movable_pcusts[:3]:  # Show first 3 movable
                move_info = pcust['move_status']
                suggestions.append(f"   [MOVABLE] {pcust['name']} (ID: {pcust['sponsee_id']}) - PQV: ${pcust['current_pqv']:.2f}")
                suggestions.append(f"             Enrolled: {move_info['enrollment_date']} | {move_info['reason']}")
            if len(movable_pcusts) > 3:
                suggestions.append(f"   ... and {len(movable_pcusts) - 3} more movable PCUSTs")
            suggestions.append("")
        
        # Show locked PCUSTs
        if locked_pcusts:
            suggestions.append(f"🔒 LOCKED PCUSTs ({len(locked_pcusts)} past 60-day window):")
            for pcust in locked_pcusts[:3]:  # Show first 3 locked
                move_info = pcust['move_status']
                suggestions.append(f"   [LOCKED] {pcust['name']} (ID: {pcust['sponsee_id']}) - PQV: ${pcust['current_pqv']:.2f}")
                if move_info['enrollment_date']:
                    suggestions.append(f"            Enrolled: {move_info['enrollment_date']} | {move_info['reason']}")
                else:
                    suggestions.append(f"            {move_info['reason']}")
            if len(locked_pcusts) > 3:
                suggestions.append(f"   ... and {len(locked_pcusts) - 3} more locked PCUSTs")
            suggestions.append("")
    
    if not underperforming_legs:
        if pcust_legs:
            suggestions.append("[OK] All distributor legs are performing optimally. Focus on PCUST volume contribution and placement strategy.")
        else:
            suggestions.append("[OK] All frontline legs are performing optimally or gaps are too large to fill with available volume.")
        return suggestions
    
    # Sort legs by smallest gap first (easiest wins)
    underperforming_legs.sort(key=lambda x: x['pqv_gap'])
    
    suggestions.append(f"[TARGET] Found {len(underperforming_legs)} DISTRIBUTOR legs with advancement opportunities:")
    suggestions.append("[OK] These are enrolled distributors who can advance with strategic volume moves.")
    suggestions.append("")
    
    available_volume = sum(order['volume'] for order in volume_donors)
    used_orders = []
    
    for leg in underperforming_legs:
        suggestions.append(
            f"[LEG] {leg['name']} (ID: {leg['sponsee_id']}) - {leg['current_rank']} -> {leg['target_rank']}"
        )
        
        # Show complete requirements analysis
        target_requirements = RANK_REQUIREMENTS[leg['target_rank']]
        suggestions.append(f"   [PQV] Current: ${leg['current_pqv']:.2f} | Need: ${target_requirements['min_pqv']:.2f} | Gap: ${leg['pqv_gap']:.2f}")
        
        if target_requirements['min_gqv_3cl'] > 0:
            suggestions.append(f"   [GQV] Current: ${leg['current_gqv']:.2f} | Need: ${target_requirements['min_gqv_3cl']:.2f} | Gap: ${leg['gqv_gap']:.2f}")
        
        if target_requirements['min_qualified_legs'] > 0:
            leg_req_rank = target_requirements['leg_rank_requirement']
            suggestions.append(f"   [LEGS] Current: {leg['current_qualifying_legs']} {leg_req_rank}+ legs | Need: {target_requirements['min_qualified_legs']} | Gap: {leg['legs_gap']}")
        
        # Priority messaging
        if leg['pqv_gap'] > 0:
            suggestions.append(f"   [PRIORITY] PQV gap can be filled with volume moves")
        if leg['legs_gap'] > 0:
            leg_req_rank = target_requirements['leg_rank_requirement']
            suggestions.append(f"   [PRIORITY] Need to build {leg['legs_gap']} more {leg_req_rank}+ qualifying legs")
        if leg['gqv_gap'] > 0:
            suggestions.append(f"   [PRIORITY] Need ${leg['gqv_gap']:.2f} more team volume (GQV-3CL)")
        
        # Find best orders for this leg
        available_orders = [order for order in volume_donors if order not in used_orders]
        # Get leg member info for personalized suggestions
        leg_member_info = {'name': leg['name'], 'member_id': leg['sponsee_id']}
        leg_suggestions = suggest_pqv_moves(leg['pqv_gap'], available_orders, leg_member_info)
        
        if "✅ PQV Gap Solution Found" in leg_suggestions[0]:
            # Mark orders as used
            running_total = 0
            for order in available_orders:
                if running_total >= leg['pqv_gap']:
                    break
                used_orders.append(order)
                running_total += order['volume']
            
            suggestions.append("   [MOVES] Recommended moves:")
            for suggestion in leg_suggestions[2:]:  # Skip header lines
                if suggestion.startswith("  •"):
                    suggestions.append(f"     {suggestion}")
        else:
            suggestions.append("   [ALERT] Insufficient available volume for this leg")
        
        suggestions.append("")
    
    return suggestions
def suggest_placement_moves(placeable_assets: List[Dict[str, Any]], 
                           downline_tree: Dict[str, List[str]]) -> List[str]:
    """
    Suggest strategic locations to place new PCUSTs within the 60-day window.
    
    Args:
        placeable_assets (List): List of PCUSTs within 60-day window
        downline_tree (Dict): The downline tree dictionary
        
    Returns:
        List[str]: List of text suggestions for strategic placements
    """
    suggestions = []
    
    if not placeable_assets:
        suggestions.append("[OK] No new PCUSTs within 60-day placement window.")
        return suggestions
    
    suggestions.append(f"[PLACEMENT] Found {len(placeable_assets)} PCUSTs available for strategic placement:")
    suggestions.append("")
    
    for asset in placeable_assets:
        days_left = 60 - asset['days_since_join']
        suggestions.append(
            f"[PCUST] {asset['pcust_name']} (ID: {asset['pcust_id']}) - {days_left} days left to move"
        )
        suggestions.append(f"   Joined: {asset['join_date']} ({asset['days_since_join']} days ago)")
        
        # Strategic placement suggestions
        suggestions.append("   [OPTIONS] Strategic Placement Options:")
        suggestions.append("     1. Move under developing legs to help with rank requirements")
        suggestions.append("     2. Create new leg if leader needs more frontline diversity")
        suggestions.append("     3. Place under top performers to maximize team growth potential")
        suggestions.append("     4. Strategic depth placement for future compression benefits")
        suggestions.append("")
    
    suggestions.append("[STRATEGY] General Placement Strategy:")
    suggestions.append("• Priority 1: Support legs close to rank advancement")
    suggestions.append("• Priority 2: Balance frontline for better qualification")
    suggestions.append("• Priority 3: Strategic depth for long-term growth")
    suggestions.append("• Remember: You have until day 60 to make these moves!")
    
    return suggestions

def analyze_leader_strategic_moves(leader_id: str, team_data: Dict[str, Dict[str, Any]], 
                                  volume_details_df: pd.DataFrame, downline_tree: Dict[str, List[str]], 
                                  calculated_ranks: Dict[str, str], today_date: datetime) -> Dict[str, Any]:
    """
    Complete strategic analysis for a team leader combining all Phase 3 functions.
    
    Args:
        leader_id (str): The team leader's ID
        team_data (Dict): The team data dictionary
        volume_details_df (pd.DataFrame): Group volume details DataFrame
        downline_tree (Dict): The downline tree dictionary
        calculated_ranks (Dict): Dictionary of calculated ranks
        today_date (datetime): Current date for analysis
        
    Returns:
        Dict[str, Any]: Complete strategic analysis with all recommendations
    """
    # Get leader's current qualifications
    leader_analysis = analyze_member_qualifications(leader_id, team_data, downline_tree, calculated_ranks)
    
    # Identify strategic assets
    assets = identify_strategic_assets(leader_id, team_data, volume_details_df, today_date)
    
    # Generate recommendations
    pqv_gap = leader_analysis.get('gaps_to_next_rank', {}).get('pqv_gap', 0)
    # Pass leader info for personalized PQV suggestions
    leader_info_for_pqv = {'name': leader_analysis.get('name', 'LEADER'), 'member_id': leader_id}
    pqv_suggestions = suggest_pqv_moves(pqv_gap, assets.get('volume_donors', []), leader_info_for_pqv)
    leg_suggestions = suggest_leg_moves(leader_id, team_data, assets.get('volume_donors', []), today_date)
    placement_suggestions = suggest_placement_moves(assets.get('placeable_assets', []), downline_tree)
    
    return {
        'leader_info': leader_analysis,
        'strategic_assets': assets,
        'pqv_recommendations': pqv_suggestions,
        'leg_development_recommendations': leg_suggestions,
        'placement_recommendations': placement_suggestions,
        'analysis_date': today_date.strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    """
    Main function to demonstrate Phase 1, Phase 2, and Phase 3 functionality.
    """
    print("=== Youngevity Strategy Tool - Phase 1, 2 & 3 ====")
    print(f"Current LA Time: {get_current_date_la_timezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    try:
        # Load CSV files
        print("Step 1: Loading CSV files...")
        group_volume_df, genealogy_df = load_csv_files()
        print()
        
        # Create team data dictionary
        print("Step 2: Creating team data dictionary...")
        team_data = create_team_data_dictionary(genealogy_df)
        print()
        
        # Build downline tree
        print("Step 3: Building downline tree...")
        downline_tree = build_downline_tree(team_data)
        print()
        
        # Calculate hierarchical levels
        print("Step 4.1: Calculating hierarchical levels...")
        hierarchical_levels = calculate_hierarchical_levels(team_data, downline_tree)
        
        # Store levels in team_data for later use
        for member_id, level in hierarchical_levels.items():
            if member_id in team_data:
                team_data[member_id]['hierarchical_level'] = level
        print()
        
        # Display summary statistics
        print("Step 4: Team Summary Statistics:")
        summary = get_member_summary(team_data)
        for key, value in summary.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print()
        
        # Display some sample data
        print("Step 5: Sample team data (first 3 members):")
        sample_members = list(team_data.keys())[:3]
        for member_id in sample_members:
            member_info = team_data[member_id]
            print(f"  ID {member_id}: {member_info['name']} ({member_info['title']}) - PQV: ${member_info['pqv']:.2f}")
        print()
        
        # Display top sponsors by downline size
        print("Step 6: Top sponsors by downline size:")
        if downline_tree:
            sorted_sponsors = sorted(downline_tree.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            for sponsor_id, sponsees in sorted_sponsors:
                sponsor_name = team_data.get(sponsor_id, {}).get('name', 'Unknown')
                print(f"  {sponsor_name} (ID: {sponsor_id}): {len(sponsees)} direct sponsees")
        print()
        
        # PHASE 2: Demonstrate calculation engine
        print("=== PHASE 2: CALCULATION ENGINE ===")
        print()
        
        print("Step 7: Calculating Paid-As Ranks for all members...")
        calculated_ranks = calculate_all_ranks(team_data, downline_tree)
        
        # Rank distribution analysis
        rank_distribution = {}
        for rank in calculated_ranks.values():
            rank_distribution[rank] = rank_distribution.get(rank, 0) + 1
        
        print("Calculated Paid-As Ranks Distribution:")
        for rank in RANK_HIERARCHY:
            count = rank_distribution.get(rank, 0)
            if count > 0:
                print(f"  {rank} ({RANK_REQUIREMENTS[rank]['description']}): {count} members")
        print()
        
        print("Step 8: Analyzing top performers...")
        # Find members with ranks above PCUST
        distributors = [(member_id, rank) for member_id, rank in calculated_ranks.items() 
                       if rank != 'PCUST']
        distributors.sort(key=lambda x: get_rank_level(x[1]), reverse=True)
        
        print(f"Found {len(distributors)} active distributors (above PCUST):")
        for member_id, rank in distributors[:10]:  # Show top 10
            member_info = team_data[member_id]
            analysis = analyze_member_qualifications(member_id, team_data, downline_tree, calculated_ranks)
            print(f"  {member_info['name']} (ID: {member_id})")
            print(f"    Current Rank: {rank} | PQV: ${analysis['pqv']:.2f} | GQV-3CL: ${analysis['gqv_3cl']:.2f}")
            if analysis['next_achievable_rank']:
                gaps = analysis['gaps_to_next_rank']
                print(f"    Next Rank: {analysis['next_achievable_rank']} | Gaps: PQV: ${gaps['pqv_gap']:.2f}, GQV: ${gaps['gqv_gap']:.2f}, Legs: {gaps['leg_gap']}")
        print()
        
        print("Step 9: Sample GQV-3CL calculations...")
        # Show some GQV-3CL calculations for key members
        top_gqv_members = []
        for member_id in team_data.keys():
            if team_data[member_id].get('pqv', 0) > 100:  # Members with significant PQV
                gqv_3cl = calculate_gqv_3cl(member_id, team_data, downline_tree)
                if gqv_3cl > 0:
                    top_gqv_members.append((member_id, gqv_3cl))
        
        top_gqv_members.sort(key=lambda x: x[1], reverse=True)
        print("Top 5 members by GQV-3CL:")
        for member_id, gqv_3cl in top_gqv_members[:5]:
            member_info = team_data[member_id]
            print(f"  {member_info['name']}: ${gqv_3cl:.2f} GQV-3CL | PQV: ${member_info['pqv']:.2f}")
        print()
        
        print(f"\n[SUCCESS] Phase 1 & 2 completed successfully!")
        
        # ===== PHASE 3: STRATEGIC MOVE IDENTIFIER DEMO =====
        print("\n=== PHASE 3: STRATEGIC MOVE IDENTIFIER ===")
        
        # Test with team leaders
        test_leaders = ['102742703', '102807573']  # Nutrientshelp LLC, Ariali PTL Properties LLC
        current_date = get_current_date_la_timezone()
        
        for leader_id in test_leaders:
            if leader_id in team_data:
                print(f"\nStep 10: Strategic Analysis for {team_data[leader_id]['name']} (ID: {leader_id})")
                
                # Run complete strategic analysis
                strategic_analysis = analyze_leader_strategic_moves(
                    leader_id, team_data, group_volume_df, downline_tree, calculated_ranks, current_date
                )
                
                # Display results
                leader_info = strategic_analysis['leader_info']
                assets = strategic_analysis['strategic_assets']
                
                print(f"  Current Rank: {leader_info['current_rank']} | PQV: ${leader_info['pqv']:.2f}")
                print(f"  Next Rank: {leader_info['next_achievable_rank']} | Gaps: PQV: ${leader_info['gaps_to_next_rank']['pqv_gap']:.2f}")
                print(f"  Frontline PCUSTs: {assets['frontline_pcusts_count']}")
                print(f"  Volume Donors (60+ days): {len(assets['volume_donors'])} orders available")
                print(f"  Placeable Assets (<60 days): {len(assets['placeable_assets'])} PCUSTs")
                
                # Show PQV recommendations
                if strategic_analysis['pqv_recommendations']:
                    print("\n  PQV Gap Solutions:")
                    for suggestion in strategic_analysis['pqv_recommendations'][:3]:  # Show first 3
                        print(f"    {suggestion}")
                
                # Show leg development opportunities
                if strategic_analysis['leg_development_recommendations']:
                    print("\n  Leg Development Opportunities:")
                    for suggestion in strategic_analysis['leg_development_recommendations'][:5]:  # Show first 5
                        if suggestion.strip():  # Skip empty lines
                            print(f"    {suggestion}")
                
                # Show placement opportunities
                if strategic_analysis['placement_recommendations']:
                    print("\n  Strategic Placement Opportunities:")
                    for suggestion in strategic_analysis['placement_recommendations'][:3]:  # Show first 3
                        if suggestion.strip():  # Skip empty lines
                            print(f"    {suggestion}")
        
        print(f"\n[SUCCESS] Phase 1, 2 & 3 completed successfully!")
        
        print("\nThe following variables are now available:")
        print("  - group_volume_df: Group Volume Details DataFrame")
        print("  - genealogy_df: Advanced Genealogy Report DataFrame")
        print("  - team_data: Central dictionary with member information")
        print("  - downline_tree: Dictionary mapping sponsors to their direct sponsees")
        print("  - calculated_ranks: Dictionary mapping member IDs to Paid-As Ranks")
        print("  - RANK_REQUIREMENTS: Dictionary with all YGY rank qualification rules")
        
        print("\nPhase 2 Functions Available:")
        print("  - calculate_gqv_3cl(member_id, team_data, downline_tree)")
        print("  - analyze_member_qualifications(member_id, team_data, downline_tree, calculated_ranks)")
        
        print("\nPhase 3 Functions Available:")
        print("  - identify_strategic_assets(leader_id, team_data, volume_details_df, today_date)")
        print("  - suggest_pqv_moves(pqv_gap, volume_donors)")
        print("  - suggest_leg_moves(leader_id, team_data, volume_donors)")
        print("  - suggest_placement_moves(placeable_assets, downline_tree)")
        print("  - analyze_leader_strategic_moves(leader_id, team_data, volume_df, downline_tree, ranks, date)")
        
        return group_volume_df, genealogy_df, team_data, downline_tree, calculated_ranks
        
    except Exception as e:
        print(f"[ERROR] Error during data setup: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the main data setup and calculation process
    group_volume_df, genealogy_df, team_data, downline_tree, calculated_ranks = main()
