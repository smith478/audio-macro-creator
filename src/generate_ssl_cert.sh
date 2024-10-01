#!/bin/bash

# Generate a private key
openssl genrsa -out server.key 2048

# Generate a Certificate Signing Request (CSR)
openssl req -new -key server.key -out server.csr

# Generate a self-signed certificate
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

# Clean up the CSR as it's no longer needed
rm server.csr

echo "Self-signed SSL certificate generated successfully."
echo "Files created: server.key, server.crt"