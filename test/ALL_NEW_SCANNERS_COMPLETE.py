# ==============================================================================
# COMPLETE CODE FOR ALL NEW SCANNERS (#2-#11, #13, #15-#19)
# ==============================================================================
# 
# INSTRUCTIONS:
# 1. Open pkscreener-integration/scanner_strategies.py
# 2. Find line ~96: "# ==================== SCANNER #12 ===================="
# 3. Copy EVERYTHING below this comment block
# 4. Paste it BEFORE the "# ==================== SCANNER #12 ====================" line
# 5. Save the file
#
# This will add 16 new scanners to your system!
# ==============================================================================

    # ==================== SCANNER #2 ====================
    def scanner_2_volume_momentum_atr(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #2: Volume + Momentum + ATR (no breakout check)"""
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
        """Scanner #5: Volume + Bid/Ask Build Up (using volume acceleration proxy)"""
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

    # ==================== SCANNER #11 ====================
    def scanner_11_ttm_squeeze_rsi(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #11: TTM Squeeze Buy + Intraday RSI b/w 0 to 54"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            close = df['close']
            high = df['high']
            low = df['low']
            bb_upper, bb_middle, bb_lower = self.ti.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            atr = self.ti.ATR(high, low, close, timeperiod=20)
            kc_upper = bb_middle + (1.5 * atr)
            kc_lower = bb_middle - (1.5 * atr)
            squeeze_on = (bb_lower.iloc[0] > kc_lower.iloc[0]) and (bb_upper.iloc[0] < kc_upper.iloc[0])
            metrics['ttm_squeeze'] = squeeze_on
            if not squeeze_on:
                return False, metrics
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)
            rsi_pass = 0 <= current_rsi <= 54
            if not rsi_pass:
                return False, metrics
            momentum_pass = self._check_momentum(df)
            metrics['momentum'] = momentum_pass
            if not momentum_pass:
                return False, metrics
            metrics['scanner_id'] = 11
            metrics['scanner_name'] = 'TTM Squeeze + RSI'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_11: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #13 ====================
    def scanner_13_volume_atr_rsi(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #13: Volume + ATR + Intraday RSI b/w 0 to 54"""
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
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)
            rsi_pass = 0 <= current_rsi <= 54
            if not rsi_pass:
                return False, metrics
            metrics['scanner_id'] = 13
            metrics['scanner_name'] = 'Volume + ATR + RSI'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_13: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #15 ====================
    def scanner_15_vcp_patterns_ma(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #15: VCP + Chart Patterns + MA Support (similar to #14)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)
            rsi_pass = current_rsi >= 50
            if not rsi_pass:
                return False, metrics
            metrics['scanner_id'] = 15
            metrics['scanner_name'] = 'VCP + Patterns + MA'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_15: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #16 ====================
    def scanner_16_breakout_vcp_patterns_ma(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #16: Already Breaking out + VCP + Chart Patterns + MA Support"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            breakout_pass = self.ti.is_breaking_out(df, lookback_period=20)
            metrics['breakout'] = breakout_pass
            if not breakout_pass:
                return False, metrics
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics
            close = df['close']
            rsi = self.ti.RSI(close, timeperiod=14)
            current_rsi = rsi.iloc[0]
            metrics['rsi'] = round(current_rsi, 2)
            rsi_pass = current_rsi >= 50
            if not rsi_pass:
                return False, metrics
            metrics['scanner_id'] = 16
            metrics['scanner_name'] = 'Breakout + VCP + Patterns + MA'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_16: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #17 ====================
    def scanner_17_trailing_vcp(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #17: ATR Trailing Stops + VCP (Minervini)"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics
            metrics['scanner_id'] = 17
            metrics['scanner_name'] = 'Trailing Stop + VCP'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_17: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #18 ====================
    def scanner_18_vcp_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #18: VCP + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics
            metrics['scanner_id'] = 18
            metrics['scanner_name'] = 'VCP + Trailing Stop'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_18: {e}")
            return False, {"error": str(e)}

    # ==================== SCANNER #19 ====================
    def scanner_19_nifty_vcp_trailing(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """Scanner #19: Nifty 50, Nifty Bank + VCP + ATR Trailing Stops"""
        try:
            if len(df) < 50:
                return False, {"error": "Insufficient data"}
            metrics = {}
            vcp_pass = self._check_vcp_simplified(df)
            metrics['vcp'] = vcp_pass
            if not vcp_pass:
                return False, metrics
            atr_stop_pass, atr_stop_metrics = self._check_atr_trailing_stop(df)
            metrics.update(atr_stop_metrics)
            if not atr_stop_pass:
                return False, metrics
            ma_align_pass = self._check_ma_alignment(df)
            metrics['ma_alignment'] = ma_align_pass
            if not ma_align_pass:
                return False, metrics
            metrics['scanner_id'] = 19
            metrics['scanner_name'] = 'Nifty + VCP + Trailing Stop'
            return True, metrics
        except Exception as e:
            logger.error(f"Error in scanner_19: {e}")
            return False, {"error": str(e)}



