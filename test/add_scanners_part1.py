#!/usr/bin/env python3
"""
Script to add scanners #2-#11 to scanner_strategies.py
"""

# Read the existing file
with open('pkscreener-integration/scanner_strategies.py', 'r') as f:
    lines = f.readlines()

# Find the line number where Scanner #12 starts
scanner_12_line = None
for i, line in enumerate(lines):
    if "# ==================== SCANNER #12 ====================" in line:
        scanner_12_line = i
        break

if scanner_12_line is None:
    print("ERROR: Could not find Scanner #12")
    exit(1)

print(f"Found Scanner #12 at line {scanner_12_line + 1}")

# New scanners to insert (as a list of lines)
new_scanners_text = '''
    # ==================== SCANNER #2 ====================
    def scanner_2_volume_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Scanner #2: Volume Scanners + High Momentum + ATR Cross
        (Same as #1 but WITHOUT "Breaking Out Now" check)
        """
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            
            if not momentum_pass:
                return False, metrics
            
            # 3. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            
            if not atr_cross_pass:
                return False, metrics
            
            metrics['scanner_id'] = 2
            metrics['scanner_name'] = 'Volume + Momentum + ATR'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_2: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #3 ====================
    def scanner_3_volume_momentum(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #3: Volume Scanners + High Momentum"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. High Momentum
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            
            if not momentum_pass:
                return False, metrics
            
            metrics['scanner_id'] = 3
            metrics['scanner_name'] = 'Volume + Momentum'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_3: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #4 ====================
    def scanner_4_volume_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #4: Volume Scanners + ATR Cross"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            
            if not atr_cross_pass:
                return False, metrics
            
            metrics['scanner_id'] = 4
            metrics['scanner_name'] = 'Volume + ATR'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_4: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #5 ====================
    def scanner_5_volume_bidask(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Scanner #5: Volume Scanners + High Bid/Ask Build Up
        Note: Bid/Ask data not available, using volume acceleration as proxy
        """
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner (higher threshold)
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 3.0
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. Volume acceleration (proxy for bid/ask build up)
            recent_5_vol = df['volume'].head(5).mean()
            prev_20_vol = df['volume'].iloc[5:25].mean()
            vol_acceleration = recent_5_vol / prev_20_vol if prev_20_vol > 0 else 0
            metrics['volume_acceleration'] = round(vol_acceleration, 2)
            
            acceleration_pass = vol_acceleration >= 1.5
            if not acceleration_pass:
                return False, metrics
            
            metrics['scanner_id'] = 5
            metrics['scanner_name'] = 'Volume + Bid/Ask Build Up'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_5: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #6 ====================
    def scanner_6_volume_atr_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #6: Volume Scanners + ATR Cross + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. ATR Cross
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            
            if not atr_cross_pass:
                return False, metrics
            
            # 3. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            
            if not atr_stop_pass:
                return False, metrics
            
            metrics['scanner_id'] = 6
            metrics['scanner_name'] = 'Volume + ATR + Trailing Stop'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_6: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #7 ====================
    def scanner_7_volume_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #7: Volume Scanners + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            
            metrics = {}
            
            # 1. Volume Scanner
            volume_ratio = self.ti.calculate_volume_ratio(df, period=20)
            volume_pass = volume_ratio >= 2.5
            metrics['volume_ratio'] = volume_ratio
            
            recent_volume = df['volume'].iloc[0]
            avg_volume = df['volume'].head(20).mean()
            has_min_volume = recent_volume >= 10000 or avg_volume >= 10000
            metrics['recent_volume'] = int(recent_volume)
            metrics['avg_volume'] = int(avg_volume)
            
            if not (volume_pass and has_min_volume):
                return False, metrics
            
            # 2. ATR Trailing Stop
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            
            if not atr_stop_pass:
                return False, metrics
            
            metrics['scanner_id'] = 7
            metrics['scanner_name'] = 'Volume + Trailing Stop'
            return True, metrics
            
        except Exception as e:
            logger.error(f"Error in scanner_7: {e}")
            return False, {"error": str(e)}
    
'''

# Convert to list of lines
new_lines = [line + '\n' for line in new_scanners_text.split('\n')]

# Insert the new scanners before Scanner #12
new_file_lines = lines[:scanner_12_line] + new_lines + lines[scanner_12_line:]

# Write back
with open('pkscreener-integration/scanner_strategies.py', 'w') as f:
    f.writelines(new_file_lines)

print(f"✅ Successfully added scanners #2-#7 to scanner_strategies.py")
print(f"   Inserted {len(new_lines)} lines before line {scanner_12_line + 1}")

