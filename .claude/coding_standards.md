# Coding Standards and Guidelines

## STRICT PROFESSIONAL CODE REQUIREMENTS

### 🚫 ABSOLUTELY PROHIBITED IN ALL CODE FILES

**NO EMOJIS - EVER**
- ❌ NO Unicode emoji characters in any Python, shell, batch, or code files
- ❌ NO decorative symbols (✅, ❌, 🎯, 🚀, etc.) in code output or comments
- ❌ NO fancy Unicode characters for status indicators
- ✅ USE plain text alternatives: "OK:", "ERROR:", "WARNING:", "SUCCESS:", "FAILED:"

**Examples of FORBIDDEN vs ALLOWED:**
```python
# FORBIDDEN - DO NOT USE
print("❌ Error occurred")
print("✅ Success!")
logger.info("🎯 Target reached")

# CORRECT - PROFESSIONAL
print("ERROR: Operation failed")
print("SUCCESS: Operation completed")
logger.info("TARGET: Objective achieved")
```

### Professional Output Standards

**Error Messages:**
- Use `ERROR:` prefix
- Be specific and actionable
- No emojis or decorative characters

**Success Messages:**
- Use `OK:`, `SUCCESS:`, or `COMPLETED:` prefixes
- Clear and concise
- Professional tone

**Status Indicators:**
- Use text-based prefixes: `INFO:`, `WARNING:`, `DEBUG:`
- Avoid Unicode symbols entirely
- Use consistent formatting

### Code Comments and Documentation

**In Code Files (.py, .sh, .bat):**
- No emojis in comments
- Professional documentation style
- Clear, technical language

**In Documentation (.md files):**
- Emojis MAY be used sparingly for section headers in documentation
- NEVER in code examples or technical specifications
- Keep professional tone throughout

### Logging Standards

All log messages must use text-based prefixes:
```python
# CORRECT
logger.info("INFO: Starting trading instance")
logger.error("ERROR: Failed to connect to MT5")
logger.warning("WARNING: High risk detected")
```

### Terminal/Console Output

All print statements and console output must be emoji-free:
```python
# CORRECT  
print("Multi-Instance RSI Trading System")
print("=" * 40)
print("Found 3 configuration files:")
print("ERROR: Config file not found")
print("OK: Configuration loaded successfully")
```

### Why This Matters

1. **Professional Standards**: Financial/trading software requires institutional-grade professionalism
2. **Cross-Platform Compatibility**: Emojis cause encoding issues on different systems
3. **Terminal Compatibility**: Many professional terminals don't render emojis properly
4. **Logs and Monitoring**: Professional monitoring systems expect plain text
5. **Code Reviews**: Emojis distract from technical content

### Enforcement

- All new code must follow these standards
- Code reviews will reject any emoji usage in code files
- Update existing code to remove emojis when encountered
- Use linting rules to prevent emoji introduction

## Summary

This is a professional quantitative trading system. All code must reflect institutional-grade standards with zero tolerance for emojis or decorative Unicode characters in any executable code files.