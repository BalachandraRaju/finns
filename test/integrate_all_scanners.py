#!/usr/bin/env python3
"""
Script to integrate all 16 new scanners into scanner_strategies.py
Adds scanners #2-#11, #13, #15-#19
"""
import os
import sys

# Path to the file
FILE_PATH = 'pkscreener-integration/scanner_strategies.py'

# Read the file
print(f"Reading {FILE_PATH}...")
with open(FILE_PATH, 'r') as f:
    content = f.read()

# Check if already added
if 'scanner_2_volume_momentum_atr' in content:
    print("✅ Scanners already added! Nothing to do.")
    sys.exit(0)

# Find the insertion point (before Scanner #12)
MARKER = "    # ==================== SCANNER #12 ===================="

if MARKER not in content:
    print(f"❌ ERROR: Could not find marker: {MARKER}")
    sys.exit(1)

# Split at the marker
parts = content.split(MARKER, 1)
if len(parts) != 2:
    print("❌ ERROR: Unexpected file structure")
    sys.exit(1)

print(f"✅ Found insertion point")

# The new scanners code (all 16 scanners)
NEW_SCANNERS = '''
    # ==================== SCANNER #2 ====================
    def scanner_2_volume_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #2: Volume + Momentum + ATR"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics
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
        """Scanner #3: Volume + Momentum"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
        """Scanner #4: Volume + ATR"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
        """Scanner #5: Volume + Bid/Ask Build Up"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
        """Scanner #6: Volume + ATR + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics
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
        """Scanner #7: Volume + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
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
    
    # ==================== SCANNER #8 ====================
    def scanner_8_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #8: Momentum + ATR"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics
            metrics['scanner_id'] = 8
            metrics['scanner_name'] = 'Momentum + ATR'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_8: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #9 ====================
    def scanner_9_momentum_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #9: Momentum + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics
            metrics['scanner_id'] = 9
            metrics['scanner_name'] = 'Momentum + Trailing Stop'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_9: {e}")
            return False, {"error": str(e)}
    
    # ==================== SCANNER #10 ====================
    def scanner_10_atr_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #10: ATR + Trailing Stop"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            atr_cross_pass, atr_metrics = self._check_atr_cross(df)
            metrics.update(atr_metrics)
            if not atr_cross_pass:
                return False, metrics
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics
            metrics['scanner_id'] = 10
            metrics['scanner_name'] = 'ATR + Trailing Stop'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_10: {e}")
            return False, {"error": str(e)}
    
'''

# Reconstruct the file
new_content = parts[0] + NEW_SCANNERS + "    " + MARKER + parts[1]

# Create backup
backup_path = FILE_PATH + '.backup'
print(f"Creating backup at {backup_path}...")
with open(backup_path, 'w') as f:
    f.write(content)

# Write the new content
print(f"Writing updated file...")
with open(FILE_PATH, 'w') as f:
    f.write(new_content)

print(f"✅ Successfully added scanners #2-#10!")
print(f"   Backup saved to: {backup_path}")
print(f"\nNext: Run integrate_scanners_part2.py to add scanners #11, #13, #15-#19")

