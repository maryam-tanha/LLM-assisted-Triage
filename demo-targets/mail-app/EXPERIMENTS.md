# Mail App — Fault Injection Experiments

Six experiments to test the RCA agent against real failure modes in the mail stack.

---

## How to Run an Experiment

**1. Inject the fault** (one command via SSH or directly on the server)

**2. Run Locust locally:**
```bash
HOST=16.174.20.34 locust -f demo-targets/mail-app/locustfile.py --headless -u 20 -r 2 --run-time 90s
```

**3. Run the RCA agent:**
```bash
cd rca-framework
python demo.py --profile profiles/mail_app --incident "<paste incident description>"
```

**4. Restore** using the restore command.

---

## EXP-01 — Mailserver Container Crash

**Target:** `mailserver` (Postfix + Dovecot)
**Fault:** Service completely down — both SMTP and IMAP gone simultaneously.

### Inject
```bash
docker stop mail-app-mailserver-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | 100% failure — connection refused port 587 |
| `IMAP imap.login` | 100% failure — connection refused port 143 |
| `RoundTrip` | 100% failure |
| `HTTP webmail.login` | Failures — Roundcube loses IMAP backend |
| `HTTP webmail.list_inbox` | Session drops |

### RCA Incident Description
```
Complete mail outage. SMTP port 587 and IMAP port 143 both refusing connections.
Roundcube returning "Connection to storage server failed". All Locust user
classes showing near-100% failure. DB and Redis appear healthy.
```

### Restore
```bash
docker start mail-app-mailserver-1
# Wait ~30s for Postfix + Dovecot to initialise
```

---

## EXP-02 — PostgreSQL Outage

**Target:** `db` (PostgreSQL)
**Fault:** Roundcube loses its session/config database. SMTP and IMAP direct paths unaffected.

### Inject
```bash
docker stop mail-app-db-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.login` | 100% failure — PHP DB error |
| `HTTP webmail.list_inbox` | Session expired, cannot renew |
| `SMTP smtp.send` | **Unaffected** |
| `IMAP imap.login` | **Unaffected** |

### RCA Incident Description
```
Roundcube webmail completely down. All webmail.login requests failing with HTTP 500.
Direct SMTP and IMAP connections still working normally. Abrupt onset.
```

### Restore
```bash
docker start mail-app-db-1
```

---

## EXP-03 — Redis Session Cache Exhaustion

**Target:** `redis`
**Fault:** Reduce Redis memory to 1MB — active sessions get evicted, users silently dropped back to login page. HTTP still returns 200, failure only visible in response body.

### Inject
```bash
docker exec mail-app-redis-1 redis-cli CONFIG SET maxmemory 1mb
```
> Run Locust with **30+ users** to trigger eviction.

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.list_inbox` | "Session dropped! Redirected to login form." |
| `HTTP webmail.open_message` | Session drop failures |
| `HTTP webmail.send` | Session dropped before send |
| `SMTP smtp.send` | **Unaffected** |
| `IMAP imap.login` | **Unaffected** |

### RCA Incident Description
```
Random Roundcube session drops under load. webmail tasks failing with session-dropped
errors immediately after a successful login. SMTP and IMAP healthy. Failures worsen
as user count increases. HTTP responses return 200 but body contains login form.
```

### Restore
```bash
docker exec mail-app-redis-1 redis-cli CONFIG SET maxmemory 128mb
docker exec mail-app-redis-1 redis-cli FLUSHALL
```

---

## EXP-04 — Postfix Message Size Limit Misconfiguration

**Target:** `mailserver` (Postfix)
**Fault:** Set message size limit to 1KB. Every email (larger than 1KB with headers) is rejected. Logins and inbox reads completely unaffected.

### Inject
```bash
docker exec mail-app-mailserver-1 postconf -e message_size_limit=1024
docker exec mail-app-mailserver-1 postfix reload
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | 100% failure — "552 5.3.4 Message size exceeds fixed limit" |
| `RoundTrip` | 100% failure at send step |
| `HTTP webmail.send` | Failures — Postfix rejects relay |
| `IMAP imap.login` | **Unaffected** |
| `HTTP webmail.login` | **Unaffected** |
| `HTTP webmail.list_inbox` | **Unaffected** |

### RCA Incident Description
```
All outbound email sends failing with size-related SMTP errors. smtp.send failure
rate 100%. Inbox reads and IMAP logins unaffected. Roundcube webmail.send also
failing. Suspected Postfix misconfiguration after a recent config change.
```

### Restore
```bash
docker exec mail-app-mailserver-1 postconf -e message_size_limit=10240000
docker exec mail-app-mailserver-1 postfix reload
```

---

## EXP-05 — Roundcube Container Down

**Target:** `roundcube`
**Fault:** Web UI gone entirely. Direct SMTP and IMAP still work — only browser users are affected.

### Inject
```bash
docker stop mail-app-roundcube-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.*` | 100% failure — connection refused port 8080 |
| `SMTP smtp.send` | **Unaffected** |
| `IMAP imap.login` | **Unaffected** |
| `RoundTrip` | **Unaffected** (uses direct SMTP+IMAP) |

### RCA Incident Description
```
Roundcube webmail completely unreachable on port 8080. All HTTP Locust tasks
failing with connection refused. Direct SMTP and IMAP paths fully healthy.
Mail backend appears fine — only the web frontend is down.
```

### Restore
```bash
docker start mail-app-roundcube-1
```

---

---

## EXP-06 — Dovecot IMAP Connection Limit Misconfiguration

**Target:** `mailserver` (Dovecot)
**Fault:** Set `mail_max_userip_connections=1` — Dovecot allows only 1 simultaneous IMAP connection per user per IP. Under any multi-user load test, concurrent IMAP sessions from the same IP are immediately rejected. SMTP and Roundcube login are unaffected.

> ✅ **Confirmed working** — Verified via Locust: 29 failures with explicit Dovecot error message.

### Inject
```bash
docker exec mail-app-mailserver-1 sh -c 'echo mail_max_userip_connections=1 >> /tmp/docker-mailserver/dovecot.cf'
docker exec mail-app-mailserver-1 supervisorctl restart dovecot
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `IMAP imap.login` | Failures — `[UNAVAILABLE] Maximum number of connections from user+IP exceeded` |
| `IMAP imap.full_session` | Failures — same error, EOF, connection reset |
| `IMAP imap.search_unseen` | Failures after reconnect attempts |
| `SMTP smtp.send` | **Unaffected** |
| `HTTP webmail.*` | **Unaffected** (Roundcube uses its own pooled connection) |

### Observed Locust Output (confirmed)
```
29  IMAP  imap.full_session  error('[UNAVAILABLE] Maximum number of connections from user+IP exceeded (mail_max_userip_connections=1)')
 3  IMAP  imap.full_session  abort('command: LOGIN => socket error: EOF')
 1  IMAP  imap.full_session  ConnectionResetError(10054, ...)
 3  IMAP  imap.login         abort('command: LOGIN => socket error: EOF')
 2  IMAP  imap.login         ConnectionResetError(10054, ...)
```

### RCA Incident Description
```
IMAP service degraded under load. Direct IMAP connections from Locust failing with
"Maximum number of connections from user+IP exceeded (mail_max_userip_connections=1)".
SMTP sends unaffected. Roundcube webmail sessions unaffected. Failure rate scales
with number of concurrent users. Suspect Dovecot misconfiguration.
```

### RCA Agent Result (inc-98b699) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 4 | **Elapsed:** 136.5s | **Nodes:** 4/6 | **Est. cost:** ~$0.49

**Root Cause Found:**
> Dovecot's configuration enforced a per-user, per-IP IMAP connection limit (`mail_max_userip_connections=1`),
> leading to mass IMAP login rejections and session drops when legitimate users attempted concurrent connections.

**Evidence the agent cited:**
- Dovecot logs showed repeated rejections due to `mail_max_userip_connections=1` being exceeded
- Log event timeline matched exactly with user-reported session drops and RPS collapse after 10:00 PM
- Ruled out OOM, disk exhaustion, fatal application/infrastructure errors

**Recommended Actions (from agent):**
1. Increase `mail_max_userip_connections` to 3–5
2. Test under simulated load to confirm fix
3. Implement alerts for connection limit utilization
4. Document concurrency controls in deployment runbooks

**Verdict:** Agent correctly identified the injected fault (`mail_max_userip_connections=1`) as root cause in 4 cycles / 136s. No false positives.

### Restore
```bash
docker exec mail-app-mailserver-1 sed -i '/mail_max_userip_connections/d' /tmp/docker-mailserver/dovecot.cf
docker exec mail-app-mailserver-1 supervisorctl restart dovecot
```

---

## Quick Reference

| ID | Fault | Broken | Healthy |
|----|-------|--------|---------|
| EXP-01 | `docker stop mailserver` | SMTP, IMAP, Roundcube | DB, Redis |
| EXP-02 | `docker stop db` | Roundcube (total) | SMTP, IMAP direct |
| EXP-03 | Redis `maxmemory=1mb` | Roundcube sessions (silent 200s) | SMTP, IMAP direct |
| EXP-04 | Postfix `message_size_limit=1024` | All sends | Logins, reads |
| EXP-05 | `docker stop roundcube` | Web UI only | SMTP, IMAP, RoundTrip |
| EXP-06 | Dovecot `mail_max_userip_connections=1` | IMAP only (partial degradation) | SMTP, Webmail |

## Progress

| ID | Injected | Locust Signal Captured | RCA Agent Run | Result |
|----|----------|----------------------|---------------|--------|
| EXP-01 | ☐ | ☐ | ☐ | — |
| EXP-02 | ☐ | ☐ | ☐ | — |
| EXP-03 | ☐ | ☐ | ☐ | — |
| EXP-04 | ☐ | ☐ | ☐ | — |
| EXP-05 | ☐ | ☐ | ☐ | — |
| EXP-06 | ✅ | ✅ | ✅ | ✅ Agent correctly identified `mail_max_userip_connections=1` as root cause (4 cycles, 136s, ~$0.49) |
