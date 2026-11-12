import html
import hashlib
import hmac
import sqlite3
import time
import json
import mimetypes
import os
import re
import secrets
import sys
import threading
import smtplib
from email.message import EmailMessage
from http.cookies import SimpleCookie
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, time as datetime_time, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import parse_qs, quote, unquote, urlsplit
import classroom
from teacher_plan import ai_access_allowed, teacher_plan_message
ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '3000'))
HOST = os.environ.get('HOST', '0.0.0.0')
PUB = ROOT / 'public'
SESSION_COOKIE = 'jeenius_session'
AUTH_DB = ROOT / 'jeenius_auth.sqlite3'
PASSWORD_ITERATIONS = 310000
SESSION_SHORT_SECONDS = 8 * 60 * 60
SESSION_REMEMBER_SECONDS = 30 * 24 * 60 * 60
DEFAULT_DAILY_RESPONSE_LIMIT = 20
QUOTA_TZ = ZoneInfo('Asia/Kolkata')
try:
    from genie import SYSTEM_PROMPT, ANIMATION_OBSERVATION_PROMPT
    from behavior import buildBehaviorPrompt
except ImportError as exc:
    raise ImportError('Required Python modules are missing or failed to import. Ensure genie.py defines SYSTEM_PROMPT and ANIMATION_OBSERVATION_PROMPT, and behavior.py defines buildBehaviorPrompt(availableLabs), and place them beside server.py.') from exc

def env():
    """Read .env for local development, then override it with real environment variables."""
    values = {}
    env_path = ROOT / ".env"
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key:
                values[key] = value
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"[env] Failed to read .env: {exc}", file=sys.stderr)
    values.update(os.environ)
    return values


_runtime_config = env()
PORT = int(_runtime_config.get("PORT", str(PORT)))
HOST = _runtime_config.get("HOST", HOST)


class _PostgresConnection:
    """Compatibility wrapper for the existing sqlite-style connection calls."""
    def __init__(self, connection):
        self._connection = connection

    @staticmethod
    def _convert_placeholders(sql):
        return sql.replace("?", "%s")

    def execute(self, sql, params=()):
        try:
            return self._connection.execute(self._convert_placeholders(sql), params)
        except Exception as exc:
            try:
                import psycopg
                if isinstance(exc, psycopg.IntegrityError):
                    raise sqlite3.IntegrityError(str(exc)) from exc
            except ImportError:
                pass
            raise

    def executescript(self, script):
        for statement in script.split(";"):
            statement = statement.strip()
            if statement:
                self.execute(statement)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def _db_connect():
    """Use PostgreSQL in hosted environments, or SQLite for local development."""
    config = env()
    database_url = config.get("DATABASE_URL", "").strip()
    if database_url:
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError("DATABASE_URL is set but psycopg is missing. Install requirements.txt.") from exc
        connection = psycopg.connect(database_url, row_factory=dict_row, connect_timeout=15)
        return _PostgresConnection(connection)

    database_path = Path(config.get("SQLITE_PATH", str(AUTH_DB))).expanduser()
    if not database_path.is_absolute():
        database_path = ROOT / database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(database_path), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_auth_db():
    """Create the persistent auth tables if they do not exist yet."""
    conn = _db_connect()
    try:
        conn.executescript('\n\n            CREATE TABLE IF NOT EXISTS users (\n\n                id TEXT PRIMARY KEY,\n\n                email TEXT NOT NULL UNIQUE,\n\n                name TEXT NOT NULL,\n\n                password_hash TEXT,\n\n                google_sub TEXT UNIQUE,\n\n                picture TEXT,\n\n                created_at BIGINT NOT NULL,\n\n                updated_at BIGINT NOT NULL\n\n            );\n\n            CREATE TABLE IF NOT EXISTS auth_sessions (\n\n                token_hash TEXT PRIMARY KEY,\n\n                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n\n                expires_at BIGINT NOT NULL,\n\n                created_at BIGINT NOT NULL\n\n            );\n\n            CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);\n\n            CREATE TABLE IF NOT EXISTS user_daily_usage (\n                user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,\n                usage_date TEXT NOT NULL,\n                response_count INTEGER NOT NULL DEFAULT 0,\n                reserved_count INTEGER NOT NULL DEFAULT 0,\n                PRIMARY KEY (user_id, usage_date)\n            );\n\n        ')
        conn.execute("CREATE TABLE IF NOT EXISTS app_settings (setting_key TEXT PRIMARY KEY, setting_value TEXT NOT NULL DEFAULT '', updated_at BIGINT NOT NULL DEFAULT 0)")
        # Portable schema migration for both PostgreSQL and SQLite.
        new_columns = {
            'email_verified': 'INTEGER NOT NULL DEFAULT 0',
            'admin_approved': 'INTEGER NOT NULL DEFAULT 0',
            'age_verified': 'INTEGER NOT NULL DEFAULT 0',
            'age_category': 'TEXT',
            'age_verification_id': 'TEXT',
            'age_verification_url': 'TEXT',
            'age_verified_at': 'BIGINT',
            'age_provider': 'TEXT',
            'age_consent_at': 'BIGINT',
            'age_consent_version': 'TEXT',
            'parent_email': 'TEXT',
            'parent_email_verified': 'INTEGER NOT NULL DEFAULT 0',
            'parent_email_otp_hash': 'TEXT',
            'parent_email_otp_expires_at': 'BIGINT',
            'parent_email_otp_attempts': 'INTEGER NOT NULL DEFAULT 0',
            'parent_email_otp_last_sent_at': 'BIGINT NOT NULL DEFAULT 0',
            'parent_phone_hash': 'TEXT',
            'parent_phone_last4': 'TEXT',
            'parent_phone_verified': 'INTEGER NOT NULL DEFAULT 0',
            'parent_sms_otp_hash': 'TEXT',
            'parent_sms_otp_expires_at': 'BIGINT',
            'parent_sms_otp_attempts': 'INTEGER NOT NULL DEFAULT 0',
            'parent_sms_otp_last_sent_at': 'BIGINT NOT NULL DEFAULT 0',
            'parent_consent_at': 'BIGINT',
            'otp_hash': 'TEXT',
            'otp_expires_at': 'BIGINT',
            'otp_attempts': 'INTEGER NOT NULL DEFAULT 0',
            'otp_last_sent_at': 'BIGINT NOT NULL DEFAULT 0',
            'subscription_status': "TEXT NOT NULL DEFAULT 'inactive'",
            'account_role': 'TEXT',
            'standard': 'TEXT',
            'daily_response_limit': 'INTEGER NOT NULL DEFAULT 20',
            'reset_otp_hash': 'TEXT',
            'reset_otp_expires_at': 'BIGINT',
            'reset_otp_attempts': 'INTEGER NOT NULL DEFAULT 0',
            'reset_otp_last_sent_at': 'BIGINT NOT NULL DEFAULT 0',
            'student_code': 'TEXT',
        }
        if env().get('DATABASE_URL', '').strip():
            found = {r['column_name'] for r in conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
            ).fetchall()}
        else:
            found = {r['name'] for r in conn.execute('PRAGMA table_info(users)').fetchall()}
        for column, definition in new_columns.items():
            if column not in found:
                conn.execute(f'ALTER TABLE users ADD COLUMN {column} {definition}')
        conn.commit()
        classroom.ensure_schema(conn)
    finally:
        conn.close()

def _quota_day_and_reset():
    """Return today's date and the next midnight in India Standard Time."""
    now = datetime.now(QUOTA_TZ)
    next_midnight = datetime.combine(now.date() + timedelta(days=1), datetime_time.min, tzinfo=QUOTA_TZ)
    reset_label = f"{next_midnight.strftime('%I:%M %p IST')} on {next_midnight.strftime('%B')} {next_midnight.day}"
    return now.date().isoformat(), next_midnight.isoformat(), reset_label

def _daily_quota_status(user_id, usage_date=None):
    """Return an account-specific daily AI quota and its midnight IST reset."""
    today, _, _ = _quota_day_and_reset()
    usage_date = usage_date or today
    reset_midnight = datetime.combine(
        datetime.fromisoformat(usage_date).date() + timedelta(days=1),
        datetime_time.min,
        tzinfo=QUOTA_TZ,
    )
    reset_at = reset_midnight.isoformat()
    reset_label = f"{reset_midnight.strftime('%I:%M %p IST')} on {reset_midnight.strftime('%B')} {reset_midnight.day}"
    conn = _db_connect()
    try:
        account = conn.execute('SELECT daily_response_limit FROM users WHERE id = ?', (user_id,)).fetchone()
        try:
            limit = int(account['daily_response_limit']) if account is not None else DEFAULT_DAILY_RESPONSE_LIMIT
        except (KeyError, TypeError, ValueError, IndexError):
            limit = DEFAULT_DAILY_RESPONSE_LIMIT
        limit = max(0, min(1000, limit))
        row = conn.execute(
            'SELECT response_count, reserved_count FROM user_daily_usage WHERE user_id = ? AND usage_date = ?',
            (user_id, usage_date),
        ).fetchone()
        used = (int(row['response_count']) + int(row['reserved_count'])) if row else 0
        return {
            'limit': limit,
            'used': min(used, limit),
            'remaining': max(0, limit - used),
            'reset_at': reset_at,
            'reset_label': reset_label,
            'timezone': 'Asia/Kolkata',
        }
    finally:
        conn.close()

def _reserve_daily_response(user_id):
    """Atomically reserve a response slot using the user's current admin-assigned limit."""
    usage_date, _, _ = _quota_day_and_reset()
    conn = _db_connect()
    try:
        account = conn.execute('SELECT daily_response_limit FROM users WHERE id = ?', (user_id,)).fetchone()
        try:
            limit = int(account['daily_response_limit']) if account is not None else DEFAULT_DAILY_RESPONSE_LIMIT
        except (KeyError, TypeError, ValueError, IndexError):
            limit = DEFAULT_DAILY_RESPONSE_LIMIT
        limit = max(0, min(1000, limit))
        row = conn.execute(
            """INSERT INTO user_daily_usage (user_id, usage_date, response_count, reserved_count)
               VALUES (?, ?, 0, 1)
               ON CONFLICT (user_id, usage_date) DO UPDATE
               SET reserved_count = user_daily_usage.reserved_count + 1
               WHERE user_daily_usage.response_count + user_daily_usage.reserved_count < ?
               RETURNING response_count, reserved_count""",
            (user_id, usage_date, limit),
        ).fetchone()
        conn.commit()
        if row is None:
            return None, usage_date
        return usage_date, usage_date
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _finish_daily_response(user_id, usage_date, succeeded):
    """Release the reservation and count the slot only when a response was produced."""
    conn = _db_connect()
    try:
        conn.execute(
            """UPDATE user_daily_usage
               SET reserved_count = CASE WHEN reserved_count > 0 THEN reserved_count - 1 ELSE 0 END,
                   response_count = response_count + ?
               WHERE user_id = ? AND usage_date = ?""",
            (1 if succeeded else 0, user_id, usage_date),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def _public_user(row):
    if row is None:
        return None
    def truthy(key):
        try:
            return bool(row[key])
        except (KeyError, IndexError):
            return False
    try:
        age_category = row['age_category']
    except (KeyError, IndexError):
        age_category = None
    try:
        subscription_status = row['subscription_status']
    except (KeyError, IndexError):
        subscription_status = 'inactive'
    return {
        'id': row['id'], 'name': row['name'], 'email': row['email'], 'picture': row['picture'],
        'email_verified': truthy('email_verified'), 'admin_approved': truthy('admin_approved'),
        'age_verified': truthy('age_verified'), 'age_category': age_category,
        'parent_email_verified': truthy('parent_email_verified'),
        'parent_email': row['parent_email'] if 'parent_email' in row.keys() else None,
        'subscription_status': subscription_status,
        'account_role': row['account_role'] if 'account_role' in row.keys() else None,
        'standard': row['standard'] if 'standard' in row.keys() else None,
        'daily_response_limit': int(row['daily_response_limit']) if 'daily_response_limit' in row.keys() and row['daily_response_limit'] is not None else DEFAULT_DAILY_RESPONSE_LIMIT,
    }

def _admin_emails():
    return {item.strip().lower() for item in env().get('ADMIN_EMAILS', '').split(',') if item.strip()}

def _is_admin(user):
    return bool(user and _normalize_email(user.get('email')) in _admin_emails())

def _account_ready(user):
    # Require verified sign-in email, completed self-declared age/contact step,
    # admin approval, and the profile context used to personalise AI replies.
    return bool(
        user and user.get('email_verified') and user.get('age_verified')
        and user.get('admin_approved') and str(user.get('name') or '').strip()
        and str(user.get('standard') or '').strip()
        and user.get('account_role') in ('teacher', 'learner')
    )

def _otp_digest(email, code):
    cfg = env()
    # OTP_PEPPER is recommended, but a missing value must never block sign-ups. Fall back to
    # another server-side secret so codes are still salted with something an attacker cannot see.
    pepper = (cfg.get('OTP_PEPPER') or cfg.get('SECRET_KEY') or cfg.get('FLASK_SECRET_KEY')
              or cfg.get('DATABASE_URL') or cfg.get('GOOGLE_CLIENT_ID') or 'jeenius-dev-otp-pepper')
    return hashlib.sha256((pepper + ':' + _normalize_email(email) + ':' + str(code)).encode('utf-8')).hexdigest()

def _dev_otp_enabled():
    cfg = env()
    return cfg.get('DEV_SHOW_OTP', '').strip().lower() in ('1', 'true', 'yes') and not _mail_provider(cfg)

def _mail_provider(config=None):
    """Return 'brevo', 'resend', 'smtp' or '' depending on which delivery settings are present."""
    config = config or env()
    sender = (config.get('MAIL_FROM') or config.get('SMTP_FROM') or '').strip()
    if config.get('BREVO_API_KEY', '').strip() and sender:
        return 'brevo'
    password = config.get('SMTP_PASSWORD', '')
    if config.get('SMTP_HOST') and config.get('SMTP_USER') and password and sender:
        host = config.get('SMTP_HOST', '').strip().lower()
        return 'resend' if (host == 'smtp.resend.com' and password.startswith('re_')) else 'smtp'
    return ''

def _email_configured():
    return bool(_mail_provider() or _dev_otp_enabled())

def _http_json(url, headers, payload):
    request = urllib.request.Request(url, data=json.dumps(payload, separators=(',', ':')).encode('utf-8'),
                                     headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(65537)
            if response.status < 200 or response.status >= 300:
                raise RuntimeError('Email provider rejected the request (HTTP %s).' % response.status)
            return json.loads(raw.decode('utf-8') or '{}')
    except urllib.error.HTTPError as exc:
        detail = ''
        try:
            data = json.loads(exc.read(8192).decode('utf-8', errors='replace'))
            detail = str(data.get('message') or data.get('name') or data.get('error') or '')[:240]
        except Exception:
            pass
        raise RuntimeError('Email provider rejected the request (HTTP %s)%s' % (exc.code, ': ' + detail if detail else '')) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Could not reach the email provider over HTTPS.') from None

def _split_sender(sender):
    match = re.match(r'^\s*(.*?)\s*<([^<>]+)>\s*$', sender)
    return ((match.group(1).strip('"') or 'JEENIUS'), match.group(2).strip()) if match else ('JEENIUS', sender.strip())

def _send_email_message(to_email, subject, body):
    """Send mail over HTTPS (Brevo or Resend) or SMTP.

    Render's free web services block outbound SMTP ports 25/465/587, so on Render use
    BREVO_API_KEY (works with a single verified sender, no domain needed) or Resend over HTTPS.
    """
    config = env()
    provider = _mail_provider(config)
    if not provider:
        if _dev_otp_enabled():
            print('[auth] DEV_SHOW_OTP enabled; email was not sent (development only).', file=sys.stderr)
            return
        raise RuntimeError('Email delivery is not configured.')
    sender = (config.get('MAIL_FROM') or config.get('SMTP_FROM') or config.get('SMTP_USER') or '').strip()
    if provider == 'brevo':
        name, address = _split_sender(sender)
        result = _http_json('https://api.brevo.com/v3/smtp/email', {
            'api-key': config.get('BREVO_API_KEY', '').strip(), 'Content-Type': 'application/json', 'Accept': 'application/json',
        }, {'sender': {'name': name, 'email': address}, 'to': [{'email': to_email}], 'subject': subject, 'textContent': body})
        if not isinstance(result, dict) or not result.get('messageId'):
            raise RuntimeError('Brevo did not confirm that the email was accepted.')
        return
    if provider == 'resend':
        result = _http_json('https://api.resend.com/emails', {
            'Authorization': 'Bearer ' + config.get('SMTP_PASSWORD', ''), 'Content-Type': 'application/json', 'Accept': 'application/json',
        }, {'from': sender, 'to': [to_email], 'subject': subject, 'text': body})
        if not isinstance(result, dict) or not result.get('id'):
            raise RuntimeError('Resend did not confirm that the email was accepted.')
        return
    host = config.get('SMTP_HOST', '').strip()
    user = config.get('SMTP_USER', '').strip()
    password = config.get('SMTP_PASSWORD', '')
    port = int(config.get('SMTP_PORT', '587'))
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = sender
    message['To'] = to_email
    message.set_content(body)
    if port in (465, 2465):
        with smtplib.SMTP_SSL(host, port, timeout=20) as smtp:
            smtp.login(user, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(message)

OTP_RESEND_SECONDS = 60

def _issue_email_otp(user_id, email, allow_immediate=False, purpose='verify'):
    """Create and email a 6-digit code. purpose is 'verify' (sign-up) or 'reset' (forgot password)."""
    prefix = 'reset_otp' if purpose == 'reset' else 'otp'
    now = int(time.time())
    conn = _db_connect()
    try:
        row = conn.execute(f'SELECT {prefix}_last_sent_at AS last_sent, email_verified FROM users WHERE id = ?', (user_id,)).fetchone()
        if row is None:
            return False, 'Account not found.', None
        if purpose == 'verify' and row['email_verified']:
            return True, 'Email already verified.', None
        wait = OTP_RESEND_SECONDS - (now - int(row['last_sent'] or 0))
        if not allow_immediate and wait > 0:
            return False, f'Please wait {wait} seconds before requesting another code.', None
        code = f'{secrets.randbelow(1_000_000):06d}'
        conn.execute(
            f'UPDATE users SET {prefix}_hash = ?, {prefix}_expires_at = ?, {prefix}_attempts = 0, {prefix}_last_sent_at = ?, updated_at = ? WHERE id = ?',
            (_otp_digest(email, code), now + 600, now, now, user_id),
        )
        conn.commit()
    finally:
        conn.close()
    what = 'password reset' if purpose == 'reset' else 'email verification'
    try:
        _send_email_message(email, f'Your JEENIUS {what} code',
            f'Your JEENIUS {what} code is: {code}\n\nIt expires in 10 minutes. Do not share this code with anyone. If you did not request it, you can ignore this email.')
    except Exception as exc:
        conn = _db_connect()
        try:
            conn.execute(f'UPDATE users SET {prefix}_hash = NULL, {prefix}_expires_at = NULL, {prefix}_last_sent_at = 0 WHERE id = ?', (user_id,))
            conn.commit()
        finally:
            conn.close()
        print(f'[email] Could not send {what} email: {exc}', file=sys.stderr)
        return False, 'We could not send the email code. Please check the email settings on the server and try again.', None
    return True, 'A 6-digit code was sent to your email. Check spam/promotions if you cannot see it.', (code if _dev_otp_enabled() else None)

# Simple in-memory throttle for password guessing (per email + client address).
_LOGIN_FAILURES = {}
_LOGIN_LOCK = threading.Lock()

def _login_throttled(key):
    now = time.time()
    with _LOGIN_LOCK:
        recent = [t for t in _LOGIN_FAILURES.get(key, []) if now - t < 900]
        _LOGIN_FAILURES[key] = recent
        return len(recent) >= 8

def _login_failed(key):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.setdefault(key, []).append(time.time())
        if len(_LOGIN_FAILURES) > 5000:
            _LOGIN_FAILURES.clear()

def _login_ok(key):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(key, None)

def _normalize_email(value):
    return str(value or '').strip().lower()

def _hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PASSWORD_ITERATIONS)
    return f'pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}'

def _verify_password(password, encoded):
    try:
        scheme, rounds, salt_hex, digest_hex = encoded.split('$', 3)
        if scheme != 'pbkdf2_sha256':
            return False
        rounds = int(rounds)
        if rounds < 100000 or rounds > 2000000:
            return False
        digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt_hex), rounds)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError, AttributeError):
        return False

def _safe_local_path(value, fallback='/'):
    """Only allow relative paths on this same site, preventing open redirects."""
    if not isinstance(value, str):
        return fallback
    value = value.strip()
    if not value.startswith('/') or value.startswith('//') or '\\' in value:
        return fallback
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return fallback
    return parsed.path + ('?' + parsed.query if parsed.query else '') + ('#' + parsed.fragment if parsed.fragment else '')

def _create_auth_session(user_id, remember=True):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    now = int(time.time())
    max_age = SESSION_REMEMBER_SECONDS if remember else SESSION_SHORT_SECONDS
    conn = _db_connect()
    try:
        conn.execute('DELETE FROM auth_sessions WHERE expires_at <= ?', (now,))
        conn.execute('INSERT INTO auth_sessions(token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)', (token_hash, user_id, now + max_age, now))
        conn.commit()
    finally:
        conn.close()
    return (token, max_age)

def _cookie_secure_enabled():
    config = env()
    explicit = config.get("COOKIE_SECURE")
    if explicit is not None:
        return explicit.strip().lower() in ("1", "true", "yes")
    return bool(config.get("RENDER") or config.get("RAILWAY_PUBLIC_DOMAIN") or config.get("PUBLIC_BASE_URL", "").startswith("https://"))


def _session_cookie(token, max_age):
    secure = "; Secure" if _cookie_secure_enabled() else ""
    return f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={int(max_age)}{secure}"


def _clear_session_cookie():
    secure = "; Secure" if _cookie_secure_enabled() else ""
    return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0{secure}"

def labs():
    """Return the JSON lab catalogue reconciled against folders that actually ship.

    Any public/animations/<folder>/index.html is surfaced even if someone forgot
    to add it to labs.json. A lab is not marked available when its index file is
    absent, preventing the chat from recommending broken links.
    """
    with (PUB / 'labs.json').open('r', encoding='utf-8') as handle:
        raw = json.load(handle)
    items = [dict(item) for item in raw if isinstance(item, dict) and item.get('id')]
    by_id = {str(item['id']): item for item in items}
    animation_root = PUB / 'animations'
    actual_dirs = {}
    if animation_root.is_dir():
        for folder in sorted(animation_root.iterdir(), key=lambda x: x.name.lower()):
            if not folder.is_dir() or folder.name.startswith('_') or not (folder / 'index.html').is_file():
                continue
            actual_dirs[folder.name] = folder
    # If a listed lab has a real index page, it is available regardless of stale JSON flags.
    for item in items:
        folder = actual_dirs.get(str(item['id']))
        item['available'] = bool(folder)
    # Add any uploaded animation folder that is not yet in labs.json.
    for lab_id, folder in actual_dirs.items():
        if lab_id in by_id:
            continue
        slug = re.sub(r'^\d+[-_ ]*', '', lab_id)
        title = re.sub(r'[-_]+', ' ', slug).strip().title() or lab_id.title()
        lower = title.lower()
        if any(word in lower for word in ('equation', 'triangle', 'ratio', 'geometry', 'factor', 'indices', 'polynomial', 'interest', 'discount', 'area', 'volume', 'coordinate', 'number', 'quadrilateral', 'variation', 'statistics', 'trigonometric', 'pythagoras', 'congruence', 'median', 'algebra')):
            subject = 'MATH'
        elif any(word in lower for word in ('cell', 'plant', 'microbe', 'digestion', 'respiration', 'excretion', 'heredity', 'biotechnology', 'organ', 'disease', 'environment', 'pollution', 'matter', 'carbon', 'acid', 'metal', 'atom', 'periodic', 'chemical', 'substance', 'star', 'solar', 'ecosystem', 'free fall', 'force', 'motion', 'gravity', 'electric', 'magnet', 'heat', 'sound', 'light', 'telescope', 'lever', 'battery')):
            subject = 'PHY' if any(word in lower for word in ('free fall', 'force', 'motion', 'gravity', 'electric', 'magnet', 'heat', 'sound', 'light', 'telescope', 'lever', 'battery', 'star', 'solar')) else 'SCI'
        else:
            subject = 'OTHER'
        item = {
            'id': lab_id,
            'title': title,
            'subject': subject,
            'class': '8–9',
            'tryThis': f'Explore the interactive {title} animation.',
            'available': True,
        }
        items.append(item)
        by_id[lab_id] = item
    return items
cleanSystemPersona = '\n\nYou are Geini, a friendly, clear-thinking science tutor for\n\nClasses 8 and 9, following the Maharashtra State Board syllabus.\n\nMANDATORY LANGUAGE RULES:\n\n1. Respond ONLY in natural Hinglish using Roman script or in English.\n\n2. NEVER use Devanagari script, even when the student writes in Hindi.\n\n3. NEVER generate pure Hindi or formal Hindi sentences.\n\n4. Default to natural Roman-script Hinglish.\n\n5. Use English for scientific concepts, definitions, formulas,\n\n   reasoning, and technical terminology.\n\n6. Explain concepts conversationally using natural Hindi in Roman\n\n   script mixed with English.\n\n7. If the student explicitly requests English, respond entirely\n\n   in English.\n\n8. Before responding, check that no Devanagari characters appear.\n\n   Rewrite any such text in Roman-script Hinglish.\n\nSTYLE:\n\n- Be warm, friendly, accurate, and engaging, like a favourite teacher.\n\n- Give complete, well-explained answers. There is NO length limit: use as many lines as the topic needs.\n\n- Explain step by step with simple real-life examples and analogies, then summarise the key idea.\n\n- Use relevant emojis naturally (for example \U0001F9EA \u26A1 \U0001F331 \U0001F680 \u2705) to make explanations lively, without overdoing it.\n\n- Use familiar terms such as force, motion, velocity,\n\n  acceleration, distance, displacement, and resistance.\n\n- Avoid repetitive slang and unnecessary introductions.\n\nSCIENCE TUTOR RULES:\n\n- Keep explanations appropriate for Classes 8-10.\n\n- Never output source code, HTML, CSS, JavaScript, or file paths\n\n  in response to ordinary student questions.\n\n- For lab or animation questions, explain the science and guide\n\n  the student to the relevant interactive lab.\n\n- For JEE, NEET, CA, or Class 11-12 preparation, politely redirect\n\n  the student toward strengthening school-level foundations.\n\nOUTPUT FORMATTING:\n\n- Use standard Markdown for headings, lists, tables, and formulas.\n\n- Do not put Markdown formatting inside unnecessary code blocks.\n\n- Do not output raw HTML.\n\n- Keep formatting simple and readable.\n\n'

def getSmartLocalFallback(text, studentName):
    """Local fallback responses preserved from the JavaScript source."""
    t = text.lower()
    if 'force' in t or 'pressure' in t:
        return f"Hey {studentName}! Force is a push or pull that changes an object's state of motion. Pressure is force acting per unit area ($P = F/A$). Check out the interactive Force & Pressure lab on your screen to see how area affects pressure!"
    elif any((word in t for word in ('motion', 'speed', 'newton', 'velocity'))):
        return f"Hi {studentName}! Newton's laws govern how objects move. According to the Second Law, force equals mass times acceleration ($F = ma$). You can explore the Laws of Motion lab workspace right now!"
    elif any((word in t for word in ('electricity', 'current', 'ohm', 'circuit'))):
        return f"Hey {studentName}! Electric current is the rate of flow of charge ($I = Q/t$), and Ohm's Law states that voltage equals current times resistance ($V = IR$). Try out circuit components in our Current Electricity lab!"
    elif any((word in t for word in ('acid', 'base', 'salt'))):
        return f'Hi {studentName}! Acids turn blue litmus red, while bases turn red litmus blue. When they react together, neutralisation forms salt and water!'
    elif any((word in t for word in ('cell', 'organelle', 'biology'))):
        return f'Hey {studentName}! The cell is the basic building block of life. Mitochondria produce energy, while the nucleus acts as the control center of the cell.'
    return f'Hey {studentName}! I am Geini, your interactive science assistant. Our primary cloud node is under high demand, but I am ready to guide you through Class 8-10 physics, chemistry, and biology! What concept shall we learn next?'

def _post_json(url, headers, payload, timeout=20):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    # Cloudflare-protected APIs reject urllib's default "Python-urllib" agent with 403 / error 1010.
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; JEENIUS/1.0; +https://jeenius.app)', 'Accept': 'application/json', **headers}
    request = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'HTTP {exc.code}: {details}') from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Network error: {exc.reason}') from exc
    except TimeoutError as exc:
        raise RuntimeError('Request timed out') from exc

# Output-size settings. Chat has no practical length cap; observations are tiny.
CHAT_PARAMS = {'max_tokens': 4096, 'temperature': 0.7}
OBSERVATION_PARAMS = {'max_tokens': 200, 'temperature': 0.2}

def _chat_content(data, provider):
    """Safely pull text out of an OpenAI-style response (content can be None or a list)."""
    choices = data.get('choices') or []
    content = (choices[0].get('message') or {}).get('content') if choices else None
    if isinstance(content, list):
        content = ''.join(str(p.get('text', '')) if isinstance(p, dict) else str(p) for p in content)
    reply = (content or '').strip()
    if not reply:
        finish = choices[0].get('finish_reason') if choices else 'no choices'
        raise RuntimeError(f'{provider} returned an empty response (finish_reason: {finish})')
    return reply

def _gemini_keys(E):
    """Gemini key 1 -> key 2 -> key 3 (duplicates skipped)."""
    keys = [
        ('Gemini Key 1', E.get('GEMINI_API_KEY_1') or E.get('GEMINI_API_KEY1') or E.get('GEMINI_KEY_1') or E.get('GEMINI_API_KEY')),
        ('Gemini Key 2', E.get('GEMINI_API_KEY_2') or E.get('GEMINI_API_KEY2') or E.get('GEMINI_KEY_2')),
        ('Gemini Key 3', E.get('GEMINI_API_KEY_3') or E.get('GEMINI_API_KEY3') or E.get('GEMINI_KEY_3')),
    ]
    seen, out = set(), []
    for label, key in keys:
        if key and key not in seen:
            seen.add(key)
            out.append((label, key))
    return out

def callGemini(model, key, sys_prompt, hist, text, params=None):
    if not key:
        raise RuntimeError('Gemini API key is not configured')
    params = params or CHAT_PARAMS
    contents = []
    for item in hist:
        contents.append({'role': 'user' if item['role'] == 'user' else 'model', 'parts': [{'text': item['content']}]})
    contents.append({'role': 'user', 'parts': [{'text': text}]})
    payload = {'systemInstruction': {'parts': [{'text': sys_prompt}]}, 'contents': contents,
               'generationConfig': {'maxOutputTokens': params['max_tokens'], 'temperature': params['temperature']}}
    data = _post_json(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                      {'content-type': 'application/json', 'x-goog-api-key': key}, payload, timeout=25)
    candidates = data.get('candidates') or [{}]
    parts = (candidates[0].get('content') or {}).get('parts') or []
    reply = ''.join((part.get('text', '') for part in parts)).strip()
    if not reply:
        # Empty / safety-blocked / token-exhausted answers must NOT stop the chain.
        reason = candidates[0].get('finishReason') or (data.get('promptFeedback') or {}).get('blockReason') or 'unknown'
        raise RuntimeError(f'Gemini returned an empty response (reason: {reason})')
    return reply

# Open model on OpenRouter. NVIDIA Nemotron 3 Ultra (550B MoE, 1M context, up to 65k output tokens).
# Override with OPENROUTER_MODEL / OPENROUTER_FALLBACK_MODEL in .env if OpenRouter rotates the free list.
OPENROUTER_DEFAULT_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b:free'
OPENROUTER_DEFAULT_BACKUP = 'nvidia/nemotron-3.5-super-vl:free'

def callOpenRouter(key, sys_prompt, hist, text, params=None):
    """Open-model fallback after the three Gemini keys. Retries rate limits / server errors."""
    if not key:
        raise RuntimeError('OPENROUTER_API_KEY is not configured')
    params = params or CHAT_PARAMS
    config = env()
    primary = (config.get('OPENROUTER_MODEL') or OPENROUTER_DEFAULT_MODEL).strip()
    backup = (config.get('OPENROUTER_FALLBACK_MODEL') or OPENROUTER_DEFAULT_BACKUP).strip()
    messages = [{'role': 'system', 'content': sys_prompt}]
    messages.extend(hist[-4:])
    messages.append({'role': 'user', 'content': text})
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key, 'X-OpenRouter-Title': 'JEENIUS'}
    site = config.get('PUBLIC_BASE_URL', '').strip()
    if site.startswith('https://'):
        headers['HTTP-Referer'] = site

    attempts = [primary, primary] + ([backup] if backup and backup != primary else [])
    last_exc = None
    for i, model in enumerate(attempts):
        if i == 1:
            time.sleep(1.5)  # brief pause before retrying a busy free pool
        try:
            data = _post_json('https://openrouter.ai/api/v1/chat/completions', headers, {
                'model': model, 'messages': messages,
                'max_tokens': params['max_tokens'], 'temperature': params['temperature'],
                'reasoning': {'exclude': True},   # keep the model's thinking out of the student's answer
            }, timeout=45)
            return _chat_content(data, 'OpenRouter'), model
        except Exception as exc:
            last_exc = exc
            if 'HTTP 429' not in str(exc) and 'HTTP 5' not in str(exc) and 'empty response' not in str(exc):
                break
    raise last_exc


def animationObservation(event):
    """Short animation observation: Gemini keys 1-3 -> OpenRouter open model. Never uses a daily chat slot."""
    E = env()
    event_text = str(event or '').strip()[:300]
    if not event_text:
        raise RuntimeError('Animation observation is empty')
    user_text = '[Student action] ' + event_text
    reply, used = None, None
    for label, key in _gemini_keys(E):
        try:
            reply, used = callGemini('gemini-3.1-flash-lite', key, ANIMATION_OBSERVATION_PROMPT, [], user_text, OBSERVATION_PARAMS), label
            break
        except Exception as exc:
            print(f'[observation] {label} failed: {exc}', file=sys.stderr)
    if reply is None:
        orKey = E.get('OPENROUTER_API_KEY')
        if not orKey:
            raise RuntimeError('No AI provider is configured')
        reply, used = callOpenRouter(orKey, ANIMATION_OBSERVATION_PROMPT, [], user_text, OBSERVATION_PARAMS)
    reply = ' '.join(reply.split())
    words = reply.split()
    if len(words) > 20:  # keep the 20-word ceiling enforced in code
        reply = ' '.join(words[:20]).rstrip()
    return {'reply': reply, 'model': used}


def genie(b):
    E = env()
    text = '[Student action] ' + str(b.get('event', ''))[:300] if b.get('event') else str(b.get('message') or '')[:1200]
    if not text.strip():
        return {'reply': '…'}
    profile = b.get('profile') or {}
    studentName = str(profile.get('name') or 'Student').strip()
    studentGender = str(profile.get('gender') or '').strip()
    studentStandard = str(profile.get('standard') or profile.get('grade') or '').strip()
    accountRole = str(profile.get('account_role') or '').strip()
    profileContext = f'\n[Student Profile Info] Name: {studentName}, Standard/Class: {studentStandard or "not provided"}, Account role: {accountRole or "learner"}, Gender Preference: {studentGender}. Address the student naturally by name, and adapt the explanation to their saved standard/class.'
    incoming_history = b.get('history')
    if not isinstance(incoming_history, list):
        incoming_history = []
    hist = []
    for item in incoming_history[-6:]:
        if isinstance(item, dict) and item.get('role') in ('user', 'assistant') and isinstance(item.get('content'), str):
            hist.append({'role': item['role'], 'content': item['content'][:600]})
    while hist and hist[0]['role'] != 'user':
        hist.pop(0)
    availableLabs = [lab for lab in labs() if lab.get('available')]
    sys_prompt = SYSTEM_PROMPT + '\n' + cleanSystemPersona + '\n' + profileContext + '\n\n' + buildBehaviorPrompt(availableLabs)
    # Failover order: Gemini key 1 -> key 2 -> key 3 -> OpenRouter open model -> local fallback.
    model = "gemini-3.1-flash-lite"
    for label, key in _gemini_keys(E):
        try:
            reply = callGemini(model, key, sys_prompt, hist, text)
            return {'reply': reply, 'model': label}
        except Exception as exc:
            print(f'[genie] {label} failed: {exc}; trying next provider...', file=sys.stderr)

    openrouter_key = E.get('OPENROUTER_API_KEY')
    if openrouter_key:
        try:
            reply, used_model = callOpenRouter(openrouter_key, sys_prompt, hist, text)
            return {'reply': reply, 'model': used_model}
        except Exception as exc:
            print(f'[genie] OpenRouter open model failed: {exc}; using local fallback.', file=sys.stderr)
    else:
        print('[genie] OPENROUTER_API_KEY is not configured; skipping OpenRouter.', file=sys.stderr)

    print('[genie] All configured AI providers failed; using local fallback.', file=sys.stderr)
    return {
        'reply': getSmartLocalFallback(text, studentName),
        'model': 'Smart Local Fallback Mode',
    }

MIME = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2'}

class JeeniusHandler(BaseHTTPRequestHandler):

    def _session_user(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            morsel = cookie.get(SESSION_COOKIE)
            raw_token = morsel.value if morsel else None
        except Exception:
            raw_token = None
        if not raw_token:
            return None
        token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
        now = int(time.time())
        conn = _db_connect()
        try:
            row = conn.execute('SELECT u.* FROM auth_sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires_at > ?', (token_hash, now)).fetchone()
            if row is None:
                conn.execute('DELETE FROM auth_sessions WHERE token_hash = ? OR expires_at <= ?', (token_hash, now))
                conn.commit()
                return None
            return _public_user(row)
        finally:
            conn.close()

    def _read_json_body(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid request length')
        if length < 0 or length > 64000:
            raise ValueError('Request body is too large')
        raw = self.rfile.read(length).decode('utf-8') if length else '{}'
        data = json.loads(raw or '{}')
        if not isinstance(data, dict):
            raise ValueError('Expected a JSON object')
        return data

    def _client_ip(self):
        forwarded = self.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()[:64]
        try:
            return self.client_address[0]
        except Exception:
            return 'unknown'

    def _json_or_error(self):
        try:
            return self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
            return None

    @staticmethod
    def _home_for(user, next_path='/'):
        """Where a signed-in user should land. Single source of truth for every sign-in route."""
        if not _account_ready(user):
            return '/account-setup.html'
        next_path = _safe_local_path(next_path, '/')
        if next_path not in ('', '/', '/auth.html'):
            return next_path
        return '/teacher-plan.html' if user.get('account_role') == 'teacher' else '/dashboard.html'

    def _verify_redirect(self, email):
        return '/verify.html?email=' + quote(email, safe='')

    def _password_login(self):
        body = self._json_or_error()
        if body is None:
            return
        email = _normalize_email(body.get('email'))
        password = body.get('password')
        if not email or not isinstance(password, str) or not password:
            self._send_json(400, {'error': 'Please enter your email address and password.'})
            return
        if len(password) > 128:
            self._send_json(400, {'error': 'Password must be 128 characters or fewer.'})
            return
        throttle_key = email + '|' + self._client_ip()
        if _login_throttled(throttle_key):
            self._send_json(429, {'error': 'Too many failed attempts. Please wait 15 minutes, or use "Forgot password".'})
            return
        conn = _db_connect()
        try:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        finally:
            conn.close()
        if row is None or not row['password_hash']:
            _login_failed(throttle_key)
            if row is not None and not row['password_hash']:
                self._send_json(401, {'error': 'This account was created with Google. Use "Continue with Google", or choose "Forgot password" to add a password.'})
            else:
                self._send_json(401, {'error': 'Email or password is incorrect.'})
            return
        if not _verify_password(password, row['password_hash']):
            _login_failed(throttle_key)
            self._send_json(401, {'error': 'Email or password is incorrect.'})
            return
        _login_ok(throttle_key)
        if not row['email_verified']:
            payload = {'error': 'Please verify your email before signing in.', 'code': 'email_verification_required',
                       'redirect': self._verify_redirect(email)}
            ok, message, dev_code = _issue_email_otp(row['id'], email)
            if not ok and 'wait' not in message.lower():
                payload['notice'] = message
            if dev_code:
                payload['dev_code'] = dev_code
            self._send_json(403, payload)
            return
        remember = body.get('remember', True) is not False
        token, max_age = _create_auth_session(row['id'], remember=remember)
        user = _public_user(row)
        self._send_json(200, {'success': True, 'user': user, 'redirect': self._home_for(user, body.get('next'))},
                        {'Set-Cookie': _session_cookie(token, max_age)})

    def _password_register(self):
        body = self._json_or_error()
        if body is None:
            return
        name = re.sub(r'\s+', ' ', str(body.get('name') or '')).strip()[:100]
        email = _normalize_email(body.get('email'))
        password = body.get('password')
        if not name or not email or not isinstance(password, str):
            self._send_json(400, {'error': 'Please complete all fields.'})
            return
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(email) > 254:
            self._send_json(400, {'error': 'Please enter a valid email address.'})
            return
        if len(password) < 8:
            self._send_json(400, {'error': 'Use a password with at least 8 characters.'})
            return
        if len(password) > 128:
            self._send_json(400, {'error': 'Password must be 128 characters or fewer.'})
            return
        if not _email_configured():
            self._send_json(503, {'error': 'Sign-up by email is not available right now because the server cannot send verification emails yet. Please use "Continue with Google", or ask the administrator to finish the email setup.'})
            return
        now = int(time.time())
        user_id = secrets.token_hex(16)
        password_hash = _hash_password(password)
        conn = _db_connect()
        try:
            conn.execute(
                "INSERT INTO users (id, email, name, password_hash, picture, created_at, updated_at, email_verified, admin_approved, age_verified, subscription_status) VALUES (?, ?, ?, ?, NULL, ?, ?, 0, 0, 0, 'inactive')",
                (user_id, email, name, password_hash, now, now),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            existing = conn.execute('SELECT id, email_verified, password_hash FROM users WHERE email = ?', (email,)).fetchone()
            if existing is not None and not existing['email_verified'] and existing['password_hash']:
                # Sign-up was started earlier but never finished: resend the code instead of a dead end.
                # The stored password is deliberately NOT replaced, so nobody can pre-claim someone else's address.
                ok, message, dev_code = _issue_email_otp(existing['id'], email)
                payload = {'code': 'email_verification_required', 'redirect': self._verify_redirect(email),
                           'error': 'This email already has an unfinished sign-up. Enter the code we email you to finish it. If you forgot the password you chose, use "Forgot password" afterwards.'}
                if dev_code:
                    payload['dev_code'] = dev_code
                self._send_json(409, payload)
            else:
                self._send_json(409, {'error': 'An account with this email already exists. Please log in instead.'})
            return
        finally:
            conn.close()
        ok, message, dev_code = _issue_email_otp(user_id, email, allow_immediate=True)
        if not ok:
            self._send_json(503, {'error': message, 'account_created': True, 'redirect': self._verify_redirect(email)})
            return
        payload = {'success': True, 'message': message, 'redirect': self._verify_redirect(email)}
        if dev_code:
            payload['dev_code'] = dev_code
        self._send_json(201, payload)

    def _verify_email_otp(self):
        body = self._json_or_error()
        if body is None:
            return
        email = _normalize_email(body.get('email'))
        code = re.sub(r'\s+', '', str(body.get('code') or ''))
        if not email or not re.fullmatch(r'\d{6}', code):
            self._send_json(400, {'error': 'Enter your email and the 6-digit code.'})
            return
        now = int(time.time())
        conn = _db_connect()
        try:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if row is None:
                self._send_json(400, {'error': 'Account not found. Please create your account first.'})
                return
            if row['email_verified']:
                self._send_json(409, {'error': 'This email is already verified. Please log in.', 'code': 'already_verified'})
                return
            if not row['otp_hash'] or not row['otp_expires_at'] or int(row['otp_expires_at']) <= now:
                self._send_json(400, {'error': 'That code has expired. Tap "Resend code" to get a new one.'})
                return
            if int(row['otp_attempts'] or 0) >= 5:
                self._send_json(429, {'error': 'Too many incorrect attempts. Tap "Resend code" to get a new one.'})
                return
            if not hmac.compare_digest(str(row['otp_hash']), _otp_digest(email, code)):
                conn.execute('UPDATE users SET otp_attempts = otp_attempts + 1 WHERE id = ?', (row['id'],))
                conn.commit()
                left = max(0, 4 - int(row['otp_attempts'] or 0))
                self._send_json(400, {'error': ('That code is incorrect. %d attempt(s) left.' % left) if left else 'That code is incorrect. Request a new code.'})
                return
            conn.execute('UPDATE users SET email_verified = 1, otp_hash = NULL, otp_expires_at = NULL, otp_attempts = 0, updated_at = ? WHERE id = ?', (now, row['id']))
            conn.commit()
            row = conn.execute('SELECT * FROM users WHERE id = ?', (row['id'],)).fetchone()
        finally:
            conn.close()
        token, max_age = _create_auth_session(row['id'], remember=True)
        self._send_json(200, {'success': True, 'message': 'Email verified.', 'user': _public_user(row), 'redirect': '/account-setup.html'},
                        {'Set-Cookie': _session_cookie(token, max_age)})

    def _resend_email_otp(self):
        body = self._json_or_error()
        if body is None:
            return
        email = _normalize_email(body.get('email'))
        if not email:
            self._send_json(400, {'error': 'Enter the email address for your account.'})
            return
        if not _email_configured():
            self._send_json(503, {'error': 'The server cannot send emails yet. Please ask the administrator to finish the email setup.'})
            return
        conn = _db_connect()
        try:
            row = conn.execute('SELECT id, email_verified FROM users WHERE email = ?', (email,)).fetchone()
        finally:
            conn.close()
        if row is None:
            self._send_json(200, {'success': True, 'message': 'If that account exists and is unverified, a code has been sent.'})
            return
        if row['email_verified']:
            self._send_json(200, {'success': True, 'message': 'This email is already verified. Please log in.', 'code': 'already_verified'})
            return
        ok, message, dev_code = _issue_email_otp(row['id'], email)
        if not ok:
            self._send_json(429 if 'wait' in message.lower() else 503, {'error': message})
            return
        payload = {'success': True, 'message': message}
        if dev_code:
            payload['dev_code'] = dev_code
        self._send_json(200, payload)

    def _forgot_password(self):
        body = self._json_or_error()
        if body is None:
            return
        email = _normalize_email(body.get('email'))
        if not email or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            self._send_json(400, {'error': 'Enter the email address of your account.'})
            return
        if not _email_configured():
            self._send_json(503, {'error': 'The server cannot send emails yet, so passwords cannot be reset by email. Please use "Continue with Google" or contact the administrator.'})
            return
        conn = _db_connect()
        try:
            row = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        finally:
            conn.close()
        payload = {'success': True, 'message': 'If an account exists for that email, a reset code has been sent.'}
        if row is not None:
            ok, message, dev_code = _issue_email_otp(row['id'], email, purpose='reset')
            if not ok and 'wait' not in message.lower():
                self._send_json(503, {'error': message})
                return
            if dev_code:
                payload['dev_code'] = dev_code
        self._send_json(200, payload)

    def _reset_password(self):
        body = self._json_or_error()
        if body is None:
            return
        email = _normalize_email(body.get('email'))
        code = re.sub(r'\s+', '', str(body.get('code') or ''))
        password = body.get('password')
        if not email or not re.fullmatch(r'\d{6}', code):
            self._send_json(400, {'error': 'Enter your email and the 6-digit code.'})
            return
        if not isinstance(password, str) or len(password) < 8 or len(password) > 128:
            self._send_json(400, {'error': 'Use a new password with 8 to 128 characters.'})
            return
        now = int(time.time())
        conn = _db_connect()
        try:
            row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if row is None or not row['reset_otp_hash'] or not row['reset_otp_expires_at'] or int(row['reset_otp_expires_at']) <= now:
                self._send_json(400, {'error': 'That code is invalid or has expired. Request a new one.'})
                return
            if int(row['reset_otp_attempts'] or 0) >= 5:
                self._send_json(429, {'error': 'Too many incorrect attempts. Request a new code.'})
                return
            if not hmac.compare_digest(str(row['reset_otp_hash']), _otp_digest(email, code)):
                conn.execute('UPDATE users SET reset_otp_attempts = reset_otp_attempts + 1 WHERE id = ?', (row['id'],))
                conn.commit()
                self._send_json(400, {'error': 'That code is incorrect.'})
                return
            conn.execute('UPDATE users SET password_hash = ?, email_verified = 1, reset_otp_hash = NULL, reset_otp_expires_at = NULL, reset_otp_attempts = 0, updated_at = ? WHERE id = ?',
                         (_hash_password(password), now, row['id']))
            conn.execute('DELETE FROM auth_sessions WHERE user_id = ?', (row['id'],))
            conn.commit()
        finally:
            conn.close()
        _login_ok(email + '|' + self._client_ip())
        self._send_json(200, {'success': True, 'message': 'Password updated. You can now log in.', 'redirect': '/auth.html'})

    def _require_session_user(self):
        user = self._session_user()
        if not user:
            self._send_json(401, {'error': 'Please sign in to continue.'})
            return None
        return user

    def _age_declare(self, user, body):
        # Store only an age band, never exact age or date of birth.
        if not user.get('email_verified'):
            self._send_json(403, {'error': 'Verify your email first.'})
            return
        try:
            age = int(body.get('age'))
        except (TypeError, ValueError):
            self._send_json(400, {'error': 'Enter your age as a whole number.'})
            return
        if age < 1 or age > 120:
            self._send_json(400, {'error': 'Please enter a valid age between 1 and 120.'})
            return
        role = str(body.get('account_role') or body.get('role') or '').strip().lower()
        now = int(time.time())
        conn = _db_connect()
        try:
            row = conn.execute('SELECT age_verified, email, account_role FROM users WHERE id = ?', (user['id'],)).fetchone()
            if not row:
                self._send_json(404, {'error': 'Account not found.'})
                return
            if row['age_verified']:
                self._send_json(200, {'success': True, 'already_complete': True, 'message': 'This account has already completed the age/contact step.'})
                return
            student_email = _normalize_email(row['email'])
            existing_role = str(row['account_role'] or '').strip().lower() if 'account_role' in row.keys() else ''
            role = existing_role if existing_role in ('teacher', 'learner') else (role or 'learner')
            if role not in ('teacher', 'learner'):
                self._send_json(400, {'error': 'Choose “As a teacher” or “As a learner” before continuing.'})
                return
        finally:
            conn.close()

        if age >= 18:
            # This is a self-declaration, not independent age verification; admin approval remains required.
            conn = _db_connect()
            try:
                conn.execute('''UPDATE users SET age_verified = 1, age_category = 'self-declared-18-plus',
                    age_provider = 'self-declaration', age_verified_at = ?, age_consent_at = ?,
                    age_consent_version = 'JEENIUS-AGE-DECLARATION-1.0', age_verification_id = NULL,
                    age_verification_url = NULL, parent_email = NULL, parent_email_verified = 0,
                    parent_email_otp_hash = NULL, parent_email_otp_expires_at = NULL,
                    parent_email_otp_attempts = 0, parent_email_otp_last_sent_at = 0,
                    parent_phone_hash = NULL, parent_phone_last4 = NULL, parent_phone_verified = 0,
                    parent_sms_otp_hash = NULL, parent_sms_otp_expires_at = NULL,
                    parent_sms_otp_attempts = 0, parent_sms_otp_last_sent_at = 0,
                    parent_consent_at = NULL, account_role = ?, updated_at = ? WHERE id = ?''', (now, now, role, now, user['id']))
                conn.commit()
            finally:
                conn.close()
            self._send_json(200, {
                'success': True, 'status': 'adult_self_declared',
                'message': 'Your age has been self-declared as 18+. This is not independent age verification; admin approval is still required.',
            })
            return

        parent_email = _normalize_email(body.get('parent_email'))
        if not parent_email or len(parent_email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", parent_email):
            self._send_json(400, {'error': 'Enter a valid parent/guardian email address.'})
            return
        if parent_email == student_email:
            self._send_json(400, {'error': 'Use a parent/guardian email address different from the student email.'})
            return
        # Parent-email-only flow: no parent OTP, SMS, or provider account is needed.
        # This is a user-supplied contact address, not proof of guardian identity or consent.
        conn = _db_connect()
        try:
            conn.execute('''UPDATE users SET age_verified = 1, age_category = 'under-18-parent-email-provided',
                age_provider = 'parent-email-self-report', age_verified_at = ?, age_consent_at = NULL,
                age_consent_version = NULL, age_verification_id = NULL, age_verification_url = NULL,
                parent_email = ?, parent_email_verified = 0, parent_email_otp_hash = NULL,
                parent_email_otp_expires_at = NULL, parent_email_otp_attempts = 0,
                parent_email_otp_last_sent_at = 0, parent_phone_hash = NULL, parent_phone_last4 = NULL,
                parent_phone_verified = 0, parent_sms_otp_hash = NULL, parent_sms_otp_expires_at = NULL,
                parent_sms_otp_attempts = 0, parent_sms_otp_last_sent_at = 0, parent_consent_at = NULL,
                account_role = ?, updated_at = ? WHERE id = ?''',
                (now, parent_email, role, now, user['id']))
            conn.commit()
        finally:
            conn.close()
        self._send_json(200, {
            'success': True, 'status': 'parent_email_recorded', 'parent_email': parent_email,
            'message': 'Parent/guardian email saved. No OTP is required. The address has not been verified; admin approval is still required before access.',
        })

    def _admin_pending_users(self):
        user = self._require_session_user()
        if not user:
            return
        if not _is_admin(user):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        conn = _db_connect()
        try:
            rows = conn.execute('SELECT id, name, email, created_at, email_verified, age_verified, age_category, admin_approved, parent_email, parent_email_verified, parent_consent_at, account_role FROM users WHERE admin_approved = 0 ORDER BY created_at ASC').fetchall()
            users = []
            for row in rows:
                users.append({
                    'id': row['id'], 'name': row['name'], 'email': row['email'], 'created_at': int(row['created_at']),
                    'email_verified': bool(row['email_verified']), 'age_verified': bool(row['age_verified']),
                    'age_category': row['age_category'], 'admin_approved': bool(row['admin_approved']),
                    'parent_email': row['parent_email'], 'parent_email_verified': bool(row['parent_email_verified']),
                    'parent_consent_recorded': bool(row['parent_consent_at']), 'account_role': row['account_role'],
                })
        finally:
            conn.close()
        self._send_json(200, {'success': True, 'users': users})

    def _admin_users(self):
        user = self._require_session_user()
        if not user:
            return
        if not _is_admin(user):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        conn = _db_connect()
        try:
            rows = conn.execute("SELECT id, name, email, created_at, email_verified, age_verified, age_category, admin_approved, parent_email, parent_email_verified, parent_consent_at, account_role, standard, daily_response_limit FROM users ORDER BY created_at DESC").fetchall()
            users = []
            for row in rows:
                users.append({
                    'id': row['id'], 'name': row['name'], 'email': row['email'], 'created_at': int(row['created_at']),
                    'email_verified': bool(row['email_verified']), 'age_verified': bool(row['age_verified']),
                    'age_category': row['age_category'], 'admin_approved': bool(row['admin_approved']),
                    'parent_email': row['parent_email'], 'parent_email_verified': bool(row['parent_email_verified']),
                    'parent_consent_recorded': bool(row['parent_consent_at']), 'account_role': row['account_role'],
                    'standard': row['standard'], 'daily_response_limit': int(row['daily_response_limit'] or 0),
                    'is_admin': _normalize_email(row['email']) in _admin_emails(),
                })
            settings_rows = conn.execute('SELECT setting_key, setting_value FROM app_settings').fetchall()
            settings = {row['setting_key']: row['setting_value'] for row in settings_rows}
        finally:
            conn.close()
        self._send_json(200, {'success': True, 'users': users, 'settings': settings})

    def _admin_set_user_limit(self):
        user = self._require_session_user()
        if not user:
            return
        if not _is_admin(user):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        try:
            body = self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
            return
        target_id = str(body.get('user_id') or '').strip()
        try:
            limit = int(body.get('limit'))
        except (TypeError, ValueError):
            self._send_json(400, {'error': 'Enter a whole-number daily limit from 0 to 1000.'})
            return
        if not target_id or limit < 0 or limit > 1000:
            self._send_json(400, {'error': 'Enter a user and a daily limit from 0 to 1000.'})
            return
        conn = _db_connect()
        try:
            result = conn.execute('UPDATE users SET daily_response_limit = ?, updated_at = ? WHERE id = ?',
                                  (limit, int(time.time()), target_id))
            conn.commit()
            row = conn.execute('SELECT id FROM users WHERE id = ?', (target_id,)).fetchone()
        finally:
            conn.close()
        if not row:
            self._send_json(404, {'error': 'User not found.'})
            return
        self._send_json(200, {'success': True, 'user_id': target_id, 'daily_response_limit': limit,
                              'message': f'Daily AI response limit saved as {limit}.'})

    def _admin_remove_user(self):
        """Permanently delete a regular user and revoke all of their sessions."""
        admin = self._require_session_user()
        if not admin:
            return
        if not _is_admin(admin):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        try:
            body = self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
            return
        target_id = str(body.get('user_id') or '').strip()
        if not target_id:
            self._send_json(400, {'error': 'Missing user ID.'})
            return
        conn = _db_connect()
        try:
            target = conn.execute('SELECT id, email FROM users WHERE id = ?', (target_id,)).fetchone()
            if target is None:
                self._send_json(404, {'error': 'User not found.'})
                return
            target_email = _normalize_email(target['email'])
            # Never allow the UI/API to delete the active admin or any configured admin.
            if target_id == admin.get('id') or target_email in _admin_emails():
                self._send_json(403, {'error': 'Admin accounts are protected and cannot be removed here.'})
                return
            conn.execute('DELETE FROM users WHERE id = ?', (target_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f'[admin] Could not remove user {target_id}: {exc}', file=sys.stderr)
            self._send_json(500, {'error': 'Could not remove this user because related data could not be deleted safely.'})
            return
        finally:
            conn.close()
        self._send_json(200, {'success': True, 'user_id': target_id,
                              'message': 'User account removed and existing login sessions revoked.'})

    def _admin_save_syllabus_tracker(self):
        user = self._require_session_user()
        if not user:
            return
        if not _is_admin(user):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        try:
            body = self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
            return
        title = re.sub(r'\s+', ' ', str(body.get('title') or 'Syllabus Tracker')).strip()[:120]
        url = str(body.get('url') or '').strip()[:2048]
        description = str(body.get('description') or '').strip()[:2000]
        # Only absolute http(s) links or safe same-site paths are supported.
        if url and not (url.startswith('/') and not url.startswith('//') and '\\' not in url):
            if not re.match(r'^https?://[^\s]+$', url, re.I):
                self._send_json(400, {'error': 'Enter an https/http URL or a safe site path such as /syllabus/class-9.html.'})
                return
        if url.startswith('//') or '\\' in url:
            self._send_json(400, {'error': 'Invalid syllabus URL.'})
            return
        now = int(time.time())
        conn = _db_connect()
        try:
            for key, value in (('syllabus_tracker_title', title), ('syllabus_tracker_url', url), ('syllabus_tracker_description', description)):
                conn.execute('INSERT INTO app_settings(setting_key, setting_value, updated_at) VALUES (?, ?, ?) ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value, updated_at = EXCLUDED.updated_at', (key, value, now))
            conn.commit()
        finally:
            conn.close()
        self._send_json(200, {'success': True, 'message': 'Syllabus Tracker settings published.'})

    def _admin_approve_user(self):
        user = self._require_session_user()
        if not user:
            return
        if not _is_admin(user):
            self._send_json(403, {'error': 'Admin access is required.'})
            return
        try:
            body = self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
            return
        target_id = str(body.get('user_id') or '').strip()
        if not target_id:
            self._send_json(400, {'error': 'Missing user ID.'})
            return
        conn = _db_connect()
        try:
            row = conn.execute('SELECT email_verified, age_verified, name, account_role, standard FROM users WHERE id = ?', (target_id,)).fetchone()
            if row is None:
                self._send_json(404, {'error': 'User not found.'})
                return
            if not row['email_verified'] or not row['age_verified']:
                self._send_json(409, {'error': 'This user must verify email and complete the age/contact step before approval.'})
                return
            if not str(row['name'] or '').strip() or not str(row['standard'] or '').strip() or row['account_role'] not in ('teacher', 'learner'):
                self._send_json(409, {'error': 'This user must save their name, class/standard and account role before approval.'})
                return
            conn.execute('UPDATE users SET admin_approved = 1, updated_at = ? WHERE id = ?', (int(time.time()), target_id))
            conn.commit()
        finally:
            conn.close()
        self._send_json(200, {'success': True, 'message': 'User approved. They can now enter JEENIUS.'})

    def _save_account(self, user):
        """Save name / class / role.

        The role (teacher or learner) is chosen ONCE and then locked: nobody can switch it afterwards,
        neither teacher -> learner nor learner -> teacher. Only an administrator can change it.
        """
        body = self._json_or_error()
        if body is None:
            return
        current_role = str(user.get('account_role') or '').strip().lower()
        requested = str(body.get('account_role') or body.get('role') or current_role).strip().lower()
        if requested not in ('teacher', 'learner'):
            self._send_json(400, {'error': 'Choose "As a teacher" or "As a learner".'})
            return
        if current_role in ('teacher', 'learner') and requested != current_role:
            self._send_json(403, {'error': 'Your role is fixed after sign-up and cannot be changed. Ask the administrator if it was chosen by mistake.', 'code': 'role_locked'})
            return
        role = current_role if current_role in ('teacher', 'learner') else requested
        name = re.sub(r'\s+', ' ', str(body.get('name') or user.get('name') or '')).strip()[:100]
        standard = str(body.get('standard') or user.get('standard') or '').strip().lower()
        if not name:
            self._send_json(400, {'error': 'Enter your name.'})
            return
        if standard not in ('8', '9', 'multiple'):
            self._send_json(400, {'error': 'Choose Class 8 or Class 9. JEENIUS covers Maharashtra State Board Classes 8 and 9.'})
            return
        if role == 'learner' and standard == 'multiple':
            self._send_json(400, {'error': 'Learners must choose Class 8 or Class 9.', 'code': 'standard_required'})
            return
        conn = _db_connect()
        try:
            conn.execute('UPDATE users SET name = ?, standard = ?, account_role = ?, updated_at = ? WHERE id = ?',
                         (name, standard, role, int(time.time()), user['id']))
            conn.commit()
            if role == 'learner':
                classroom.ensure_student_code(conn, user['id'])
            row = conn.execute('SELECT * FROM users WHERE id = ?', (user['id'],)).fetchone()
        finally:
            conn.close()
        saved = _public_user(row)
        self._send_json(200, {'success': True, 'account_role': role, 'user': saved, 'redirect': self._home_for(saved)})

    def _classroom(self, method, parsed, user):
        """Teacher classroom API. Role checks happen inside classroom.py."""
        conn = _db_connect()
        try:
            if method == 'GET':
                if parsed.path == '/api/classroom/assignment':
                    status, payload = classroom.assignment_detail(conn, user, (parse_qs(parsed.query).get('id') or [''])[0])
                else:
                    status, payload = classroom.summary(conn, user)
            else:
                action = classroom.ACTIONS.get(parsed.path.rsplit('/', 1)[-1])
                if action is None:
                    status, payload = 404, {'error': 'Unknown classroom action.'}
                else:
                    body = self._json_or_error()
                    if body is None:
                        return
                    lab_ids = {str(item['id']) for item in labs() if item.get('available')}
                    status, payload = action(conn, user, body, lab_ids)
        finally:
            conn.close()
        self._send_json(status, payload)

    def _logout(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            morsel = cookie.get(SESSION_COOKIE)
            raw_token = morsel.value if morsel else None
        except Exception:
            raw_token = None
        if raw_token:
            token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
            conn = _db_connect()
            try:
                conn.execute('DELETE FROM auth_sessions WHERE token_hash = ?', (token_hash,))
                conn.commit()
            finally:
                conn.close()
        self._send_json(200, {'success': True}, {'Set-Cookie': _clear_session_cookie()})

    def do_POST(self):
        parsed = urlsplit(self.path)
        if parsed.path == '/auth/callback':
            self._google_auth_callback()
            return
        if parsed.path == '/api/auth/login':
            self._password_login()
            return
        if parsed.path == '/api/auth/register':
            self._password_register()
            return
        if parsed.path == '/api/auth/verify-otp':
            self._verify_email_otp()
            return
        if parsed.path == '/api/auth/resend-otp':
            self._resend_email_otp()
            return
        if parsed.path == '/api/auth/forgot':
            self._forgot_password()
            return
        if parsed.path == '/api/auth/reset':
            self._reset_password()
            return
        if parsed.path == '/api/auth/google':
            self._google_json_login()
            return
        if parsed.path == '/api/account/profile':
            user = self._require_session_user()
            if user:
                self._save_account(user)
            return
        if parsed.path.startswith('/api/classroom/'):
            user = self._require_session_user()
            if user:
                if not _account_ready(user):
                    self._send_json(403, {'error': 'Finish account setup and wait for approval first.'})
                else:
                    self._classroom('POST', parsed, user)
            return
        if parsed.path == '/api/age/declare':
            user = self._require_session_user()
            if user:
                try:
                    body = self._read_json_body()
                except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send_json(400, {'error': str(exc) or 'Invalid JSON request'})
                else:
                    self._age_declare(user, body)
            return
        if parsed.path == '/api/admin/set-user-limit':
            self._admin_set_user_limit()
            return
        if parsed.path == '/api/admin/remove-user':
            self._admin_remove_user()
            return
        if parsed.path == '/api/admin/syllabus-tracker':
            self._admin_save_syllabus_tracker()
            return
        if parsed.path == '/api/admin/approve':
            self._admin_approve_user()
            return
        if parsed.path in ('/api/auth/logout', '/auth/logout'):
            self._logout()
            return
        if parsed.path not in ('/api/genie', '/api/animation-observation'):
            self.send_error(404, 'Not found')
            return
        user = self._session_user()
        if not user:
            self._send_json(401, {'error': 'Please sign in to continue.'})
            return
        if not _account_ready(user):
            self._send_json(403, {'error': 'account_setup_required', 'message': 'Verify your email, complete the age/consent step, and wait for admin approval before using JEENIUS.'})
            return
        if not ai_access_allowed(user):
            self._send_json(402, {'error': 'teacher_plan_required', 'message': teacher_plan_message(user)})
            return
        try:
            body = self._read_json_body()
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            message = str(exc) or 'Invalid JSON request'
            status = 413 if 'too large' in message.lower() else 400
            self._send_json(status, {'error': message})
            return

        # Animation observations use Gemini -> OpenRouter directly and NEVER reserve or consume a daily chat slot.
        # The /api/genie event form is also accepted for backward compatibility with cached clients.
        is_animation_observation = (
            parsed.path == '/api/animation-observation'
            or (
                parsed.path == '/api/genie'
                and bool(str(body.get('event') or '').strip())
                and not bool(str(body.get('message') or '').strip())
            )
        )
        if is_animation_observation:
            try:
                out = animationObservation(body.get('event'))
                self._send_json(200, out)
            except Exception as exc:
                print(f'[animation-observation] failed: {exc}', file=sys.stderr)
                missing_key = 'No AI provider is configured' in str(exc)
                self._send_json(503 if missing_key else 502, {
                    'error': 'ai_not_configured' if missing_key else 'observation_failed',
                    'message': (
                        'No AI key is configured yet. Add GEMINI_API_KEY or OPENROUTER_API_KEY to your Render environment variables.'
                        if missing_key else
                        'Could not create this observation. Please try again.'
                    ),
                })
            return

        # Always send the server-saved name, standard and role to the AI; never trust a browser-only profile.
        body_profile = body.get('profile') if isinstance(body.get('profile'), dict) else {}
        body['profile'] = {
            'name': user.get('name') or body_profile.get('name') or 'Student',
            'standard': user.get('standard') or body_profile.get('standard') or '',
            'account_role': user.get('account_role') or 'learner',
            'gender': body_profile.get('gender') or '',
        }

        # Empty regular-chat submissions do not use a response slot.
        request_text = str(body.get('message') or '').strip()
        if not request_text:
            out = genie(body)
            out['quota'] = _daily_quota_status(user['id'])
            self._send_json(200, out)
            return

        try:
            reserved_date, usage_date = _reserve_daily_response(user['id'])
        except Exception as exc:
            print(f'[quota] Could not reserve daily response: {exc}', file=sys.stderr)
            self._send_json(500, {'error': 'quota_unavailable', 'message': 'Could not check your daily limit. Please try again shortly.'})
            return

        if reserved_date is None:
            quota = _daily_quota_status(user['id'], usage_date)
            self._send_json(429, {
                'error': 'daily_limit_reached',
                'message': f"You've reached your daily limit of {quota['limit']} responses. Your limit resets at {quota['reset_label']}.",
                'quota': quota,
            })
            return

        try:
            out = genie(body)
            if not isinstance(out, dict) or not str(out.get('reply') or '').strip():
                raise RuntimeError('No response was generated')
            # Gemini keys are tried first and the OpenRouter open model is the backup inside genie(). A local
            # fallback counts as a response because the student still received an answer.
            _finish_daily_response(user['id'], reserved_date, succeeded=True)
            out['quota'] = _daily_quota_status(user['id'])
            self._send_json(200, out)
        except Exception as exc:
            print(f'[server] Request failed: {exc}', file=sys.stderr)
            try:
                _finish_daily_response(user['id'], reserved_date, succeeded=False)
            except Exception as quota_exc:
                print(f'[quota] Could not release failed response reservation: {quota_exc}', file=sys.stderr)
            self._send_json(500, {
                'error': 'request_failed',
                'message': "Kuch gadbad ho gayi, let's try again!",
                'quota': _daily_quota_status(user['id']),
            })

    def _google_identity(self, credential):
        """Verify a Google ID token and return (user_row, is_new). Raises ValueError(code) on failure."""
        client_id = env().get('GOOGLE_CLIENT_ID', '').strip()
        if not client_id:
            raise ValueError('google_not_configured')
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
        except ImportError as exc:
            print(f'[auth] Google auth import failed: {exc}', file=sys.stderr)
            raise ValueError('google_failed')
        try:
            # A few seconds of clock skew tolerance prevents random "Token used too early" failures.
            info = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id, clock_skew_in_seconds=10)
        except Exception as exc:
            print(f'[auth] Google token rejected: {exc}', file=sys.stderr)
            raise ValueError('google_failed')
        if info.get('iss') not in ('accounts.google.com', 'https://accounts.google.com') or not info.get('email_verified'):
            raise ValueError('google_failed')
        email = _normalize_email(info.get('email'))
        google_sub = str(info.get('sub') or '').strip()
        name = re.sub(r'\s+', ' ', str(info.get('name') or 'Student')).strip()[:100] or 'Student'
        picture = str(info.get('picture') or '')[:2048] or None
        if not email or not google_sub:
            raise ValueError('google_failed')
        now = int(time.time())
        conn = _db_connect()
        is_new = False
        try:
            row = conn.execute('SELECT * FROM users WHERE google_sub = ?', (google_sub,)).fetchone()
            if row is None:
                row = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
                if row is not None:
                    if row['google_sub'] and row['google_sub'] != google_sub:
                        raise ValueError('account_conflict')
                    conn.execute("UPDATE users SET google_sub = ?, picture = COALESCE(picture, ?), name = CASE WHEN TRIM(name) = '' THEN ? ELSE name END, email_verified = 1, updated_at = ? WHERE id = ?",
                                 (google_sub, picture, name, now, row['id']))
                else:
                    user_id = secrets.token_hex(16)
                    conn.execute("INSERT INTO users(id, email, name, password_hash, google_sub, picture, created_at, updated_at, email_verified, admin_approved, age_verified, subscription_status) VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 1, 0, 0, 'inactive')",
                                 (user_id, email, name, google_sub, picture, now, now))
                    row = {'id': user_id}
                    is_new = True
            elif not row['email_verified']:
                conn.execute('UPDATE users SET email_verified = 1, updated_at = ? WHERE id = ?', (now, row['id']))
            conn.commit()
            row = conn.execute('SELECT * FROM users WHERE id = ?', (row['id'],)).fetchone()
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError('account_conflict')
        finally:
            conn.close()
        return row, is_new

    def _google_json_login(self):
        """JSON sign-in used by the Google button: the page gets the destination back and navigates itself."""
        body = self._json_or_error()
        if body is None:
            return
        credential = str(body.get('credential') or '')
        if not credential:
            self._send_json(400, {'error': 'Google did not return a sign-in credential. Please try again.'})
            return
        try:
            row, is_new = self._google_identity(credential)
        except ValueError as exc:
            code = str(exc)
            message = {
                'account_conflict': 'This email is already connected to a different Google account. Sign in with the method you first used.',
                'google_not_configured': 'Google sign-in is not configured on the server (GOOGLE_CLIENT_ID is missing).',
            }.get(code, 'Google sign-in could not be completed. Please try again or use email and password.')
            self._send_json(503 if code == 'google_not_configured' else 401, {'error': message, 'code': code})
            return
        token, max_age = _create_auth_session(row['id'], remember=True)
        user = _public_user(row)
        self._send_json(200, {'success': True, 'new_user': is_new, 'user': user, 'redirect': self._home_for(user, body.get('next'))},
                        {'Set-Cookie': _session_cookie(token, max_age)})

    def _google_auth_callback(self):
        """Classic form-POST fallback (login_uri redirect mode). Sets the cookie and redirects."""
        next_path = '/'
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or length > 128000:
                self.send_error(413, 'Request body is too large')
                return
            raw = self.rfile.read(length).decode('utf-8') if length else ''
            form = parse_qs(raw, keep_blank_values=True)
            credential = (form.get('credential') or [''])[0]
            next_path = _safe_local_path((form.get('next') or ['/'])[0], '/')
            if not credential:
                self._redirect_auth_error('google_failed', next_path)
                return
            row, _ = self._google_identity(credential)
        except ValueError as exc:
            self._redirect_auth_error('account_conflict' if str(exc) == 'account_conflict' else 'google_failed', next_path)
            return
        except Exception as exc:
            print(f'[auth] Google callback failed: {exc}', file=sys.stderr)
            self._redirect_auth_error('google_failed', next_path)
            return
        token, max_age = _create_auth_session(row['id'], remember=True)
        self.send_response(303)
        self.send_header('Location', self._home_for(_public_user(row), next_path))
        self.send_header('Set-Cookie', _session_cookie(token, max_age))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def _redirect_auth_error(self, error_code, next_path='/'):
        safe_next = _safe_local_path(next_path, '/')
        from urllib.parse import urlencode
        query = urlencode({'error': error_code, 'next': safe_next})
        self.send_response(303)
        self.send_header('Location', '/auth.html?' + query)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def _send_json(self, status, payload, extra_headers=None):
        encoded = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        if extra_headers:
            for name, value in extra_headers.items():
                self.send_header(name, value)
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/healthz":
            self._send_json(200, {"status": "ok"})
            return
        if parsed.path == '/api/animations/catalog':
            user = self._require_session_user()
            if not user:
                return
            if not user.get('email_verified') or not user.get('age_verified'):
                self._send_json(403, {'error': 'Complete email and age/consent steps before browsing the animation catalogue.'})
                return
            if not _account_ready(user):
                self._send_json(403, {'error': 'Finish your profile and wait for admin approval before browsing the animation catalogue.'})
                return
            self._send_json(200, labs())
            return
        if parsed.path == '/api/syllabus-tracker':
            user = self._require_session_user()
            if not user:
                return
            if not _account_ready(user) and not _is_admin(user):
                self._send_json(403, {'error': 'Account approval is still required to view the Syllabus Tracker.'})
                return
            conn = _db_connect()
            try:
                rows = conn.execute("SELECT setting_key, setting_value FROM app_settings WHERE setting_key IN ('syllabus_tracker_title','syllabus_tracker_url','syllabus_tracker_description')").fetchall()
                settings = {row['setting_key']: row['setting_value'] for row in rows}
            finally:
                conn.close()
            self._send_json(200, {
                'success': True,
                'title': settings.get('syllabus_tracker_title') or 'Syllabus Tracker',
                'url': settings.get('syllabus_tracker_url') or '',
                'description': settings.get('syllabus_tracker_description') or 'The administrator has not published the syllabus tracker yet. Check back later.',
                'published': bool(settings.get('syllabus_tracker_url')),
            })
            return
        if parsed.path == '/api/classroom' or parsed.path == '/api/classroom/assignment':
            user = self._require_session_user()
            if user:
                if not _account_ready(user):
                    self._send_json(403, {'error': 'Finish account setup and wait for approval first.'})
                else:
                    self._classroom('GET', parsed, user)
            return
        if parsed.path == '/api/admin/pending-users':
            self._admin_pending_users()
            return
        if parsed.path == '/api/admin/users':
            self._admin_users()
            return
        if parsed.path == '/api/auth/me':
            user = self._session_user()
            self._send_json(200, {'authenticated': bool(user), 'user': user, 'access_ready': _account_ready(user), 'is_admin': _is_admin(user), 'quota': _daily_quota_status(user['id']) if user else None})
            return
        if parsed.path == '/admin.html':
            user = self._session_user()
            if not user:
                self.send_response(303); self.send_header('Location', '/auth.html'); self.end_headers(); return
            if not _is_admin(user):
                self.send_error(403, 'Admin access is required'); return
        if parsed.path == '/teacher-plan.html':
            user = self._session_user()
            if not user:
                self.send_response(303); self.send_header('Location', '/auth.html'); self.end_headers(); return
            if not _account_ready(user) or user.get('account_role') != 'teacher':
                self.send_response(303); self.send_header('Location', '/account-setup.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
        if parsed.path == '/account-setup.html' and not self._session_user():
            self.send_response(303); self.send_header('Location', '/auth.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
        if parsed.path in ('/dashboard.html', '/index.html', '/animation-lab.html', '/syllabus-tracker.html', '/classroom.html') or parsed.path.startswith('/animations/'):
            page_user = self._session_user()
            if not page_user:
                self.send_response(303); self.send_header('Location', '/auth.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
            if not _account_ready(page_user):
                self.send_response(303); self.send_header('Location', '/account-setup.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
        if parsed.path == '/auth.html' and self._session_user():
            current = self._session_user()
            self.send_response(303)
            self.send_header('Location', self._home_for(current, parse_qs(parsed.query).get('next', ['/'])[0]))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        if parsed.path == '/':
            home_user = self._session_user()
            if home_user and _account_ready(home_user):
                self.send_response(303); self.send_header('Location', '/dashboard.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
            if home_user:
                self.send_response(303); self.send_header('Location', '/account-setup.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
        if parsed.path in ('/', '/index.html') and (not self._session_user()):
            from urllib.parse import urlencode
            target = parsed.path or '/'
            if parsed.query:
                target += '?' + parsed.query
            self.send_response(303)
            self.send_header('Location', '/auth.html?' + urlencode({'next': _safe_local_path(target, '/')}))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        try:
            request_path = unquote(parsed.path)
        except Exception:
            self.send_error(400, 'Bad request path')
            return
        relative = request_path.lstrip('/') or 'index.html'
        # All application and animation HTML pages are protected server-side.
        if target_is_html_path := (relative.lower().endswith(('.html', '.htm')) and relative.lower() not in ('auth.html', 'verify.html', 'account-setup.html', 'admin.html', 'teacher-plan.html')):
            user = self._session_user()
            if not user:
                from urllib.parse import urlencode
                self.send_response(303); self.send_header('Location', '/auth.html?' + urlencode({'next': _safe_local_path('/' + relative, '/')})); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
            if not _account_ready(user) and not _is_admin(user):
                self.send_response(303); self.send_header('Location', '/account-setup.html'); self.send_header('Cache-Control', 'no-store'); self.end_headers(); return
        target = (PUB / relative).resolve()
        try:
            target.relative_to(PUB.resolve())
        except ValueError:
            self.send_error(404, 'Not found')
            return
        if target.is_dir():
            target = target / 'index.html'
        if not target.exists() or not target.is_file():
            self.send_error(404, 'Not found')
            return
        content_type = MIME.get(target.suffix.lower(), mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        try:
            data = target.read_bytes()
            if target.suffix.lower() in ('.html', '.htm'):
                client_id = env().get('GOOGLE_CLIENT_ID', '')
                page = data.decode('utf-8')
                page = page.replace('__GOOGLE_CLIENT_ID__', html.escape(client_id, quote=True))
                data = page.encode('utf-8')
        except OSError:
            self.send_error(500, 'Could not read file')
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        if target.suffix.lower() in ('.html', '.htm'):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
        else:
            self.send_header('Cache-Control', 'public, max-age=300')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        origin = self.headers.get('Origin', '')
        allowed_origin = env().get('FRONTEND_URL', f'http://localhost:{PORT}').rstrip('/')
        self.send_response(204)
        if origin == allowed_origin:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Vary', 'Origin')
        self.end_headers()

    def log_message(self, fmt, *args):
        print(f'[http] {self.address_string()} - {fmt % args}')
if __name__ == '__main__':
    initialize_auth_db()
    server = ThreadingHTTPServer((HOST, PORT), JeeniusHandler)
    database_name = 'PostgreSQL' if env().get('DATABASE_URL') else 'SQLite'
    print(f'Jeenius listening on {HOST}:{PORT} (database: {database_name})')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down Jeenius...')
    finally:
        server.server_close()
