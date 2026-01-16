"""
MT5 to Flask Dashboard Bridge
Runs on your PC/VPS alongside MT5 and sends data to web dashboard
"""

import MetaTrader5 as mt5
import requests
import time
from datetime import datetime
import json

# ============= CONFIGURATION =============
# Change this to your Render dashboard URL
DASHBOARD_URL = "https://your-app-name.onrender.com"

# Your MT5 account details
MT5_ACCOUNT = 12345678  # Your account number
MT5_PASSWORD = "your_password"  # Your password
MT5_SERVER = "YourBroker-Demo"  # Your server name

# Update interval (seconds)
UPDATE_INTERVAL = 5

# EA Magic Number (must match EA)
MAGIC_NUMBER = 123456
# ========================================

def initialize_mt5():
    """Initialize MT5 connection"""
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return False
    
    # Login to account
    if not mt5.login(MT5_ACCOUNT, password=MT5_PASSWORD, server=MT5_SERVER):
        print(f"❌ Login failed: {mt5.last_error()}")
        return False
    
    print("✅ MT5 connected successfully")
    print(f"Account: {mt5.account_info().login}")
    print(f"Balance: ${mt5.account_info().balance}")
    return True

def get_mama_fama_values():
    """
    Get MAMA/FAMA values from custom indicator
    You need to create a custom indicator that calculates these values
    For now, we'll use placeholder values
    """
    # TODO: Implement actual MAMA/FAMA calculation or read from indicator
    # For demonstration, using placeholder values
    return 4350.0, 4340.0

def calculate_trend(mama, fama):
    """Calculate trend based on MAMA/FAMA"""
    if mama > fama:
        return "BULLISH"
    elif mama < fama:
        return "BEARISH"
    else:
        return "NEUTRAL"

def get_position_status():
    """Get current position status"""
    positions = mt5.positions_get(symbol="XAUUSD")
    
    if not positions:
        return "NONE"
    
    # Filter by magic number
    ea_positions = [p for p in positions if p.magic == MAGIC_NUMBER]
    
    if not ea_positions:
        return "NONE"
    
    # Return first position type
    pos = ea_positions[0]
    return "LONG" if pos.type == mt5.ORDER_TYPE_BUY else "SHORT"

def get_closed_trades():
    """Get recently closed trades"""
    # Get deals from history
    from_date = datetime.now().replace(hour=0, minute=0, second=0)
    deals = mt5.history_deals_get(from_date, datetime.now())
    
    if not deals:
        return []
    
    trades = []
    for deal in deals:
        if deal.magic == MAGIC_NUMBER and deal.entry == mt5.DEAL_ENTRY_OUT:
            trades.append({
                'ticket': deal.order,
                'open_time': datetime.fromtimestamp(deal.time).isoformat(),
                'close_time': datetime.fromtimestamp(deal.time).isoformat(),
                'symbol': deal.symbol,
                'type': 'buy' if deal.type == mt5.DEAL_TYPE_BUY else 'sell',
                'volume': deal.volume,
                'open_price': deal.price,
                'close_price': deal.price,
                'sl': 0,
                'tp': 0,
                'profit': deal.profit,
                'status': 'closed'
            })
    
    return trades

def send_update():
    """Send update to dashboard"""
    try:
        # Get account info
        account_info = mt5.account_info()
        if not account_info:
            print("❌ Failed to get account info")
            return False
        
        # Get MAMA/FAMA values
        mama, fama = get_mama_fama_values()
        
        # Calculate trend
        trend = calculate_trend(mama, fama)
        
        # Get position status
        position_status = get_position_status()
        
        # Prepare data
        data = {
            "mama_value": mama,
            "fama_value": fama,
            "trend": trend,
            "position_status": position_status,
            "balance": account_info.balance,
            "equity": account_info.equity
        }
        
        # Get recent closed trades
        recent_trades = get_closed_trades()
        if recent_trades:
            data['trade'] = recent_trades[-1]  # Send most recent trade
        
        # Send to dashboard
        response = requests.post(
            f"{DASHBOARD_URL}/api/update",
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Update sent - Balance: ${account_info.balance:.2f}, Position: {position_status}, Trend: {trend}")
            return True
        else:
            print(f"⚠️ Update failed - Status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main loop"""
    print("=" * 60)
    print("🚀 RAJUMAMA MT5 to Dashboard Bridge")
    print("=" * 60)
    print(f"Dashboard URL: {DASHBOARD_URL}")
    print(f"Update interval: {UPDATE_INTERVAL} seconds")
    print("=" * 60)
    
    # Initialize MT5
    if not initialize_mt5():
        print("Failed to initialize MT5. Exiting...")
        return
    
    print("\n📡 Starting data bridge...")
    print("Press Ctrl+C to stop\n")
    
    update_count = 0
    error_count = 0
    
    try:
        while True:
            update_count += 1
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Update #{update_count}")
            
            if send_update():
                error_count = 0  # Reset error count on success
            else:
                error_count += 1
                if error_count >= 5:
                    print("⚠️ Too many consecutive errors. Reinitializing MT5...")
                    mt5.shutdown()
                    time.sleep(5)
                    if not initialize_mt5():
                        print("Failed to reinitialize. Exiting...")
                        break
                    error_count = 0
            
            # Wait before next update
            time.sleep(UPDATE_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹ Stopping bridge...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
    finally:
        mt5.shutdown()
        print("✅ MT5 disconnected")
        print("👋 Bridge stopped")

if __name__ == "__main__":
    # Check if MetaTrader5 module is installed
    try:
        import MetaTrader5
    except ImportError:
        print("❌ MetaTrader5 module not installed")
        print("Install it with: pip install MetaTrader5")
        exit(1)
    
    # Check if requests module is installed
    try:
        import requests
    except ImportError:
        print("❌ requests module not installed")
        print("Install it with: pip install requests")
        exit(1)
    
    main()
