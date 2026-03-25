# Mail App — Agent Task Tracker

Tracks experiment runs, agent findings, and outstanding tasks for the mail-app demo target.

---

## Infrastructure Status

| Component | Status | Notes |
|-----------|--------|-------|
| AWS instance | ✅ Running | `ubuntu@16.174.20.34` |
| docker-compose | ✅ From repo | `/home/ubuntu/LLM-assisted-Triage/demo-targets/mail-app/` |
| mailserver | ✅ Healthy | Ports 25/143/587/993 |
| roundcube | ✅ Healthy | Port 8080 |
| db (postgres) | ✅ Healthy | |
| redis | ✅ Healthy | |
| Restart policy | ✅ `always` | Survives reboots |
| Test accounts | ✅ Created | alice, bob, admin @example.test |

---

## Experiment Progress

| ID | Fault | Injected | Locust Signal | RCA Agent | Verdict |
|----|-------|----------|---------------|-----------|---------|
| EXP-01 | Mailserver stopped | ☐ | ☐ | ☐ | — |
| EXP-02 | PostgreSQL stopped | ☐ | ☐ | ☐ | — |
| EXP-03 | Redis maxmemory=1mb | ☐ | ☐ | ☐ | — |
| EXP-04 | Postfix size_limit=1024 | ☐ | ☐ | ☐ | — |
| EXP-05 | Roundcube stopped | ☐ | ☐ | ☐ | — |
| EXP-06 | Dovecot mail_max_userip_connections=1 | ✅ | ✅ | ☐ | — |

> Update each cell with ✅ / ❌ and a one-line finding as you run experiments.

---

## Tasks

### Done
- [x] Deploy mail-app stack on AWS EC2
- [x] Configure `restart=always` on all containers
- [x] Run from GitHub repo (not manual copy)
- [x] Fix Roundcube healthcheck (case-insensitive grep)
- [x] Fix locustfile bugs: `r.url` None, IMAP state after reconnect, round-trip polling
- [x] Write 5 fault injection experiments (EXPERIMENTS.md)

### Up Next
- [ ] Restore EXP-06 fault (run restore command), then run RCA agent against it first
- [ ] Run EXP-01 end-to-end (inject → Locust → RCA agent → restore)
- [ ] Run EXP-02 end-to-end
- [ ] Run EXP-03 end-to-end
- [ ] Run EXP-04 end-to-end
- [ ] Run EXP-05 end-to-end
- [ ] Wire mail-app profile into `rca-framework/configs/` (if not already)
- [ ] Document RCA agent findings per experiment

---

## SSH Quick Reference

```bash
# Connect
ssh -o StrictHostKeyChecking=no -i "/p/LLM-RCA-Reasearch/Keys/mail-server-kalhar-laptop.pem" ubuntu@16.174.20.34

# Check containers
docker compose -f /home/ubuntu/LLM-assisted-Triage/demo-targets/mail-app/docker-compose.yml ps

# Pull latest
cd /home/ubuntu/LLM-assisted-Triage && git pull
```
