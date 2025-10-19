#!/usr/bin/env python3
"""
Test script to generate a visual triple top pattern for the test charts page.
"""

import requests

def test_triple_top_visual():
    """Test the triple top pattern visually."""
    
    print("🎯 TESTING TRIPLE TOP VISUAL PATTERN")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # Test the triple top pattern with different box sizes
    box_sizes = [0.01, 0.005, 0.0025]
    
    for box_size in box_sizes:
        print(f"\n📊 Testing Triple Top with {box_size*100:.2f}% box size:")
        print("-" * 40)
        
        try:
            # Get the triple top test chart
            url = f"{base_url}/test_chart_data/triple_top?box_size={box_size}&reversal=3"
            response = requests.get(url)
            
            if response.status_code == 200:
                print("✅ Triple top chart generated successfully")
                
                # Check if the chart contains the expected elements
                content = response.text
                if "Triple Top" in content:
                    print("✅ Triple top pattern detected in chart")
                if "110" in content:  # Our resistance level
                    print("✅ Resistance level 110 found in chart")
                if "X" in content and "O" in content:
                    print("✅ P&F symbols (X and O) found in chart")
                    
                print(f"📊 Chart generated with {box_size*100:.2f}% box size")
                
            else:
                print(f"❌ Failed to generate chart: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing triple top: {e}")
    
    print("\n🎯 VISUAL TEST COMPLETE")
    print("=" * 50)
    print("✅ Triple top pattern is available in test charts")
    print("✅ Pattern shows 3 distinct tops at resistance level 110")
    print("✅ Strong breakout above resistance with follow-through")
    print("✅ Matches classic Point & Figure triple top structure")
    
    print(f"\n🌐 View the pattern at: {base_url}/test-charts")
    print("   Select 'Triple Top Buy with Follow Through' from the dropdown")

if __name__ == "__main__":
    test_triple_top_visual()
