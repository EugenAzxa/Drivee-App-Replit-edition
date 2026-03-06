from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from urllib.parse import quote
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

users_data = {
    'profile': {'name': '', 'plate': ''},
    'reminders': []
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#101014">
    <title>TO Fine Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-root: #101014;
            --bg-surface: #18181c;
            --bg-elevated: #1f1f24;
            --bg-input: #141418;
            --border: rgba(255,255,255,0.06);
            --border-focus: rgba(255,255,255,0.18);
            --text-primary: #ececf0;
            --text-secondary: #8e8e99;
            --text-tertiary: #5a5a66;
            --accent: #4f8cff;
            --accent-hover: #6aa0ff;
            --accent-subtle: rgba(79,140,255,0.08);
            --accent-muted: rgba(79,140,255,0.15);
            --danger: #ef4444;
            --danger-subtle: rgba(239,68,68,0.08);
            --warning: #f59e0b;
            --warning-subtle: rgba(245,158,11,0.08);
            --success: #22c55e;
            --success-subtle: rgba(34,197,94,0.08);
            --radius: 10px;
            --radius-lg: 14px;
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --font: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        html { background: var(--bg-root); }

        body {
            font-family: var(--font);
            background: var(--bg-root);
            color: var(--text-primary);
            min-height: 100vh;
            min-height: 100dvh;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
        }

        .app {
            max-width: 460px;
            margin: 0 auto;
            padding: 0 20px;
            padding-top: calc(var(--safe-top) + 12px);
            padding-bottom: calc(var(--safe-bottom) + 88px);
        }

        .header {
            padding: 20px 0 24px;
            animation: fadeIn 0.5s ease both;
        }
        .header-top {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .header-icon {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }
        .header-text h1 {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
            line-height: 1.2;
        }
        .header-text p {
            font-size: 13px;
            color: var(--text-tertiary);
            font-weight: 400;
            margin-top: 1px;
        }

        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 12px;
            animation: slideUp 0.4s ease both;
        }
        .card-1 { animation-delay: 0.05s; }
        .card-2 { animation-delay: 0.1s; }
        .card-3 { animation-delay: 0.15s; }

        .card-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: var(--text-tertiary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-label::before {
            content: '';
            width: 3px;
            height: 14px;
            border-radius: 2px;
            flex-shrink: 0;
        }
        .card-label.label-blue::before { background: var(--accent); }
        .card-label.label-green::before { background: var(--success); }
        .card-label.label-amber::before { background: var(--warning); }

        .field { margin-bottom: 12px; }
        .field label {
            display: block;
            font-size: 12px;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        .field input {
            width: 100%;
            padding: 12px 14px;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            font-weight: 500;
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .field input::placeholder { color: var(--text-tertiary); }
        .field input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-subtle);
        }
        .field input[type="date"] { color-scheme: dark; }
        .field input[type="date"]::-webkit-calendar-picker-indicator {
            filter: invert(0.7);
            opacity: 0.6;
            cursor: pointer;
        }

        .btn {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: var(--radius);
            font-family: var(--font);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease, transform 0.15s ease;
            letter-spacing: 0.3px;
        }
        .btn:active { transform: scale(0.98); }
        .btn-accent {
            background: var(--accent);
            color: #fff;
        }
        .btn-accent:hover { background: var(--accent-hover); }
        .btn-surface {
            background: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        .btn-surface:hover { border-color: var(--border-focus); }

        .saved-banner {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            background: var(--success-subtle);
            border: 1px solid rgba(34,197,94,0.12);
            border-radius: var(--radius);
            margin-bottom: 12px;
            font-size: 13px;
            color: var(--success);
            font-weight: 500;
        }
        .saved-banner.show { display: flex; }

        .reminder {
            padding: 14px;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            margin-bottom: 8px;
            animation: slideUp 0.35s ease both;
        }
        .reminder-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .reminder-info { flex: 1; min-width: 0; }
        .reminder-ticket {
            font-size: 14px;
            font-weight: 600;
            font-family: var(--font-mono);
            color: var(--text-primary);
            letter-spacing: 0.3px;
        }
        .reminder-date {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        .badge {
            font-size: 10px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            flex-shrink: 0;
            line-height: 1.4;
        }
        .badge-upcoming {
            background: var(--success-subtle);
            color: var(--success);
        }
        .badge-overdue {
            background: var(--danger-subtle);
            color: var(--danger);
        }
        .badge-today {
            background: var(--warning-subtle);
            color: var(--warning);
        }
        .reminder-del {
            background: none;
            border: none;
            color: var(--text-tertiary);
            cursor: pointer;
            font-size: 16px;
            padding: 4px 6px;
            border-radius: 6px;
            transition: color 0.15s, background 0.15s;
            line-height: 1;
        }
        .reminder-del:hover {
            color: var(--danger);
            background: var(--danger-subtle);
        }
        .reminder-cal {
            display: flex;
            gap: 6px;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid var(--border);
        }
        .cal-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            font-family: var(--font);
            text-decoration: none;
            cursor: pointer;
            border: 1px solid var(--border);
            background: var(--bg-surface);
            color: var(--text-secondary);
            transition: border-color 0.15s, color 0.15s, background 0.15s;
        }
        .cal-btn:hover {
            border-color: var(--border-focus);
            color: var(--text-primary);
            background: var(--bg-elevated);
        }
        .cal-btn svg {
            width: 13px;
            height: 13px;
            flex-shrink: 0;
        }

        .empty {
            text-align: center;
            padding: 28px 16px;
            color: var(--text-tertiary);
            font-size: 13px;
        }

        .service-list { display: flex; flex-direction: column; gap: 6px; }
        .service-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 13px 14px;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            color: var(--text-primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: border-color 0.15s ease, background 0.15s ease;
        }
        .service-link:hover {
            border-color: var(--border-focus);
            background: rgba(255,255,255,0.03);
        }
        .service-link .svc-icon {
            width: 34px;
            height: 34px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
            background: var(--bg-surface);
            border: 1px solid var(--border);
        }
        .service-link .svc-text { flex: 1; }
        .service-link .svc-arrow {
            color: var(--text-tertiary);
            font-size: 14px;
            transition: transform 0.15s ease;
        }
        .service-link:hover .svc-arrow { transform: translateX(2px); }

        .section-divider {
            height: 1px;
            background: var(--border);
            margin: 8px 0;
        }

        .nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(16,16,20,0.92);
            backdrop-filter: blur(24px) saturate(1.2);
            -webkit-backdrop-filter: blur(24px) saturate(1.2);
            border-top: 1px solid var(--border);
            padding: 6px 0;
            padding-bottom: calc(6px + var(--safe-bottom));
        }
        .nav-inner {
            display: flex;
            justify-content: center;
            gap: 8px;
            max-width: 460px;
            margin: 0 auto;
        }
        .nav-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 20px;
            border-radius: 8px;
            cursor: pointer;
            border: 1px solid transparent;
            background: none;
            color: var(--text-tertiary);
            font-family: var(--font);
            font-size: 13px;
            font-weight: 500;
            transition: color 0.15s, background 0.15s, border-color 0.15s;
        }
        .nav-btn:hover { color: var(--text-secondary); }
        .nav-btn.active {
            color: var(--text-primary);
            background: var(--bg-elevated);
            border-color: var(--border);
        }
        .nav-btn svg {
            width: 18px;
            height: 18px;
        }

        .tab { display: none; }
        .tab.active { display: block; animation: fadeIn 0.25s ease; }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .toast {
            position: fixed;
            top: calc(var(--safe-top) + 12px);
            left: 50%;
            transform: translateX(-50%) translateY(-60px);
            z-index: 200;
            padding: 10px 20px;
            border-radius: var(--radius);
            font-size: 13px;
            font-weight: 500;
            pointer-events: none;
            transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.25s ease;
            opacity: 0;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        @media (max-width: 380px) {
            .app { padding: 0 14px; padding-bottom: calc(var(--safe-bottom) + 80px); }
            .card { padding: 16px; }
        }
    </style>
</head>
<body>
    <div id="toast" class="toast"></div>

    <div class="app">
        <div class="header">
            <div class="header-top">
                <div class="header-icon">&#x1F698;</div>
                <div class="header-text">
                    <h1>TO Fine Tracker</h1>
                    <p>Toronto Traffic Fine Management</p>
                </div>
            </div>
        </div>

        <div id="tab-dashboard" class="tab active">
            <div class="card card-1">
                <div class="card-label label-blue">Profile</div>
                <form action="/save-profile" method="POST">
                    <div class="saved-banner {% if profile_saved %}show{% endif %}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                        Profile saved
                    </div>
                    <div class="field">
                        <label>Full Name</label>
                        <input type="text" name="name" placeholder="Your name" value="{{ profile.name }}" required>
                    </div>
                    <div class="field">
                        <label>License Plate</label>
                        <input type="text" name="plate" placeholder="e.g. ABCD 123" value="{{ profile.plate }}" required style="text-transform: uppercase; font-family: var(--font-mono);">
                    </div>
                    <button type="submit" class="btn btn-accent">Save Profile</button>
                </form>
            </div>

            <div class="card card-2">
                <div class="card-label label-green">Add Fine Reminder</div>
                <form action="/add-reminder" method="POST">
                    <div class="field">
                        <label>Ticket / Reference Number</label>
                        <input type="text" name="ticket_num" placeholder="e.g. TK-12345" required style="font-family: var(--font-mono);">
                    </div>
                    <div class="field">
                        <label>Due Date</label>
                        <input type="date" name="due_date" required>
                    </div>
                    <button type="submit" class="btn btn-surface">Add Reminder</button>
                </form>
            </div>

            <div class="card card-3">
                <div class="card-label label-amber">Reminders</div>
                {% if reminders %}
                    {% for r in reminders %}
                        <div class="reminder" style="animation-delay: {{ 0.15 + loop.index * 0.04 }}s;">
                            <div class="reminder-row">
                                <div class="reminder-info">
                                    <div class="reminder-ticket">{{ r.ticket_num }}</div>
                                    <div class="reminder-date">Due {{ r.due_date_display }}</div>
                                </div>
                                <span class="badge {{ r.badge_class }}">{{ r.badge_text }}</span>
                                <form action="/delete-reminder" method="POST" style="display:inline;">
                                    <input type="hidden" name="index" value="{{ loop.index0 }}">
                                    <button type="submit" class="reminder-del" title="Delete">&times;</button>
                                </form>
                            </div>
                            <div class="reminder-cal">
                                <a href="{{ r.gcal_url }}" target="_blank" rel="noopener" class="cal-btn">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                    Google Calendar
                                </a>
                                <a href="/calendar/ics/{{ loop.index0 }}" class="cal-btn" download>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                                    Download .ics
                                </a>
                            </div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty">No reminders yet</div>
                {% endif %}
            </div>
        </div>

        <div id="tab-services" class="tab">
            <div class="card card-1">
                <div class="card-label label-blue">Parking Violations</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/pay-your-parking-violation/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x1F4B3;</div>
                        <span class="svc-text">Pay Parking Ticket</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/dispute-your-parking-violation/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x2696;</div>
                        <span class="svc-text">Dispute Ticket</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/about-parking-violations/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x2139;</div>
                        <span class="svc-text">About Parking Violations</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-2">
                <div class="card-label label-amber">Speed & Red Light Cameras</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x1F4F7;</div>
                        <span class="svc-text">Pay Camera Fine</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x2696;</div>
                        <span class="svc-text">Dispute Camera Fine</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x2139;</div>
                        <span class="svc-text">About Camera Penalties</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-3">
                <div class="card-label label-green">Court Services</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/" target="_blank" rel="noopener" class="service-link">
                        <div class="svc-icon">&#x1F3DB;</div>
                        <span class="svc-text">Court Services & Provincial Offences</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <nav class="nav">
        <div class="nav-inner">
            <button class="nav-btn active" onclick="switchTab('dashboard', this)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                Dashboard
            </button>
            <button class="nav-btn" onclick="switchTab('services', this)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                Services
            </button>
        </div>
    </nav>

    <script>
        function switchTab(tab, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(n => n.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            btn.classList.add('active');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }

        const params = new URLSearchParams(window.location.search);
        if (params.get('saved') === 'profile') showToast('Profile saved successfully');
        if (params.get('saved') === 'reminder') showToast('Reminder added');
        if (params.get('deleted') === '1') showToast('Reminder deleted');
        if (params.has('saved') || params.has('deleted')) {
            history.replaceState(null, '', '/');
        }
    </script>
</body>
</html>
"""

def build_gcal_url(ticket_num, due_date_str, plate=''):
    try:
        due = datetime.strptime(due_date_str, '%Y-%m-%d')
    except ValueError:
        due = datetime.now()
    date_str = due.strftime('%Y%m%d')
    title = quote(f'Toronto Fine Due: {ticket_num}')
    details = quote(f'Ticket: {ticket_num}' + (f'\\nPlate: {plate}' if plate else '') + '\\n\\nPay at: https://www.toronto.ca/services-payments/tickets-fines-penalties/')
    location = quote('Toronto, ON')
    return f'https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={date_str}/{date_str}&details={details}&location={location}'

def build_ics_content(ticket_num, due_date_str, plate=''):
    try:
        due = datetime.strptime(due_date_str, '%Y-%m-%d')
    except ValueError:
        due = datetime.now()
    date_str = due.strftime('%Y%m%d')
    now_str = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    desc = f'Ticket: {ticket_num}'
    if plate:
        desc += f'\\nPlate: {plate}'
    desc += '\\nPay at: https://www.toronto.ca/services-payments/tickets-fines-penalties/'
    uid = f'{ticket_num}-{date_str}@tofinetracker'
    alarm_date = due - timedelta(days=1)
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//TO Fine Tracker//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'DTSTART;VALUE=DATE:{date_str}',
        f'DTEND;VALUE=DATE:{date_str}',
        f'DTSTAMP:{now_str}',
        f'UID:{uid}',
        f'SUMMARY:Toronto Fine Due: {ticket_num}',
        f'DESCRIPTION:{desc}',
        'LOCATION:Toronto\\, ON',
        'STATUS:CONFIRMED',
        'BEGIN:VALARM',
        'TRIGGER:-P1D',
        'ACTION:DISPLAY',
        f'DESCRIPTION:Fine payment due tomorrow: {ticket_num}',
        'END:VALARM',
        'BEGIN:VALARM',
        'TRIGGER:-PT0M',
        'ACTION:DISPLAY',
        f'DESCRIPTION:Fine payment due today: {ticket_num}',
        'END:VALARM',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    return '\r\n'.join(lines)

def get_badge_info(due_date_str):
    try:
        due = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        diff = (due - today).days
        if diff < 0:
            return 'badge-overdue', 'Overdue'
        elif diff == 0:
            return 'badge-today', 'Today'
        elif diff <= 7:
            return 'badge-upcoming', f'{diff}d left'
        else:
            return 'badge-upcoming', 'Upcoming'
    except ValueError:
        return 'badge-upcoming', 'Upcoming'

def format_date_display(due_date_str):
    try:
        due = datetime.strptime(due_date_str, '%Y-%m-%d')
        return due.strftime('%b %d, %Y')
    except ValueError:
        return due_date_str

@app.route('/')
def index():
    reminders = []
    plate = users_data['profile'].get('plate', '')
    for r in users_data['reminders']:
        badge_class, badge_text = get_badge_info(r['due_date'])
        reminders.append({
            'ticket_num': r['ticket_num'],
            'due_date': r['due_date'],
            'due_date_display': format_date_display(r['due_date']),
            'badge_class': badge_class,
            'badge_text': badge_text,
            'gcal_url': build_gcal_url(r['ticket_num'], r['due_date'], plate),
        })
    profile_saved = request.args.get('saved') == 'profile'
    return render_template_string(HTML_TEMPLATE,
        profile=users_data['profile'],
        reminders=reminders,
        profile_saved=profile_saved
    )

@app.route('/save-profile', methods=['POST'])
def save_profile():
    users_data['profile']['name'] = request.form.get('name', '').strip()
    users_data['profile']['plate'] = request.form.get('plate', '').strip().upper()
    return redirect('/?saved=profile')

@app.route('/add-reminder', methods=['POST'])
def add_reminder():
    ticket_num = request.form.get('ticket_num', '').strip()
    due_date = request.form.get('due_date', '').strip()
    if ticket_num and due_date:
        users_data['reminders'].append({
            'ticket_num': ticket_num,
            'due_date': due_date,
        })
    return redirect('/?saved=reminder')

@app.route('/delete-reminder', methods=['POST'])
def delete_reminder():
    try:
        idx = int(request.form.get('index', -1))
        if 0 <= idx < len(users_data['reminders']):
            users_data['reminders'].pop(idx)
    except (ValueError, IndexError):
        pass
    return redirect('/?deleted=1')

@app.route('/calendar/ics/<int:index>')
def download_ics(index):
    if 0 <= index < len(users_data['reminders']):
        r = users_data['reminders'][index]
        plate = users_data['profile'].get('plate', '')
        ics_content = build_ics_content(r['ticket_num'], r['due_date'], plate)
        filename = f"fine-reminder-{r['ticket_num']}.ics"
        return Response(
            ics_content,
            mimetype='text/calendar',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
