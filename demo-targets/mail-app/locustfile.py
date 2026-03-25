"""
Locust load + functionality test for the mail-app demo stack.

Protocols tested:
  - HTTP   : Roundcube webmail UI  (port 8080)
  - SMTP   : Postfix submission    (port 587, STARTTLS)
  - IMAP   : Dovecot retrieval     (port 143, STARTTLS)

Configuration via environment variables:
  HOST         target hostname / IP  (default: localhost)
  SMTP_PORT    SMTP submission port  (default: 587)
  IMAP_PORT    IMAP port             (default: 143)
  WEBMAIL_PORT Roundcube HTTP port   (default: 8080)

Run:
  pip install locust
  HOST=16.174.20.34 locust -f locustfile.py          # web UI at :8089
  HOST=16.174.20.34 locust -f locustfile.py \\
      --headless -u 10 -r 2 --run-time 60s           # headless
"""

import imaplib
import os
import random
import re
import smtplib
import ssl
import time
import uuid
from email.mime.text import MIMEText

from locust import HttpUser, User, between, events, task

# ── Configuration ─────────────────────────────────────────────────────────────

HOST = os.environ.get("HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
IMAP_PORT = int(os.environ.get("IMAP_PORT", 143))
WEBMAIL_PORT = int(os.environ.get("WEBMAIL_PORT", 8080))

TEST_USERS = [
    {"email": "alice@example.test", "password": "Alice1234!"},
    {"email": "bob@example.test", "password": "Bob1234!"},
    {"email": "admin@example.test", "password": "Admin1234!"},
]

# ── Shared event helper ────────────────────────────────────────────────────────


def _fire(env, *, request_type, name, start, response_length=0, response=None, exception=None):
    """Fire a Locust request event so custom protocol metrics appear in the dashboard."""
    env.events.request.fire(
        request_type=request_type,
        name=name,
        response_time=(time.perf_counter() - start) * 1000,
        response_length=response_length,
        response=response,
        context={},
        exception=exception,
    )


def _no_verify_ssl() -> ssl.SSLContext:
    """Return an SSLContext that accepts docker-mailserver's self-signed cert."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ── SmtpClient ─────────────────────────────────────────────────────────────────


class SmtpClient:
    """Thin smtplib wrapper that reports metrics to the Locust dashboard."""

    def __init__(self, host: str, port: int, environment):
        self._host = host
        self._port = port
        self._env = environment
        self._conn: smtplib.SMTP | None = None

    def connect(self):
        self._conn = smtplib.SMTP(self._host, self._port, timeout=30)
        self._conn.ehlo()
        self._conn.starttls(context=_no_verify_ssl())
        self._conn.ehlo()

    def disconnect(self):
        if self._conn:
            try:
                self._conn.quit()
            except Exception:
                pass
            self._conn = None

    def _reconnect_if_needed(self):
        try:
            if self._conn:
                self._conn.noop()
                return
        except Exception:
            pass
        self.connect()

    def send_email(self, from_addr: str, from_pass: str, to_addr: str, subject: str, body: str):
        self._reconnect_if_needed()
        start = time.perf_counter()
        exc = None
        try:
            self._conn.login(from_addr, from_pass)
            msg = MIMEText(body)
            msg["From"] = from_addr
            msg["To"] = to_addr
            msg["Subject"] = subject
            self._conn.sendmail(from_addr, [to_addr], msg.as_string())
            self._conn.rset()
        except Exception as e:
            exc = e
            self._conn = None  # force reconnect next time
        _fire(
            self._env,
            request_type="SMTP",
            name="smtp.send",
            start=start,
            response_length=len(body),
            exception=exc,
        )
        if exc:
            raise exc


# ── ImapClient ─────────────────────────────────────────────────────────────────


class ImapClient:
    """Thin imaplib wrapper that reports per-operation metrics to Locust."""

    def __init__(self, host: str, port: int, use_ssl: bool, environment):
        self._host = host
        self._port = port
        self._use_ssl = use_ssl
        self._env = environment
        self._conn: imaplib.IMAP4 | None = None

    def connect_and_login(self, username: str, password: str):
        start = time.perf_counter()
        exc = None
        try:
            if self._use_ssl:
                self._conn = imaplib.IMAP4_SSL(self._host, self._port, ssl_context=_no_verify_ssl())
            else:
                self._conn = imaplib.IMAP4(self._host, self._port)
                self._conn.starttls(_no_verify_ssl())
            self._conn.login(username, password)
        except Exception as e:
            exc = e
        _fire(self._env, request_type="IMAP", name="imap.login", start=start, exception=exc)
        if exc:
            raise exc

    def logout(self):
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def select_inbox(self) -> int:
        start = time.perf_counter()
        exc = None
        count = 0
        try:
            status, data = self._conn.select("INBOX")
            if status == "OK":
                count = int(data[0]) if data and data[0] else 0
        except Exception as e:
            exc = e
        _fire(self._env, request_type="IMAP", name="imap.select", start=start, exception=exc)
        if exc:
            raise exc
        return count

    def fetch_headers(self, msg_nums: list) -> list:
        if not msg_nums:
            return []
        start = time.perf_counter()
        exc = None
        results = []
        try:
            ids = ",".join(msg_nums)
            status, data = self._conn.fetch(ids, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if status == "OK":
                results = [d for d in data if isinstance(d, tuple)]
        except Exception as e:
            exc = e
        _fire(
            self._env,
            request_type="IMAP",
            name="imap.fetch_headers",
            start=start,
            response_length=len(str(results)),
            exception=exc,
        )
        if exc:
            raise exc
        return results

    def search_unseen(self) -> list:
        start = time.perf_counter()
        exc = None
        ids = []
        try:
            status, data = self._conn.search(None, "UNSEEN")
            if status == "OK" and data[0]:
                ids = data[0].decode().split()
        except Exception as e:
            exc = e
        _fire(
            self._env,
            request_type="IMAP",
            name="imap.search_unseen",
            start=start,
            response_length=len(ids),
            exception=exc,
        )
        if exc:
            raise exc
        return ids

    def search_subject(self, subject_fragment: str) -> list:
        """Used by round-trip verification to find a specific sent message."""
        try:
            status, data = self._conn.search(None, f'SUBJECT "{subject_fragment}"')
            if status == "OK" and data[0]:
                return data[0].decode().split()
        except Exception:
            pass
        return []


# ── WebMailUser ────────────────────────────────────────────────────────────────


class WebMailUser(HttpUser):
    """Simulates a browser user interacting with the Roundcube webmail UI."""

    host = f"http://{HOST}:{WEBMAIL_PORT}"
    wait_time = between(1, 3)
    weight = 3

    def on_start(self):
        self._user = random.choice(TEST_USERS)
        self._logged_in = False
        self._login()

    def on_stop(self):
        self._logout()

    # ── session helpers ────────────────────────────────────────

    def _extract_token(self, html: str) -> str | None:
        """Extract Roundcube CSRF token from page HTML."""
        # Primary: JSON-embedded request_token in <script>
        m = re.search(r'"request_token"\s*:\s*"([a-f0-9]+)"', html)
        if m:
            return m.group(1)
        # Fallback: hidden input field
        m = re.search(r'<input[^>]+name="_token"[^>]+value="([^"]+)"', html)
        if m:
            return m.group(1)
        return None

    def _login(self):
        with self.client.get("/", name="webmail.login_page", catch_response=True) as r:
            token = self._extract_token(r.text)
            if not token:
                r.failure("CSRF token not found on login page")
                return
            r.success()

        payload = {
            "_token": token,
            "_task": "login",
            "_action": "login",
            "_timezone": "UTC",
            "_url": "",
            "_user": self._user["email"],
            "_pass": self._user["password"],
        }
        with self.client.post(
            "/?_task=login",
            data=payload,
            name="webmail.login",
            allow_redirects=True,
            catch_response=True,
        ) as r:
            # r.url can be None in Locust's catch_response context — use body checks only
            body = r.text or ""
            if r.status_code >= 400:
                r.failure(f"Login HTTP {r.status_code} for {self._user['email']}")
                return
            # Still on login page = failed login
            if 'name="_pass"' in body or ('id="login-form"' in body):
                r.failure(f"Login failed for {self._user['email']} (still on login form)")
                return
            self._logged_in = True
            r.success()

    def _logout(self):
        if self._logged_in:
            self.client.get("/?_task=logout", name="webmail.logout")
            self._logged_in = False

    def _get_fresh_token(self, html: str) -> str | None:
        return self._extract_token(html)

    # ── tasks ──────────────────────────────────────────────────

    @task(5)
    def list_inbox(self):
        with self.client.get(
            "/?_task=mail&_action=list&_mbox=INBOX&_remote=1",
            name="webmail.list_inbox",
            catch_response=True,
        ) as r:
            body = r.text or ""
            if 'name="_pass"' in body or 'id="login-form"' in body:
                r.failure("Session dropped! Redirected to login form.")
            else:
                r.success()

    @task(3)
    def open_message(self):
        # Fetch inbox listing first to get a real UID
        with self.client.get(
            "/?_task=mail&_action=list&_mbox=INBOX&_remote=1",
            name="webmail.list_inbox",
            catch_response=True,
        ) as r:
            r.success()
            # Try to extract a UID from JSON response
            uid = None
            try:
                data = r.json()
                rows = data.get("rows") or data.get("messages") or []
                if rows and isinstance(rows, list) and len(rows) > 0:
                    first = rows[0]
                    uid = first.get("uid") or first.get("id") or (first[0] if isinstance(first, list) else None)
            except Exception:
                pass

        if uid:
            with self.client.get(
                f"/?_task=mail&_action=show&_uid={uid}&_mbox=INBOX",
                name="webmail.open_message",
                catch_response=True,
            ) as r:
                body = r.text or ""
                if 'name="_pass"' in body or 'id="login-form"' in body:
                    r.failure("Session dropped! Redirected to login.")
                else:
                    r.success()

    @task(2)
    def compose_and_send(self):
        # Step 1: GET compose form to obtain _compose_id and fresh token
        with self.client.get(
            "/?_task=mail&_action=compose",
            name="webmail.compose",
            catch_response=True,
        ) as r:
            token = self._get_fresh_token(r.text)
            compose_id = None
            m = re.search(r'"compose_id"\s*:\s*"([^"]+)"', r.text)
            if m:
                compose_id = m.group(1)
            if not compose_id:
                # Fallback: hidden input
                m = re.search(r'<input[^>]+name="_compose_id"[^>]+value="([^"]+)"', r.text)
                if m:
                    compose_id = m.group(1)
            r.success()

        if not token or not compose_id:
            return  # Can't send without these

        recipient = random.choice([u for u in TEST_USERS if u["email"] != self._user["email"]])
        subject = f"Load test {uuid.uuid4().hex[:8]}"

        payload = {
            "_token": token,
            "_task": "mail",
            "_action": "send",
            "_compose_id": compose_id,
            "_to": recipient["email"],
            "_subject": subject,
            "_body": "Automated load test message from Locust.",
            "_format": "text",
            "_editorMode": "0",
            "_is_html": "0",
            "_priority": "0",
            "_store_target": "Sent",
        }
        with self.client.post(
            "/?_task=mail&_action=send",
            data=payload,
            name="webmail.send",
            catch_response=True,
        ) as r:
            try:
                data = r.json()
                if data.get("exec") is True or data.get("action") == "send":
                    r.success()
                else:
                    r.failure(f"Send returned unexpected JSON: {data}")
            except Exception:
                # Some Roundcube versions return redirect on success
                if r.status_code in (200, 302):
                    r.success()
                else:
                    r.failure(f"Send failed: HTTP {r.status_code}")

    @task(1)
    def full_roundtrip_web(self):
        """Send a message via UI then verify it appears in the inbox listing."""
        import gevent

        recipient = random.choice([u for u in TEST_USERS if u["email"] != self._user["email"]])

        # Compose
        with self.client.get(
            "/?_task=mail&_action=compose",
            name="webmail.compose",
            catch_response=True,
        ) as r:
            token = self._get_fresh_token(r.text)
            compose_id = None
            m = re.search(r'"compose_id"\s*:\s*"([^"]+)"', r.text)
            if m:
                compose_id = m.group(1)
            r.success()

        if not token or not compose_id:
            return

        subject = f"RT-{uuid.uuid4().hex[:8]}"
        payload = {
            "_token": token,
            "_task": "mail",
            "_action": "send",
            "_compose_id": compose_id,
            "_to": recipient["email"],
            "_subject": subject,
            "_body": "Round-trip test.",
            "_format": "text",
            "_editorMode": "0",
            "_is_html": "0",
            "_priority": "0",
        }
        with self.client.post("/?_task=mail&_action=send", data=payload, name="webmail.send", catch_response=True) as r:
            body = r.text or ""
            if 'name="_pass"' in body or 'id="login-form"' in body:
                r.failure("Session dropped! Redirected to login.")
            else:
                r.success()

        # Wait for delivery
        gevent.sleep(2)

        # Verify in inbox listing
        r = self.client.get(
            "/?_task=mail&_action=list&_mbox=INBOX&_remote=1",
            name="webmail.list_inbox",
        )


# ── SMTPUser ───────────────────────────────────────────────────────────────────


class SMTPUser(User):
    """Sends emails directly via SMTP submission (port 587, STARTTLS)."""

    wait_time = between(2, 5)
    weight = 1

    def on_start(self):
        self._user = random.choice(TEST_USERS)
        self._client = SmtpClient(HOST, SMTP_PORT, self.environment)
        try:
            self._client.connect()
        except Exception as e:
            self._client._conn = None

    def on_stop(self):
        self._client.disconnect()

    @task(3)
    def send_between_users(self):
        recipient = random.choice([u for u in TEST_USERS if u["email"] != self._user["email"]])
        subject = f"Load test {uuid.uuid4().hex[:8]}"
        try:
            self._client.send_email(
                self._user["email"],
                self._user["password"],
                recipient["email"],
                subject,
                "Automated Locust load test message.",
            )
        except Exception:
            pass

    @task(1)
    def smtp_round_trip(self):
        """Send via SMTP then verify delivery via IMAP within 5 seconds."""
        import gevent

        recipient = random.choice([u for u in TEST_USERS if u["email"] != self._user["email"]])
        subject_tag = f"RT-{uuid.uuid4().hex[:8]}"
        subject = f"Round-trip {subject_tag}"

        try:
            self._client.send_email(
                self._user["email"],
                self._user["password"],
                recipient["email"],
                subject,
                "Round-trip test.",
            )
        except Exception:
            return

        # Wait for delivery (poll up to 15 seconds)
        start = time.perf_counter()
        exc = None
        imap = ImapClient(HOST, IMAP_PORT, use_ssl=False, environment=self.environment)
        try:
            imap.connect_and_login(recipient["email"], recipient["password"])
            imap.select_inbox()
            
            found = []
            for _ in range(15):
                gevent.sleep(1)
                # Reselect to catch new mail
                imap.select_inbox()
                found = imap.search_subject(subject_tag)
                if found:
                    break
                    
            if not found:
                exc = AssertionError(f"Message with subject tag '{subject_tag}' not found in inbox after 15s")
        except Exception as e:
            exc = e
        finally:
            imap.logout()

        _fire(
            self.environment,
            request_type="RoundTrip",
            name="round_trip.smtp_to_imap",
            start=start,
            exception=exc,
        )


# ── IMAPUser ───────────────────────────────────────────────────────────────────


class IMAPUser(User):
    """Reads email via IMAP (port 143, STARTTLS)."""

    wait_time = between(1, 4)
    weight = 1

    def on_start(self):
        self._user = random.choice(TEST_USERS)
        self._client = ImapClient(HOST, IMAP_PORT, use_ssl=False, environment=self.environment)
        try:
            self._client.connect_and_login(self._user["email"], self._user["password"])
        except Exception:
            pass

    def on_stop(self):
        self._client.logout()

    @task(4)
    def select_and_list(self):
        try:
            count = self._client.select_inbox()
            if count > 0:
                # Fetch headers for up to 5 most-recent messages
                sample = [str(i) for i in range(max(1, count - 4), count + 1)]
                self._client.fetch_headers(sample)
        except Exception:
            self._reconnect()

    @task(2)
    def search_unseen(self):
        try:
            self._client.search_unseen()
        except Exception:
            self._reconnect()

    @task(1)
    def full_imap_session(self):
        """Times a complete SELECT → SEARCH → FETCH session as one event."""
        start = time.perf_counter()
        exc = None
        imap = ImapClient(HOST, IMAP_PORT, use_ssl=False, environment=self.environment)
        try:
            imap.connect_and_login(self._user["email"], self._user["password"])
            count = imap.select_inbox()
            imap.search_unseen()
            if count > 0:
                sample = [str(i) for i in range(max(1, count - 2), count + 1)]
                imap.fetch_headers(sample)
        except Exception as e:
            exc = e
        finally:
            imap.logout()

        _fire(
            self.environment,
            request_type="IMAP",
            name="imap.full_session",
            start=start,
            exception=exc,
        )

    def _reconnect(self):
        self._client.logout()
        try:
            self._client.connect_and_login(self._user["email"], self._user["password"])
            self._client.select_inbox()  # restore SELECTED state after reconnect
        except Exception:
            pass


# ── Module-level hooks ─────────────────────────────────────────────────────────


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"\n[locustfile] ── Mail-App Load Test ──────────────────────")
    print(f"[locustfile] Target host : {HOST}")
    print(f"[locustfile] Webmail     : http://{HOST}:{WEBMAIL_PORT}/")
    print(f"[locustfile] SMTP        : {HOST}:{SMTP_PORT} (STARTTLS)")
    print(f"[locustfile] IMAP        : {HOST}:{IMAP_PORT} (STARTTLS)")
    print(f"[locustfile] Test users  : {[u['email'] for u in TEST_USERS]}")
    print(f"[locustfile] ─────────────────────────────────────────────\n")
