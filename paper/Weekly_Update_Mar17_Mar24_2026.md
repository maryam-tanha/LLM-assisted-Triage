# Weekly Progress Update: March 17 to March 24, 2026

**Project:** LLM-Assisted Triage (AI-Infra-Project v1)
**Author:** Kalhar Pandya

---

## Summary

This week was focused on building a realistic demo environment for the RCA framework, getting it deployed on a live cloud server, connecting it to the agent pipeline, and running the first real fault injection experiment. A lot of ground was covered across infrastructure setup, testing, bug fixing, and actual agent evaluation.

---

## 1. Mail Server Deployment on AWS

The biggest effort this week was setting up a real mail server on an AWS EC2 instance to use as a target environment for the RCA agents. The idea was to have something more realistic than a toy local app, something closer to what you would actually find in a production environment.

The setup includes four services running together: a mail backend handling both sending and receiving of emails, a web-based mail client that users interact with through a browser, a database storing user and session data, and a Redis cache sitting in front of the database to handle sessions more efficiently. Getting all four services to talk to each other correctly and stay stable under load took several rounds of configuration and debugging.

A few scripts were written along the way to make the setup repeatable. One script creates test user accounts automatically, another bootstraps a fresh server from zero, and a third validates that everything is reachable from the outside after deployment. All containers were also configured to restart automatically after a reboot, which was confirmed by actually rebooting the instance during testing.

One bug caught during deployment was a health check that was silently always failing. It was checking for the word "roundcube" in the page response but the page was actually returning "Roundcube" with a capital letter, so the check never matched. The whole service looked unhealthy even when everything was working fine. That was a small fix but it would have caused confusing behavior if left in.

---

## 2. Redis for Session Management

To make one of the planned fault injection experiments more interesting, the webmail application was configured to store user sessions in Redis rather than on the filesystem. This matters because it means a Redis failure directly causes users to get logged out, which is a much more realistic and visible failure mode. It also means the RCA agent has a harder problem to solve since the failure looks like a session issue on the surface rather than an obvious infrastructure outage.

Getting this wired up correctly required a fair amount of digging into how the webmail Docker image initializes itself. The first approach of mounting a config file directly into the container did not work because the image was overwriting that config at startup. The working solution was to hook into the image's own post-setup mechanism so the session configuration gets applied at the right point in the startup sequence.

---

## 3. Load and Functionality Testing with Locust

A load testing script was written to simulate real user activity against the mail stack. It covers three different types of users simultaneously: browser users going through the web interface, users sending mail directly, and users checking their mail directly. This gives a more complete picture of how the system behaves under stress and makes it easier to see which part of the system is affected when a fault is injected.

The testing tool used does not natively understand email protocols, so some extra work was needed to make those operations show up in the test dashboard alongside the usual web metrics. That way when running an experiment you can see in one place whether the web interface, sending, and receiving are all healthy or which specific ones are failing.

A few bugs also came up during early test runs. The login flow was crashing because it was trying to read a field that could be empty under certain conditions. The mail-checking logic was failing after a reconnect because it was skipping a required step in the protocol handshake. And a delivery verification check was timing out too aggressively, marking deliveries as failed when the mail had actually arrived a few seconds later than expected. All three were fixed.

---

## 4. Connecting the Mail App to the RCA Agents

A significant amount of work went into configuring the RCA framework to investigate the mail server environment. This involved writing a detailed profile for the mail app that tells the agents what services exist, what normal behavior looks like for each one, what kinds of failures are common, where to find the relevant logs, and what commands to run to get a baseline picture of the system's health.

Four specialist agents were configured for this environment, each focused on a different angle: one reads and interprets logs, one looks at resource usage and process health, one inspects container configuration and setup, and one checks network connectivity between services. The orchestrator and synthesis agents were also tuned to work well with mail-specific failure patterns.

One thing that became clearer through this work is that the web interface and the command-line tool for running investigations are doing the exact same thing under the hood. The web interface is just a visual layer on top. Both talk to the same agents, which in turn connect to the live server over SSH to run their investigation commands.

---

## 5. Bug Fix in the SSH Connection Tool

While debugging agent failures, a bug was found in the tool responsible for connecting to the remote server. It was hardcoded to only handle one specific type of SSH key, which meant that if the server's key was in a different format it would fail silently in a way that caused agents to receive garbage instead of real command output. An agent getting error messages instead of actual server data would then produce unreliable findings, which is obviously a problem for an RCA system.

The fix was to let the underlying library figure out the key type automatically rather than assuming it upfront. This means the tool now works regardless of what key format is being used.

---

## 6. Fault Injection Experiments

A playbook was written covering six different fault scenarios for the mail stack, ranging from taking down a service entirely to subtle misconfigurations that only affect a specific subset of operations. Each entry in the playbook has the exact command to inject the fault, a description of what the load test output should look like if the fault is active, a ready-to-use incident description to feed to the RCA agent, and the command to restore everything back to normal afterward.

The six scenarios are designed to test different things. Some cause total outages that should be easy for the agent to spot. Others cause partial failures that only affect sending or only affect the web interface, which require the agent to correctly localize the problem rather than just saying "something is broken." One scenario produces a particularly subtle failure where the web interface returns successful responses on the surface but the content is wrong because user sessions are silently being dropped.

The first experiment was run end-to-end this week. The fault was a configuration setting in the mail server that limited each user to only one simultaneous connection for reading mail. Under any load test with multiple simulated users, this immediately causes a flood of rejected connections. The load test confirmed the fault was working as expected, with clear error messages in the output and the request rate dropping sharply.

The RCA agent was then given a description of the incident and asked to investigate. It correctly identified the configuration setting as the root cause, matched the timing to the incident window in the logs, and ruled out every other possible cause it checked. The whole investigation took just over two minutes and cost under fifty cents to run. The server was then cleaned up and restored to its original state, which involved an extra step because the misconfiguration had been written into a deeper config file by the server software at startup and needed to be removed from two places rather than one.

---

## 7. Documentation and Tracking

Two tracking documents were set up for the mail-app work. One is a living task tracker that shows the current state of the infrastructure and a progress table for each experiment. The other is the experiment playbook itself, which was updated after the first run with the full results including what the agent found, what evidence it cited, and what it recommended.

---

## Next Steps

- Run the remaining five experiments end-to-end
- Track agent performance across all experiments, looking at how accurate it was, how many cycles it needed, how long it took, and what it cost
- Use the results to fill in the evaluation section of the research paper
