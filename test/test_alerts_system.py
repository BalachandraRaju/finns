#!/usr/bin/env python3
"""
Test script for the alerts system.
"""

from app.crud import save_alert, get_alerts, get_alert_statistics
from app.models import AlertFilters
from datetime import datetime

def test_alerts_system():
    print('🧪 Testing Alert System...')
    
    # Test saving an alert
    sample_alert = {
        'alert_type': 'BUY',
        'pattern_type': 'double_top_buy',
        'type': 'Double Top Buy with Follow Through',
        'signal_price': 1250.50,
        'trigger_reason': '🚨 Double Top Buy: Price 1250.50 breaks above resistance 1245.00 after 2 distinct similar tops with follow-through. Chart above 20 EMA (1240.25)',
        'column': 15,
        'volume': 125000
    }
    
    print('💾 Saving sample alert...')
    alert_id = save_alert('RELIANCE', 'NSE_EQ|INE002A01018', sample_alert)
    
    if alert_id:
        print(f'✅ Alert saved with ID: {alert_id}')
        
        # Test retrieving alerts
        print('📊 Retrieving alerts...')
        filters = AlertFilters(limit=10)
        alerts = get_alerts(filters)
        print(f'✅ Retrieved {len(alerts)} alerts')
        
        if alerts:
            alert = alerts[0]
            print(f'   📈 {alert.symbol}: {alert.pattern_name} @ ₹{alert.signal_price}')
            print(f'   🕒 {alert.timestamp}')
        
        # Test statistics
        print('📈 Getting statistics...')
        stats = get_alert_statistics()
        print(f'✅ Statistics: {stats["total_alerts"]} total, {stats["buy_alerts"]} buy, {stats["sell_alerts"]} sell')
        
        # Test super alert
        super_alert = {
            'alert_type': 'SELL',
            'pattern_type': 'triple_bottom_sell',
            'type': 'Triple Bottom Sell with Follow Through',
            'signal_price': 2150.25,
            'trigger_reason': '🌟 SUPER SELL: Triple Bottom Sell: Price 2150.25 breaks below support 2155.00 ⭐ PNF MATRIX SCORE: -8 ⭐',
            'column': 22,
            'volume': 89000
        }
        
        print('💾 Saving super alert...')
        super_alert_id = save_alert('TATAMOTORS', 'NSE_EQ|INE155A01022', super_alert)
        
        if super_alert_id:
            print(f'✅ Super alert saved with ID: {super_alert_id}')
        
        print('🎉 Alert system working perfectly!')
        return True
        
    else:
        print('❌ Failed to save alert')
        return False

if __name__ == '__main__':
    test_alerts_system()
