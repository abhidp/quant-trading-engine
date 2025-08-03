# Trading Bot Deployment Workflow

A simple, reliable deployment setup for trading bots between development machine (A) and production machine (B).

## Architecture Overview

```
Machine A (Development)          Machine B (Production)
├── Dev Projects/                ├── C:\TradingBots\Projects\
│   ├── py-trading-bot/          │   ├── py-trading-bot/
│   └── quant-trading-engine/    │   └── quant-trading-engine/
│                                │
├── Local Git Server/            └── MetaTrader 5
│   ├── py-trading-bot.git/
│   └── quant-trading-engine.git/
│
└── GitHub (Remote Backup)
```

## Machine Setup

### Machine A (Development)

- **Location**: `C:\Users\abhid\Documents\Projects\`
- **Git Remotes**:
  - `origin` → GitHub (backup)
  - `local` → Local git server (fast deployment)

### Machine B (Production)

- **Location**: `C:\TradingBots\Projects\`
- **Purpose**: Run trading bots 24/7
- **Access**: RustDesk remote desktop + SSH

## Network Configuration

### Static IP Setup

- **Machine A**: `192.168.0.6` (adp)
- **Machine B**: `192.168.0.14` (nucboxg3_plus)
- **SSH User**: `sshuser` / `password123`
- **Network Share**: `\\192.168.0.6\git-repos` mapped as `Z:`

### SSH Authentication

- **Passwordless SSH**: Using existing `id_ed25519` keys
- **Key location**: `C:\ProgramData\ssh\administrators_authorized_keys`

## PowerShell Aliases

Add these to your PowerShell profile (`$PROFILE`):

```powershell
# Basic deployment functions
function push-py {
    cd "C:\Users\abhid\Documents\Projects\py-trading-bot"
    git add .
    git commit -m "Auto-commit: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
    git push origin main      # To GitHub
    git push local main       # To local server
}

function deploy-py {
    ssh sshuser@192.168.0.14 "cd C:\TradingBots\Projects\py-trading-bot && git pull origin main"
}

function ship-py {
    push-py
    deploy-py
}

function ssh-b {
    ssh sshuser@192.168.0.14
}

# Quick status checks
function status-py {
    ssh sshuser@192.168.0.14 "cd C:\TradingBots\Projects\py-trading-bot && git status"
}

function logs-py {
    ssh sshuser@192.168.0.14 "cd C:\TradingBots\Projects\py-trading-bot && Get-Content bot.log -Tail 20"
}
```

## Daily Workflow

### 1. Development Phase

```bash
# Work on Machine A as usual
# Edit code, test locally, etc.
```

### 2. Deployment Phase

```bash
# Push changes to both GitHub and local server
ship-py

# Verify deployment
status-py
```

### 3. Production Phase

```bash
# Connect to Machine B via RustDesk
# Navigate to: C:\TradingBots\Projects\py-trading-bot
# Activate venv: venv\Scripts\activate
# Run bot: python main.py
# Monitor: Watch console logs + MT5 interface
```

## Quick Commands Reference

| Command     | Description                                         |
| ----------- | --------------------------------------------------- |
| `ship-py`   | Commit, push to GitHub & local, deploy to Machine B |
| `deploy-py` | Deploy latest changes to Machine B                  |
| `ssh-b`     | SSH into Machine B                                  |
| `status-py` | Check git status on Machine B                       |
| `logs-py`   | View recent bot logs                                |

## Bot Management on Machine B

### Start Trading Bot

```bash
# Navigate to project
cd C:\TradingBots\Projects\py-trading-bot

# Activate virtual environment
venv\Scripts\activate

# Run bot with logging
python main.py 2>&1 | tee bot.log
```

### Background Execution (if needed)

```bash
# Start bot in background (survives SSH disconnect)
start /B python main.py > bot.log 2>&1

# Check if running
tasklist | findstr python
```

## File Structure

### Machine A

```
C:\Users\abhid\Documents\Projects\
├── py-trading-bot/
│   ├── .git/
│   ├── venv/
│   ├── main.py
│   └── requirements.txt
│
C:\git-repos\
├── py-trading-bot.git/     # Bare repository
└── quant-trading-engine.git/
```

### Machine B

```
C:\TradingBots\Projects\
├── py-trading-bot/
│   ├── .git/
│   ├── venv/
│   ├── main.py
│   ├── bot.log
│   └── requirements.txt
└── quant-trading-engine/
```

## Troubleshooting

### SSH Connection Issues

```bash
# Test basic connectivity
ping 192.168.0.14

# Test SSH
ssh sshuser@192.168.0.14 "whoami"

# Check git repos accessibility
dir Z:\
```

### Git Issues

```bash
# If pull fails, check remotes
ssh-b
cd C:\TradingBots\Projects\py-trading-bot
git remote -v
git status
```

### Bot Issues

```bash
# Check logs
logs-py

# Kill stuck processes
ssh sshuser@192.168.0.14 "taskkill /f /im python.exe"
```

## Important Notes

⚠️ **Always deploy via git** - Never use shared folders for live code  
⚠️ **Test on Machine B first** - Before running with real money  
⚠️ **Monitor MT5 visually** - Use RustDesk to watch live trading  
⚠️ **Keep backups** - Code is automatically backed up to GitHub

## Why This Setup Works

✅ **Simple**: Just RustDesk + basic git commands  
✅ **Reliable**: Git ensures atomic deployments  
✅ **Visual**: See MT5 and logs in real-time  
✅ **Fast**: Local git server for instant deployment  
✅ **Safe**: Version control with rollback capability  
✅ **Scalable**: Easy to add more trading projects

---

Workflow Summary:

1. Code on Machine A
2. ship-quant (commits, pushes to GitHub & local server, deploys to Machine B)
3. RustDesk → navigate to C:\TradingBots\Projects\quant-trading-engine
4. Activate venv and run your trading bot
5. Monitor MT5 + console logs visually
