#!/usr/bin/env python3
"""
Test Modbus TCP connectivity to FBox
Industrial IoT gateways like FBox typically use Modbus TCP (port 502)
"""

import socket
import sys

def test_modbus_tcp(ip, port=502, timeout=2):
    """Test if device responds to Modbus TCP on port 502"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def scan_network():
    """Scan 192.168.1.38-53 for Modbus TCP"""
    print("Scanning for Modbus TCP (port 502) on 192.168.1.x...")
    print("")

    found_devices = []

    for last_octet in range(38, 54):
        ip = f"192.168.1.{last_octet}"
        sys.stdout.write(f"Checking {ip} ... ")
        sys.stdout.flush()

        if test_modbus_tcp(ip):
            print("✓ MODBUS TCP FOUND")
            found_devices.append(ip)
        else:
            print("no response")

    print("")
    if found_devices:
        print(f"Found {len(found_devices)} device(s) with Modbus TCP:")
        for ip in found_devices:
            print(f"  → {ip}:502")
            print(f"     Test: python scripts/read_fbox_modbus.py {ip}")
    else:
        print("No Modbus TCP devices found.")
        print("")
        print("The FBox might use:")
        print("  1. HTTP API (check http://FBOX_IP/api/data or similar)")
        print("  2. MQTT (check if broker shows FBox as client)")
        print("  3. Proprietary protocol")
        print("")
        print("Check the FBox manual for API endpoints or check router")
        print("for device name to identify correct IP.")

if __name__ == "__main__":
    scan_network()
