# Mail App — Demo Target

A 4-service Docker Compose mail stack used as the RCA framework's fault-injection test environment. Deployed on AWS EC2 (ca-west-1).

## Stack

| Service | Image | Role | Ports |
|---------|-------|------|-------|
| `mailserver` | docker-mailserver (Postfix + Dovecot) | SMTP + IMAP | 25, 587, 143, 993 |
| `roundcube` | roundcube/roundcubemail | Webmail UI | 8080 |
| `db` | postgres:15-alpine | Roundcube session/config store | 5432 (internal) |
| `redis` | redis:7-alpine | Roundcube session cache (128MB) | 6379 (internal) |

All containers use `restart: always` and have healthchecks configured.

---

## Setup

### Option A — Local (Docker on your machine)

```bash
# 1. Copy env and start the stack
cp .env.example .env
docker compose up -d

# 2. Wait for mailserver to be healthy, then create test accounts
bash setup.sh

# 3. Open webmail
open http://localhost:8080
```

### Option B — AWS EC2 (remote host)

**Prerequisites:** AWS CLI configured, SSH key available.

```bash
# 1. Provision the EC2 instance and configure security group rules
bash aws-setup.sh

# 2. SSH into the instance
ssh -i /path/to/key.pem ubuntu@<ELASTIC_IP>

# 3. On the server: clone repo and start the stack
git clone https://github.com/maryam-tanha/LLM-assisted-Triage.git
cd LLM-assisted-Triage/demo-targets/mail-app
cp .env.example .env
docker compose up -d

# 4. Create test accounts (run from the server)
bash setup.sh

# 5. Validate everything from your local machine
bash validate-aws.sh
```

**Test accounts created by `setup.sh`:**

| Email | Password |
|-------|----------|
| alice@example.test | Alice1234! |
| bob@example.test | Bob1234! |
| admin@example.test | Admin1234! |

---

## Load Testing (Locust)

`locustfile.py` exercises all three mail protocols simultaneously:

| User Class | Protocol | What It Tests |
|------------|----------|---------------|
| `WebMailUser` | HTTP (port 8080) | Roundcube login, inbox, compose, send |
| `SMTPUser` | SMTP/STARTTLS (port 587) | Direct authenticated mail submission |
| `IMAPUser` | IMAP/STARTTLS (port 143) | Direct mailbox retrieval |

**Install and run:**

```bash
pip install locust

# Web UI at http://localhost:8089 — configure users interactively
HOST=<server-ip> locust -f locustfile.py

# Headless — 20 users, ramp 2/s, run 90s
HOST=<server-ip> locust -f locustfile.py --headless -u 20 -r 2 --run-time 90s
```

Configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `localhost` | Target hostname or IP |
| `SMTP_PORT` | `587` | SMTP submission port |
| `IMAP_PORT` | `143` | IMAP port |
| `WEBMAIL_PORT` | `8080` | Roundcube HTTP port |

---

## Fault Injection Experiments

Six experiments covering different failure domains. Full injection commands, expected Locust signals, and RCA agent outputs are documented in `EXPERIMENTS.md`.

| Exp | Fault | Domain | Result |
|-----|-------|--------|--------|
| EXP-01 | Dovecot connection limit (`mail_max_userip_connections=1`) | IMAP protocol | 4 cycles, 136s, ~$0.49 ✅ |
| EXP-02 | PostgreSQL max connections exhausted | Database | 1 cycle, ~30s, ~$0.027 ✅ |
| EXP-03 | PHP memory limit too low in Roundcube | Web server | 2 cycles, 75s, ~$0.14 ✅ |
| EXP-04 | Postfix per-client send rate limit | Mail transport | 1 cycle, 45s, ~$0.04 ✅ |
| EXP-05 | DNS resolver corruption in mailserver | Network/DNS | 3 cycles, 155s, ~$0.58 ✅ |
| EXP-06 | Container hard memory limit (OOM) | OS/memory | 2 cycles, 95s, ~$0.32 ✅ |

**General experiment workflow:**

```bash
# 1. Inject the fault (see EXPERIMENTS.md for per-experiment command)
ssh -i key.pem ubuntu@<server-ip> '<inject command>'

# 2. Run Locust to generate load and surface the failure
HOST=<server-ip> locust -f locustfile.py --headless -u 20 -r 2 --run-time 90s

# 3. Run the RCA agent from the repo root
cd rca-framework
python demo.py --profile profiles/mail_app --incident "<paste incident description from EXPERIMENTS.md>"

# 4. Restore the system (see EXPERIMENTS.md for per-experiment restore command)
ssh -i key.pem ubuntu@<server-ip> '<restore command>'
```

---

## Useful Commands

```bash
# Check container health status
docker compose ps

# Tail all logs
docker compose logs -f

# Tail a specific service
docker logs -f mail-app-mailserver-1

# Check mail queue
docker exec mail-app-mailserver-1 mailq

# List mail accounts
docker exec mail-app-mailserver-1 setup email list

# Restart a service
docker compose restart mailserver
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Stack definition |
| `mailserver.env` | docker-mailserver configuration (SMTP/IMAP settings) |
| `.env.example` | PostgreSQL credentials template |
| `setup.sh` | Creates test accounts after first startup |
| `locustfile.py` | Locust load + functionality test (HTTP, SMTP, IMAP) |
| `aws-setup.sh` | Provisions EC2 security group rules and Elastic IP |
| `validate-aws.sh` | Validates EC2 instance, security groups, and port reachability |
| `EXPERIMENTS.md` | Fault injection commands, expected signals, and RCA outputs |
| `config/setup-redis.sh` | Post-startup script that configures Roundcube to use Redis sessions |
