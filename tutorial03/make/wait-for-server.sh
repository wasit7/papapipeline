#!/bin/sh
echo "Waiting for Prefect Server to be ready at http://prefect-server:4200/api/health..."
while ! curl -s http://prefect-server:4200/api/health > /dev/null; do
  sleep 2
done
echo "Prefect Server is ready, starting Prefect Worker..."
exec prefect worker start --pool default-agent-pool
