#!/usr/bin/env bash
set -euo pipefail

DEST_DIR="./certs"
DAYS_VALID=365
CA_SUBJECT="/CN=Kafka-CA"
BROKER_SUBJECT="/CN=kafka-broker"

rm -rf "${DEST_DIR}"
mkdir -p "${DEST_DIR}"
chmod 700 "${DEST_DIR}"

echo "1) Generating CA"
openssl genrsa -out "${DEST_DIR}/ca-key.pem" 4096
openssl req -new -x509 -key "${DEST_DIR}/ca-key.pem" -out "${DEST_DIR}/ca-cert.pem" -days "${DAYS_VALID}" -subj "${CA_SUBJECT}"

echo "2) Generating broker key"
openssl genrsa -out "${DEST_DIR}/broker-key.pem" 2048

echo "3) Creating CSR for broker"
openssl req -new -key "${DEST_DIR}/broker-key.pem" -out "${DEST_DIR}/broker.csr" -subj "${BROKER_SUBJECT}"

cat > "${DEST_DIR}/san.cnf" <<EOF
[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req

[ req_distinguished_name ]

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
DNS.2 = kafka
IP.1 = 127.0.0.1
EOF

echo "4) Signing broker certificate with SAN"
openssl x509 -req -in "${DEST_DIR}/broker.csr" -CA "${DEST_DIR}/ca-cert.pem" -CAkey "${DEST_DIR}/ca-key.pem" -CAcreateserial -out "${DEST_DIR}/broker-cert.pem" -days "${DAYS_VALID}" -sha256 -extfile "${DEST_DIR}/san.cnf" -extensions v3_req

echo "5) Creating broker keypair (key + cert)"
cat "${DEST_DIR}/broker-key.pem" "${DEST_DIR}/broker-cert.pem" > "${DEST_DIR}/broker-keypair.pem"
chmod 600 "${DEST_DIR}/broker-keypair.pem"

echo "6) Creating fullchain (cert + CA)"
cat "${DEST_DIR}/broker-cert.pem" "${DEST_DIR}/ca-cert.pem" > "${DEST_DIR}/fullchain.pem"
chmod 644 "${DEST_DIR}/fullchain.pem"

rm -f "${DEST_DIR}/broker.csr" "${DEST_DIR}/san.cnf" "${DEST_DIR}/ca-cert.srl" || true

echo "Done. Files in ${DEST_DIR}:"
ls -1 "${DEST_DIR}"
