# Trading Bot Deployment - Quick Guide

Simple deployment setup between development machine (A) and production machine (B).

## Setup Summary

- **Machine A**: `192.168.0.6` (Development)
- **Machine B**: `192.168.0.14` (Production)
- **Network**: Local git server + RustDesk remote access
- **SSH**: Passwordless with `adp-gmtec@192.168.0.14`

## Daily Workflow

### 1. Development (Machine A)

```powershell
# Work on code as usual
# When ready to deploy:
ship-quant
```

### 2. Deployment (Machine B)

```powershell
# Connect via RustDesk, then:
qd    # Quick deploy - pulls latest code
qr    # Quick deploy + run bot
```

## PowerShell Aliases

### Machine A

```powershell
ship-quant    # Push to GitHub + local server, show deploy instructions
push-quant    # Push only
```

### Machine B

```powershell
qd            # Quick deploy (pull latest code)
qr            # Quick deploy + run bot
```

## File Structure

```
Machine A: C:\Users\abhid\Documents\Projects\quant-trading-engine\
Machine B: C:\TradingBots\Projects\quant-trading-engine\
Local Git: C:\git-repos\quant-trading-engine.git\
```

## Notes

- **Wait 1 minute after Machine B restart** for network drives to connect
- **Branch-aware**: Automatically works with any git branch
- **Dual backup**: Code saved to GitHub + local git server
- **Visual monitoring**: Use RustDesk to watch MT5 + bot logs

## Troubleshooting

- Network issues: Restart takes ~1 minute to establish connections
- Git errors: Run `net use \\192.168.0.6\git-repos /user:gituser password123`
- SSH issues: Use `ssh adp-gmtec@192.168.0.14`
