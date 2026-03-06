from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime
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
    <meta name="theme-color" content="#0a0a1a">
    <title>TO Fine Tracker</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-primary: #0a0a1a;
            --bg-secondary: #111128;
            --bg-card: rgba(255, 255, 255, 0.04);
            --bg-card-hover: rgba(255, 255, 255, 0.07);
            --border-glass: rgba(255, 255, 255, 0.08);
            --border-glass-hover: rgba(255, 255, 255, 0.15);
            --text-primary: #f0f0f8;
            --text-secondary: rgba(240, 240, 248, 0.6);
            --text-muted: rgba(240, 240, 248, 0.35);
            --neon-blue: #00d4ff;
            --neon-pink: #ff2d78;
            --neon-green: #00ff88;
            --neon-blue-glow: rgba(0, 212, 255, 0.25);
            --neon-pink-glow: rgba(255, 45, 120, 0.25);
            --neon-green-glow: rgba(0, 255, 136, 0.25);
            --neon-blue-subtle: rgba(0, 212, 255, 0.08);
            --neon-pink-subtle: rgba(255, 45, 120, 0.08);
            --neon-green-subtle: rgba(0, 255, 136, 0.08);
            --radius-sm: 12px;
            --radius-md: 16px;
            --radius-lg: 24px;
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-bottom: env(safe-area-inset-bottom, 0px);
        }

        html { background: var(--bg-primary); }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            min-height: 100dvh;
            overflow-x: hidden;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        .bg-mesh {
            position: fixed;
            inset: 0;
            z-index: 0;
            overflow: hidden;
            pointer-events: none;
        }
        .bg-mesh .orb {
            position: absolute;
            border-radius: 50%;
            filter: blur(80px);
            opacity: 0.3;
            animation: orbFloat 20s ease-in-out infinite alternate;
        }
        .bg-mesh .orb-1 { width: 300px; height: 300px; background: var(--neon-blue); top: -80px; left: -60px; animation-delay: 0s; }
        .bg-mesh .orb-2 { width: 250px; height: 250px; background: var(--neon-pink); bottom: 20%; right: -80px; animation-delay: -7s; }
        .bg-mesh .orb-3 { width: 200px; height: 200px; background: var(--neon-green); bottom: -60px; left: 30%; animation-delay: -14s; }

        @keyframes orbFloat {
            0% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -20px) scale(1.05); }
            66% { transform: translate(-20px, 30px) scale(0.95); }
            100% { transform: translate(10px, -10px) scale(1.02); }
        }

        .app-container {
            position: relative;
            z-index: 1;
            max-width: 480px;
            margin: 0 auto;
            padding: 0 16px;
            padding-top: calc(var(--safe-top) + 16px);
            padding-bottom: calc(var(--safe-bottom) + 100px);
        }

        .app-header {
            text-align: center;
            padding: 24px 0 8px;
            animation: slideDown 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }
        .app-header .logo-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 56px;
            height: 56px;
            border-radius: 18px;
            background: linear-gradient(135deg, var(--neon-blue), var(--neon-pink));
            margin-bottom: 12px;
            font-size: 28px;
            box-shadow: 0 8px 32px var(--neon-blue-glow);
        }
        .app-header h1 {
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.5px;
            background: linear-gradient(135deg, var(--text-primary), var(--neon-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .app-header .subtitle {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
            font-weight: 400;
        }

        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(40px) saturate(1.4);
            -webkit-backdrop-filter: blur(40px) saturate(1.4);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 16px;
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.3s ease, box-shadow 0.3s ease;
        }
        .glass-card:hover {
            border-color: var(--border-glass-hover);
        }

        .section-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border-glass);
        }
        .section-label .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .section-label.blue { color: var(--neon-blue); }
        .section-label.blue .dot { background: var(--neon-blue); box-shadow: 0 0 8px var(--neon-blue-glow); }
        .section-label.pink { color: var(--neon-pink); }
        .section-label.pink .dot { background: var(--neon-pink); box-shadow: 0 0 8px var(--neon-pink-glow); }
        .section-label.green { color: var(--neon-green); }
        .section-label.green .dot { background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green-glow); }

        .form-group { margin-bottom: 14px; }
        .form-group label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .form-group input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            font-size: 15px;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            outline: none;
            transition: border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
        }
        .form-group input::placeholder { color: var(--text-muted); }
        .form-group input:focus {
            border-color: var(--neon-blue);
            box-shadow: 0 0 0 3px var(--neon-blue-subtle), 0 0 20px var(--neon-blue-subtle);
            background: rgba(0, 212, 255, 0.03);
        }
        .form-group input[type="date"] {
            color-scheme: dark;
        }
        .form-group input[type="date"]::-webkit-calendar-picker-indicator {
            filter: invert(1);
            opacity: 0.5;
        }

        .btn-primary {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: var(--radius-sm);
            font-family: 'Inter', sans-serif;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .btn-primary:active { transform: scale(0.97); }
        .btn-save-profile {
            background: linear-gradient(135deg, var(--neon-blue), #0090ff);
            color: #fff;
            box-shadow: 0 4px 20px var(--neon-blue-glow);
        }
        .btn-save-profile:hover { box-shadow: 0 6px 30px rgba(0, 212, 255, 0.4); }
        .btn-add-reminder {
            background: linear-gradient(135deg, var(--neon-green), #00cc6a);
            color: #0a0a1a;
            box-shadow: 0 4px 20px var(--neon-green-glow);
        }
        .btn-add-reminder:hover { box-shadow: 0 6px 30px rgba(0, 255, 136, 0.4); }

        .profile-saved {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: var(--neon-blue-subtle);
            border: 1px solid rgba(0, 212, 255, 0.15);
            border-radius: var(--radius-sm);
            margin-bottom: 14px;
            font-size: 13px;
            color: var(--neon-blue);
            font-weight: 500;
            animation: bounceIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .profile-saved.show { display: flex; }

        .reminder-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            margin-bottom: 8px;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.2s ease;
            animation: slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
        }
        .reminder-item:hover { background: rgba(255, 255, 255, 0.05); }
        .reminder-info { flex: 1; }
        .reminder-info .reminder-ticket {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
        }
        .reminder-info .reminder-meta {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        .reminder-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }
        .badge-upcoming {
            background: var(--neon-green-subtle);
            color: var(--neon-green);
            border: 1px solid rgba(0, 255, 136, 0.15);
        }
        .badge-overdue {
            background: var(--neon-pink-subtle);
            color: var(--neon-pink);
            border: 1px solid rgba(255, 45, 120, 0.15);
        }
        .badge-today {
            background: rgba(255, 200, 0, 0.08);
            color: #ffc800;
            border: 1px solid rgba(255, 200, 0, 0.15);
        }
        .reminder-delete {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 18px;
            padding: 4px 8px;
            margin-left: 8px;
            border-radius: 8px;
            transition: color 0.2s, background 0.2s;
        }
        .reminder-delete:hover {
            color: var(--neon-pink);
            background: var(--neon-pink-subtle);
        }

        .empty-state {
            text-align: center;
            padding: 24px 16px;
            color: var(--text-muted);
            font-size: 13px;
        }
        .empty-state .empty-icon {
            font-size: 32px;
            margin-bottom: 8px;
            opacity: 0.5;
        }

        .link-grid { display: flex; flex-direction: column; gap: 8px; }
        .link-btn {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            color: var(--text-primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.2s ease, border-color 0.2s ease, box-shadow 0.3s ease;
        }
        .link-btn:active { transform: scale(0.98); }
        .link-btn .link-icon {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }
        .link-btn .link-text { flex: 1; }
        .link-btn .link-arrow {
            color: var(--text-muted);
            font-size: 18px;
            transition: transform 0.2s ease;
        }
        .link-btn:hover .link-arrow { transform: translateX(3px); }

        .link-btn.blue-link:hover {
            border-color: rgba(0, 212, 255, 0.2);
            background: var(--neon-blue-subtle);
            box-shadow: 0 4px 20px var(--neon-blue-subtle);
        }
        .link-btn.blue-link .link-icon {
            background: var(--neon-blue-subtle);
            color: var(--neon-blue);
        }
        .link-btn.pink-link:hover {
            border-color: rgba(255, 45, 120, 0.2);
            background: var(--neon-pink-subtle);
            box-shadow: 0 4px 20px var(--neon-pink-subtle);
        }
        .link-btn.pink-link .link-icon {
            background: var(--neon-pink-subtle);
            color: var(--neon-pink);
        }
        .link-btn.green-link:hover {
            border-color: rgba(0, 255, 136, 0.2);
            background: var(--neon-green-subtle);
            box-shadow: 0 4px 20px var(--neon-green-subtle);
        }
        .link-btn.green-link .link-icon {
            background: var(--neon-green-subtle);
            color: var(--neon-green);
        }

        .nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            background: rgba(10, 10, 26, 0.85);
            backdrop-filter: blur(30px) saturate(1.5);
            -webkit-backdrop-filter: blur(30px) saturate(1.5);
            border-top: 1px solid var(--border-glass);
            padding: 8px 0;
            padding-bottom: calc(8px + var(--safe-bottom));
        }
        .nav-inner {
            display: flex;
            justify-content: space-around;
            max-width: 480px;
            margin: 0 auto;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 6px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s ease;
            border: none;
            background: none;
            color: var(--text-muted);
            font-family: 'Inter', sans-serif;
        }
        .nav-item.active { color: var(--neon-blue); }
        .nav-item .nav-icon { font-size: 22px; }
        .nav-item .nav-label { font-size: 10px; font-weight: 600; letter-spacing: 0.3px; }

        .tab-content { display: none; }
        .tab-content.active { display: block; animation: fadeIn 0.3s ease; }

        .stagger-1 { animation-delay: 0.05s; }
        .stagger-2 { animation-delay: 0.1s; }
        .stagger-3 { animation-delay: 0.15s; }
        .stagger-4 { animation-delay: 0.2s; }
        .stagger-5 { animation-delay: 0.25s; }

        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes bounceIn {
            from { opacity: 0; transform: scale(0.9); }
            to { opacity: 1; transform: scale(1); }
        }

        .toast {
            position: fixed;
            top: calc(var(--safe-top) + 16px);
            left: 50%;
            transform: translateX(-50%) translateY(-100px);
            z-index: 200;
            padding: 12px 24px;
            border-radius: var(--radius-sm);
            font-size: 13px;
            font-weight: 600;
            pointer-events: none;
            transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
            opacity: 0;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
        .toast-success {
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid rgba(0, 255, 136, 0.3);
            color: var(--neon-green);
        }

        @media (max-width: 380px) {
            .app-container { padding: 0 12px; }
            .glass-card { padding: 16px; }
        }
    </style>
</head>
<body>
    <div class="bg-mesh">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
    </div>

    <div id="toast" class="toast toast-success"></div>

    <div class="app-container">
        <div class="app-header">
            <div class="logo-icon">&#x1F698;</div>
            <h1>TO Fine Tracker</h1>
            <p class="subtitle">Toronto Traffic Fine Management</p>
        </div>

        <!-- TAB: Dashboard -->
        <div id="tab-dashboard" class="tab-content active">
            <div class="glass-card stagger-1" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.05s both;">
                <div class="section-label blue">
                    <span class="dot"></span>
                    My Profile
                </div>
                <form id="profile-form" action="/save-profile" method="POST">
                    <div id="profile-saved" class="profile-saved {% if profile_saved %}show{% endif %}">
                        &#x2713; Profile saved
                    </div>
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" name="name" placeholder="Enter your name" value="{{ profile.name }}" required>
                    </div>
                    <div class="form-group">
                        <label>License Plate</label>
                        <input type="text" name="plate" placeholder="e.g. ABCD 123" value="{{ profile.plate }}" required style="text-transform: uppercase;">
                    </div>
                    <button type="submit" class="btn-primary btn-save-profile">Save Profile</button>
                </form>
            </div>

            <div class="glass-card stagger-2" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.1s both;">
                <div class="section-label green">
                    <span class="dot"></span>
                    Add Fine Reminder
                </div>
                <form id="reminder-form" action="/add-reminder" method="POST">
                    <div class="form-group">
                        <label>Ticket / Reference Number</label>
                        <input type="text" name="ticket_num" placeholder="e.g. TK-12345" required>
                    </div>
                    <div class="form-group">
                        <label>Due Date</label>
                        <input type="date" name="due_date" required>
                    </div>
                    <button type="submit" class="btn-primary btn-add-reminder">Add Reminder</button>
                </form>
            </div>

            <div class="glass-card stagger-3" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.15s both;">
                <div class="section-label pink">
                    <span class="dot"></span>
                    My Reminders
                </div>
                {% if reminders %}
                    {% for r in reminders %}
                        <div class="reminder-item" style="animation-delay: {{ loop.index * 0.05 }}s;">
                            <div class="reminder-info">
                                <div class="reminder-ticket">{{ r.ticket_num }}</div>
                                <div class="reminder-meta">Due {{ r.due_date_display }}</div>
                            </div>
                            <span class="reminder-badge {{ r.badge_class }}">{{ r.badge_text }}</span>
                            <form action="/delete-reminder" method="POST" style="display:inline;">
                                <input type="hidden" name="index" value="{{ loop.index0 }}">
                                <button type="submit" class="reminder-delete" title="Delete">&times;</button>
                            </form>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="empty-state">
                        <div class="empty-icon">&#x1F4CB;</div>
                        <p>No reminders yet. Add one above!</p>
                    </div>
                {% endif %}
            </div>
        </div>

        <!-- TAB: Services -->
        <div id="tab-services" class="tab-content">
            <div class="glass-card" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.05s both;">
                <div class="section-label blue">
                    <span class="dot"></span>
                    Parking Violations
                </div>
                <div class="link-grid">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/pay-your-parking-violation/" target="_blank" rel="noopener" class="link-btn blue-link">
                        <div class="link-icon">&#x1F4B3;</div>
                        <span class="link-text">Pay Parking Ticket</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/dispute-your-parking-violation/" target="_blank" rel="noopener" class="link-btn blue-link">
                        <div class="link-icon">&#x2696;</div>
                        <span class="link-text">Dispute Ticket</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/about-parking-violations/" target="_blank" rel="noopener" class="link-btn blue-link">
                        <div class="link-icon">&#x2139;</div>
                        <span class="link-text">About Parking Violations</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="glass-card" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.1s both;">
                <div class="section-label pink">
                    <span class="dot"></span>
                    Speed & Red Light Cameras
                </div>
                <div class="link-grid">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/" target="_blank" rel="noopener" class="link-btn pink-link">
                        <div class="link-icon">&#x1F4F7;</div>
                        <span class="link-text">Pay Camera Fine</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="link-btn pink-link">
                        <div class="link-icon">&#x2696;</div>
                        <span class="link-text">Dispute Camera Fine</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="link-btn pink-link">
                        <div class="link-icon">&#x2139;</div>
                        <span class="link-text">About Camera Penalties</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="glass-card" style="animation: slideUp 0.5s cubic-bezier(0.34,1.56,0.64,1) 0.15s both;">
                <div class="section-label green">
                    <span class="dot"></span>
                    Court Services
                </div>
                <div class="link-grid">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/" target="_blank" rel="noopener" class="link-btn green-link">
                        <div class="link-icon">&#x1F3DB;</div>
                        <span class="link-text">Court Services & Provincial Offences</span>
                        <span class="link-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>
        </div>
    </div>

    <nav class="nav-bar">
        <div class="nav-inner">
            <button class="nav-item active" onclick="switchTab('dashboard', this)">
                <span class="nav-icon">&#x1F3E0;</span>
                <span class="nav-label">Dashboard</span>
            </button>
            <button class="nav-item" onclick="switchTab('services', this)">
                <span class="nav-icon">&#x1F517;</span>
                <span class="nav-label">Services</span>
            </button>
        </div>
    </nav>

    <script>
        function switchTab(tab, btn) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
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
    for r in users_data['reminders']:
        badge_class, badge_text = get_badge_info(r['due_date'])
        reminders.append({
            'ticket_num': r['ticket_num'],
            'due_date': r['due_date'],
            'due_date_display': format_date_display(r['due_date']),
            'badge_class': badge_class,
            'badge_text': badge_text,
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
