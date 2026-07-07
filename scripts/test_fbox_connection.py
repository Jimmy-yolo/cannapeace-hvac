#!/usr/bin/env python3
"""
Flexem FBox WiFi Connection Test
Tests all possible connection methods to determine best integration path
"""

import subprocess
import sys

print("=" * 70)
print("FLEXEM FBOX WIFI CONNECTION TEST")
print("=" * 70)
print()

# Get FBox IP from user
fbox_ip = input("Enter your FBox WiFi IP address (e.g., 192.168.1.100): ").strip()
if not fbox_ip:
    print("Error: IP address required")
    sys.exit(1)

print(f"\nTesting connection to FBox at: {fbox_ip}")
print("=" * 70)

results = {}

# Test 1: Network Reachability (Ping)
print("\n[1/5] Testing Network Reachability (Ping)...")
try:
    import platform
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    result = subprocess.run(['ping', param, '1', fbox_ip],
                          capture_output=True, timeout=5)
    if result.returncode == 0:
        print(f"  ✓ FBox is reachable on network")
        results['network'] = True
    else:
        print(f"  ✗ Cannot reach FBox (check IP address or network)")
        results['network'] = False
except Exception as e:
    print(f"  ✗ Ping test failed: {e}")
    results['network'] = False

# Test 2: HTTP/Web Interface
print("\n[2/5] Testing HTTP Web Interface...")
try:
    import requests
    response = requests.get(f"http://{fbox_ip}", timeout=5)
    print(f"  ✓ Web interface accessible")
    print(f"    Status: {response.status_code}")
    print(f"    Try: http://{fbox_ip} in your browser")
    results['http'] = True
except Exception as e:
    print(f"  ✗ Web interface not accessible: {e}")
    results['http'] = False

# Test 3: Modbus TCP
print("\n[3/5] Testing Modbus TCP...")
try:
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient(fbox_ip, port=502, timeout=5)
    if client.connect():
        print(f"  ✓ Modbus TCP is ENABLED and accessible!")
        print(f"    Port: 502")
        print(f"    → This is the BEST option for real-time monitoring")

        # Try reading a test register
        try:
            result = client.read_holding_registers(address=0, count=1, slave=1)
            if not result.isError():
                print(f"    ✓ Successfully read test register")
            else:
                print(f"    ⚠ Connected but register read failed (may need configuration)")
        except:
            pass

        client.close()
        results['modbus'] = True
    else:
        print(f"  ✗ Modbus TCP not accessible (may not be enabled)")
        results['modbus'] = False
except ImportError:
    print(f"  ⚠ Cannot test Modbus (pymodbus not installed)")
    print(f"    Install: pip install pymodbus")
    results['modbus'] = None
except Exception as e:
    print(f"  ✗ Modbus test failed: {e}")
    results['modbus'] = False

# Test 4: FTP
print("\n[4/5] Testing FTP...")
try:
    import ftplib
    ftp = ftplib.FTP(timeout=5)
    ftp.connect(fbox_ip, 21)

    # Try common FBox credentials
    credentials = [
        ('admin', 'admin'),
        ('fbox', 'fbox'),
        ('root', 'root'),
        ('', ''),  # Anonymous
    ]

    ftp_logged_in = False
    for username, password in credentials:
        try:
            ftp.login(username, password)
            print(f"  ✓ FTP accessible")
            print(f"    Credentials: {username}/{password if password else '(none)'}")
            ftp_logged_in = True
            ftp.quit()
            break
        except:
            continue

    if not ftp_logged_in:
        print(f"  ⚠ FTP port open but credentials unknown")
        print(f"    Try accessing via web interface to configure")

    results['ftp'] = ftp_logged_in
except Exception as e:
    print(f"  ✗ FTP not accessible: {e}")
    results['ftp'] = False

# Test 5: MQTT (if applicable)
print("\n[5/5] Testing MQTT...")
try:
    import paho.mqtt.client as mqtt
    import time

    mqtt_connected = False

    def on_connect(client, userdata, flags, rc):
        global mqtt_connected
        if rc == 0:
            mqtt_connected = True

    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(fbox_ip, 1883, 5)
    client.loop_start()
    time.sleep(2)
    client.loop_stop()

    if mqtt_connected:
        print(f"  ✓ MQTT broker accessible")
        print(f"    Port: 1883")
        results['mqtt'] = True
    else:
        print(f"  ✗ MQTT not accessible")
        results['mqtt'] = False
except ImportError:
    print(f"  ⚠ Cannot test MQTT (paho-mqtt not installed)")
    print(f"    Install: pip install paho-mqtt")
    results['mqtt'] = None
except Exception as e:
    print(f"  ✗ MQTT test failed: {e}")
    results['mqtt'] = False

# Summary and Recommendations
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

print("\nConnection Methods Available:")
for method, status in results.items():
    if status is True:
        print(f"  ✓ {method.upper()}")
    elif status is False:
        print(f"  ✗ {method.upper()}")
    elif status is None:
        print(f"  ? {method.upper()} (cannot test - missing library)")

print("\n" + "=" * 70)
print("RECOMMENDED INTEGRATION PATH")
print("=" * 70)

if results.get('modbus') is True:
    print("\n🏆 BEST: Modbus TCP Real-Time Monitoring")
    print("\nNext Steps:")
    print("  1. Access FBox web interface: http://" + fbox_ip)
    print("  2. Find Modbus register map (Settings → Modbus)")
    print("  3. Note sensor register addresses")
    print("  4. Use scripts/fbox_collector.py for real-time collection")
    print("\nBenefits:")
    print("  - Real-time data (10-second updates)")
    print("  - Immediate anomaly detection")
    print("  - Professional industrial protocol")

elif results.get('mqtt') is True:
    print("\n🥈 GOOD: MQTT Integration")
    print("\nNext Steps:")
    print("  1. Configure FBox to publish sensor data to MQTT topics")
    print("  2. Integrate with Home Assistant")
    print("  3. Use HA automations for alerts")
    print("\nBenefits:")
    print("  - Real-time data")
    print("  - Easy Home Assistant integration")
    print("  - Lightweight protocol")

elif results.get('ftp') is True:
    print("\n🥉 OKAY: Automated FTP Download")
    print("\nNext Steps:")
    print("  1. Configure FBox to export data to FTP")
    print("  2. Use Windows Task Scheduler to fetch files hourly")
    print("  3. Run pipeline on downloaded files")
    print("\nBenefits:")
    print("  - No protocol complexity")
    print("  - Works with existing export mechanism")
    print("\nLimitations:")
    print("  - Higher latency (hours)")
    print("  - May miss short-duration events")

elif results.get('http') is True:
    print("\n📋 BASIC: Manual or Scheduled Export")
    print("\nNext Steps:")
    print("  1. Access FBox web interface: http://" + fbox_ip)
    print("  2. Check for API documentation or export scheduling")
    print("  3. Automate via Windows Task Scheduler if possible")
    print("\nBenefits:")
    print("  - Simple setup")
    print("  - Uses existing manual process")
    print("\nLimitations:")
    print("  - Manual intervention needed")
    print("  - Highest latency")

else:
    print("\n⚠️  LIMITED CONNECTIVITY")
    print("\nTroubleshooting:")
    print("  - Verify FBox IP address is correct")
    print("  - Check Windows firewall settings")
    print("  - Ensure FBox and server on same network")
    print("  - Try accessing web interface manually")

print("\n" + "=" * 70)
print("DOCUMENTATION")
print("=" * 70)
print(f"\nFull integration guide:")
print(f"  docs/flexem_fbox_integration_guide.md")
print(f"\nFor detailed Modbus setup:")
print(f"  See: Tier 2 in integration guide")
print(f"\nFor Home Assistant integration:")
print(f"  See: Tier 3 in integration guide")

print("\n" + "=" * 70)
print("\nTest complete! Save these results and proceed with recommended path.")
print("=" * 70)
