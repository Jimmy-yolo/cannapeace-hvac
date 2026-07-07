#!/bin/bash
# Find FBox on local network by checking for web interfaces

echo "Scanning 192.168.1.x network for FBox web interface..."
echo ""

for ip in {38..53}; do
    target="192.168.1.$ip"
    echo -n "Checking $target ... "

    # Try HTTP (port 80)
    response=$(curl -s -m 2 "http://$target/" 2>/dev/null | head -c 100)
    if [ ! -z "$response" ]; then
        echo "✓ HTTP FOUND"
        echo "  → Open: http://$target"
        continue
    fi

    # Try HTTPS (port 443)
    response=$(curl -s -k -m 2 "https://$target/" 2>/dev/null | head -c 100)
    if [ ! -z "$response" ]; then
        echo "✓ HTTPS FOUND"
        echo "  → Open: https://$target"
        continue
    fi

    # Try common alternate port 8080
    response=$(curl -s -m 2 "http://$target:8080/" 2>/dev/null | head -c 100)
    if [ ! -z "$response" ]; then
        echo "✓ HTTP:8080 FOUND"
        echo "  → Open: http://$target:8080"
        continue
    fi

    echo "no web server"
done

echo ""
echo "Also check Modbus TCP (port 502) with:"
echo "  python scripts/test_fbox_modbus.py"
