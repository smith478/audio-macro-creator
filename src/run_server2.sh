#!/bin/bash

# Show usage if no argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 [local|remote]"
    echo "  local  - Run server for localhost access (HTTP)"
    echo "  remote - Run server for remote access (HTTPS)"
    exit 1
fi

MODE=$1

# Function to show available IP addresses
show_addresses() {
    echo "Available addresses:"
    echo "  - Local: http://localhost:8000/static/index.html"
    echo "  - Network addresses:"
    ip addr show | grep "inet " | grep -v "127.0.0.1" | awk '{print "    - http://" $2}' | cut -d'/' -f1
}

case $MODE in
    "local")
        echo "Starting server in local mode..."
        echo "Access via: http://localhost:8000/static/index.html"
        uvicorn app:app --host localhost --port 8000
        ;;
    "remote")
        echo "Starting server in remote mode..."
        echo "Access via one of these addresses:"
        show_addresses | sed 's/http:/https:/g'
        echo "(Note: You'll need to accept the security certificate warning)"
        uvicorn app:app --host 0.0.0.0 --port 8000 \
            --ssl-keyfile=/audio-macro-creator/server.key \
            --ssl-certfile=/audio-macro-creator/server.crt
        ;;
    *)
        echo "Invalid mode. Use 'local' or 'remote'"
        exit 1
        ;;
esac