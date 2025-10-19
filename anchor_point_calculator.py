#!/usr/bin/env python3
"""
Anchor Point Calculator for Point & Figure Charts
Identifies the most populated price levels between reference points.
"""

from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnchorPoint:
    """Represents an anchor point in P&F chart."""
    price_level: float
    box_count: int
    start_column: int
    end_column: int
    anchor_type: str  # 'single', 'zone', 'major_formation'
    confidence: float  # 0.0 to 1.0
    
@dataclass
class AnchorPointZone:
    """Represents multiple anchor points forming a zone."""
    anchor_points: List[AnchorPoint]
    zone_center: float
    zone_range: Tuple[float, float]
    total_activity: int

class AnchorPointCalculator:
    """Calculate anchor points for Point & Figure charts."""
    
    def __init__(self, min_column_separation: int = 7):
        """
        Initialize anchor point calculator.
        
        Args:
            min_column_separation: Minimum columns between reference points
        """
        self.min_column_separation = min_column_separation
    
    def calculate_anchor_points(self, pnf_matrix: pd.DataFrame, 
                              start_col: Optional[int] = None, 
                              end_col: Optional[int] = None) -> List[AnchorPoint]:
        """
        Calculate anchor points from P&F matrix.
        
        Args:
            pnf_matrix: P&F matrix with columns as time, rows as price levels
            start_col: Starting column index (None for auto-detect)
            end_col: Ending column index (None for auto-detect)
            
        Returns:
            List of AnchorPoint objects
        """
        if start_col is None or end_col is None:
            start_col, end_col = self._find_reference_points(pnf_matrix)
        
        # Validate column separation
        if end_col - start_col < self.min_column_separation:
            return []
        
        # Count boxes in each price row
        box_counts = self._count_boxes_per_row(pnf_matrix, start_col, end_col)
        
        # Find anchor points
        anchor_points = self._identify_anchor_points(box_counts, start_col, end_col)
        
        return anchor_points
    
    def calculate_major_formation_anchors(self, pnf_matrix: pd.DataFrame,
                                        swing_highs: List[Tuple[int, float]],
                                        swing_lows: List[Tuple[int, float]]) -> List[AnchorPoint]:
        """
        Calculate anchor points from major tops and bottoms.
        
        Args:
            pnf_matrix: P&F matrix
            swing_highs: List of (column, price) tuples for swing highs
            swing_lows: List of (column, price) tuples for swing lows
            
        Returns:
            List of AnchorPoint objects for major formations
        """
        anchor_points = []
        
        # Process each swing high to swing low pair
        for high in swing_highs:
            for low in swing_lows:
                if abs(high[0] - low[0]) >= self.min_column_separation:
                    start_col = min(high[0], low[0])
                    end_col = max(high[0], low[0])
                    
                    # Calculate anchor between this high and low
                    formation_anchors = self.calculate_anchor_points(
                        pnf_matrix, start_col, end_col
                    )
                    
                    # Mark as major formation anchors
                    for anchor in formation_anchors:
                        anchor.anchor_type = 'major_formation'
                        anchor.confidence = self._calculate_formation_confidence(
                            anchor, high[1], low[1]
                        )
                    
                    anchor_points.extend(formation_anchors)
        
        return anchor_points
    
    def create_anchor_zones(self, anchor_points: List[AnchorPoint],
                           price_tolerance: float = 0.02) -> List[AnchorPointZone]:
        """
        Group nearby anchor points into zones.
        
        Args:
            anchor_points: List of individual anchor points
            price_tolerance: Price tolerance for grouping (as percentage)
            
        Returns:
            List of AnchorPointZone objects
        """
        if not anchor_points:
            return []
        
        # Sort by price level
        sorted_anchors = sorted(anchor_points, key=lambda x: x.price_level)
        
        zones = []
        current_zone = [sorted_anchors[0]]
        
        for anchor in sorted_anchors[1:]:
            # Check if anchor belongs to current zone
            zone_center = np.mean([a.price_level for a in current_zone])
            price_diff = abs(anchor.price_level - zone_center) / zone_center
            
            if price_diff <= price_tolerance:
                current_zone.append(anchor)
            else:
                # Create zone from current group
                if len(current_zone) > 1:
                    zones.append(self._create_zone(current_zone))
                current_zone = [anchor]
        
        # Add final zone
        if len(current_zone) > 1:
            zones.append(self._create_zone(current_zone))
        
        return zones
    
    def _find_reference_points(self, pnf_matrix: pd.DataFrame) -> Tuple[int, int]:
        """Find suitable reference points automatically."""
        total_cols = len(pnf_matrix.columns)
        
        # Use first and last columns with minimum separation
        start_col = 0
        end_col = total_cols - 1
        
        # Ensure minimum separation
        if end_col - start_col < self.min_column_separation:
            end_col = start_col + self.min_column_separation
            if end_col >= total_cols:
                start_col = max(0, total_cols - self.min_column_separation - 1)
                end_col = total_cols - 1
        
        return start_col, end_col
    
    def _count_boxes_per_row(self, pnf_matrix: pd.DataFrame, 
                           start_col: int, end_col: int) -> Dict[float, int]:
        """Count filled boxes in each price row between columns."""
        box_counts = {}
        
        # Get price levels (row indices)
        price_levels = pnf_matrix.index.tolist()
        
        for price in price_levels:
            count = 0
            
            # Count filled boxes in this row between start and end columns
            for col_idx in range(start_col, end_col + 1):
                if col_idx < len(pnf_matrix.columns):
                    cell_value = pnf_matrix.iloc[
                        pnf_matrix.index.get_loc(price), col_idx
                    ]
                    
                    # Count X's and O's as filled boxes
                    if cell_value in ['X', 'O']:
                        count += 1
            
            if count > 0:  # Only include rows with activity
                box_counts[price] = count
        
        return box_counts
    
    def _identify_anchor_points(self, box_counts: Dict[float, int],
                              start_col: int, end_col: int) -> List[AnchorPoint]:
        """Identify anchor points from box counts."""
        if not box_counts:
            return []
        
        # Find maximum box count
        max_count = max(box_counts.values())
        
        # Find all price levels with maximum count
        max_levels = [price for price, count in box_counts.items() 
                     if count == max_count]
        
        anchor_points = []
        
        for price in max_levels:
            # Calculate confidence based on activity level
            total_activity = sum(box_counts.values())
            confidence = box_counts[price] / total_activity if total_activity > 0 else 0
            
            # Determine anchor type
            anchor_type = 'zone' if len(max_levels) > 1 else 'single'
            
            anchor_point = AnchorPoint(
                price_level=price,
                box_count=box_counts[price],
                start_column=start_col,
                end_column=end_col,
                anchor_type=anchor_type,
                confidence=confidence
            )
            
            anchor_points.append(anchor_point)
        
        return anchor_points
    
    def _calculate_formation_confidence(self, anchor: AnchorPoint,
                                      high_price: float, low_price: float) -> float:
        """Calculate confidence for major formation anchors."""
        # Position within the formation range
        formation_range = high_price - low_price
        if formation_range == 0:
            return 0.5
        
        # Distance from middle of formation
        formation_middle = (high_price + low_price) / 2
        distance_from_middle = abs(anchor.price_level - formation_middle)
        position_factor = 1 - (distance_from_middle / (formation_range / 2))
        
        # Activity factor (already in anchor.confidence)
        activity_factor = anchor.confidence
        
        # Combined confidence
        return (position_factor + activity_factor) / 2
    
    def _create_zone(self, anchor_group: List[AnchorPoint]) -> AnchorPointZone:
        """Create an anchor zone from a group of anchor points."""
        prices = [a.price_level for a in anchor_group]
        zone_center = np.mean(prices)
        zone_range = (min(prices), max(prices))
        total_activity = sum(a.box_count for a in anchor_group)
        
        return AnchorPointZone(
            anchor_points=anchor_group,
            zone_center=zone_center,
            zone_range=zone_range,
            total_activity=total_activity
        )

class AnchorPointVisualizer:
    """Visualize anchor points on charts."""
    
    def __init__(self):
        self.anchor_line_style = {
            'color': '#2E86AB',  # Blue
            'width': 2,
            'dash': 'dot'
        }
        self.zone_line_style = {
            'color': '#A23B72',  # Purple
            'width': 1,
            'dash': 'dash'
        }
    
    def add_anchor_points_to_chart(self, fig, anchor_points: List[AnchorPoint],
                                 chart_width: int) -> None:
        """Add anchor point lines to Plotly chart."""
        import plotly.graph_objects as go
        
        for anchor in anchor_points:
            # Determine line style based on anchor type
            if anchor.anchor_type == 'zone':
                line_style = self.zone_line_style
                line_name = f"Anchor Zone ({anchor.box_count} boxes)"
            else:
                line_style = self.anchor_line_style
                line_name = f"Anchor Point ({anchor.box_count} boxes)"
            
            # Add horizontal line
            fig.add_hline(
                y=anchor.price_level,
                line=dict(
                    color=line_style['color'],
                    width=line_style['width'],
                    dash=line_style['dash']
                ),
                annotation_text=line_name,
                annotation_position="right",
                annotation=dict(
                    font=dict(size=10, color=line_style['color']),
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor=line_style['color'],
                    borderwidth=1
                )
            )
    
    def add_anchor_zones_to_chart(self, fig, zones: List[AnchorPointZone]) -> None:
        """Add anchor zones to Plotly chart."""
        import plotly.graph_objects as go
        
        for i, zone in enumerate(zones):
            # Add zone boundary lines
            fig.add_hline(
                y=zone.zone_range[0],
                line=dict(color=self.zone_line_style['color'], width=1, dash='dash'),
                annotation_text=f"Zone {i+1} Bottom",
                annotation_position="right"
            )
            
            fig.add_hline(
                y=zone.zone_range[1],
                line=dict(color=self.zone_line_style['color'], width=1, dash='dash'),
                annotation_text=f"Zone {i+1} Top",
                annotation_position="right"
            )
            
            # Add center line
            fig.add_hline(
                y=zone.zone_center,
                line=dict(color=self.zone_line_style['color'], width=2),
                annotation_text=f"Anchor Zone Center ({zone.total_activity} boxes)",
                annotation_position="right",
                annotation=dict(
                    font=dict(size=12, color=self.zone_line_style['color']),
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor=self.zone_line_style['color'],
                    borderwidth=2
                )
            )
