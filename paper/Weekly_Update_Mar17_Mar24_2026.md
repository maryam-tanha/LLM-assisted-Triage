# Weekly Progress Update: March 17 to March 24, 2026

**Project:** LLM-Assisted Triage (AI-Infra-Project v1)
**Author:** Kalhar Pandya

---

## Summary

This week was heavily focused on building out a realistic demo target environment for the RCA framework, deploying it on a live AWS EC2 instance, wiring it into the multi-agent LangGraph pipeline, and running the first complete fault injection experiment from end to end. A significant amount of infrastructure work, debugging, scripting, and testing was done across the full stack.

---

## 1. Mail Server Deployment on AWS EC2

The first major effort of the week was designing and deploying a full mail server stack on a live AWS EC2 instance. The goal was to move away from a synthetic or local demo environment and work with something that behaves like a real production mail service. This involved writing the entire Docker Compose configuration from scratch, configuring each service to communicate properly with the others, and getting everything stable enough to run load tests against.

The stack consists of four containers running together:

- **Postfix and Dovecot** via the `docker-mailserver` image, which handles both outbound SMTP mail delivery on ports 25 and 587, and inbound IMAP mailbox access on ports 143 and 993. This is the core mail backend that everything else depends on.
- **Roundcube webmail** which provides a browser-based interface to the mailboxes. It talks to the mailserver over IMAP for reading mail and SMTP for sending, and also connects to the PostgreSQL database for storing user preferences, contacts, and session data.
- **PostgreSQL** as the relational database backend for Roundcube, storing all persistent application data including user identities and contact books.
- **Redis** as an in-memory session cache for Roundcube's PHP session handler, reducing database load under concurrent users.

Getting this stack stable took several rounds of configuration work. The `mailserver.env` file required careful tuning of Postfix and Dovecot options. A `setup.sh` script was written to automatically provision three test mail accounts (alice, bob, and admin at example.test) after the mailserver container reaches a healthy state. An `aws-setup.sh` bootstrap script was also written to prepare a fresh EC2 instance from zero, installing Docker, configuring kernel parameters, and cloning the repository. A `validate-aws.sh` script was added to verify that all services are reachable from outside the instance after deployment.

All four containers were configured with `restart: always` so the entire stack comes back up automatically after any reboot without needing manual intervention. During testing, the instance was rebooted to confirm this worked correctly.

The stack is deployed and run entirely from the GitHub repository clone at `/home/ubuntu/LLM-assisted-Triage/demo-targets/mail-app/` on the instance. An earlier approach of manually copying files over SCP was identified and removed, cleaning up a stale `/home/ubuntu/mail-app/` directory that had been created during initial setup experiments.

One specific bug that was caught and fixed during deployment was the Roundcube health check. The check used `grep -q 'roundcube'` to verify the webmail UI was responding, but the actual HTML served by Roundcube contains the word capitalized as "Roundcube". Because grep is case-sensitive by default, the health check was always failing and marking the container as unhealthy even when it was working perfectly. This was fixed by adding the `-i` flag to make the grep case-insensitive.

---

## 2. Redis Session Integration in PHP Roundcube

One of the specific requirements for later fault injection experiments was that Roundcube's PHP session handling should go through Redis rather than the default filesystem-based sessions. This matters because it allows us to inject a Redis memory fault and observe the effect as real session drops in the webmail interface, which is a much more realistic and interesting failure mode than just killing a container.

Getting this working required understanding how the Roundcube Docker image initializes itself and where configuration can be injected. The image uses an entrypoint task system where scripts placed in a specific directory are executed as part of the container startup sequence. A `setup-redis.sh` post-setup script was written and mounted into the container at `/entrypoint-tasks/post-setup/setup-redis.sh`. This script writes the necessary PHP session configuration into Roundcube's config directory at startup, pointing the PHP session handler at `tcp://redis:6379` instead of the filesystem.

An earlier attempt used a static PHP config file mounted directly into the container, but this approach conflicted with how the image manages its own configuration at startup. Switching to the entrypoint task hook approach resolved the conflict and the Redis session integration works correctly.

---

## 3. Locust Load and Functionality Testing Suite

A complete Locust test suite was written from scratch to exercise all three protocols exposed by the mail stack simultaneously. The file is 635 lines and covers HTTP, SMTP, and IMAP in a single coordinated test run.

The three user classes in the suite are:

- **WebMailUser** simulates a browser user interacting with the Roundcube UI. It logs in by first fetching the login page to extract the CSRF token, then submitting the login form. After login it cycles through listing the inbox, opening individual messages by fetching a real UID from the inbox listing response, composing and sending new messages, and running a round-trip verification that sends a message and then checks whether it appears in the inbox listing.
- **SMTPUser** connects directly to port 587 over STARTTLS and authenticates as a test user. It sends emails directly between test accounts without going through the webmail UI, and also runs a round-trip task that sends a message via SMTP and then verifies delivery by connecting via IMAP and polling the inbox.
- **IMAPUser** connects directly to port 143 over STARTTLS and exercises the Dovecot IMAP server by selecting the inbox, fetching headers for recent messages, and searching for unseen messages.

Because SMTP and IMAP are not HTTP protocols, Locust does not automatically track their metrics. Custom `SmtpClient` and `ImapClient` wrapper classes were written that emit timing data to the Locust event system via `events.request.fire()`, so every SMTP send and every IMAP operation appears as its own row in the Locust stats table and dashboard, alongside the HTTP metrics.

Three bugs were discovered and fixed during development and early test runs:

- The login response check was using `r.url` to determine whether the login succeeded by checking if the browser was still on the login page. Inside Locust's `catch_response=True` context manager, `r.url` can be `None`, which caused an `AttributeError` that crashed every WebMailUser on startup. This was fixed by inspecting the response body text instead, checking for the presence of the password input field or the login form element, which is a more reliable indicator regardless of URL.

- After an IMAP command failure, the `_reconnect()` method was calling `connect_and_login()` to re-establish the session, but it was not calling `select_inbox()` afterward. The IMAP protocol requires that a folder must be explicitly selected via the `SELECT` command before any `SEARCH` commands can run. Without this, the connection was left in `AUTH` state, and subsequent `SEARCH` tasks would fail with "command SEARCH illegal in state AUTH". This was fixed by adding `select_inbox()` to the reconnect flow.

- The round-trip delivery verification was using a single fixed sleep of three seconds before checking whether the sent message had arrived in the inbox. Under any meaningful load, Postfix's internal delivery queue slows down and messages take longer than three seconds to arrive. This caused the round-trip test to fail consistently under load even when the mail system was working correctly. The fix was to replace the fixed sleep with a polling loop that checks once per second for up to fifteen seconds, breaking out as soon as the message is found.

---

## 4. RCA Framework Agent Wiring for Mail App

A substantial amount of work went into connecting the mail-app stack to the RCA framework's LangGraph agent pipeline so that investigations can be launched against it from both the command-line demo script and the Streamlit web UI.

The profile system was built out to support the mail app. The `profiles/mail_app/profile.yaml` file defines all four services in detail, including the container name for each service, what ports it uses, what its expected behavior is under normal conditions, a list of known failure patterns with their likely causes, a set of context commands that agents run at the start of every investigation to gather baseline data, and log hints that tell agents where to look for relevant log files inside each container. The access method is set to SSH so that all agent commands are executed remotely on the EC2 instance rather than locally.

Four specialist agent system prompts were written and placed in `profiles/mail_app/agents/`:

- `log_agent.yaml` contains a detailed prompt tuned for reading and interpreting mail server logs, understanding Postfix queue semantics, Dovecot authentication patterns, and correlating log timestamps with incident windows.
- `runtime_status_agent.yaml` is tuned for inspecting container resource usage, identifying OOM conditions, swap pressure, disk exhaustion, and process state.
- `docker_specs_agent.yaml` focuses on container configuration, image versions, volume mounts, network topology, and environment variable inspection.
- `network_agent.yaml` handles port reachability checks, TLS handshake verification, and DNS resolution within the container network.

The parent agent prompt (`parent.yaml`) and synthesis agent prompt (`synthesis.yaml`) were also written to coordinate investigation cycles and aggregate findings into a coherent RCA report.

Changes were also made to the core framework code to support SSH-based profiles. The `base_specialist.py` was updated with a `run()` method that creates an `SSHExecutor` instance, runs the context commands remotely, passes the output to the LLM tool loop along with the investigation task, and parses the findings from the response. The `models.py` was updated with an `SSHConfig` dataclass holding host, port, username, key path, and timeout. The `graph/builder.py` was updated to route investigation commands through SSH when the profile's access method is SSH rather than local Docker exec.

A key clarification that emerged during debugging sessions is that `ui.py` and `demo.py` are functionally identical at the agent level. The Streamlit UI is purely a visual wrapper around the same LangGraph graph. When a user selects the mail_app profile in the UI and clicks Start Investigation, the agents SSH into the EC2 instance and run the exact same `docker exec` commands that the CLI demo would run.

---

## 5. SSH Tool Key Type Fix

During investigation of agent failures, a bug was found in `rca-framework/core/tools/ssh_tool.py`. The connection setup code was loading the private key using `paramiko.RSAKey.from_private_key_file()`, which is hardcoded to parse RSA keys only. If the PEM file on disk is an Ed25519 or ECDSA key, this call raises a `paramiko.SSHException` with the message "not a valid RSA private key file". This exception is caught and re-raised as an `SSHExecutionError`, which the specialist agent receives as the output of every command it tries to run. An agent receiving `SSH_ERROR: not a valid RSA private key file` instead of real command output can produce completely fabricated findings, which is a serious correctness issue for an RCA system.

The fix was straightforward: replace the explicit key object construction with the `key_filename` parameter in the `client.connect()` call. Paramiko's `connect()` method accepts a file path via `key_filename` and automatically tries all supported key types in order until one succeeds. This makes the SSH tool work correctly regardless of whether the key is RSA, Ed25519, ECDSA, or any other format paramiko supports.

---

## 6. Fault Injection Experiment Design and First Run

A complete fault injection playbook was written in `demo-targets/mail-app/EXPERIMENTS.md` covering six distinct failure scenarios. Each experiment entry includes a one-line inject command, a table of the expected Locust signal per metric, a pre-written incident description string that can be pasted directly into the RCA agent, and a restore command to undo the fault.

The six experiments cover a range of failure categories:

- **EXP-01** takes down the entire mailserver container, causing simultaneous loss of SMTP and IMAP. This represents a total backend outage and should produce 100% failure rates across all mail-related Locust metrics.
- **EXP-02** stops the PostgreSQL database, which breaks only the Roundcube web UI while leaving direct SMTP and IMAP access completely unaffected. This tests whether the agent can correctly localize a failure to the web stack rather than the mail backend.
- **EXP-03** reduces the Redis memory limit to 1MB using a live `CONFIG SET` command, which causes aggressive session eviction under load. This produces a subtle failure mode where Roundcube returns HTTP 200 responses but the response body contains the login form instead of the expected content, because the user's session was silently evicted. This is exactly the kind of grey failure that is difficult to diagnose without understanding the session architecture.
- **EXP-04** uses `postconf` to set Postfix's message size limit to 1024 bytes, which causes every outbound email to be rejected with an SMTP size error. Only sending operations fail. Reading, listing, and logging in are completely unaffected.
- **EXP-05** stops the Roundcube container, taking down only the web UI while leaving direct SMTP and IMAP access healthy. This is the inverse of EXP-02 in terms of what survives.
- **EXP-06** modifies the Dovecot configuration to set `mail_max_userip_connections=1`, which limits each user to a single simultaneous IMAP connection from any given IP address. Under load testing, where multiple Locust workers are simulating the same three test accounts from the same machine, this causes immediate and widespread IMAP rejections while leaving SMTP and the webmail UI completely healthy.

**EXP-06 was run end-to-end this week.** The fault was injected by appending the setting to `/tmp/docker-mailserver/dovecot.cf` and restarting the Dovecot process via supervisorctl. The Locust test confirmed the fault was active, showing 29 failures with the explicit Dovecot error message `[UNAVAILABLE] Maximum number of connections from user+IP exceeded (mail_max_userip_connections=1)`, along with additional connection reset and EOF errors caused by the cascading load on the limited connection slots. The RPS chart showed a collapse from 1.8 requests per second to near zero, and the p95 latency spiked to over 100,000 milliseconds.

The RCA agent was then run against this incident using the `openai/gpt-4.1` model. The agent completed 4 investigation cycles, used 4 of 6 available specialist nodes, and returned a correct root cause identification in 136.5 seconds at an estimated cost of approximately $0.49. The agent's conclusion was that `mail_max_userip_connections=1` in the Dovecot configuration was the direct cause of the IMAP session rejections, that the log timestamps matched the reported incident window exactly, and that OOM, disk exhaustion, and database or Redis issues had all been ruled out through direct investigation. The recommended remediation was to increase the limit to at least 3 to 5 connections and add monitoring alerts for connection limit utilization.

After the experiment, the server was fully restored. The `dovecot.cf` override file was cleared, but `doveadm config` still showed the injected value because docker-mailserver had written the override to `/etc/dovecot/local.conf` at startup time. This file was identified and cleaned, and the value was confirmed back to the default of 10 after a Dovecot reload.

---

## 7. Project Tracking and Documentation

Two tracking documents were created for the mail-app work:

- `demo-targets/mail-app/AGENTS.md` serves as a living task tracker, with sections for current infrastructure status, a per-experiment progress table that gets updated as experiments run, a list of completed tasks, and a list of upcoming work items.
- `demo-targets/mail-app/EXPERIMENTS.md` is the fault injection playbook, updated after EXP-06 with the full RCA agent result including the root cause found, the evidence cited, the recommended actions from the agent, and the overall verdict.

The SSH connection pattern used throughout all server work this week was also documented in project memory for future reference: use `-o StrictHostKeyChecking=no` with the key flag and pass commands non-interactively as quoted strings to the SSH invocation rather than relying on interactive shell sessions.

---

## Commits This Week

- `eb31635` Kalhar: Add mail-app demo target and RCA profile
- `8ec6be9` feat: Introduce mail-app Locust load testing and Docker Compose configuration
- `40c985f` Kalhar: Fix Roundcube healthcheck case-sensitivity (grep -qi)
- `fb5f3dd` feat: Introduce core RCA framework data models and mail_app profile
- `663a6c4` feat: Introduce initial RCA framework with agent architecture and Docker integration
- `c70e588` fix(mail-app): add redis session config for roundcube
- `46a7262` fix(mail-app): use post-setup script for redis config
- `752e241` Kalhar: Add mail-app fault injection experiments guide
- `9913c43` Kalhar: Simplify experiments and add AGENTS.md task tracker for mail-app
- `e7b4938` Kalhar: Add AGENTS.md project task tracker
- `e4658e1` Kalhar: Add EXP-06 Dovecot connection limit (confirmed working), update AGENTS.md progress
- `606cf7d` Kalhar: Fix ssh_tool to auto-detect key type instead of hardcoding RSAKey

---

## Next Steps

- Restore the EXP-06 server state fully and confirm clean baseline before the next experiment
- Run EXP-01 through EXP-05 end-to-end in sequence
- Document agent findings per experiment in AGENTS.md as results come in
- Analyze agent performance across all six experiments including accuracy, number of cycles needed, cost, and time to conclusion
- Use the experimental results to populate the evaluation section of the IEEE paper
