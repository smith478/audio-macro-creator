#!/bin/bash

# Show usage if no argument is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 [local|remote]"
    echo "  local  - Run server for localhost access (HTTP)"
    echo "  remote - Run server for remote access (HTTPS)"
    exit 1
fi

MODE=$1

# Set the deployment mode environment variable
export DEPLOYMENT_MODE=$MODE

case $MODE in
    "local")
        echo "Starting server in local mode..."
        uvicorn app:app --host localhost --port 8000
        ;;
    "remote")
        echo "Starting server in remote mode..."
        uvicorn app:app --host 0.0.0.0 --port 8000 \
            --ssl-keyfile="$PWD/server.key" \
            --ssl-certfile="$PWD/server.crt"
        ;;
    *)
        echo "Invalid mode. Use 'local' or 'remote'"
        exit 1
        ;;
esac