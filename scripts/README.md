# Scripts Directory

## Quick Start - Test FBox Connection

### On Your Windows Server:

1. **Open Command Prompt** (or PowerShell)

2. **Navigate to project:**
   ```cmd
   cd C:\CannaPeace\hvac-analytics
   ```

3. **Run connection test:**
   ```cmd
   python scripts\test_fbox_connection.py
   ```

4. **Enter your FBox IP** when prompted
   - Find it in your router or FBox web interface
   - Example: 192.168.1.100

5. **Review results** and follow recommendations

---

## What the Test Will Tell You:

✅ **If Modbus TCP works** → Real-time monitoring (10-second updates) ← BEST OPTION

✅ **If HTTP works** → Scheduled exports (hourly) ← GOOD OPTION

✅ **If FTP works** → Automated file transfer ← OKAY OPTION

---

## After Testing:

### Option A: Modbus TCP (If Available)
**→ See:** `docs/flexem_fbox_integration_guide.md` - Tier 2

**Setup Time:** ~2 hours
**Benefits:** Real-time alerts, immediate leak detection

### Option B: Scheduled Export (If Modbus Not Available)
**→ See:** `docs/flexem_fbox_integration_guide.md` - Tier 1

**Setup Time:** ~30 minutes
**Benefits:** Simple, works with current exports

---

## Home Assistant Integration

**Once data collection works**, integrate with your existing HA:

1. Add sensors to HA configuration
2. Create dashboard with pressure gauges
3. Set up mobile alerts
4. Beautiful visualization!

**→ See:** `docs/flexem_fbox_integration_guide.md` - Tier 3

---

## Need Help?

1. **Connection issues?** Check Windows firewall
2. **FBox IP changed?** Set static IP in router
3. **Modbus not working?** Check FBox settings
4. **Want to discuss?** Share results with Claude.ai

---

**Next:** Run the test and let me know what protocols are available!
