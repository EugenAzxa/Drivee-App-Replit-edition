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
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
    <script src="https://unpkg.com/tesseract.js@v4.0.1/dist/tesseract.min.js"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-root: #0c0c10;
            --bg-surface: #16161b;
            --bg-elevated: #1e1e25;
            --bg-input: #121216;
            --border: rgba(255,255,255,0.07);
            --border-focus: rgba(255,255,255,0.18);
            --text-primary: #f0f0f5;
            --text-secondary: #9898a8;
            --text-tertiary: #5c5c6e;
            --blue: #5b9aff;
            --blue-vivid: #3d85ff;
            --blue-subtle: rgba(91,154,255,0.10);
            --blue-glow: rgba(91,154,255,0.20);
            --purple: #a78bfa;
            --purple-subtle: rgba(167,139,250,0.10);
            --purple-glow: rgba(167,139,250,0.18);
            --teal: #2dd4bf;
            --teal-subtle: rgba(45,212,191,0.10);
            --teal-glow: rgba(45,212,191,0.18);
            --rose: #f43f5e;
            --rose-subtle: rgba(244,63,94,0.10);
            --rose-glow: rgba(244,63,94,0.18);
            --amber: #fbbf24;
            --amber-subtle: rgba(251,191,36,0.10);
            --amber-glow: rgba(251,191,36,0.18);
            --green: #34d399;
            --green-subtle: rgba(52,211,153,0.10);
            --green-glow: rgba(52,211,153,0.18);
            --orange: #fb923c;
            --orange-subtle: rgba(251,146,60,0.10);
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
            width: 46px;
            height: 46px;
            border-radius: 13px;
            background: linear-gradient(135deg, var(--blue-vivid), var(--purple));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
            box-shadow: 0 4px 16px var(--blue-glow);
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
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 2px;
        }

        .card {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 20px;
            margin-bottom: 12px;
            animation: slideUp 0.4s ease both;
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
        }
        .card-blue::before { background: linear-gradient(90deg, var(--blue), var(--purple)); }
        .card-teal::before { background: linear-gradient(90deg, var(--teal), var(--green)); }
        .card-amber::before { background: linear-gradient(90deg, var(--amber), var(--orange)); }
        .card-rose::before { background: linear-gradient(90deg, var(--rose), var(--orange)); }
        .card-purple::before { background: linear-gradient(90deg, var(--purple), var(--rose)); }
        .card-green::before { background: linear-gradient(90deg, var(--green), var(--teal)); }
        .card-1 { animation-delay: 0.05s; }
        .card-2 { animation-delay: 0.1s; }
        .card-3 { animation-delay: 0.15s; }

        .card-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-label.label-blue { color: var(--blue); }
        .card-label.label-teal { color: var(--teal); }
        .card-label.label-amber { color: var(--amber); }
        .card-label.label-rose { color: var(--rose); }
        .card-label.label-purple { color: var(--purple); }
        .card-label.label-green { color: var(--green); }

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
            border-color: var(--blue);
            box-shadow: 0 0 0 3px var(--blue-subtle);
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
        .btn-blue {
            background: linear-gradient(135deg, var(--blue-vivid), var(--blue));
            color: #fff;
            box-shadow: 0 2px 12px var(--blue-glow);
        }
        .btn-blue:hover { box-shadow: 0 4px 20px rgba(91,154,255,0.30); }
        .btn-teal {
            background: linear-gradient(135deg, var(--teal), var(--green));
            color: #0c0c10;
            box-shadow: 0 2px 12px var(--teal-glow);
        }
        .btn-teal:hover { box-shadow: 0 4px 20px rgba(45,212,191,0.30); }

        .saved-banner {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            background: var(--green-subtle);
            border: 1px solid rgba(52,211,153,0.15);
            border-radius: var(--radius);
            margin-bottom: 12px;
            font-size: 13px;
            color: var(--green);
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
            background: var(--green-subtle);
            color: var(--green);
            border: 1px solid rgba(52,211,153,0.12);
        }
        .badge-overdue {
            background: var(--rose-subtle);
            color: var(--rose);
            border: 1px solid rgba(244,63,94,0.12);
        }
        .badge-today {
            background: var(--amber-subtle);
            color: var(--amber);
            border: 1px solid rgba(251,191,36,0.12);
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
            color: var(--rose);
            background: var(--rose-subtle);
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
            transition: border-color 0.15s, color 0.15s, background 0.15s, box-shadow 0.15s;
        }
        .cal-btn svg {
            width: 13px;
            height: 13px;
            flex-shrink: 0;
        }
        .cal-btn-gcal {
            border: 1px solid rgba(91,154,255,0.15);
            background: var(--blue-subtle);
            color: var(--blue);
        }
        .cal-btn-gcal:hover {
            border-color: rgba(91,154,255,0.30);
            background: rgba(91,154,255,0.14);
            box-shadow: 0 2px 10px var(--blue-subtle);
        }
        .cal-btn-ics {
            border: 1px solid rgba(167,139,250,0.15);
            background: var(--purple-subtle);
            color: var(--purple);
        }
        .cal-btn-ics:hover {
            border-color: rgba(167,139,250,0.30);
            background: rgba(167,139,250,0.14);
            box-shadow: 0 2px 10px var(--purple-subtle);
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
            transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
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
        }
        .service-link .svc-text { flex: 1; }
        .service-link .svc-arrow {
            color: var(--text-tertiary);
            font-size: 14px;
            transition: transform 0.15s ease, color 0.15s ease;
        }
        .service-link:hover .svc-arrow { transform: translateX(2px); }
        .svc-blue .svc-icon { background: var(--blue-subtle); color: var(--blue); }
        .svc-blue:hover { border-color: rgba(91,154,255,0.20); background: rgba(91,154,255,0.04); }
        .svc-blue:hover .svc-arrow { color: var(--blue); }
        .svc-rose .svc-icon { background: var(--rose-subtle); color: var(--rose); }
        .svc-rose:hover { border-color: rgba(244,63,94,0.20); background: rgba(244,63,94,0.04); }
        .svc-rose:hover .svc-arrow { color: var(--rose); }
        .svc-purple .svc-icon { background: var(--purple-subtle); color: var(--purple); }
        .svc-purple:hover { border-color: rgba(167,139,250,0.20); background: rgba(167,139,250,0.04); }
        .svc-purple:hover .svc-arrow { color: var(--purple); }
        .svc-amber .svc-icon { background: var(--amber-subtle); color: var(--amber); }
        .svc-amber:hover { border-color: rgba(251,191,36,0.20); background: rgba(251,191,36,0.04); }
        .svc-amber:hover .svc-arrow { color: var(--amber); }
        .svc-teal .svc-icon { background: var(--teal-subtle); color: var(--teal); }
        .svc-teal:hover { border-color: rgba(45,212,191,0.20); background: rgba(45,212,191,0.04); }
        .svc-teal:hover .svc-arrow { color: var(--teal); }
        .svc-green .svc-icon { background: var(--green-subtle); color: var(--green); }
        .svc-green:hover { border-color: rgba(52,211,153,0.20); background: rgba(52,211,153,0.04); }
        .svc-green:hover .svc-arrow { color: var(--green); }

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
            color: var(--blue);
            background: var(--blue-subtle);
            border-color: rgba(91,154,255,0.12);
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
            background: rgba(52,211,153,0.12);
            border: 1px solid rgba(52,211,153,0.20);
            color: var(--green);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        #map {
            height: 380px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            z-index: 1;
        }
        .map-caption {
            text-align: center;
            font-size: 12px;
            color: var(--text-tertiary);
            margin-top: 10px;
            line-height: 1.5;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 11px;
            font-weight: 500;
            color: var(--text-secondary);
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .dot-high { background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.5); }
        .dot-med { background: #84cc16; box-shadow: 0 0 6px rgba(132,204,22,0.4); }
        .dot-low { background: #3b82f6; box-shadow: 0 0 6px rgba(59,130,246,0.4); }
        .leaflet-container { background: var(--bg-root) !important; }

        .street-select {
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg-root);
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            appearance: none;
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 14px center;
            cursor: pointer;
        }
        .street-select:focus {
            outline: none;
            border-color: var(--green);
        }
        .rate-box {
            background: rgba(52,211,153,0.05);
            border-left: 3px solid var(--green);
            padding: 14px 16px;
            margin-top: 14px;
            border-radius: 0 var(--radius) var(--radius) 0;
            display: none;
            animation: fadeIn 0.25s ease;
        }
        .rate-box.show { display: block; }
        .rate-row {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 5px 0;
            font-size: 13px;
            line-height: 1.4;
        }
        .rate-row-icon {
            flex-shrink: 0;
            font-size: 14px;
        }
        .rate-row-label {
            color: var(--text-tertiary);
            min-width: 55px;
            font-weight: 500;
        }
        .rate-row-value {
            color: var(--text-primary);
            font-weight: 500;
        }
        .rate-row-value.rate-warn {
            color: var(--rose);
            font-size: 12px;
        }
        .rate-row-value.rate-free {
            color: var(--green);
        }
        .rate-row-value.rate-cost {
            color: var(--amber);
            font-family: var(--font-mono);
        }
        .green-p-link {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 14px;
            padding: 12px;
            border-radius: var(--radius);
            background: linear-gradient(135deg, rgba(52,211,153,0.15), rgba(52,211,153,0.06));
            border: 1px solid rgba(52,211,153,0.20);
            color: var(--green);
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: background 0.15s ease;
        }
        .green-p-link:hover {
            background: linear-gradient(135deg, rgba(52,211,153,0.22), rgba(52,211,153,0.10));
        }
        .towed-link {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px;
            border-radius: var(--radius);
            background: linear-gradient(135deg, rgba(244,63,94,0.12), rgba(244,63,94,0.04));
            border: 1px solid rgba(244,63,94,0.20);
            color: var(--rose);
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: background 0.15s ease;
        }
        .towed-link:hover {
            background: linear-gradient(135deg, rgba(244,63,94,0.20), rgba(244,63,94,0.08));
        }
        .dispute-select {
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg-root);
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            appearance: none;
            -webkit-appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 14px center;
            cursor: pointer;
        }
        .dispute-select:focus {
            outline: none;
            border-color: var(--purple);
        }
        .dispute-textarea {
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            background: var(--bg-root);
            color: var(--text-primary);
            font-family: var(--font-mono);
            font-size: 13px;
            height: 140px;
            resize: none;
            margin-top: 12px;
            line-height: 1.6;
            box-sizing: border-box;
        }
        .dispute-textarea:focus {
            outline: none;
            border-color: var(--purple);
        }
        .copy-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding: 8px 16px;
            border-radius: var(--radius);
            border: none;
            background: rgba(167,139,250,0.12);
            border: 1px solid rgba(167,139,250,0.2);
            color: var(--purple);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            font-family: var(--font);
            transition: background 0.15s ease;
        }
        .copy-btn:hover {
            background: rgba(167,139,250,0.2);
        }

        .notif-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 14px 16px;
            border-radius: var(--radius);
            background: linear-gradient(135deg, rgba(91,154,255,0.12), rgba(91,154,255,0.04));
            border: 1px solid rgba(91,154,255,0.20);
            margin-bottom: 16px;
        }
        .notif-banner.granted {
            background: linear-gradient(135deg, rgba(52,211,153,0.10), rgba(52,211,153,0.03));
            border-color: rgba(52,211,153,0.20);
        }
        .notif-banner-left {
            display: flex;
            align-items: center;
            gap: 10px;
            flex: 1;
            min-width: 0;
        }
        .notif-banner-icon {
            font-size: 18px;
            flex-shrink: 0;
        }
        .notif-banner-text {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
            line-height: 1.4;
        }
        .notif-banner-text small {
            display: block;
            font-size: 11px;
            font-weight: 400;
            color: var(--text-tertiary);
            margin-top: 2px;
        }
        .notif-enable-btn {
            flex-shrink: 0;
            padding: 7px 16px;
            border-radius: 20px;
            border: none;
            background: var(--blue);
            color: #fff;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.12s ease, background 0.15s ease;
            font-family: var(--font);
        }
        .notif-enable-btn:hover {
            transform: scale(1.04);
        }
        .notif-enable-btn:active {
            transform: scale(0.96);
        }
        .notif-enable-btn.active {
            background: var(--green);
            cursor: default;
        }

        .scan-btn {
            background: linear-gradient(135deg, var(--purple), var(--rose));
            color: #fff;
            padding: 14px 20px;
            border-radius: var(--radius);
            text-align: center;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            border: none;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: transform 0.15s ease, box-shadow 0.2s ease;
            box-shadow: 0 4px 16px rgba(167,139,250,0.25);
            font-family: var(--font);
        }
        .scan-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 24px rgba(167,139,250,0.35);
        }
        .scan-btn:active {
            transform: scale(0.98);
        }
        .scan-btn svg {
            width: 18px;
            height: 18px;
            flex-shrink: 0;
        }
        .scan-status {
            text-align: center;
            font-size: 13px;
            font-weight: 500;
            padding: 10px 0;
            display: none;
        }
        .scan-status.loading {
            display: block;
            color: var(--purple);
            animation: pulse 1.5s ease-in-out infinite;
        }
        .scan-status.done {
            display: block;
            color: var(--green);
        }
        .scan-status.error {
            display: block;
            color: var(--rose);
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .scan-result {
            background: rgba(167,139,250,0.06);
            border: 1px solid rgba(167,139,250,0.15);
            border-radius: var(--radius);
            padding: 12px 14px;
            margin-top: 12px;
            display: none;
        }
        .scan-result.show { display: block; animation: fadeIn 0.25s ease; }
        .scan-result-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            margin-bottom: 4px;
        }
        .scan-result-value {
            font-family: var(--font-mono);
            font-size: 15px;
            color: var(--text-primary);
            margin-bottom: 10px;
        }
        .scan-result-value:last-child { margin-bottom: 0; }
        .scan-autofill {
            display: inline-block;
            margin-top: 8px;
            padding: 8px 16px;
            background: rgba(167,139,250,0.12);
            border: 1px solid rgba(167,139,250,0.2);
            color: var(--purple);
            border-radius: var(--radius);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: var(--font);
        }
        .scan-autofill:hover {
            background: rgba(167,139,250,0.2);
        }
        .scan-help {
            font-size: 11px;
            color: var(--text-tertiary);
            margin-top: 10px;
            line-height: 1.5;
        }

        .roi-input-wrap {
            position: relative;
        }
        .roi-input-wrap .currency-sign {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-tertiary);
            font-family: var(--font-mono);
            font-size: 15px;
            pointer-events: none;
        }
        .roi-input-wrap input {
            padding-left: 28px !important;
            font-family: var(--font-mono);
        }
        .roi-box {
            background: rgba(244,63,94,0.06);
            border-left: 3px solid var(--rose);
            padding: 14px 16px;
            margin-top: 14px;
            border-radius: 0 var(--radius) var(--radius) 0;
            animation: fadeIn 0.25s ease;
        }
        .roi-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 6px 0;
            font-size: 13px;
            color: var(--text-secondary);
        }
        .roi-row span:last-child {
            font-family: var(--font-mono);
            font-weight: 500;
        }
        .roi-fee {
            color: var(--rose) !important;
        }
        .roi-total {
            border-top: 1px solid var(--border);
            margin-top: 8px;
            padding-top: 10px;
        }
        .roi-total span {
            font-size: 15px !important;
            font-weight: 600 !important;
        }
        .roi-total span:last-child {
            color: var(--rose);
        }
        .roi-savings {
            text-align: center;
            margin-top: 10px;
            font-size: 12px;
            color: var(--green);
            font-weight: 500;
        }

        @media (max-width: 380px) {
            .app { padding: 0 14px; padding-bottom: calc(var(--safe-bottom) + 80px); }
            .card { padding: 16px; }
            #map { height: 300px; }
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
            <div id="notifBanner" class="notif-banner">
                <div class="notif-banner-left">
                    <span class="notif-banner-icon">&#x1F514;</span>
                    <div class="notif-banner-text">
                        <span id="notifTitle">24h Deadline Alerts</span>
                        <small id="notifDesc">Get notified before your fine fees increase.</small>
                    </div>
                </div>
                <button id="notifBtn" class="notif-enable-btn" onclick="enableNotifications()">Enable</button>
            </div>

            <div class="card card-purple card-1">
                <div class="card-label label-purple">AI Ticket Scanner</div>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 14px; line-height: 1.5;">Photograph a physical parking ticket to auto-extract the plate number and date.</p>
                <button class="scan-btn" onclick="document.getElementById('imageUpload').click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>
                    Scan Ticket Photo
                </button>
                <input type="file" id="imageUpload" accept="image/*" capture="environment" style="display:none" onchange="performOCR(event)">
                <div id="scanStatus" class="scan-status"></div>
                <div id="scanResult" class="scan-result">
                    <div class="scan-result-label">Detected Plate</div>
                    <div class="scan-result-value" id="scanPlate">—</div>
                    <div class="scan-result-label">Detected Date</div>
                    <div class="scan-result-value" id="scanDate">—</div>
                    <button class="scan-autofill" onclick="autofillFromScan()">Auto-fill Reminder Form</button>
                </div>
                <p class="scan-help">Works best with clear, well-lit photos. Looks for Ontario plate patterns (e.g. ABCD 123) and dates.</p>
            </div>

            <div class="card card-blue card-2">
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
                    <button type="submit" class="btn btn-blue">Save Profile</button>
                </form>
            </div>

            <div class="card card-rose card-3">
                <div class="card-label label-rose">Deadline ROI Calculator</div>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 14px; line-height: 1.5;">See how much extra you'll pay by missing parking ticket deadlines.</p>
                <div class="field">
                    <label>Base Ticket Amount</label>
                    <div class="roi-input-wrap">
                        <span class="currency-sign">$</span>
                        <input type="number" id="baseAmount" placeholder="e.g. 30" oninput="calculateROI()" min="0" step="0.01">
                    </div>
                </div>
                <div class="roi-box" id="roiResults" style="display:none;">
                    <div class="roi-row"><span>Day 1–15 (Standard Fine)</span> <span id="valBase">$0.00</span></div>
                    <div class="roi-row"><span>Day 16 (Address Search Fee)</span> <span class="roi-fee">+$15.39</span></div>
                    <div class="roi-row"><span>Day 31 (Late Payment Fee)</span> <span class="roi-fee">+$32.10</span></div>
                    <div class="roi-row"><span>Day 60 (Plate Denial Fee)</span> <span class="roi-fee">+$32.10</span></div>
                    <div class="roi-row roi-total"><span>Total if paid after 60 days</span> <span id="valTotal">$0.00</span></div>
                    <div class="roi-savings" id="roiSavings">You save $79.59 by paying today.</div>
                </div>
            </div>

            <div class="card card-teal card-4">
                <div class="card-label label-teal">Add Fine Reminder</div>
                <form action="/add-reminder" method="POST">
                    <div class="field">
                        <label>Ticket / Reference Number</label>
                        <input type="text" name="ticket_num" placeholder="e.g. TK-12345" required style="font-family: var(--font-mono);">
                    </div>
                    <div class="field">
                        <label>Due Date</label>
                        <input type="date" name="due_date" required>
                    </div>
                    <button type="submit" class="btn btn-teal">Add Reminder</button>
                </form>
            </div>

            <div class="card card-amber card-5">
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
                                <a href="{{ r.gcal_url }}" target="_blank" rel="noopener" class="cal-btn cal-btn-gcal">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                    Google Calendar
                                </a>
                                <a href="/calendar/ics/{{ loop.index0 }}" class="cal-btn cal-btn-ics" download>
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
            <div class="card card-blue card-1">
                <div class="card-label label-blue">Parking Violations</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/pay-your-parking-violation/" target="_blank" rel="noopener" class="service-link svc-blue">
                        <div class="svc-icon">&#x1F4B3;</div>
                        <span class="svc-text">Pay Parking Ticket</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/dispute-your-parking-violation/" target="_blank" rel="noopener" class="service-link svc-purple">
                        <div class="svc-icon">&#x2696;</div>
                        <span class="svc-text">Dispute Ticket</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/about-parking-violations/" target="_blank" rel="noopener" class="service-link svc-teal">
                        <div class="svc-icon">&#x2139;</div>
                        <span class="svc-text">About Parking Violations</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-rose card-2">
                <div class="card-label label-rose">Speed & Red Light Cameras</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/" target="_blank" rel="noopener" class="service-link svc-rose">
                        <div class="svc-icon">&#x1F4F7;</div>
                        <span class="svc-text">Pay Camera Fine</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="service-link svc-amber">
                        <div class="svc-icon">&#x2696;</div>
                        <span class="svc-text">Dispute Camera Fine</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/red-light-camera-penalties/dispute-your-red-light-camera-penalty/" target="_blank" rel="noopener" class="service-link svc-purple">
                        <div class="svc-icon">&#x2139;</div>
                        <span class="svc-text">About Camera Penalties</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-green card-3">
                <div class="card-label label-green">Court Services</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/" target="_blank" rel="noopener" class="service-link svc-green">
                        <div class="svc-icon">&#x1F3DB;</div>
                        <span class="svc-text">Court Services & Provincial Offences</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-green card-4">
                <div class="card-label label-green">Street Parking Checker</div>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 14px; line-height: 1.5;">Select a street to see rates, enforcement hours, and free parking times.</p>
                <select id="streetSelect" class="street-select" onchange="checkStreet()">
                    <option value="">Choose a Street / Area</option>
                    <option value="queen_west">Queen St W (Spadina to Bathurst)</option>
                    <option value="bloor_yorkville">Bloor St W (Yorkville Area)</option>
                    <option value="kensington">Kensington Market</option>
                    <option value="front_st">Front St (Near Scotiabank Arena)</option>
                </select>
                <div id="rateInfo" class="rate-box">
                    <div class="rate-row"><span class="rate-row-icon">&#x1F4CD;</span> <span class="rate-row-label">Area</span> <span class="rate-row-value" id="streetName"></span></div>
                    <div class="rate-row"><span class="rate-row-icon">&#x1F4B0;</span> <span class="rate-row-label">Rate</span> <span class="rate-row-value rate-cost" id="streetRate"></span></div>
                    <div class="rate-row"><span class="rate-row-icon">&#x23F0;</span> <span class="rate-row-label">Hours</span> <span class="rate-row-value" id="streetHours"></span></div>
                    <div class="rate-row"><span class="rate-row-icon">&#x1F7E2;</span> <span class="rate-row-label">Free</span> <span class="rate-row-value rate-free" id="streetFree"></span></div>
                    <div class="rate-row"><span class="rate-row-icon">&#x26A0;</span> <span class="rate-row-label">Rush</span> <span class="rate-row-value rate-warn" id="streetRush"></span></div>
                </div>
                <a href="https://apps.apple.com/ca/app/green-p-parking/id983111045" target="_blank" rel="noopener" class="green-p-link">
                    &#x1F17F; Pay with Green P App
                </a>
            </div>

            <div class="card card-rose card-5">
                <div class="card-label label-rose">Vehicle Towed?</div>
                <a href="https://www.tps.ca/services/towing/" target="_blank" rel="noopener" class="towed-link">
                    &#x1F6A8; Find which pound has your car
                </a>
            </div>

            <div class="card card-purple card-6">
                <div class="card-label label-purple">Dispute Script Builder</div>
                <p style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 14px; line-height: 1.5;">Select a reason to generate a pre-written dispute script for your ticket.</p>
                <select id="disputeReason" class="dispute-select" onchange="generateScript()">
                    <option value="">Select a Reason</option>
                    <option value="hidden_sign">Sign was hidden or missing</option>
                    <option value="wrong_data">Officer wrote wrong plate/date</option>
                    <option value="broken_meter">Parking meter was broken</option>
                    <option value="valid_permit">I had a valid residential permit</option>
                </select>
                <textarea id="scriptOutput" class="dispute-textarea" placeholder="Your dispute script will appear here…" readonly></textarea>
                <button class="copy-btn" onclick="copyScript()">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path></svg>
                    Copy Script
                </button>
            </div>
        </div>

        <div id="tab-hotspots" class="tab">
            <div class="card card-rose card-1">
                <div class="card-label label-rose">Live Ticket Hotspots</div>
                <div id="map"></div>
                <div class="legend">
                    <div class="legend-item"><span class="legend-dot dot-high"></span> High enforcement</div>
                    <div class="legend-item"><span class="legend-dot dot-med"></span> Moderate</div>
                    <div class="legend-item"><span class="legend-dot dot-low"></span> Low activity</div>
                </div>
                <p class="map-caption">Simulated enforcement hotspots across Toronto.<br>Check the map before you park.</p>
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
            <button class="nav-btn" onclick="switchTab('hotspots', this)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                Hotspots
            </button>
        </div>
    </nav>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script>
        var mapInstance = null;

        function initMap() {
            if (mapInstance) {
                mapInstance.invalidateSize();
                return;
            }
            mapInstance = L.map('map').setView([43.6532, -79.3832], 13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; OpenStreetMap',
                maxZoom: 18
            }).addTo(mapInstance);

            var hotspots = [
                [43.6545, -79.3807, 1.0],
                [43.6489, -79.3850, 0.9],
                [43.6592, -79.3627, 0.95],
                [43.6426, -79.3871, 0.85],
                [43.6488, -79.3802, 0.7],
                [43.6677, -79.3948, 0.6],
                [43.6510, -79.3470, 0.5],
                [43.6613, -79.3955, 0.75],
                [43.6380, -79.3812, 0.65],
                [43.6710, -79.3865, 0.55],
                [43.6560, -79.3740, 0.80],
                [43.6455, -79.3920, 0.70],
                [43.6630, -79.3780, 0.60],
                [43.6350, -79.3750, 0.50],
                [43.6520, -79.4010, 0.45]
            ];

            L.heatLayer(hotspots, {
                radius: 28,
                blur: 18,
                maxZoom: 15,
                gradient: { 0.3: '#3b82f6', 0.5: '#06b6d4', 0.7: '#84cc16', 0.85: '#f59e0b', 1.0: '#ef4444' }
            }).addTo(mapInstance);
        }

        function checkStreet() {
            var street = document.getElementById('streetSelect').value;
            var rateBox = document.getElementById('rateInfo');
            if (!street) { rateBox.classList.remove('show'); return; }
            rateBox.classList.add('show');
            var db = {
                'queen_west': { name: 'Queen St W', rate: '$3.00 / hour', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', free: 'Every day after 9:00 PM', rush: '3:30–6:30 PM (Mon–Fri) — WILL TOW' },
                'bloor_yorkville': { name: 'Bloor St W (Yorkville)', rate: '$4.00 / hour', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', free: 'Every day after 9:00 PM', rush: '3:30–6:30 PM (Mon–Fri) — WILL TOW' },
                'kensington': { name: 'Kensington Market', rate: '$2.25 / hour', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', free: 'Every day after 9:00 PM', rush: 'None' },
                'front_st': { name: 'Front St (Arena Area)', rate: '$5.00 / hour (Event Rates)', hours: 'Mon–Sun 8am–Midnight', free: 'After Midnight', rush: '3:30–6:30 PM (Mon–Fri)' }
            };
            var d = db[street];
            document.getElementById('streetName').textContent = d.name;
            document.getElementById('streetRate').textContent = d.rate;
            document.getElementById('streetHours').textContent = d.hours;
            document.getElementById('streetFree').textContent = d.free;
            document.getElementById('streetRush').textContent = d.rush;
        }

        function generateScript() {
            var reason = document.getElementById('disputeReason').value;
            var output = document.getElementById('scriptOutput');
            var scripts = {
                'hidden_sign': 'To the Screening Officer,\n\nI respectfully request cancellation of this parking infraction notice. The regulatory signage at the location was completely obscured by overgrown foliage/construction materials, rendering the parking restrictions illegible to a reasonable person.\n\nI have attached photographic evidence of the sign obstruction taken at the time of the infraction.\n\nThank you for your consideration.',
                'wrong_data': 'To the Screening Officer,\n\nI respectfully request cancellation under Section 1.0 (Incorrect Data). Upon reviewing the parking infraction notice, I have identified that the officer recorded incorrect information (licence plate number/date/time/location), rendering this notice legally invalid.\n\nPlease review the attached documentation.\n\nThank you for your consideration.',
                'broken_meter': 'To the Screening Officer,\n\nI respectfully request cancellation of this infraction. I attempted to pay for parking at the location, however the Green P pay station was malfunctioning and would not accept payment. I have attached a photograph of the error screen on the machine.\n\nThank you for your consideration.',
                'valid_permit': 'To the Screening Officer,\n\nI respectfully request cancellation under Section 3.1 (Valid Permit). At the time of the infraction, I held a valid City of Toronto On-Street Residential Parking Permit for this area, which was properly displayed.\n\nPlease see the attached copy of my valid permit.\n\nThank you for your consideration.'
            };
            output.value = scripts[reason] || '';
        }

        function copyScript() {
            var textarea = document.getElementById('scriptOutput');
            if (!textarea.value) { showToast('Generate a script first'); return; }
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(textarea.value).then(function() {
                    showToast('Script copied to clipboard');
                }).catch(function() {
                    textarea.select();
                    document.execCommand('copy');
                    showToast('Script copied to clipboard');
                });
            } else {
                textarea.select();
                document.execCommand('copy');
                showToast('Script copied to clipboard');
            }
        }

        function enableNotifications() {
            var banner = document.getElementById('notifBanner');
            var btn = document.getElementById('notifBtn');
            var title = document.getElementById('notifTitle');
            var desc = document.getElementById('notifDesc');
            if (!('Notification' in window)) {
                showToast('Your browser does not support notifications');
                return;
            }
            if (Notification.permission === 'granted') {
                banner.classList.add('granted');
                btn.textContent = 'Active';
                btn.classList.add('active');
                title.textContent = 'Alerts Active';
                desc.textContent = 'You will be notified 24h before fees increase.';
                showToast('Notifications already enabled');
                return;
            }
            if (Notification.permission === 'denied') {
                showToast('Notifications blocked. Please enable in browser settings.');
                return;
            }
            Notification.requestPermission().then(function(perm) {
                if (perm === 'granted') {
                    banner.classList.add('granted');
                    btn.textContent = 'Active';
                    btn.classList.add('active');
                    title.textContent = 'Alerts Active';
                    desc.textContent = 'You will be notified 24h before fees increase.';
                    new Notification('TO Fine Tracker', {
                        body: 'Deadline alerts enabled. We will notify you 24h before fees increase.',
                        icon: 'https://www.toronto.ca/wp-content/themes/toronto/assets/images/toronto-logo.png'
                    });
                    showToast('Notifications enabled');
                } else {
                    showToast('Notification permission denied');
                }
            });
        }

        (function checkNotifState() {
            if ('Notification' in window && Notification.permission === 'granted') {
                var banner = document.getElementById('notifBanner');
                var btn = document.getElementById('notifBtn');
                var title = document.getElementById('notifTitle');
                var desc = document.getElementById('notifDesc');
                banner.classList.add('granted');
                btn.textContent = 'Active';
                btn.classList.add('active');
                title.textContent = 'Alerts Active';
                desc.textContent = 'You will be notified 24h before fees increase.';
            }
        })();

        var scannedPlate = '';
        var scannedDate = '';

        function fileToDataURL(file) {
            return new Promise(function(resolve, reject) {
                var reader = new FileReader();
                reader.onload = function() { resolve(reader.result); };
                reader.onerror = function() { reject(new Error('Failed to read file')); };
                reader.readAsDataURL(file);
            });
        }

        async function performOCR(event) {
            var file = event.target.files[0];
            if (!file) return;
            var statusEl = document.getElementById('scanStatus');
            var resultEl = document.getElementById('scanResult');
            statusEl.className = 'scan-status loading';
            statusEl.textContent = 'AI is reading your ticket…';
            resultEl.classList.remove('show');
            try {
                var dataUrl = await fileToDataURL(file);
                var result = await Tesseract.recognize(dataUrl, 'eng');
                var text = result.data.text.toUpperCase();
                var plateMatch = text.match(/[A-Z]{4}\s?\d{3}/);
                var dateMatch = text.match(/\d{4}[\/\-]\d{2}[\/\-]\d{2}/) || text.match(/\d{2}[\/\-]\d{2}[\/\-]\d{4}/);
                scannedPlate = plateMatch ? plateMatch[0].trim() : '';
                scannedDate = '';
                if (dateMatch) {
                    var raw = dateMatch[0].replace(/\//g, '-');
                    if (raw.match(/^\d{4}-\d{2}-\d{2}$/)) {
                        scannedDate = raw;
                    } else if (raw.match(/^\d{2}-\d{2}-\d{4}$/)) {
                        var parts = raw.split('-');
                        var y = parseInt(parts[2]), m = parseInt(parts[0]), d = parseInt(parts[1]);
                        if (m > 12) { var tmp = m; m = d; d = tmp; }
                        scannedDate = y + '-' + String(m).padStart(2,'0') + '-' + String(d).padStart(2,'0');
                    }
                }
                document.getElementById('scanPlate').textContent = scannedPlate || 'Not detected';
                document.getElementById('scanDate').textContent = scannedDate || 'Not detected';
                resultEl.classList.add('show');
                if (scannedPlate || scannedDate) {
                    statusEl.className = 'scan-status done';
                    statusEl.textContent = 'Scan complete!';
                } else {
                    statusEl.className = 'scan-status error';
                    statusEl.textContent = 'No plate or date found. Try a clearer photo.';
                }
            } catch (err) {
                statusEl.className = 'scan-status error';
                statusEl.textContent = 'Scan failed. Try a clearer photo.';
            }
            event.target.value = '';
        }

        function autofillFromScan() {
            var filled = 0;
            if (scannedPlate) {
                var ticketField = document.querySelector('#tab-dashboard input[name="ticket_num"]');
                if (ticketField) { ticketField.value = scannedPlate; filled++; }
            }
            if (scannedDate) {
                var dateField = document.querySelector('#tab-dashboard input[name="due_date"]');
                if (dateField) { dateField.value = scannedDate; filled++; }
            }
            if (filled > 0) {
                showToast('Reminder form auto-filled from scan');
            } else {
                showToast('Nothing to auto-fill');
            }
        }

        function calculateROI() {
            var input = document.getElementById('baseAmount').value;
            var roiBox = document.getElementById('roiResults');
            if (input > 0) {
                roiBox.style.display = 'block';
                var base = parseFloat(input);
                var total = base + 15.39 + 32.10 + 32.10;
                var savings = 79.59;
                document.getElementById('valBase').innerText = '$' + base.toFixed(2);
                document.getElementById('valTotal').innerText = '$' + total.toFixed(2);
                document.getElementById('roiSavings').innerText = 'You save $' + savings.toFixed(2) + ' by paying today.';
            } else {
                roiBox.style.display = 'none';
            }
        }

        function switchTab(tab, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(n => n.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            btn.classList.add('active');
            window.scrollTo({ top: 0, behavior: 'smooth' });
            if (tab === 'hotspots') {
                setTimeout(initMap, 100);
            }
        }

        function showToast(msg) {
            var toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.classList.add('show');
            setTimeout(function() { toast.classList.remove('show'); }, 2500);
        }

        var params = new URLSearchParams(window.location.search);
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
