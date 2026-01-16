# RAJUMAMA EA Flask Dashboard

Web dashboard for monitoring and controlling your MT5 RAJUMAMA EA from anywhere!

## 🌟 Features

- ✅ Real-time EA status monitoring
- ✅ Live MAMA/FAMA values display
- ✅ Account balance and equity tracking
- ✅ Trade history with profit/loss
- ✅ Trading statistics (win rate, profit factor, etc.)
- ✅ Remote settings configuration
- ✅ Start/Stop EA remotely
- ✅ Beautiful responsive UI
- ✅ Auto-refresh every 5 seconds

## 📦 What's Included

```
rajumama_flask_app/
├── app.py                 # Main Flask application
├── templates/
│   └── index.html        # Dashboard HTML template
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
└── README.md             # This file
```

## 🚀 Deploy to Render (Free)

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click **"New Repository"**
3. Name: `rajumama-dashboard`
4. Make it **Public**
5. Click **"Create repository"**

### Step 2: Upload Files to GitHub

**Option A: Using GitHub Web Interface**

1. In your repository, click **"Upload files"**
2. Drag and drop all files from `rajumama_flask_app` folder
3. Commit changes

**Option B: Using Git Command Line**

```bash
cd rajumama_flask_app
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rajumama-dashboard.git
git push -u origin main
```

### Step 3: Deploy on Render

1. Go to [Render.com](https://render.com)
2. Sign up/Login (can use GitHub account)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository
5. Select `rajumama-dashboard` repo
6. Render auto-detects settings from `render.yaml`
7. Click **"Create Web Service"**

**Build Settings (auto-detected):**
```
Name: rajumama-ea-dashboard
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

8. Wait 2-5 minutes for deployment
9. Your dashboard will be live at: `https://rajumama-ea-dashboard.onrender.com`

## 🔗 Connect MT5 EA to Dashboard

You need to modify your MT5 EA to send updates to the dashboard API.

### Option 1: Simple Python Script (Recommended)

Create `mt5_bridge.py` on your VPS/PC where MT5 runs:

```python
import MetaTrader5 as mt5
import requests
import time
from datetime import datetime

# Your Render dashboard URL
DASHBOARD_URL = "https://rajumama-ea-dashboard.onrender.com"

def send_update():
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    # Get account info
    account_info = mt5.account_info()
    
    # Get open positions
    positions = mt5.positions_get()
    position_status = "NONE"
    if positions:
        position_status = "LONG" if positions[0].type == 0 else "SHORT"
    
    # Prepare data
    data = {
        "mama_value": 4350.0,  # Get from EA custom indicators
        "fama_value": 4340.0,  # Get from EA custom indicators
        "trend": "BULLISH",    # Calculate based on MAMA/FAMA
        "position_status": position_status,
        "balance": account_info.balance,
        "equity": account_info.equity
    }
    
    # Send to dashboard
    try:
        response = requests.post(f"{DASHBOARD_URL}/api/update", json=data)
        print(f"Update sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending update: {e}")
    
    mt5.shutdown()

# Run every 5 seconds
while True:
    send_update()
    time.sleep(5)
```

Install requirements:
```bash
pip install MetaTrader5 requests
```

Run the bridge:
```bash
python mt5_bridge.py
```

### Option 2: MQL5 HTTP Requests (Advanced)

Add to your EA (requires MT5 build 3400+):

```mql5
#include <WinHttpPost.mqh>

void SendDashboardUpdate()
{
   string url = "https://rajumama-ea-dashboard.onrender.com/api/update";
   string data = StringFormat(
      "{\"mama_value\":%.2f,\"fama_value\":%.2f,\"trend\":\"%s\",\"position_status\":\"%s\",\"balance\":%.2f,\"equity\":%.2f}",
      mama_val, fama_val, trend, positionStatus, AccountInfoDouble(ACCOUNT_BALANCE), AccountInfoDouble(ACCOUNT_EQUITY)
   );
   
   // Send HTTP POST
   char post[];
   char result[];
   string headers = "Content-Type: application/json\r\n";
   
   ArrayResize(post, StringToCharArray(data, post, 0, WHOLE_ARRAY) - 1);
   
   int timeout = 5000;
   int res = WebRequest("POST", url, headers, timeout, post, result, headers);
   
   if(res == 200)
   {
      Print("Dashboard updated successfully");
   }
}

// Call in OnTick every 5 seconds
static datetime lastUpdate = 0;
if(TimeCurrent() - lastUpdate > 5)
{
   SendDashboardUpdate();
   lastUpdate = TimeCurrent();
}
```

## 📱 Access Dashboard

Once deployed, access from anywhere:

- **Desktop**: Open browser → `https://your-app-name.onrender.com`
- **Mobile**: Same URL works on phone
- **Tablet**: Same URL works on tablet

## 🎨 Dashboard Features

### Main Dashboard
- Real-time EA status (Running/Stopped)
- Current MAMA and FAMA values
- Market trend indicator (Bullish/Bearish/Neutral)
- Current position (LONG/SHORT/NONE)

### Account Section
- Account balance
- Equity
- Total profit
- Profit factor

### Trading Stats
- Total trades
- Win rate percentage
- Winning trades count
- Losing trades count
- Average win/loss

### Settings Panel
- Adjust Stop Loss %
- Adjust Take Profit %
- Adjust Trailing Stop %
- Change lot size
- Modify Fast/Slow limits
- Enable/Disable SHORT trades
- Save changes remotely

### Controls
- Start EA button
- Stop EA button
- Refresh data button

### Trade History Table
- Recent 50 trades
- Trade details (ticket, time, type, volume, prices, profit)
- Color-coded profits (green/red)

## 🔒 Security

**Important:** This is a basic implementation. For production:

1. **Add Authentication:**
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == "admin" and password == "your-secure-password":
        return username

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

2. **Use Environment Variables:**
```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me')
```

3. **Add HTTPS (Render provides automatically)**

4. **Rate Limiting:**
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)
```

## 🐛 Troubleshooting

### Dashboard shows "No data"
- Check MT5 bridge script is running
- Verify DASHBOARD_URL is correct
- Check MT5 EA is running

### Render deployment fails
- Check all files are in repository
- Verify `requirements.txt` exists
- Check Python version compatibility

### Can't save settings
- Check browser console for errors
- Verify API endpoint is accessible
- Check browser allows JavaScript

## 📊 API Endpoints

- `GET /` - Main dashboard
- `GET /api/status` - Get EA status
- `GET /api/trades` - Get trade history
- `GET /api/settings` - Get current settings
- `POST /api/settings` - Update settings
- `POST /api/update` - Receive EA updates (from MT5)
- `GET /api/stats` - Get trading statistics
- `POST /api/control/start` - Start EA
- `POST /api/control/stop` - Stop EA

## 🔄 Updates

To update the dashboard:

1. Modify files locally
2. Push to GitHub:
```bash
git add .
git commit -m "Updated dashboard"
git push
```
3. Render auto-deploys new version (2-3 minutes)

## 💰 Cost

**Render Free Tier:**
- ✅ 750 hours/month free
- ✅ Enough for 24/7 operation
- ✅ Automatic HTTPS
- ✅ Custom domain support
- ⚠️ Sleeps after 15 min inactivity (wakes on request)

**To keep always active:**
- Upgrade to Starter plan ($7/month)
- Or use cron job to ping every 10 minutes

## 🎯 Next Steps

1. ✅ Deploy dashboard to Render
2. ✅ Set up MT5 bridge script
3. ✅ Test connection
4. ✅ Monitor trades from mobile
5. ✅ Adjust settings remotely

## 📞 Support

Need help? Check:
- Render documentation: https://render.com/docs
- Flask documentation: https://flask.palletsprojects.com/
- MetaTrader5 Python docs: https://www.mql5.com/en/docs/python_metatrader5

---

**Version**: 1.0  
**Python**: 3.11+  
**Flask**: 3.0.0  
**Deployment**: Render.com
