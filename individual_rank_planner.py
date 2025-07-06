#!/usr/bin/env python3
"""
Individual Rank Advancement Planner
Focused analysis for a single member's rank advancement strategy
"""

from typing import Dict, List, Any, Optional
from ygy_data_setup import (
    RANK_REQUIREMENTS, RANK_HIERARCHY, get_rank_level, 
    calculate_gqv_3cl, build_downline_tree, get_paid_as_rank
)

def analyze_individual_rank_advancement(
    target_member_id: str, 
    desired_rank: str,
    team_data: Dict[str, Dict[str, Any]], 
    volume_donors: List[Dict[str, Any]],
    current_date
) -> Dict[str, Any]:
    """
    Analyze what a specific member needs to achieve a desired rank.
    
    Args:
        target_member_id: The member to analyze
        desired_rank: The rank they want to achieve
        team_data: Team data dictionary
        volume_donors: Available movable orders
        current_date: Current date for analysis
        
    Returns:
        Dict with complete advancement strategy
    """
    
    if target_member_id not in team_data:
        return {"error": f"Member ID {target_member_id} not found"}
    
    if desired_rank not in RANK_REQUIREMENTS:
        return {"error": f"Invalid rank: {desired_rank}"}
    
    # Get member info
    member_info = team_data[target_member_id]
    member_name = member_info['name']
    
    # Calculate current status
    downline_tree = build_downline_tree(team_data)
    calculated_ranks = {}
    current_rank = get_paid_as_rank(target_member_id, team_data, downline_tree, calculated_ranks)
    current_pqv = member_info.get('pqv', 0.0)
    current_gqv = calculate_gqv_3cl(target_member_id, team_data, downline_tree)
    
    # Get target requirements
    target_requirements = RANK_REQUIREMENTS[desired_rank]
    
    # Calculate gaps
    pqv_gap = max(0, target_requirements['min_pqv'] - current_pqv)
    gqv_gap = max(0, target_requirements['min_gqv_3cl'] - current_gqv)
    
    # Analyze qualifying legs
    direct_legs = downline_tree.get(target_member_id, [])
    qualifying_legs_needed = target_requirements.get('min_qualified_legs', 0)
    leg_requirement_rank = target_requirements.get('leg_rank_requirement')
    
    current_qualifying_legs = []
    potential_qualifying_legs = []
    
    for leg_id in direct_legs:
        if leg_id not in team_data:
            continue
            
        leg_info = team_data[leg_id]
        leg_rank = get_paid_as_rank(leg_id, team_data, downline_tree, calculated_ranks)
        leg_pqv = leg_info.get('pqv', 0.0)
        
        if leg_requirement_rank and get_rank_level(leg_rank) >= get_rank_level(leg_requirement_rank):
            current_qualifying_legs.append({
                'id': leg_id,
                'name': leg_info['name'],
                'rank': leg_rank,
                'pqv': leg_pqv
            })
        else:
            # Check if this leg could be upgraded
            if leg_requirement_rank:
                leg_req = RANK_REQUIREMENTS[leg_requirement_rank]
                leg_pqv_gap = max(0, leg_req['min_pqv'] - leg_pqv)
                
                potential_qualifying_legs.append({
                    'id': leg_id,
                    'name': leg_info['name'],
                    'current_rank': leg_rank,
                    'current_pqv': leg_pqv,
                    'target_rank': leg_requirement_rank,
                    'pqv_gap': leg_pqv_gap
                })
    
    legs_gap = max(0, qualifying_legs_needed - len(current_qualifying_legs))
    
    # Generate specific move recommendations
    move_recommendations = generate_individual_move_strategy(
        target_member_id, member_name, pqv_gap, potential_qualifying_legs, 
        legs_gap, volume_donors, leg_requirement_rank
    )
    
    return {
        'member_id': target_member_id,
        'member_name': member_name,
        'current_rank': current_rank,
        'desired_rank': desired_rank,
        'current_pqv': current_pqv,
        'current_gqv': current_gqv,
        'target_requirements': target_requirements,
        'gaps': {
            'pqv_gap': pqv_gap,
            'gqv_gap': gqv_gap,
            'legs_gap': legs_gap
        },
        'current_qualifying_legs': current_qualifying_legs,
        'potential_qualifying_legs': potential_qualifying_legs,
        'move_recommendations': move_recommendations,
        'is_achievable': pqv_gap == 0 or len(volume_donors) > 0
    }

def generate_individual_move_strategy(
    target_member_id: str,
    member_name: str,
    pqv_gap: float,
    potential_legs: List[Dict],
    legs_gap: int,
    volume_donors: List[Dict[str, Any]],
    leg_requirement_rank: str
) -> List[str]:
    """
    Generate specific move recommendations for individual rank advancement.
    """
    recommendations = []
    recommendations.append(f"[STRATEGY] Complete Rank Advancement Plan for {member_name}")
    recommendations.append("")
    
    # Personal PQV strategy
    if pqv_gap > 0:
        recommendations.append(f"[PERSONAL PQV] Need ${pqv_gap:.2f} additional personal volume:")
        
        # Find orders that could be moved to this member
        available_volume = sum(order['volume'] for order in volume_donors)
        if available_volume >= pqv_gap:
            recommendations.append(f"   [SOLUTION] Move orders to {member_name} (ID: {target_member_id}):")
            
            running_total = 0
            move_count = 0
            for order in sorted(volume_donors, key=lambda x: x['volume'], reverse=True):
                if running_total >= pqv_gap:
                    break
                move_count += 1
                running_total += order['volume']
                donor_name = order.get('donor_name', 'Unknown')
                order_num = order.get('order_number', 'N/A')
                recommendations.append(f"   [MOVE {move_count}] {donor_name} {order_num} → {target_member_id} {member_name}: ${order['volume']:.2f}")
            
            remaining_gap = max(0, pqv_gap - running_total)
            if remaining_gap > 0:
                recommendations.append(f"   [PERSONAL] Add ${remaining_gap:.2f}+ new personal orders")
        else:
            recommendations.append(f"   [ALERT] Only ${available_volume:.2f} available volume - need ${pqv_gap - available_volume:.2f} new personal orders")
        
        recommendations.append("")
    
    # Qualifying legs strategy
    if legs_gap > 0:
        recommendations.append(f"[QUALIFYING LEGS] Need {legs_gap} more {leg_requirement_rank}+ legs:")
        
        # Sort potential legs by smallest gap first
        potential_legs_sorted = sorted(potential_legs, key=lambda x: x['pqv_gap'])
        
        used_volume = sum(order['volume'] for order in volume_donors[:legs_gap]) if volume_donors else 0
        available_for_legs = [order for order in volume_donors if order not in volume_donors[:legs_gap]] if volume_donors else []
        
        leg_solutions = []
        for i, leg in enumerate(potential_legs_sorted[:legs_gap]):
            leg_name = leg['name']
            leg_id = leg['id']
            leg_gap = leg['pqv_gap']
            
            recommendations.append(f"   [LEG {i+1}] {leg_name} (ID: {leg_id}) - {leg['current_rank']} → {leg['target_rank']}")
            recommendations.append(f"            Current PQV: ${leg['current_pqv']:.2f} | Need: ${leg_gap:.2f}")
            
            # Find orders for this specific leg
            leg_volume_available = sum(order['volume'] for order in available_for_legs)
            if leg_volume_available >= leg_gap:
                recommendations.append(f"            [SOLUTION] Move orders to {leg_name}:")
                
                leg_running_total = 0
                leg_move_count = 0
                for order in sorted(available_for_legs, key=lambda x: x['volume'], reverse=True):
                    if leg_running_total >= leg_gap:
                        break
                    leg_move_count += 1
                    leg_running_total += order['volume']
                    donor_name = order.get('donor_name', 'Unknown')
                    order_num = order.get('order_number', 'N/A')
                    recommendations.append(f"            [MOVE] {donor_name} {order_num} → {leg_id} {leg_name}: ${order['volume']:.2f}")
                    available_for_legs.remove(order)
                
                leg_solutions.append(leg_name)
            else:
                recommendations.append(f"            [ALERT] Insufficient volume - need ${leg_gap - leg_volume_available:.2f} more")
            
            recommendations.append("")
        
        if len(leg_solutions) >= legs_gap:
            recommendations.append(f"   [SUCCESS] All {legs_gap} qualifying legs can be built!")
        else:
            recommendations.append(f"   [PARTIAL] Only {len(leg_solutions)} of {legs_gap} legs have sufficient volume")
        
        recommendations.append("")
    
    # Summary
    total_moves = len([r for r in recommendations if '[MOVE' in r])
    recommendations.append(f"[SUMMARY] Total Strategic Moves Required: {total_moves}")
    recommendations.append(f"[OUTCOME] {member_name} advancement to {leg_requirement_rank if 'leg_requirement_rank' in locals() else 'next rank'}")
    
    return recommendations

def get_available_ranks_for_member(current_rank: str) -> List[str]:
    """
    Get list of achievable ranks for a member based on their current rank.
    """
    current_level = get_rank_level(current_rank)
    available_ranks = []
    
    for rank in RANK_HIERARCHY:
        if get_rank_level(rank) > current_level:
            available_ranks.append(rank)
    
    return available_ranks
