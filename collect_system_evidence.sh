#!/usr/bin/env bash
set -euo pipefail

echo "AWS CPU Node - System Resource Evidence"
echo "======================================="
echo "Captured (UTC): $(date -u --iso-8601=seconds)"
echo "Hostname: $(hostname)"

token="$(curl --silent --show-error --fail --request PUT \
  --header 'X-aws-ec2-metadata-token-ttl-seconds: 60' \
  http://169.254.169.254/latest/api/token)"
instance_id="$(curl --silent --show-error --fail \
  --header "X-aws-ec2-metadata-token: ${token}" \
  http://169.254.169.254/latest/meta-data/instance-id)"
instance_type="$(curl --silent --show-error --fail \
  --header "X-aws-ec2-metadata-token: ${token}" \
  http://169.254.169.254/latest/meta-data/instance-type)"
availability_zone="$(curl --silent --show-error --fail \
  --header "X-aws-ec2-metadata-token: ${token}" \
  http://169.254.169.254/latest/meta-data/placement/availability-zone)"

echo "Instance ID: ${instance_id}"
echo "Instance type: ${instance_type}"
echo "Availability zone: ${availability_zone}"
echo "Logical CPUs: $(nproc)"
echo "Uptime: $(uptime -p)"

echo
echo "--- CPU snapshot (top) ---"
top -b -n 1 | head -n 15

echo
echo "--- Memory (free -h) ---"
free -h

echo
echo "--- Network counters (ip -s link) ---"
ip -s link

echo
echo "--- Disk usage (df -h) ---"
df -h /
