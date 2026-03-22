#!/usr/bin/env bash
# -----------------------------------------------------------------------
# aws-setup.sh — Inspect and configure the mail-app EC2 instance
# Region: ca-west-1 (Calgary)
# Usage: Run each section manually or: bash aws-setup.sh
# -----------------------------------------------------------------------

REGION="ca-west-1"
INSTANCE_ID="i-07fe2aed96d176985"

# ── 1. Get full instance details ─────────────────────────────────────────
echo "=== Instance Info ==="
aws ec2 describe-instances \
  --region $REGION \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].{
    State:State.Name,
    Type:InstanceType,
    PublicIP:PublicIpAddress,
    PrivateIP:PrivateIpAddress,
    PublicDNS:PublicDnsName,
    AZ:Placement.AvailabilityZone,
    AMI:ImageId,
    KeyPair:KeyName,
    VPC:VpcId,
    Subnet:SubnetId,
    SecurityGroups:SecurityGroups
  }' \
  --output table

# ── 2. Get the security group ID attached to the instance ────────────────
echo ""
echo "=== Security Group IDs ==="
SG_ID=$(aws ec2 describe-instances \
  --region $REGION \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
  --output text)
echo "Security Group: $SG_ID"

# ── 3. Show current inbound rules ────────────────────────────────────────
echo ""
echo "=== Current Inbound Rules ==="
aws ec2 describe-security-groups \
  --region $REGION \
  --group-ids $SG_ID \
  --query 'SecurityGroups[0].IpPermissions[*].{
    Port:FromPort,
    Protocol:IpProtocol,
    CIDR:IpRanges[0].CidrIp
  }' \
  --output table

# ── 4. Get your current public IP ────────────────────────────────────────
echo ""
echo "=== Your current public IP ==="
MY_IP=$(curl -s https://checkip.amazonaws.com)
echo "Your IP: $MY_IP"

# ── 5. Add required inbound rules ────────────────────────────────────────
# SSH — restricted to your IP only
echo ""
echo "=== Adding inbound rules to $SG_ID ==="

aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 22 \
  --cidr "${MY_IP}/32" \
  --tag-specifications "ResourceType=security-group-rule,Tags=[{Key=Name,Value=SSH-MyIP}]" \
  && echo "  [OK] Port 22 (SSH) -> ${MY_IP}/32" \
  || echo "  [SKIP] Port 22 rule may already exist"

# SMTP (inbound receiving)
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 25 \
  --cidr "0.0.0.0/0" \
  && echo "  [OK] Port 25 (SMTP)" \
  || echo "  [SKIP] Port 25 rule may already exist"

# SMTP Submission (authenticated send)
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 587 \
  --cidr "0.0.0.0/0" \
  && echo "  [OK] Port 587 (Submission)" \
  || echo "  [SKIP] Port 587 rule may already exist"

# IMAP
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 143 \
  --cidr "0.0.0.0/0" \
  && echo "  [OK] Port 143 (IMAP)" \
  || echo "  [SKIP] Port 143 rule may already exist"

# IMAPS
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 993 \
  --cidr "0.0.0.0/0" \
  && echo "  [OK] Port 993 (IMAPS)" \
  || echo "  [SKIP] Port 993 rule may already exist"

# Roundcube webmail
aws ec2 authorize-security-group-ingress \
  --region $REGION \
  --group-id $SG_ID \
  --protocol tcp --port 8080 \
  --cidr "0.0.0.0/0" \
  && echo "  [OK] Port 8080 (Roundcube)" \
  || echo "  [SKIP] Port 8080 rule may already exist"

# ── 6. Allocate and associate an Elastic IP ──────────────────────────────
echo ""
echo "=== Allocating Elastic IP ==="
EIP_ALLOC=$(aws ec2 allocate-address \
  --region $REGION \
  --domain vpc \
  --query 'AllocationId' \
  --output text)
echo "Allocation ID: $EIP_ALLOC"

aws ec2 associate-address \
  --region $REGION \
  --instance-id $INSTANCE_ID \
  --allocation-id $EIP_ALLOC

ELASTIC_IP=$(aws ec2 describe-addresses \
  --region $REGION \
  --allocation-ids $EIP_ALLOC \
  --query 'Addresses[0].PublicIp' \
  --output text)
echo "Elastic IP assigned: $ELASTIC_IP"

# ── 7. Final summary ─────────────────────────────────────────────────────
echo ""
echo "=== Done ==="
echo "  Instance:    $INSTANCE_ID"
echo "  Elastic IP:  $ELASTIC_IP"
echo "  Region:      $REGION"
echo ""
echo "SSH command:"
echo "  ssh -i your-key.pem ubuntu@$ELASTIC_IP"
echo ""
echo "Webmail (after stack is running):"
echo "  http://$ELASTIC_IP:8080"
