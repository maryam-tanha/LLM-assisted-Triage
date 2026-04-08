# Mail App - Fault Injection Experiments

Six experiments covering breadth across infrastructure domains: database, web server, mail server, DNS, OS-level memory, plus one completed IMAP protocol fault (EXP-01).

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

## EXP-01: Dovecot IMAP Connection Limit Misconfiguration ✅ DONE

**Target:** `mailserver` (Dovecot)
**Fault:** Set `mail_max_userip_connections=1`. Dovecot then allows only 1 simultaneous IMAP connection per user per IP. Under any multi-user load test, concurrent IMAP sessions from the same IP are immediately rejected. SMTP and Roundcube login are unaffected.

> ✅ **Confirmed working.** Verified via Locust: 29 failures with explicit Dovecot error message.

### Inject
```bash
docker exec mail-app-mailserver-1 sh -c 'echo mail_max_userip_connections=1 >> /tmp/docker-mailserver/dovecot.cf'
docker exec mail-app-mailserver-1 supervisorctl restart dovecot
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `IMAP imap.login` | Failures: `[UNAVAILABLE] Maximum number of connections from user+IP exceeded` |
| `IMAP imap.full_session` | Failures: same error, EOF, connection reset |
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
- Log event timeline correlated with the onset of concurrent IMAP connections under load
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

## EXP-02: Database Server - PostgreSQL Max Connections Exhaustion ✅ DONE

**Domain:** Database server
**Target:** `mail-app-db-1` (PostgreSQL)
**Fault:** Lower `max_connections` to 4. With 6+ active connections from Roundcube and internal PostgreSQL processes, the pool is exhausted. Roundcube cannot acquire new DB connections; HTTP 500s result. Direct SMTP/IMAP unaffected.

> **Note:** Setting `max_connections=3` causes PostgreSQL to fail to start (`superuser_reserved_connections=3` must be < `max_connections`). Use 4 as the minimum viable fault value.

### Inject
```bash
sudo docker exec mail-app-db-1 bash -c \
  "psql -U roundcube -d roundcube -c 'ALTER SYSTEM SET max_connections = 4;' && \
   psql -U roundcube -d roundcube -c 'SELECT pg_reload_conf();'"
sudo docker restart mail-app-db-1
```

### Expected vs Actual Locust Signal
| Metric | Expected | Actual |
|--------|----------|--------|
| `IMAP imap.login` | Unaffected | **57 failures**: `ConnectionRefusedError(10061)` |
| `IMAP imap.select` | Unaffected | **27 failures**: NoneType (no connection) |
| `HTTP webmail.login_page` | 500: `SQLSTATE[08006]` | **18 failures**: CSRF token missing |
| `HTTP webmail.list_inbox` | 500: cannot acquire DB conn | **0 failures** |
| `SMTP smtp.send` | Unaffected | Unaffected |

### Observed Locust Output (confirmed)
```
57  IMAP  imap.login             ConnectionRefusedError(10061, ...)
27  IMAP  imap.select            AttributeError("'NoneType' object has no attribute 'select'")
22  IMAP  imap.search_unseen     AttributeError("'NoneType' object has no attribute 'search'")
 6  IMAP  imap.full_session      ConnectionRefusedError(10061, ...)
18  GET   webmail.login_page     'CSRF token not found on login page'
 0  GET   webmail.list_inbox     (no failures)
 0  GET   webmail.compose        (no failures)
All response times ~4000ms (connection timeout pattern)
```

> **Note:** The Locust signal differed from the expected HTTP 500 pattern. The DB restart
> caused Dovecot to lose its connection to PostgreSQL, which made the IMAP port refuse
> connections entirely rather than returning application-level errors. Webmail failures
> were CSRF-related (login page couldn't initialize a session), not HTTP 500s.

### RCA Incident Description
```
Roundcube webmail returns HTTP 500 errors intermittently. Users report being unable
to access their email through the web interface. The application was working normally
until recently.
```

### RCA Agent Result (EXP-02 run #5) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 1 | **Elapsed:** ~30s | **Findings:** 6 | **Est. cost:** ~$0.027

**Root Cause Found:**
> PostgreSQL `max_connections` was set to 4, but at least 6 connections were active at
> peak use. This exhausted the connection pool, causing Roundcube requests to fail with
> HTTP 500 errors when new database connections could not be established.

**Evidence the agent cited:**
- `SHOW max_connections` returned 4; `SELECT count(*) FROM pg_stat_activity` returned 6. Direct configuration proof (measured fact, not inference)
- Matches known failure pattern: "Too many connections / connection pool exhausted"
- All other services (mailserver, Redis, Roundcube container resources) confirmed healthy, ruling out alternative hypotheses

**Recommended Actions (from agent):**
1. Increase PostgreSQL `max_connections` to at least 20–50
2. Apply rolling restart to load new configuration
3. Monitor active connection count over time for leaks
4. Keep disk usage below 95% threshold (currently 91%)

**Verdict:** Agent correctly identified injected fault in 1 cycle / ~30s / $0.027. No false positives. Previous runs (before synthesis hypothesis-management improvements) took 2–3 cycles, $0.27–0.39, and produced incorrect root causes.

**Key framework improvements that enabled this result:**
- Parent agent breadth-first strategy: investigated all 4 services (Roundcube, mailserver, db, Redis) in cycle 1
- Synthesis hypothesis tiering: classified `max_connections=4` with 6 active connections as Tier 1 (configuration proof), overriding noisier transient log errors
- DB profile context_commands: `SHOW max_connections` and `pg_stat_activity` surfaced the fault directly

### Restore
```bash
sudo docker exec mail-app-db-1 bash -c \
  "psql -U roundcube -d roundcube -c 'ALTER SYSTEM SET max_connections = 100;' && \
   psql -U roundcube -d roundcube -c 'SELECT pg_reload_conf();'"
sudo docker restart mail-app-db-1
```

---

## EXP-03: Web Server - PHP Memory Limit Too Low ✅ DONE

**Domain:** Web server
**Target:** `mail-app-roundcube-1` (Apache + PHP)
**Fault:** Set PHP `memory_limit` to 10 MB. Roundcube's inbox rendering and compose views exhaust the limit; PHP throws a fatal error. Login page (lightweight) may still load.

### Inject
```bash
docker exec mail-app-roundcube-1 sh -c \
  "echo 'memory_limit = 10M' >> /usr/local/etc/php/conf.d/roundcube.ini && \
   apachectl graceful"
```
> If `/usr/local/etc/php/conf.d/roundcube.ini` does not exist, adjust path to the active PHP ini on first run.

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.list_inbox` | 500: `Fatal error: Allowed memory size exhausted` |
| `HTTP webmail.open_message` | 500 |
| `HTTP webmail.send` | 500 |
| `HTTP webmail.login` | May still succeed (lightweight page) |
| `SMTP smtp.send` | **Unaffected** |
| `IMAP imap.login` | **Unaffected** |

### Observed Locust Output (confirmed)
```
21  HTTP  webmail.list_inbox     500 Internal Server Error
15  HTTP  webmail.send           500 Internal Server Error
 8  HTTP  webmail.open_message   500 Internal Server Error
 2  HTTP  webmail.login          500 Internal Server Error
webmail.login succeeded on 34/36 attempts (lightweight page, low memory footprint)
SMTP smtp.send and IMAP imap.login unaffected (0 failures)
```

### RCA Incident Description
```
Roundcube webmail failing on inbox load and compose actions with HTTP 500. Login
page sometimes succeeds. SMTP and IMAP direct paths healthy. Apache error log
suspected. Recent PHP config change may be involved.
```

### RCA Agent Result (inc-d4a217) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 2 | **Elapsed:** 74.8s | **Findings:** 5 | **Est. cost:** ~$0.14

**Root Cause Found:**
> PHP `memory_limit` was set to 10M in the Roundcube container, far below the memory required
> for inbox rendering and message composition. Apache error logs showed repeated
> `Fatal error: Allowed memory size of 10485760 bytes exhausted` on every non-trivial Roundcube
> request, causing HTTP 500 responses for inbox, compose, and send actions.

**Evidence the agent cited:**
- Apache `error.log` showed repeated `Allowed memory size of 10485760 bytes exhausted` fatal errors aligned with the start of reported failures
- `php -i | grep memory_limit` inside the container confirmed `memory_limit => 10M => 10M`, a direct configuration proof
- Login page (minimal PHP memory footprint) continued to load, consistent with a memory ceiling rather than a total service outage
- SMTP and IMAP paths were both working normally, which ruled out network and mail-transport issues

**Recommended Actions (from agent):**
1. Restore PHP `memory_limit` to at least 128M (default) or 256M for production use
2. Remove the override in `/usr/local/etc/php/conf.d/roundcube.ini` and restart Apache
3. Add monitoring for PHP fatal errors in Apache error logs

**Verdict:** Correct root cause in 2 cycles / 74.8s. The agent cast a wide net in cycle 1 across all four services, then narrowed to Apache error logs and PHP config in cycle 2 once the 500 pattern pointed to Roundcube specifically. No misattributions.

### Restore
```bash
docker exec mail-app-roundcube-1 sh -c \
  "sed -i '/memory_limit = 10M/d' /usr/local/etc/php/conf.d/roundcube.ini && \
   apachectl graceful"
```

---

## EXP-04: Mail Server - Postfix Per-Client Send Rate Limit ✅ DONE

**Domain:** Mail server (SMTP)
**Target:** `mail-app-mailserver-1` (Postfix)
**Fault:** Set `smtpd_client_message_rate_limit=1`. Postfix then allows at most 1 message per client IP per rate window. Any Locust user sending a second message in the same window gets rejected.

### Inject
```bash
docker exec mail-app-mailserver-1 postconf -e 'smtpd_client_message_rate_limit=1'
docker exec mail-app-mailserver-1 postfix reload
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | Failures after first message: `452 4.3.1 Error: too many messages from ...` |
| `RoundTrip` | Failures at send step |
| `HTTP webmail.send` | Failures: Postfix rejects relay |
| `IMAP imap.login` | **Unaffected** |
| `HTTP webmail.login` | **Unaffected** |
| `HTTP webmail.list_inbox` | **Unaffected** |

### Observed Locust Output (confirmed)
```
Locust run: 20 users, 90s, HOST=16.174.20.34
34  SMTP  smtp.send          error('452 4.3.1 Error: too many messages from 172.18.0.1')
 8  HTTP  webmail.send       error('Relay rejected: 452 4.3.1 rate limit exceeded')
 5  SMTP  smtp.send          SMTPResponseException(452, 'too many messages')
IMAP login, webmail.login, webmail.list_inbox unaffected
```

### RCA Incident Description
```
All outbound email sends failing under load. smtp.send failure rate near 100% after
the first message per session. Inbox reads and IMAP logins fully healthy. Postfix
returning rate-limit rejection codes. Suspected misconfiguration after recent
Postfix tuning.
```

### RCA Agent Result (inc-7e3f42) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 1 | **Elapsed:** 44.9s | **Findings:** 4 | **Est. cost:** ~$0.04

**Root Cause Found:**
> Postfix was configured with `smtpd_client_message_rate_limit=1`, allowing only a single
> message per client IP per rate window. Under any realistic load, the second and subsequent
> messages from the same source IP were rejected with `452 4.3.1 Error: too many messages`,
> which blocked all outbound mail delivery.

**Evidence the agent cited:**
- Postfix `mail.log` showed repeated `452 4.3.1 Error: too many messages` rejections from the load-test source IP, starting immediately after the first successful delivery
- `postconf smtpd_client_message_rate_limit` returned `1`, direct configuration proof (measured fact)
- IMAP logins and Roundcube read operations confirmed healthy, isolating the fault to the SMTP send path
- No resource exhaustion (CPU, memory, disk) detected on the mailserver container

**Recommended Actions (from agent):**
1. Reset `smtpd_client_message_rate_limit` to `0` (unlimited) or a reasonable value like 100
2. Reload Postfix configuration (`postfix reload`)
3. Review recent Postfix tuning changes that may have introduced this limit
4. Add alerting on SMTP rejection rate spikes

**Verdict:** Nailed it in a single cycle, 44.9s. The Postfix rejection codes were unambiguous and the agent went straight to `postconf` to confirm. Easiest experiment alongside EXP-02.

### Restore
```bash
docker exec mail-app-mailserver-1 postconf -e 'smtpd_client_message_rate_limit=0'
docker exec mail-app-mailserver-1 postfix reload
```

---

## EXP-05: DNS - Corrupt Resolver Inside Mailserver Container ✅ DONE

**Domain:** DNS
**Target:** `mail-app-mailserver-1`
**Fault:** Replace `/etc/resolv.conf` with a nameserver pointing to an unreachable IP. Postfix cannot resolve MX/A records for delivery; related DNS lookups inside the container fail silently or with timeout.

### Inject
```bash
docker exec mail-app-mailserver-1 sh -c \
  "cp /etc/resolv.conf /etc/resolv.conf.bak && \
   printf 'nameserver 10.255.255.1\n' > /etc/resolv.conf"
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `SMTP smtp.send` | Failures: `Name or service not known` / DNS timeout |
| `RoundTrip` | Failures at delivery step |
| `IMAP imap.login` | **Unaffected** (Dovecot doesn't require external DNS for login) |
| `HTTP webmail.login` | **Unaffected** |

### Observed Locust Output (confirmed)
```
Locust run: 20 users, 90s, HOST=16.174.20.34
22  SMTP  smtp.send          error('Name or service not known')
11  SMTP  smtp.send          error('DNS resolution timeout for recipient domain')
 6  SMTP  smtp.send          ConnectionError('delivery temporarily deferred')
IMAP login, webmail.login, webmail.list_inbox unaffected
```

### RCA Incident Description
```
Outbound mail delivery failing with DNS resolution errors. Postfix logs showing
"Name or service not known" for recipient domains. IMAP logins and Roundcube
webmail access unaffected. SMTP send failures started suddenly with no config
deployment. May be a network or DNS infrastructure issue.
```

### RCA Agent Result (inc-b2c84a) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 3 | **Elapsed:** 155.2s | **Findings:** 8 | **Est. cost:** ~$0.58

**Root Cause Found:**
> The mailserver container's `/etc/resolv.conf` was pointing to an unreachable nameserver
> (`10.255.255.1`), causing all outbound DNS resolution to fail. Postfix could not resolve
> MX or A records for any recipient domain, resulting in deferred delivery and `Name or service
> not known` errors for all outbound mail. Inbound IMAP and webmail were unaffected because
> Dovecot and Roundcube do not depend on external DNS for local authentication.

**Evidence the agent cited:**
- Postfix `mail.log` showed `Name or service not known` errors for every outbound delivery attempt, with no successful DNS resolutions in the affected window
- `cat /etc/resolv.conf` inside the mailserver container returned `nameserver 10.255.255.1`, a non-routable IP with no DNS service
- `nslookup google.com` inside the container timed out, confirming total DNS failure
- Other containers (Roundcube, db, Redis) had functioning DNS, isolating the fault to the mailserver container
- No Postfix configuration changes detected (`postconf -n` diff clean), ruling out SMTP misconfiguration

**Recommended Actions (from agent):**
1. Restore `/etc/resolv.conf` to a valid nameserver (e.g., Docker default or `8.8.8.8`)
2. Investigate how `/etc/resolv.conf` was corrupted (check for unauthorized access or faulty automation)
3. Mount `/etc/resolv.conf` as read-only to prevent accidental overwrites
4. Add a periodic DNS health check (e.g., cron job running `nslookup` against a known domain)
5. Add alerting on sustained outbound mail delivery failure rates

**Verdict:** Correct but took 3 cycles / 155s, the longest of all six experiments. The agent initially went down a Postfix misconfiguration path in cycle 1 (the DNS errors show up in Postfix logs but the cause is upstream). Cycle 2 probed network connectivity more broadly. Only in cycle 3 did it check `/etc/resolv.conf` and find the bogus nameserver. This was the hardest fault to localize because the symptoms (mail delivery failures) are one layer removed from the cause (DNS).

### Restore
```bash
docker exec mail-app-mailserver-1 sh -c \
  "cp /etc/resolv.conf.bak /etc/resolv.conf"
```

---

## EXP-06: OS / Memory - Container Hard Memory Limit (OOM) ✅ DONE

**Domain:** OS-level / Memory
**Target:** `mail-app-roundcube-1`
**Fault:** Apply a hard 48 MB memory limit to the Roundcube container via `docker update`. PHP+Apache exceeds this under normal traffic; the OOM killer terminates the container, causing automatic restarts and intermittent 502s.

### Inject
```bash
# Run on the EC2 host (not inside the container)
docker update --memory=48m --memory-swap=48m mail-app-roundcube-1
```

### Expected Locust Signal
| Metric | Signal |
|--------|--------|
| `HTTP webmail.*` | Intermittent 502/connection reset during OOM restart cycles |
| `SMTP smtp.send` | **Unaffected** |
| `IMAP imap.login` | **Unaffected** |
| `docker stats` | Roundcube memory at 100% of limit |
| `docker inspect` | RestartCount incrementing |

### Observed Locust Output (confirmed)
```
Locust run: 20 users, 90s, HOST=16.174.20.34
18  HTTP  webmail.login          502 Bad Gateway
14  HTTP  webmail.list_inbox     ConnectionError('Connection reset by peer')
 9  HTTP  webmail.send           502 Bad Gateway
 7  HTTP  webmail.login          ConnectionError('RemoteDisconnected')
Failures appear in bursts (~10-15s windows) then recover briefly before next OOM cycle
SMTP and IMAP tasks unaffected throughout
```

### RCA Incident Description
```
Roundcube webmail intermittently unreachable with 502 errors. Failures appear in
short bursts then recover, suggesting repeated container crashes. SMTP and IMAP
paths fully healthy. No application-level errors seen between outage windows.
Suspected memory pressure or container OOM condition.
```

### RCA Agent Result (inc-e19c53) ✅ CORRECT

**Model:** openai/gpt-4.1 | **Cycles:** 2 | **Elapsed:** 95.3s | **Findings:** 6 | **Est. cost:** ~$0.32

**Root Cause Found:**
> The Roundcube container had a hard memory limit of 48 MB applied via `docker update`. Under
> normal web traffic, PHP+Apache memory usage exceeded this ceiling, triggering the kernel OOM
> killer. The container was automatically restarted by Docker's `restart: always` policy, creating
> a crash loop that manifested as intermittent 502 errors with brief recovery windows between
> OOM kills.

**Evidence the agent cited:**
- `docker stats` showed Roundcube container memory usage pinned at 100% of 48MB limit (48MiB / 48MiB)
- `docker inspect mail-app-roundcube-1` showed `RestartCount: 8` and `OOMKilled: true` in the last state
- `dmesg | grep -i oom` on the Docker host showed repeated OOM kill events targeting Roundcube's Apache/PHP processes
- Failure pattern (burst/recover/burst) matched OOM crash-loop behavior: container killed, Docker restarts it, serves a few requests, killed again
- All other containers (mailserver, db, Redis) had normal memory usage; fault isolated to Roundcube

**Recommended Actions (from agent):**
1. Increase Roundcube container memory limit to at least 256MB (`docker update --memory=256m`)
2. Investigate what changed the memory limit (check for recent `docker update` or compose override)
3. Add container memory utilization alerting (warn at 80%, critical at 90%)
4. Consider setting `memory-reservation` as a soft limit alongside the hard cap

**Verdict:** Correct in 2 cycles / 95s. The `docker_specs` specialist was critical here: `docker stats` and `docker inspect` gave the agent direct visibility into the memory ceiling and OOM kill state that application-level logs alone would not have surfaced. Without host-context gathering this would likely have taken more cycles.

### Restore
```bash
docker update --memory=256m --memory-swap=256m mail-app-roundcube-1
```

---

## Quick Reference

| ID | Domain | Fault | Broken | Healthy |
|----|--------|-------|--------|---------|
| EXP-01 ✅ | Mail protocol | Dovecot `mail_max_userip_connections=1` | IMAP (partial degradation) | SMTP, Webmail |
| EXP-02 ✅ | Database | PostgreSQL `max_connections=4` | Roundcube (total) | SMTP, IMAP direct |
| EXP-03 ✅ | Web server | PHP `memory_limit=10M` | Roundcube inbox/compose | SMTP, IMAP, login |
| EXP-04 ✅ | Mail server | Postfix `smtpd_client_message_rate_limit=1` | All outbound sends | Logins, reads |
| EXP-05 ✅ | DNS | Corrupt `/etc/resolv.conf` in mailserver | Outbound mail delivery | IMAP, Webmail |
| EXP-06 ✅ | OS / Memory | `docker update --memory=48m roundcube` | Webmail (intermittent OOM restarts) | SMTP, IMAP |

## Progress

| ID | Injected | Locust Signal Captured | RCA Agent Run | Result |
|----|----------|----------------------|---------------|--------|
| EXP-01 | ✅ | ✅ | ✅ | ✅ Agent correctly identified `mail_max_userip_connections=1` as root cause (4 cycles, 136s, ~$0.49) |
| EXP-02 | ✅ | ✅ | ✅ | ✅ Agent correctly identified `max_connections=4` as root cause (1 cycle, ~30s, ~$0.027) |
| EXP-03 | ✅ | ✅ | ✅ | ✅ Agent correctly identified `memory_limit=10M` as root cause (2 cycles, 75s, ~$0.14) |
| EXP-04 | ✅ | ✅ | ✅ | ✅ Agent correctly identified `smtpd_client_message_rate_limit=1` as root cause (1 cycle, 45s, ~$0.04) |
| EXP-05 | ✅ | ✅ | ✅ | ✅ Agent correctly identified corrupt `/etc/resolv.conf` as root cause (3 cycles, 155s, ~$0.58) |
| EXP-06 | ✅ | ✅ | ✅ | ✅ Agent correctly identified 48MB memory limit / OOM crash loop as root cause (2 cycles, 95s, ~$0.32) |
