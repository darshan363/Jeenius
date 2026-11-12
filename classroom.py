"""Teacher classroom: student IDs, invitations, homework and auto-graded tests.

Kept in its own module so server.py only needs a few lines to route to it.
Every function takes an open DB connection (the same wrapper server.py uses, so it works on
SQLite and PostgreSQL) and returns (http_status, payload).
"""
import json
import re
import secrets
import threading
import time

CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'   # no I, L, O, 0, 1 so IDs are easy to read aloud
CODE_PREFIX = 'JNS-'

SCHEMA = '''
CREATE TABLE IF NOT EXISTS classroom_links (
    id TEXT PRIMARY KEY,
    teacher_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    UNIQUE (teacher_id, student_id)
);
CREATE TABLE IF NOT EXISTS classroom_assignments (
    id TEXT PRIMARY KEY,
    teacher_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    due_date TEXT,
    lab_id TEXT,
    questions_json TEXT,
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS classroom_targets (
    assignment_id TEXT NOT NULL REFERENCES classroom_assignments(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'assigned',
    answer_text TEXT,
    answers_json TEXT,
    score INTEGER,
    total INTEGER,
    submitted_at BIGINT,
    PRIMARY KEY (assignment_id, student_id)
);
'''


def ensure_schema(conn):
    conn.executescript(SCHEMA)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_classroom_links_student ON classroom_links(student_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_classroom_targets_student ON classroom_targets(student_id)')
    conn.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_student_code ON users(student_code)')
    backfill_student_codes(conn)
    conn.commit()


# --------------------------------------------------------------------------- student IDs
def _new_code():
    return CODE_PREFIX + ''.join(secrets.choice(CODE_ALPHABET) for _ in range(6))


def ensure_student_code(conn, user_id):
    row = conn.execute('SELECT student_code FROM users WHERE id = ?', (user_id,)).fetchone()
    if row is None:
        return None
    if row['student_code']:
        return row['student_code']
    for _ in range(20):
        code = _new_code()
        taken = conn.execute('SELECT 1 AS x FROM users WHERE student_code = ?', (code,)).fetchone()
        if taken:
            continue
        conn.execute('UPDATE users SET student_code = ? WHERE id = ? AND student_code IS NULL', (code, user_id))
        conn.commit()
        return conn.execute('SELECT student_code FROM users WHERE id = ?', (user_id,)).fetchone()['student_code']
    return None


def backfill_student_codes(conn):
    rows = conn.execute("SELECT id FROM users WHERE account_role = 'learner' AND (student_code IS NULL OR student_code = '')").fetchall()
    for row in rows:
        ensure_student_code(conn, row['id'])


def normalize_code(value):
    raw = re.sub(r'[^A-Za-z0-9]', '', str(value or '')).upper()
    if raw.startswith('JNS'):
        raw = raw[3:]
    return CODE_PREFIX + raw if len(raw) == 6 and all(ch in CODE_ALPHABET for ch in raw) else ''


# --------------------------------------------------------------------------- throttling
_INVITES = {}
_LOCK = threading.Lock()


def _invite_allowed(teacher_id):
    now = time.time()
    with _LOCK:
        recent = [t for t in _INVITES.get(teacher_id, []) if now - t < 3600]
        if len(recent) >= 20:
            _INVITES[teacher_id] = recent
            return False
        recent.append(now)
        _INVITES[teacher_id] = recent
        return True


# --------------------------------------------------------------------------- helpers
def _clean(value, limit):
    return re.sub(r'[ \t]+', ' ', str(value or '')).strip()[:limit]


def _questions_public(raw, reveal):
    try:
        items = json.loads(raw or '[]')
    except ValueError:
        items = []
    out = []
    for item in items:
        entry = {'q': item.get('q', ''), 'options': item.get('options', [])}
        if reveal:
            entry['correct'] = item.get('correct')
        out.append(entry)
    return out


def _is_teacher(user):
    return user.get('account_role') == 'teacher'


# --------------------------------------------------------------------------- GET
def summary(conn, user):
    if _is_teacher(user):
        students = []
        for r in conn.execute('''SELECT l.id AS link_id, l.status, l.created_at, u.id AS student_id, u.name, u.standard, u.student_code
                                 FROM classroom_links l JOIN users u ON u.id = l.student_id
                                 WHERE l.teacher_id = ? ORDER BY l.status, u.name''', (user['id'],)).fetchall():
            pending = r['status'] != 'active'
            students.append({'link_id': r['link_id'], 'student_id': r['student_id'], 'status': r['status'],
                             'code': r['student_code'], 'name': None if pending else r['name'], 'standard': None if pending else r['standard']})
        assignments = []
        for a in conn.execute('SELECT * FROM classroom_assignments WHERE teacher_id = ? ORDER BY created_at DESC', (user['id'],)).fetchall():
            counts = conn.execute("SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'submitted' THEN 1 ELSE 0 END) AS done FROM classroom_targets WHERE assignment_id = ?", (a['id'],)).fetchone()
            assignments.append({'id': a['id'], 'kind': a['kind'], 'title': a['title'], 'due_date': a['due_date'], 'lab_id': a['lab_id'],
                                'assigned': int(counts['total'] or 0), 'submitted': int(counts['done'] or 0), 'created_at': a['created_at']})
        return 200, {'role': 'teacher', 'students': students, 'assignments': assignments}
    code = ensure_student_code(conn, user['id'])
    invites = [{'link_id': r['id'], 'teacher_name': r['name']} for r in conn.execute(
        "SELECT l.id, u.name FROM classroom_links l JOIN users u ON u.id = l.teacher_id WHERE l.student_id = ? AND l.status = 'pending' ORDER BY l.created_at DESC", (user['id'],)).fetchall()]
    teachers = [{'teacher_id': r['id'], 'name': r['name']} for r in conn.execute(
        "SELECT u.id, u.name FROM classroom_links l JOIN users u ON u.id = l.teacher_id WHERE l.student_id = ? AND l.status = 'active' ORDER BY u.name", (user['id'],)).fetchall()]
    work = []
    for r in conn.execute('''SELECT a.*, t.status AS tstatus, t.answer_text, t.answers_json, t.score, t.total, t.submitted_at, u.name AS teacher_name
                             FROM classroom_targets t
                             JOIN classroom_assignments a ON a.id = t.assignment_id
                             JOIN classroom_links l ON l.teacher_id = a.teacher_id AND l.student_id = t.student_id AND l.status = 'active'
                             JOIN users u ON u.id = a.teacher_id
                             WHERE t.student_id = ? ORDER BY a.created_at DESC''', (user['id'],)).fetchall():
        submitted = r['tstatus'] == 'submitted'
        item = {'id': r['id'], 'kind': r['kind'], 'title': r['title'], 'body': r['body'], 'due_date': r['due_date'], 'lab_id': r['lab_id'],
                'teacher_name': r['teacher_name'], 'status': r['tstatus'], 'questions': _questions_public(r['questions_json'], submitted)}
        if submitted:
            item.update({'score': r['score'], 'total': r['total'], 'answer_text': r['answer_text'],
                         'answers': json.loads(r['answers_json'] or '[]')})
        work.append(item)
    return 200, {'role': 'learner', 'student_code': code, 'invites': invites, 'teachers': teachers, 'assignments': work}


def assignment_detail(conn, user, assignment_id):
    if not _is_teacher(user):
        return 403, {'error': 'Only teachers can view submissions.'}
    a = conn.execute('SELECT * FROM classroom_assignments WHERE id = ? AND teacher_id = ?', (assignment_id, user['id'])).fetchone()
    if a is None:
        return 404, {'error': 'Assignment not found.'}
    rows = conn.execute('''SELECT t.*, u.name FROM classroom_targets t JOIN users u ON u.id = t.student_id
                           WHERE t.assignment_id = ? ORDER BY u.name''', (assignment_id,)).fetchall()
    return 200, {'id': a['id'], 'kind': a['kind'], 'title': a['title'], 'body': a['body'], 'due_date': a['due_date'], 'lab_id': a['lab_id'],
                 'questions': _questions_public(a['questions_json'], True),
                 'students': [{'student_id': r['student_id'], 'name': r['name'], 'status': r['status'], 'score': r['score'], 'total': r['total'],
                               'answer_text': r['answer_text'], 'answers': json.loads(r['answers_json'] or '[]')} for r in rows]}


# --------------------------------------------------------------------------- POST actions
def invite(conn, user, body):
    if not _is_teacher(user):
        return 403, {'error': 'Only teachers can invite students.'}
    code = normalize_code(body.get('student_code'))
    if not code:
        return 400, {'error': 'Enter the 6-character student ID, for example JNS-4K7QX2.'}
    if not _invite_allowed(user['id']):
        return 429, {'error': 'Too many invitations in the last hour. Please try again later.'}
    student = conn.execute("SELECT id, name FROM users WHERE student_code = ? AND account_role = 'learner'", (code,)).fetchone()
    if student is None:
        return 404, {'error': 'No student found with that ID. Ask the student to check the ID on their Classroom page.'}
    link = conn.execute('SELECT id, status FROM classroom_links WHERE teacher_id = ? AND student_id = ?', (user['id'], student['id'])).fetchone()
    if link is not None:
        return 409, {'error': 'This student is already in your class.' if link['status'] == 'active' else 'An invitation is already waiting for this student.'}
    now = int(time.time())
    conn.execute('INSERT INTO classroom_links (id, teacher_id, student_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
                 (secrets.token_hex(8), user['id'], student['id'], 'pending', now, now))
    conn.commit()
    return 201, {'success': True, 'message': 'Invitation sent to ' + code + '. It appears in your list once the student accepts.'}


def remove_link(conn, user, body):
    link_id = str(body.get('link_id') or '')
    row = conn.execute('SELECT id FROM classroom_links WHERE id = ? AND teacher_id = ?', (link_id, user['id'])).fetchone()
    if row is None:
        return 404, {'error': 'Student not found in your class.'}
    conn.execute('DELETE FROM classroom_links WHERE id = ?', (link_id,))
    conn.commit()
    return 200, {'success': True}


def respond(conn, user, body):
    if _is_teacher(user):
        return 403, {'error': 'Only students can accept invitations.'}
    link = conn.execute("SELECT id FROM classroom_links WHERE id = ? AND student_id = ? AND status = 'pending'", (str(body.get('link_id') or ''), user['id'])).fetchone()
    if link is None:
        return 404, {'error': 'Invitation not found.'}
    if body.get('accept') is True:
        conn.execute("UPDATE classroom_links SET status = 'active', updated_at = ? WHERE id = ?", (int(time.time()), link['id']))
    else:
        conn.execute('DELETE FROM classroom_links WHERE id = ?', (link['id'],))
    conn.commit()
    return 200, {'success': True}


def leave(conn, user, body):
    if _is_teacher(user):
        return 403, {'error': 'Only students can leave a class.'}
    conn.execute('DELETE FROM classroom_links WHERE teacher_id = ? AND student_id = ?', (str(body.get('teacher_id') or ''), user['id']))
    conn.commit()
    return 200, {'success': True}


def _valid_questions(raw):
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        return None, 'Add between 1 and 20 questions to a test.'
    out = []
    for i, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            return None, f'Question {i} is not valid.'
        q = _clean(item.get('q'), 300)
        options = [_clean(o, 120) for o in (item.get('options') or []) if _clean(o, 120)]
        correct = item.get('correct')
        if not q or not 2 <= len(options) <= 4:
            return None, f'Question {i} needs text and 2 to 4 answer options.'
        if not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct < len(options):
            return None, f'Choose the correct answer for question {i}.'
        out.append({'q': q, 'options': options, 'correct': correct})
    return out, None


def assign(conn, user, body, lab_ids):
    if not _is_teacher(user):
        return 403, {'error': 'Only teachers can assign work.'}
    kind = body.get('kind')
    if kind not in ('homework', 'test'):
        return 400, {'error': 'Choose homework or test.'}
    title = _clean(body.get('title'), 120)
    if not title:
        return 400, {'error': 'Give the assignment a title.'}
    text = str(body.get('body') or '').strip()[:2000]
    due = str(body.get('due_date') or '').strip()
    if due and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', due):
        return 400, {'error': 'Use a valid due date.'}
    lab_id = str(body.get('lab_id') or '').strip() or None
    if lab_id and lab_id not in lab_ids:
        return 400, {'error': 'That animation does not exist.'}
    questions = None
    if kind == 'test':
        questions, error = _valid_questions(body.get('questions'))
        if error:
            return 400, {'error': error}
    elif not text and not lab_id:
        return 400, {'error': 'Write the homework instructions or attach an animation.'}
    active = {r['student_id'] for r in conn.execute("SELECT student_id FROM classroom_links WHERE teacher_id = ? AND status = 'active'", (user['id'],)).fetchall()}
    wanted = body.get('student_ids')
    targets = sorted(active) if wanted in (None, 'all') else sorted({s for s in wanted if s in active}) if isinstance(wanted, list) else []
    if not targets:
        return 400, {'error': 'Choose at least one student from your class. Invite students first if the list is empty.'}
    aid, now = secrets.token_hex(8), int(time.time())
    conn.execute('INSERT INTO classroom_assignments (id, teacher_id, kind, title, body, due_date, lab_id, questions_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                 (aid, user['id'], kind, title, text, due or None, lab_id, json.dumps(questions) if questions else None, now))
    for sid in targets:
        conn.execute("INSERT INTO classroom_targets (assignment_id, student_id, status) VALUES (?, ?, 'assigned')", (aid, sid))
    conn.commit()
    return 201, {'success': True, 'id': aid, 'assigned': len(targets)}


def delete_assignment(conn, user, body):
    row = conn.execute('SELECT id FROM classroom_assignments WHERE id = ? AND teacher_id = ?', (str(body.get('id') or ''), user['id'])).fetchone()
    if row is None:
        return 404, {'error': 'Assignment not found.'}
    conn.execute('DELETE FROM classroom_targets WHERE assignment_id = ?', (row['id'],))
    conn.execute('DELETE FROM classroom_assignments WHERE id = ?', (row['id'],))
    conn.commit()
    return 200, {'success': True}


def submit(conn, user, body):
    if _is_teacher(user):
        return 403, {'error': 'Only students can submit work.'}
    aid = str(body.get('assignment_id') or '')
    row = conn.execute('''SELECT a.kind, a.questions_json, t.status FROM classroom_targets t
                          JOIN classroom_assignments a ON a.id = t.assignment_id
                          JOIN classroom_links l ON l.teacher_id = a.teacher_id AND l.student_id = t.student_id AND l.status = 'active'
                          WHERE t.assignment_id = ? AND t.student_id = ?''', (aid, user['id'])).fetchone()
    if row is None:
        return 404, {'error': 'Assignment not found.'}
    if row['status'] == 'submitted':
        return 409, {'error': 'You have already submitted this. Submissions cannot be changed.'}
    now = int(time.time())
    if row['kind'] == 'homework':
        conn.execute("UPDATE classroom_targets SET status = 'submitted', answer_text = ?, submitted_at = ? WHERE assignment_id = ? AND student_id = ?",
                     (str(body.get('answer_text') or '').strip()[:2000], now, aid, user['id']))
        conn.commit()
        return 200, {'success': True}
    questions = json.loads(row['questions_json'] or '[]')
    answers = body.get('answers')
    if not isinstance(answers, list) or len(answers) != len(questions) or any(not isinstance(a, int) or isinstance(a, bool) for a in answers):
        return 400, {'error': 'Answer every question before submitting.'}
    score = sum(1 for q, a in zip(questions, answers) if a == q['correct'])
    conn.execute("UPDATE classroom_targets SET status = 'submitted', answers_json = ?, score = ?, total = ?, submitted_at = ? WHERE assignment_id = ? AND student_id = ?",
                 (json.dumps(answers), score, len(questions), now, aid, user['id']))
    conn.commit()
    return 200, {'success': True, 'score': score, 'total': len(questions)}


ACTIONS = {
    'invite': lambda conn, user, body, labs: invite(conn, user, body),
    'remove': lambda conn, user, body, labs: remove_link(conn, user, body) if _is_teacher(user) else (403, {'error': 'Only teachers can remove students.'}),
    'respond': lambda conn, user, body, labs: respond(conn, user, body),
    'leave': lambda conn, user, body, labs: leave(conn, user, body),
    'assign': lambda conn, user, body, labs: assign(conn, user, body, labs),
    'delete': lambda conn, user, body, labs: delete_assignment(conn, user, body) if _is_teacher(user) else (403, {'error': 'Only teachers can delete assignments.'}),
    'submit': lambda conn, user, body, labs: submit(conn, user, body),
}
