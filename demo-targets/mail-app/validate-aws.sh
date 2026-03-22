#!/usr/bin/env bash
# -----------------------------------------------------------------------
# validate-aws.sh — Validate EC2 instance and security group for mail-app
# Region: ca-west-1 (Calgary)
# Usage: bash validate-aws.sh
# -----------------------------------------------------------------------
set -euo pipefail

REGION="ca-west-1"
INSTANCE_ID="i-07fe2aed96d176985"
REQUIRED_PORTS=(22 25 143 587 993 8080)

PASS=0
FAIL=0

pass() { echo "  [PASS] $1"; ((PASS++)); }
fail() { echo "  [FAIL] $1"; ((FAIL++)); }
header() { echo ""; echo "── $1 ──────────────────────────────────────────"; }

# ── 1. Instance state ────────────────────────────────────────────────────
header "1. Instance State"
STATE=$(aws ec2 describe-instances \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].State.Name' --output text)
TYPE=$(aws ec2 describe-instances \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].InstanceType' --output text)
AZ=$(aws ec2 describe-instances \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' --output text)
echo "  Instance: $INSTANCE_ID | Type: $TYPE | AZ: $AZ"
[[ "$STATE" == "running" ]] && pass "State = running" || fail "State = $STATE (expected: running)"

# ── 2. Elastic IP ────────────────────────────────────────────────────────
header "2. Elastic IP"
ELASTIC_IP=$(aws ec2 describe-addresses \
  --region $REGION \
  --filters "Name=instance-id,Values=$INSTANCE_ID" \
  --query 'Addresses[0].PublicIp' --output text 2>/dev/null || echo "None")
ASSOC_ID=$(aws ec2 describe-addresses \
  --region $REGION \
  --filters "Name=instance-id,Values=$INSTANCE_ID" \
  --query 'Addresses[0].AssociationId' --output text 2>/dev/null || echo "None")
echo "  Elastic IP:     $ELASTIC_IP"
echo "  Association ID: $ASSOC_ID"
[[ "$ELASTIC_IP" != "None" && "$ELASTIC_IP" != "null" ]] && pass "Elastic IP allocated: $ELASTIC_IP" || fail "No Elastic IP allocated"
[[ "$ASSOC_ID"   != "None" && "$ASSOC_ID"   != "null" ]] && pass "Elastic IP associated with instance"   || fail "Elastic IP not associated"

# ── 3. Instance health checks ────────────────────────────────────────────
header "3. Instance Health Checks"
INST_STATUS=$(aws ec2 describe-instance-status \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'InstanceStatuses[0].InstanceStatus.Status' --output text 2>/dev/null || echo "unknown")
SYS_STATUS=$(aws ec2 describe-instance-status \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'InstanceStatuses[0].SystemStatus.Status' --output text 2>/dev/null || echo "unknown")
echo "  Instance check: $INST_STATUS  |  System check: $SYS_STATUS"
[[ "$INST_STATUS" == "ok" ]] && pass "Instance status check = ok" || fail "Instance status = $INST_STATUS (may still be initialising)"
[[ "$SYS_STATUS"  == "ok" ]] && pass "System status check = ok"   || fail "System status = $SYS_STATUS (may still be initialising)"

# ── 4. Security group rules ──────────────────────────────────────────────
header "4. Security Group Rules"
SG_ID=$(aws ec2 describe-instances \
  --region $REGION --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' --output text)
SG_NAME=$(aws ec2 describe-security-groups \
  --region $REGION --group-ids $SG_ID \
  --query 'SecurityGroups[0].GroupName' --output text)
echo "  Security Group: $SG_ID ($SG_NAME)"

OPEN_PORTS=$(aws ec2 describe-security-groups \
  --region $REGION --group-ids $SG_ID \
  --query 'SecurityGroups[0].IpPermissions[*].FromPort' \
  --output text | tr '\t' '\n' | sort -n)

for PORT in "${REQUIRED_PORTS[@]}"; do
  if echo "$OPEN_PORTS" | grep -qx "$PORT"; then
    pass "Port $PORT is open"
  else
    fail "Port $PORT is MISSING from security group"
  fi
done

# ── 5. Network reachability (nc) ─────────────────────────────────────────
header "5. Network Reachability (from this machine)"
if [[ "$ELASTIC_IP" == "None" || "$ELASTIC_IP" == "null" ]]; then
  echo "  Skipped — no Elastic IP to test against"
  ((FAIL++))
else
  # SSH must be reachable; mail ports will be refused until Docker is running (that's OK)
  for PORT in "${REQUIRED_PORTS[@]}"; do
    RESULT=$(nc -zv -w3 "$ELASTIC_IP" "$PORT" 2>&1 || true)
    if echo "$RESULT" | grep -q "succeeded"; then
      pass "Port $PORT reachable ($ELASTIC_IP:$PORT)"
    elif echo "$RESULT" | grep -q "refused"; then
      if [[ "$PORT" == "22" ]]; then
        fail "Port 22 (SSH) — connection refused (SG rule missing or instance not ready)"
      else
        echo "  [INFO] Port $PORT refused — expected until Docker stack is running"
      fi
    else
      fail "Port $PORT — timeout or unreachable (SG rule may be missing)"
    fi
  done
fi

# ── 6. Instance type memory reminder ────────────────────────────────────
header "6. Instance Capacity"
MEM=$(aws ec2 describe-instance-types \
  --region $REGION --instance-types $TYPE \
  --query 'InstanceTypes[0].MemoryInfo.SizeInMiB' --output text)
VCPU=$(aws ec2 describe-instance-types \
  --region $REGION --instance-types $TYPE \
  --query 'InstanceTypes[0].VCpuInfo.DefaultVCpus' --output text)
echo "  $TYPE: ${VCPU} vCPU | ${MEM} MiB RAM"
if [[ "$MEM" -lt 1024 ]]; then
  echo "  [WARN] < 1GB RAM — mail stack may OOM. Upgrade to t3.micro or t3.small if containers crash."
elif [[ "$MEM" -lt 2048 ]]; then
  echo "  [WARN] < 2GB RAM — monitor with: docker stats --no-stream"
else
  pass "Memory sufficient for mail stack (${MEM} MiB)"
fi

# ── Summary ──────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
if [[ $FAIL -eq 0 ]]; then
  echo "  All checks passed."
  echo ""
  echo "  Next step — SSH in:"
  echo "    ssh -i your-key.pem ubuntu@$ELASTIC_IP"
else
  echo "  Fix the failures above before proceeding."
fi
echo "════════════════════════════════════════════════════"
