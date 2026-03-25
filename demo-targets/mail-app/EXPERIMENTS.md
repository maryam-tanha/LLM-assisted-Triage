# Mail App — Fault Injection Experiments

Five experiments to test the RCA agent against real failure modes in the mail stack. Each experiment induces a specific fault, produces measurable signal in Locust, and is diagnosed by running the RCA agent.

---

## How to Run an Experiment

**1. SSH into the server:**
```bash
ssh -o StrictHostKeyChecking=no -i "/p/LLM-RCA-Reasearch/Keys/mail-server-kalhar-laptop.pem" ubuntu@16.174.20.34
```

**2. Inject the fault** (commands in each experiment below)

**3. Run Locust locally while the fault is active:**
```bash
HOST=16.174.20.34 locust -f demo-targets/mail-app/locustfile.py --headless -u 20 -r 2 --run-time 90s
```

**4. Run the RCA agent from `rca-framework/`:**
```bash
python demo.py --profile profiles/mail_app --incident "<paste incident description>"
```

**5. Restore** using the restore commands below.

---

## EXP-01 — Dovecot IMAP Connection Limit Exhaustion

**Target:** `mailserver` (Dovecot)
**Fault type:** Misconfiguration → resource exhaustion
**Description:** Sets the per-user IMAP connection limit to 1. With 20 concurrent Locust users, any second parallel IMAP connection from the same user is rejected. Simulates a Dovecot config mistake that causes connection exhaustion under load.

### Inject
```bash
# On the server:
docker exec mail-app-mailserver-1 \
  sh -c 'echo "mail_max_userip_connections=1" >> /tmp/docker-mailserver/dovecot.cf'
docker exec mail-app-mailserver-1 doveadm reload
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `IMAP imap.login` | Spike in failures — "Maximum number of connections exceeded" |
| `IMAP imap.full_session` | High failure rate as concurrent sessions breach the limit |
| `RoundTrip round_trip.smtp_to_imap` | Failures — IMAP verify step cannot connect |
| `SMTP smtp.send` | **Unaffected** — SMTP uses Postfix, not Dovecot |
| `HTTP webmail.login` | Partial failures — Roundcube IMAP backend rejects second session |

### RCA Agent Incident Description
```
IMAP login failures spiking across all test users. Locust shows
'Maximum number of connections exceeded' on imap.login and imap.full_session.
SMTP sends still succeeding. Roundcube logins intermittently failing.
```

### Restore
```bash
docker exec mail-app-mailserver-1 \
  sh -c "sed -i '/mail_max_userip_connections=1/d' /tmp/docker-mailserver/dovecot.cf"
docker exec mail-app-mailserver-1 doveadm reload
# Verify:
docker exec mail-app-mailserver-1 doveadm who
```

---

## EXP-02 — PostgreSQL Database Outage

**Target:** `db` (PostgreSQL)
**Fault type:** Service down
**Description:** Stops the PostgreSQL container. Roundcube cannot start new sessions or persist preferences. SMTP and IMAP direct connections are completely unaffected — only the web UI breaks.

### Inject
```bash
# On the server:
docker stop mail-app-db-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.login` | 100% failure — Roundcube returns PHP DB error page |
| `HTTP webmail.list_inbox` | Session dropped — sessions expire, cannot renew |
| `SMTP smtp.send` | **Unaffected** — direct path bypasses db |
| `IMAP imap.login` | **Unaffected** — direct path bypasses db |
| `RoundTrip round_trip.smtp_to_imap` | **Unaffected** — uses direct SMTP + IMAP |

### RCA Agent Incident Description
```
Roundcube webmail completely inaccessible. All webmail.login requests
failing with HTTP 500. Direct SMTP and IMAP connections still working normally.
Abrupt onset with no prior warnings.
```

### Restore
```bash
docker start mail-app-db-1
# Verify:
docker exec mail-app-db-1 pg_isready -U roundcube -d roundcube
```

---

## EXP-03 — Redis Session Cache Memory Exhaustion

**Target:** `redis`
**Fault type:** Resource exhaustion (silent)
**Description:** Reduces Redis `maxmemory` to 1MB. With 30+ Locust WebMailUsers, Redis hits the limit and evicts active sessions via `allkeys-lru`. Roundcube users are silently redirected to the login page mid-task. HTTP status codes still return 200 — the failure is only visible in the body content. This is the most subtle experiment.

### Inject
```bash
# On the server:
docker exec mail-app-redis-1 redis-cli CONFIG SET maxmemory 1mb
```
Run Locust with **30+ users** to generate enough session data to trigger eviction.

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.list_inbox` | "Session dropped! Redirected to login form." failures |
| `HTTP webmail.open_message` | Same session-drop failures |
| `HTTP webmail.send` | Session dropped before send completes |
| `HTTP webmail.login` | Initially succeeds but next task fails within seconds |
| `SMTP smtp.send` | **Unaffected** — bypasses Redis |
| `IMAP imap.login` | **Unaffected** — bypasses Redis |

### RCA Agent Incident Description
```
Random Roundcube session drops under load. webmail.list_inbox and
webmail.open_message failing with session-dropped errors even immediately
after a successful login. SMTP and IMAP direct connections healthy.
Failures get worse as user count increases. HTTP responses return 200
but the body contains the login form.
```

### Restore
```bash
docker exec mail-app-redis-1 redis-cli CONFIG SET maxmemory 128mb
docker exec mail-app-redis-1 redis-cli FLUSHALL
# Verify:
docker exec mail-app-redis-1 redis-cli INFO memory | grep used_memory_human
```

---

## EXP-04 — Postfix Message Size Limit Misconfiguration

**Target:** `mailserver` (Postfix)
**Fault type:** Misconfiguration
**Description:** Sets Postfix `message_size_limit` to 1024 bytes (1KB). Every outbound email — which is larger than 1KB including headers — is rejected with `552 5.3.4 Message size exceeds fixed limit`. Simulates an operator accidentally entering bytes instead of megabytes during a config change. Logins and inbox reads are completely unaffected.

### Inject
```bash
# On the server:
docker exec mail-app-mailserver-1 postconf -e message_size_limit=1024
docker exec mail-app-mailserver-1 postfix reload
# Verify the change:
docker exec mail-app-mailserver-1 postconf message_size_limit
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | 100% failure — "552 5.3.4 Message size exceeds fixed limit" |
| `RoundTrip round_trip.smtp_to_imap` | 100% failure at send step |
| `HTTP webmail.send` | Failures — Roundcube SMTP relay rejected by Postfix |
| `IMAP imap.login` | **Unaffected** |
| `HTTP webmail.login` | **Unaffected** |
| `HTTP webmail.list_inbox` | **Unaffected** |

### RCA Agent Incident Description
```
All outbound email sends failing. smtp.send failure rate 100% with
size-related SMTP errors. Inbox reads and IMAP logins unaffected.
Roundcube webmail.send also failing. Suspected Postfix misconfiguration
after a recent config reload.
```

### Restore
```bash
docker exec mail-app-mailserver-1 postconf -e message_size_limit=10240000
docker exec mail-app-mailserver-1 postfix reload
# Verify:
docker exec mail-app-mailserver-1 postconf message_size_limit
```

---

## EXP-05 — Full Mailserver Container Crash

**Target:** `mailserver` (Postfix + Dovecot)
**Fault type:** Service down (total)
**Description:** Stops the mailserver container entirely, taking down both Postfix (SMTP) and Dovecot (IMAP) simultaneously. All three Locust user classes are affected. This is the broadest failure scenario — a complete mail stack outage. It tests whether the agent can identify the single root cause behind multiple simultaneous failure signals.

> **Note:** `docker stop` sends SIGTERM (clean shutdown, won't auto-restart).
> Use `docker kill` to simulate a crash that triggers `restart=always`.

### Inject
```bash
# On the server:
docker stop mail-app-mailserver-1
# Or simulate a crash (triggers restart=always):
# docker kill mail-app-mailserver-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | 100% failure — connection refused on port 587 |
| `IMAP imap.login` | 100% failure — connection refused on port 143 |
| `RoundTrip round_trip.smtp_to_imap` | 100% failure at both send and verify steps |
| `HTTP webmail.login` | Failures — "Connection to storage server failed" |
| `HTTP webmail.list_inbox` | Session dropped — existing sessions lose IMAP backing |

### RCA Agent Incident Description
```
Complete mail service outage. SMTP port 587 and IMAP port 143 both
refusing connections. Roundcube webmail login returning 'Connection to
storage server failed'. All three Locust user classes showing near-100%
failure rates. Abrupt onset with no gradual degradation. Database and
Redis appear healthy.
```

### Restore
```bash
docker start mail-app-mailserver-1
# Wait ~20s for Postfix + Dovecot to initialise, then verify:
docker exec mail-app-mailserver-1 ss -lntp | grep -E ':25|:587|:143|:993'
```

---

## Quick Reference

| ID | Fault | Broken | Healthy |
|----|-------|--------|---------|
| EXP-01 | Dovecot `max_connections=1` | IMAP, Roundcube (partial) | SMTP |
| EXP-02 | PostgreSQL stopped | Roundcube (total) | SMTP, IMAP direct |
| EXP-03 | Redis `maxmemory=1mb` | Roundcube sessions (silent) | SMTP, IMAP direct |
| EXP-04 | Postfix `message_size_limit=1024` | All sends | Logins, reads |
| EXP-05 | Mailserver stopped | Everything | DB, Redis |
