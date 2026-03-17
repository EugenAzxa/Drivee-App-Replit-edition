from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

users_data = {
    'profile': {'name': '', 'plate': ''},
    'reminders': []
}

reports_data = [
    {"type": "Pothole", "lat": 43.650, "lng": -79.390, "status": "Pending 311"},
    {"type": "Broken Meter", "lat": 43.652, "lng": -79.383, "status": "Pending 311"},
    {"type": "Hidden Sign", "lat": 43.648, "lng": -79.396, "status": "Pending 311"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#000000">
    <title>DriveSafe TO | Professional</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous"/>
    <script src="https://unpkg.com/tesseract.js@v4.0.1/dist/tesseract.min.js"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        :root {
            --bg-root: #000000;
            --bg-surface: #1C1C1E;
            --bg-elevated: #2C2C2E;
            --bg-input: #1C1C1E;
            --border: rgba(255,255,255,0.08);
            --border-focus: rgba(255,255,255,0.18);
            --text-primary: #FFFFFF;
            --text-secondary: #8E8E93;
            --text-tertiary: #636366;
            --blue: #0A84FF;
            --blue-vivid: #0A84FF;
            --blue-subtle: rgba(10,132,255,0.12);
            --blue-glow: rgba(10,132,255,0.20);
            --purple: #BF5AF2;
            --purple-subtle: rgba(191,90,242,0.12);
            --purple-glow: rgba(191,90,242,0.18);
            --teal: #64D2FF;
            --teal-subtle: rgba(100,210,255,0.12);
            --teal-glow: rgba(100,210,255,0.18);
            --rose: #FF453A;
            --rose-subtle: rgba(255,69,58,0.12);
            --rose-glow: rgba(255,69,58,0.18);
            --amber: #FFD60A;
            --amber-subtle: rgba(255,214,10,0.12);
            --amber-glow: rgba(255,214,10,0.18);
            --green: #30D158;
            --green-subtle: rgba(48,209,88,0.12);
            --green-glow: rgba(48,209,88,0.18);
            --orange: #FF9F0A;
            --orange-subtle: rgba(255,159,10,0.12);
            --radius: 12px;
            --radius-lg: 16px;
            --safe-top: env(safe-area-inset-top, 0px);
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, monospace;
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
            padding-bottom: calc(var(--safe-bottom) + 120px);
        }

        .header {
            padding: 20px 0 24px;
            animation: fadeIn 0.6s ease-out both;
        }
        .header-top {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .header-text h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
            line-height: 1.2;
        }
        .header-text h1 span {
            font-weight: 400;
            color: var(--text-secondary);
        }
        .header-text p {
            font-size: 15px;
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 4px;
        }

        .card {
            background: var(--bg-surface);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            animation: slideUp 0.5s ease-out both;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        }
        .card-1 { animation-delay: 0.05s; }
        .card-2 { animation-delay: 0.1s; }
        .card-3 { animation-delay: 0.15s; }
        .card-4 { animation-delay: 0.2s; }
        .card-5 { animation-delay: 0.25s; }
        .card-6 { animation-delay: 0.3s; }

        .card-label {
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.3px;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card-label i { color: var(--blue); }
        .card-label.label-blue { color: var(--text-primary); }
        .card-label.label-blue i { color: var(--blue); }
        .card-label.label-teal { color: var(--text-primary); }
        .card-label.label-teal i { color: var(--teal); }
        .card-label.label-amber { color: var(--text-primary); }
        .card-label.label-amber i { color: var(--amber); }
        .card-label.label-rose { color: var(--text-primary); }
        .card-label.label-rose i { color: var(--rose); }
        .card-label.label-purple { color: var(--text-primary); }
        .card-label.label-purple i { color: var(--purple); }
        .card-label.label-green { color: var(--text-primary); }
        .card-label.label-green i { color: var(--green); }
        .card-desc {
            font-size: 14px;
            color: var(--text-secondary);
            margin: 0 0 16px 0;
            line-height: 1.4;
        }

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
            background: var(--bg-elevated);
            border: none;
            border-radius: var(--radius);
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            font-weight: 500;
            outline: none;
            transition: box-shadow 0.2s ease;
        }
        .field input::placeholder { color: var(--text-tertiary); }
        .field input:focus {
            box-shadow: 0 0 0 2px var(--blue);
        }
        .field input[type="date"] { color-scheme: dark; }
        .field input[type="date"]::-webkit-calendar-picker-indicator {
            filter: invert(0.7);
            opacity: 0.6;
            cursor: pointer;
        }

        .btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 12px;
            font-family: var(--font);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.2s;
        }
        .btn:active { opacity: 0.8; transform: scale(0.98); }
        .btn-blue {
            background: var(--blue);
            color: #fff;
        }
        .btn-teal {
            background: var(--teal);
            color: #000;
        }

        .saved-banner {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 10px 14px;
            background: var(--green-subtle);
            border: none;
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
            border: none;
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
        }
        .badge-overdue {
            background: var(--rose-subtle);
            color: var(--rose);
        }
        .badge-today {
            background: var(--amber-subtle);
            color: var(--amber);
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
            border: none;
            background: var(--blue-subtle);
            color: var(--blue);
        }
        .cal-btn-ics {
            border: none;
            background: var(--purple-subtle);
            color: var(--purple);
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
            border: none;
            border-radius: var(--radius);
            color: var(--text-primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.15s ease;
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
        .svc-rose .svc-icon { background: var(--rose-subtle); color: var(--rose); }
        .svc-purple .svc-icon { background: var(--purple-subtle); color: var(--purple); }
        .svc-amber .svc-icon { background: var(--amber-subtle); color: var(--amber); }
        .svc-teal .svc-icon { background: var(--teal-subtle); color: var(--teal); }
        .svc-green .svc-icon { background: var(--green-subtle); color: var(--green); }

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
            height: 90px;
            background: rgba(28, 28, 30, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 0.5px solid rgba(255,255,255,0.1);
            padding-bottom: var(--safe-bottom);
        }
        .nav-inner {
            display: flex;
            justify-content: space-around;
            align-items: flex-start;
            padding-top: 12px;
            height: 100%;
            max-width: 460px;
            margin: 0 auto;
        }
        .nav-btn {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            border: none;
            background: none;
            color: var(--text-secondary);
            font-family: var(--font);
            font-size: 10px;
            font-weight: 500;
            width: 60px;
            transition: color 0.2s;
        }
        .nav-btn.active {
            color: var(--blue);
        }
        .nav-btn i {
            font-size: 22px;
            display: block;
        }
        .nav-btn svg {
            width: 22px;
            height: 22px;
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
            border: none;
            color: var(--green);
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        #map {
            height: 250px;
            border-radius: var(--radius);
            border: none;
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
            border: none;
            background: var(--bg-elevated);
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
            box-shadow: 0 0 0 2px var(--green);
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
            gap: 10px;
            margin-top: 14px;
            padding: 16px;
            border-radius: 12px;
            background: var(--green);
            color: #000;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            transition: opacity 0.2s, transform 0.2s;
            border: none;
        }
        .green-p-link:active {
            opacity: 0.8;
            transform: scale(0.98);
        }
        .towed-link {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 16px;
            border-radius: 12px;
            background: var(--rose);
            color: #fff;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
            animation: pulseDanger 2s infinite;
            transition: opacity 0.2s, transform 0.2s;
            border: none;
        }
        .towed-link:active {
            opacity: 0.8;
            transform: scale(0.98);
        }
        .dispute-select {
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius);
            border: none;
            background: var(--bg-elevated);
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
            box-shadow: 0 0 0 2px var(--purple);
        }
        .dispute-textarea {
            width: 100%;
            padding: 12px 14px;
            border-radius: var(--radius);
            border: none;
            background: var(--bg-elevated);
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
            box-shadow: 0 0 0 2px var(--purple);
        }
        .copy-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding: 8px 16px;
            border-radius: var(--radius);
            border: none;
            background: var(--purple-subtle);
            color: var(--purple);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            font-family: var(--font);
            transition: background 0.15s ease;
        }

        .guide-step {
            display: flex;
            gap: 14px;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
        }
        .guide-step:last-child { border-bottom: none; }
        .guide-num {
            flex-shrink: 0;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 700;
            font-family: var(--font-mono);
        }
        .guide-num-1 { background: rgba(91,154,255,0.15); color: var(--blue); }
        .guide-num-2 { background: rgba(167,139,250,0.15); color: var(--purple); }
        .guide-num-3 { background: rgba(45,212,191,0.15); color: var(--teal); }
        .guide-num-4 { background: rgba(244,63,94,0.15); color: var(--rose); }
        .guide-num-5 { background: rgba(251,191,36,0.15); color: var(--amber); }
        .guide-num-6 { background: rgba(52,211,153,0.15); color: var(--green); }
        .guide-num-7 { background: rgba(251,146,60,0.15); color: var(--orange); }
        .guide-num-8 { background: rgba(191,90,242,0.15); color: var(--purple); }
        .guide-content {
            flex: 1;
            min-width: 0;
        }
        .guide-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        .guide-desc {
            font-size: 12px;
            color: var(--text-tertiary);
            line-height: 1.5;
        }
        .guide-tab-ref {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 6px;
        }
        .guide-tab-dash { background: rgba(91,154,255,0.12); color: var(--blue); }
        .guide-tab-svc { background: rgba(45,212,191,0.12); color: var(--teal); }
        .guide-tab-hot { background: rgba(244,63,94,0.12); color: var(--rose); }
        .guide-tab-legal { background: rgba(191,90,242,0.12); color: var(--purple); }

        .firm-type-badge {
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 5px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 10px;
        }
        .firm-type-lawyer { background: rgba(10,132,255,0.15); color: var(--blue); }
        .firm-type-paralegal { background: rgba(191,90,242,0.15); color: var(--purple); }
        .firm-type-mixed { background: rgba(100,210,255,0.15); color: var(--teal); }

        .firm-name {
            font-size: 17px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.2px;
            margin-bottom: 6px;
        }
        .firm-price {
            font-size: 12px;
            color: var(--text-tertiary);
            margin-bottom: 12px;
        }
        .specialty-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 14px;
        }
        .specialty-pill {
            font-size: 11px;
            font-weight: 500;
            padding: 3px 9px;
            border-radius: 6px;
            background: var(--bg-elevated);
            color: var(--text-secondary);
        }
        .firm-actions {
            display: flex;
            gap: 8px;
        }
        .firm-btn {
            flex: 1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 12px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: 600;
            font-family: var(--font);
            text-decoration: none;
            cursor: pointer;
            border: none;
            transition: opacity 0.15s;
        }
        .firm-btn:active { opacity: 0.75; }
        .firm-btn-email { background: var(--blue-subtle); color: var(--blue); }
        .firm-btn-web { background: var(--bg-elevated); color: var(--text-secondary); }
        .firm-card-highlight {
            box-shadow: 0 0 0 2px var(--blue), 0 4px 24px rgba(10,132,255,0.18) !important;
            transition: box-shadow 0.3s ease;
        }

        .advisor-textarea {
            width: 100%;
            padding: 12px 14px;
            background: var(--bg-elevated);
            border: none;
            border-radius: var(--radius);
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            font-weight: 400;
            outline: none;
            resize: none;
            min-height: 90px;
            transition: box-shadow 0.2s ease;
            margin-bottom: 12px;
            line-height: 1.5;
        }
        .advisor-textarea::placeholder { color: var(--text-tertiary); }
        .advisor-textarea:focus { box-shadow: 0 0 0 2px var(--blue); }

        .advisor-result {
            display: none;
            padding: 14px;
            border-radius: var(--radius);
            margin-top: 12px;
            animation: slideUp 0.3s ease;
        }
        .advisor-result.show { display: block; }
        .advisor-severity {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 6px;
        }
        .advisor-action {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 6px;
        }
        .advisor-reason {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        .advisor-result-minor { background: var(--green-subtle); }
        .advisor-result-minor .advisor-severity { color: var(--green); }
        .advisor-result-serious { background: var(--amber-subtle); }
        .advisor-result-serious .advisor-severity { color: var(--amber); }
        .advisor-result-urgent { background: var(--rose-subtle); }
        .advisor-result-urgent .advisor-severity { color: var(--rose); }

        .lawyer-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 12px 14px;
            background: var(--blue-subtle);
            border-radius: var(--radius);
            margin-top: 12px;
            animation: slideUp 0.3s ease;
        }
        .lawyer-banner-text {
            font-size: 13px;
            font-weight: 500;
            color: var(--blue);
            flex: 1;
        }
        .lawyer-banner-actions {
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }
        .lawyer-banner-go {
            padding: 6px 12px;
            border-radius: 8px;
            border: none;
            background: var(--blue);
            color: #fff;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            transition: opacity 0.15s;
        }
        .lawyer-banner-go:active { opacity: 0.8; }
        .lawyer-banner-dismiss {
            padding: 6px 8px;
            border-radius: 8px;
            border: none;
            background: none;
            color: var(--text-tertiary);
            font-size: 14px;
            cursor: pointer;
            font-family: var(--font);
        }
        .guide-start-btn {
            width: 100%;
            padding: 16px;
            border-radius: var(--radius);
            border: none;
            background: var(--blue);
            color: #fff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            font-family: var(--font);
            transition: opacity 0.2s, transform 0.2s;
            margin-top: 8px;
        }
        .guide-start-btn:active { opacity: 0.8; transform: scale(0.98); }

        .notif-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 14px 16px;
            border-radius: var(--radius);
            background: var(--bg-surface);
            border: none;
            margin-bottom: 16px;
        }
        .notif-banner.granted {
            background: var(--green-subtle);
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
            background: var(--purple);
            color: #fff;
            padding: 16px 20px;
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
            transition: opacity 0.2s, transform 0.2s;
            font-family: var(--font);
        }
        .scan-btn:active {
            opacity: 0.8;
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
        @keyframes pulseDanger {
            0% { box-shadow: 0 0 0 0 rgba(244, 63, 94, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(244, 63, 94, 0); }
            100% { box-shadow: 0 0 0 0 rgba(244, 63, 94, 0); }
        }
        .scan-result {
            background: var(--bg-elevated);
            border: none;
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
            background: var(--purple-subtle);
            border: none;
            color: var(--purple);
            border-radius: var(--radius);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s ease;
            font-family: var(--font);
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

        .report-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 14px;
        }
        .report-btn {
            background: var(--bg-elevated);
            padding: 18px 10px;
            border-radius: 12px;
            text-align: center;
            font-size: 13px;
            cursor: pointer;
            border: none;
            color: var(--text-primary);
            font-weight: 500;
            font-family: var(--font);
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        .report-btn:active {
            background: #3A3A3C;
            transform: scale(0.97);
        }
        .report-btn i {
            font-size: 22px;
            color: var(--blue);
        }

        .loading-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
            z-index: 2000;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: var(--blue);
            font-weight: 500;
            font-size: 16px;
            font-family: var(--font);
        }
        .loading-overlay.show { display: flex; }
        .loading-overlay i { font-size: 36px; margin-bottom: 16px; }

        .report-count {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 12px;
            padding: 6px 12px;
            border-radius: 20px;
            background: var(--blue-subtle);
            border: none;
            color: var(--blue);
            font-size: 12px;
            font-weight: 600;
        }

        .gps-alert {
            background: var(--rose);
            color: white;
            padding: 16px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            margin-bottom: 16px;
            display: none;
            animation: pulseDanger 1.5s infinite;
            border: none;
            font-size: 15px;
            line-height: 1.5;
        }
        .gps-alert.show { display: block; }
        .gps-alert i { font-size: 24px; display: block; margin-bottom: 6px; }

        .btn-gps {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            padding: 16px;
            border-radius: 12px;
            background: var(--blue);
            color: #fff;
            font-weight: 600;
            font-size: 16px;
            border: none;
            cursor: pointer;
            transition: opacity 0.2s, transform 0.2s;
            font-family: var(--font);
        }
        .btn-gps:active { opacity: 0.8; transform: scale(0.98); }
        .btn-gps.active-gps {
            background: var(--green);
        }
        .gps-status {
            text-align: center;
            font-size: 12px;
            color: var(--text-tertiary);
            margin-top: 10px;
            line-height: 1.5;
        }

        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }

        @media (max-width: 380px) {
            .app { padding: 0 14px; padding-bottom: calc(var(--safe-bottom) + 110px); }
            .card { padding: 16px; }
            #map { height: 300px; }
        }
    </style>
</head>
<body>
    <div id="loadingOverlay" class="loading-overlay">
        <i class="fa-solid fa-satellite-dish fa-spin"></i>
        <span>Grabbing GPS Coordinates...</span>
    </div>

    <div id="toast" class="toast"></div>

    <div class="app">
        <div class="header">
            <div class="header-top">
                <div class="header-text">
                    <h1>DriveSafe <span>TO</span></h1>
                    <p>Community Infrastructure Tracker</p>
                </div>
            </div>
        </div>

        <div id="tab-guide" class="tab active">
            <div class="card card-blue card-1">
                <div class="card-label label-blue"><i class="fa-solid fa-book-open"></i> How to Use This App</div>
                <p class="card-desc">Welcome to DriveSafe TO — your all-in-one Toronto parking and traffic fine manager. Here is a quick walkthrough of everything you can do.</p>

                <div class="guide-step">
                    <div class="guide-num guide-num-1">1</div>
                    <div class="guide-content">
                        <div class="guide-title">Save Your Profile</div>
                        <div class="guide-desc">Enter your name and licence plate number. This is stored locally so you do not have to re-enter it each time.</div>
                        <span class="guide-tab-ref guide-tab-dash">Dashboard</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-2">2</div>
                    <div class="guide-content">
                        <div class="guide-title">Scan a Ticket with AI</div>
                        <div class="guide-desc">Tap "Scan Ticket Photo" to photograph a physical parking ticket. The AI reads the plate number and date automatically, then fills in the reminder form for you.</div>
                        <span class="guide-tab-ref guide-tab-dash">Dashboard</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-3">3</div>
                    <div class="guide-content">
                        <div class="guide-title">Add Fine Reminders</div>
                        <div class="guide-desc">Enter your ticket number and due date to create a reminder. Each reminder shows whether it is upcoming, due today, or overdue. You can also add it to Google Calendar or download an .ics file.</div>
                        <span class="guide-tab-ref guide-tab-dash">Dashboard</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-4">4</div>
                    <div class="guide-content">
                        <div class="guide-title">Check Late Fee Costs</div>
                        <div class="guide-desc">Use the Deadline ROI Calculator to see exactly how much extra you will pay if you miss the 15-day, 31-day, or 60-day deadlines. Enter your base fine amount and the total is calculated instantly.</div>
                        <span class="guide-tab-ref guide-tab-dash">Dashboard</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-5">5</div>
                    <div class="guide-content">
                        <div class="guide-title">Pay or Dispute Your Fine</div>
                        <div class="guide-desc">Go to the Services tab for direct links to the City of Toronto payment portals for parking tickets, camera fines, and court services. Use the Dispute Script Builder to generate a pre-written legal letter you can copy and paste.</div>
                        <span class="guide-tab-ref guide-tab-svc">Services</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-6">6</div>
                    <div class="guide-content">
                        <div class="guide-title">Check Parking Rates</div>
                        <div class="guide-desc">The Street Parking Checker shows rates, enforcement hours, free parking times, and rush-hour tow warnings for popular Toronto streets. There is also a link to download the Green P payment app.</div>
                        <span class="guide-tab-ref guide-tab-svc">Services</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-7">7</div>
                    <div class="guide-content">
                        <div class="guide-title">View Enforcement Hotspots</div>
                        <div class="guide-desc">The Hotspots tab shows an interactive heatmap of Toronto areas with heavy parking enforcement. Check it before you park to avoid high-risk zones.</div>
                        <span class="guide-tab-ref guide-tab-hot">Hotspots</span>
                    </div>
                </div>

                <div class="guide-step">
                    <div class="guide-num guide-num-8">8</div>
                    <div class="guide-content">
                        <div class="guide-title">Get Legal Help</div>
                        <div class="guide-desc">If you received a serious charge — stunt driving, careless driving, DUI, or a high-fine camera offence — the Legal tab connects you with Toronto's top traffic defence firms. Use the AI Ticket Advisor to find out if you need a lawyer.</div>
                        <span class="guide-tab-ref guide-tab-legal">Legal</span>
                    </div>
                </div>
            </div>

            <div class="card card-teal card-2">
                <div class="card-label label-teal"><i class="fa-solid fa-lightbulb"></i> Quick Tips</div>
                <div class="guide-step">
                    <div class="guide-num guide-num-5">&#x26A1;</div>
                    <div class="guide-content">
                        <div class="guide-desc">Enable 24h Deadline Alerts on the Dashboard to get browser notifications before your fees increase.</div>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="guide-num guide-num-6">&#x1F4F1;</div>
                    <div class="guide-content">
                        <div class="guide-desc">Add this app to your iPhone home screen for a full-screen experience: tap the Share button in Safari, then "Add to Home Screen."</div>
                    </div>
                </div>
                <div class="guide-step">
                    <div class="guide-num guide-num-4">&#x1F6A8;</div>
                    <div class="guide-content">
                        <div class="guide-desc">If your car was towed, use the "Vehicle Towed?" link on the Services tab to find which impound lot has it.</div>
                    </div>
                </div>
            </div>

            <button class="guide-start-btn" onclick="switchTab('dashboard', document.querySelectorAll('.nav-btn')[1])">Get Started</button>
        </div>

        <div id="tab-dashboard" class="tab">
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
                <div class="card-label label-purple"><i class="fa-solid fa-receipt"></i> AI Ticket Scanner</div>
                <p class="card-desc">Photograph a physical parking ticket to auto-extract the plate number and date.</p>
                <button class="scan-btn" onclick="document.getElementById('imageUpload').click()">
                    <i class="fa-solid fa-camera"></i>
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
                <div class="card-label label-blue"><i class="fa-solid fa-user"></i> Profile</div>
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
                <div class="card-label label-rose"><i class="fa-solid fa-calculator"></i> Deadline ROI Calculator</div>
                <p class="card-desc">See how much extra you'll pay by missing parking ticket deadlines.</p>
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
                <div class="card-label label-teal"><i class="fa-solid fa-bell"></i> Add Fine Reminder</div>
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
                <div class="card-label label-amber"><i class="fa-solid fa-clock"></i> Reminders</div>
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
                <div class="card-label label-blue"><i class="fa-solid fa-ticket"></i> Parking Violations</div>
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
                <div class="card-label label-rose"><i class="fa-solid fa-camera"></i> Speed & Red Light Cameras</div>
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
                <div class="card-label label-green"><i class="fa-solid fa-gavel"></i> Court Services</div>
                <div class="service-list">
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/" target="_blank" rel="noopener" class="service-link svc-green">
                        <div class="svc-icon">&#x1F3DB;</div>
                        <span class="svc-text">Court Services & Provincial Offences</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
            </div>

            <div class="card card-green card-4">
                <div class="card-label label-green"><i class="fa-solid fa-square-parking"></i> Street Parking Checker</div>
                <p class="card-desc">Select a street to see rates, enforcement hours, and free parking times.</p>
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
                    <i class="fa-solid fa-mobile-screen"></i> OPEN GREEN P
                </a>
            </div>

            <div class="card card-rose card-5">
                <div class="card-label label-rose"><i class="fa-solid fa-truck-ramp-box"></i> Vehicle Towed?</div>
                <a href="https://www.tps.ca/services/towing/" target="_blank" rel="noopener" class="towed-link">
                    <i class="fa-solid fa-truck-ramp-box"></i> FIND TOWED CAR
                </a>
                <p style="text-align:center; font-size:12px; margin-top:10px; color:var(--text-secondary);">Storage fees start at $75/day. Act fast.</p>
            </div>

            <div class="card card-purple card-6">
                <div class="card-label label-purple"><i class="fa-solid fa-scroll"></i> Dispute Script Builder</div>
                <p class="card-desc">Select a reason to generate a pre-written dispute script for your ticket.</p>
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
            <div id="gpsAlertBanner" class="gps-alert">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="gpsAlertText">WARNING!</span>
            </div>

            <div class="card card-blue card-1">
                <div class="card-label label-blue"><i class="fa-solid fa-location-crosshairs"></i> Proximity Scanner</div>
                <p class="card-desc">Detects $200 Bike Lane and $100 Fire Hydrant fine zones near your live GPS position.</p>
                <button class="btn-gps" onclick="startGPSGuardian()" id="gpsBtn">
                    <i class="fa-solid fa-satellite-dish"></i> Start Live GPS Guardian
                </button>
                <p class="gps-status">Requires location permission. Works best on mobile.</p>
            </div>

            <div class="card card-rose card-2">
                <div class="card-label label-rose"><i class="fa-solid fa-map-location-dot"></i> Live Ticket Hotspots</div>
                <div id="map"></div>
                <div class="legend">
                    <div class="legend-item"><span class="legend-dot dot-high"></span> High enforcement</div>
                    <div class="legend-item"><span class="legend-dot dot-med"></span> Moderate</div>
                    <div class="legend-item"><span class="legend-dot dot-low"></span> Low activity</div>
                </div>
                <p class="map-caption">Simulated enforcement hotspots across Toronto.<br>Bike lanes and hydrants shown when GPS is active.</p>
            </div>

            <div class="card card-purple card-3">
                <div class="card-label label-purple"><i class="fa-solid fa-bullhorn"></i> Report an Issue</div>
                <p class="card-desc" style="margin-bottom: 4px;">Tap to instantly map a hazard using your live GPS. Reports appear on the map for other drivers.</p>
                <div class="report-count"><i class="fa-solid fa-map-pin"></i> {{ reports|length }} community reports on the map</div>
                <div class="report-grid">
                    <button class="report-btn" onclick="submitReport('Broken Meter')">
                        <i class="fa-solid fa-plug-circle-xmark"></i>
                        Broken Meter
                    </button>
                    <button class="report-btn" onclick="submitReport('Hidden Sign')">
                        <i class="fa-solid fa-eye-slash"></i>
                        Hidden Sign
                    </button>
                    <button class="report-btn" onclick="submitReport('Pothole')">
                        <i class="fa-solid fa-road"></i>
                        Pothole
                    </button>
                    <button class="report-btn" onclick="submitReport('Bike Lane Blocked')">
                        <i class="fa-solid fa-bicycle"></i>
                        Bike Lane Block
                    </button>
                </div>
                <form id="reportForm" action="/report_311" method="POST" style="display:none;">
                    <input type="hidden" name="issue_type" id="issueTypeInput">
                    <input type="hidden" name="lat" id="latInput">
                    <input type="hidden" name="lng" id="lngInput">
                </form>
            </div>
        </div>

        <div id="tab-legal" class="tab">

            <div class="card card-1">
                <div class="card-label label-purple"><i class="fa-solid fa-robot"></i> AI Ticket Advisor</div>
                <p class="card-desc">Describe your ticket and get an instant severity assessment and legal recommendation — no account needed.</p>
                <textarea id="advisorInput" class="advisor-textarea" placeholder="e.g. I got a 50 km/h over the limit stunt driving charge in Toronto…" rows="3"></textarea>
                <button class="btn btn-blue" onclick="analyseTicket()"><i class="fa-solid fa-magnifying-glass"></i> Analyse My Ticket</button>
                <div id="advisorResult" class="advisor-result">
                    <div class="advisor-severity" id="advisorSeverity"></div>
                    <div class="advisor-action" id="advisorAction"></div>
                    <div class="advisor-reason" id="advisorReason"></div>
                </div>
            </div>

            <div class="card card-label-text card-2" style="margin-bottom:8px; padding:14px 20px;">
                <div style="font-size:13px; font-weight:600; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px;">Toronto Traffic Defence Directory</div>
            </div>

            <div class="card card-2 firm-card" id="firm-xcopper">
                <div class="firm-type-badge firm-type-lawyer">Lawyer</div>
                <div class="firm-name">X-Copper Professional Corporation</div>
                <div class="firm-price">Free consultation &middot; $350&ndash;$900</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">DUI</span>
                    <span class="specialty-pill">Careless Driving</span>
                    <span class="specialty-pill">Criminal</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@xcopper.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.xcopper.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card card-3 firm-card" id="firm-xcops">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">X-COPS Traffic Ticket Fighters</div>
                <div class="firm-price">Free consultation &middot; $200&ndash;$600</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Red Light Camera</span>
                    <span class="specialty-pill">Parking Tickets</span>
                    <span class="specialty-pill">Careless Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@x-cops.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.x-cops.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card card-4 firm-card" id="firm-pointts">
                <div class="firm-type-badge firm-type-mixed">Lawyer &amp; Paralegal</div>
                <div class="firm-name">POINTTS Advisory Services</div>
                <div class="firm-price">Free consultation &middot; $250&ndash;$700</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">School Zone</span>
                    <span class="specialty-pill">Careless Driving</span>
                    <span class="specialty-pill">Insurance Impact</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:toronto@pointts.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.pointts.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card card-5 firm-card" id="firm-ottlegal">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">OTT Legal — Ontario Traffic Tickets</div>
                <div class="firm-price">Free consultation &middot; $200&ndash;$550</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Red Light Camera</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Parking</span>
                    <span class="specialty-pill">HOV Lane</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@ontariotraffictickets.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.ontariotraffictickets.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card card-6 firm-card" id="firm-xpolice">
                <div class="firm-type-badge firm-type-lawyer">Lawyer</div>
                <div class="firm-name">X-Police / Fight Your Ticket</div>
                <div class="firm-price">Free consultation &middot; $300&ndash;$800</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">DUI / Impaired</span>
                    <span class="specialty-pill">Criminal HTA</span>
                    <span class="specialty-pill">Careless Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:help@xpolice.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.xpolice.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card firm-card" id="firm-streetlegal">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">Street Legal Paralegal Services</div>
                <div class="firm-price">Free consultation &middot; $150&ndash;$500</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Bike Lane</span>
                    <span class="specialty-pill">Parking Tickets</span>
                    <span class="specialty-pill">Cell Phone</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@street-legal.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.street-legal.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card firm-card" id="firm-trafficexperts">
                <div class="firm-type-badge firm-type-mixed">Lawyer &amp; Paralegal</div>
                <div class="firm-name">Traffic Ticket Experts</div>
                <div class="firm-price">Free consultation &middot; $200&ndash;$650</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">All HTA Charges</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">Red Light</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@trafficticket.legal?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.trafficticket.legal" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

            <div class="card firm-card" id="firm-hwylaw">
                <div class="firm-type-badge firm-type-lawyer">Lawyer</div>
                <div class="firm-name">HWY-LAW Criminal Defence</div>
                <div class="firm-price">Free consultation &middot; $400&ndash;$1,200</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">DUI / Impaired</span>
                    <span class="specialty-pill">Criminal HTA</span>
                    <span class="specialty-pill">Dangerous Driving</span>
                    <span class="specialty-pill">Stunt Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@hwy-law.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20DriveSafe%20TO"><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.hwy-law.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Website</a>
                </div>
            </div>

        </div>
    </div>

    <nav class="nav">
        <div class="nav-inner">
            <button class="nav-btn active" onclick="switchTab('guide', this)">
                <i class="fa-solid fa-circle-question"></i>
                Guide
            </button>
            <button class="nav-btn" onclick="switchTab('dashboard', this)">
                <i class="fa-solid fa-house"></i>
                Dashboard
            </button>
            <button class="nav-btn" onclick="switchTab('services', this)">
                <i class="fa-solid fa-credit-card"></i>
                Services
            </button>
            <button class="nav-btn" onclick="switchTab('hotspots', this)">
                <i class="fa-solid fa-map-location-dot"></i>
                Hotspots
            </button>
            <button class="nav-btn" onclick="switchTab('legal', this)">
                <i class="fa-solid fa-gavel"></i>
                Legal
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

            var bikeLaneCoords = [
                [43.6475, -79.3980],
                [43.6490, -79.3920]
            ];
            var bikeLane = L.polyline(bikeLaneCoords, {color: '#da3633', weight: 6, opacity: 0.8}).addTo(mapInstance);
            bikeLane.bindPopup('<b>Protected Bike Lane</b><br>$200 Fine Zone');

            var hydrantPos = [43.6485, -79.3950];
            var hydrant = L.circleMarker(hydrantPos, {color: '#d29922', radius: 8, fillOpacity: 1}).addTo(mapInstance);
            hydrant.bindPopup('<b>Fire Hydrant</b><br>Must be 3m away ($100 Fine)');

            var hazardIcon = L.divIcon({
                className: 'custom-icon',
                html: '<i class="fa-solid fa-location-dot" style="color: #0A84FF; font-size: 32px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.5));"></i>',
                iconSize: [32, 32],
                iconAnchor: [16, 32]
            });

            var liveReports = {{ reports_json|safe }};
            liveReports.forEach(function(report) {
                var marker = L.marker([report.lat, report.lng], {icon: hazardIcon}).addTo(mapInstance);
                marker.bindPopup('<b style="font-family:-apple-system,sans-serif;">' + report.type + '</b><br><span style="color:#8E8E93; font-size:12px;">' + report.status + '</span>');
            });
        }

        var userMarker = null;
        var gpsWatchId = null;
        var hydrantLatLng = L.latLng(43.6485, -79.3950);
        var bikeLaneSegments = [
            [L.latLng(43.6475, -79.3980), L.latLng(43.6490, -79.3920)]
        ];

        function distToSegment(p, a, b) {
            var dx = b.lng - a.lng, dy = b.lat - a.lat;
            if (dx === 0 && dy === 0) return p.distanceTo(a);
            var t = ((p.lng - a.lng) * dx + (p.lat - a.lat) * dy) / (dx * dx + dy * dy);
            t = Math.max(0, Math.min(1, t));
            var proj = L.latLng(a.lat + t * dy, a.lng + t * dx);
            return p.distanceTo(proj);
        }

        function distToBikeLane(userLatLng) {
            var minDist = Infinity;
            for (var i = 0; i < bikeLaneSegments.length; i++) {
                var d = distToSegment(userLatLng, bikeLaneSegments[i][0], bikeLaneSegments[i][1]);
                if (d < minDist) minDist = d;
            }
            return minDist;
        }

        function startGPSGuardian() {
            var btn = document.getElementById('gpsBtn');

            if (gpsWatchId !== null) {
                navigator.geolocation.clearWatch(gpsWatchId);
                gpsWatchId = null;
                btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Start Live GPS Guardian';
                btn.classList.remove('active-gps');
                document.getElementById('gpsAlertBanner').classList.remove('show');
                if (userMarker) { mapInstance.removeLayer(userMarker); userMarker = null; }
                showToast('GPS Guardian stopped');
                return;
            }

            if (!('geolocation' in navigator)) {
                showToast('Geolocation is not supported by your browser');
                return;
            }

            initMap();
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Locating...';
            btn.classList.add('active-gps');

            gpsWatchId = navigator.geolocation.watchPosition(
                function(position) {
                    btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Guardian Active — Tap to Stop';

                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    var userLatLng = L.latLng(lat, lng);

                    if (!userMarker) {
                        userMarker = L.circleMarker(userLatLng, {color: '#58a6ff', radius: 10, fillOpacity: 1, weight: 3}).addTo(mapInstance);
                        userMarker.bindPopup('<b>You are here</b>');
                        mapInstance.setView(userLatLng, 17);
                    } else {
                        userMarker.setLatLng(userLatLng);
                    }

                    var alertBanner = document.getElementById('gpsAlertBanner');
                    var alertText = document.getElementById('gpsAlertText');
                    var isHazard = false;

                    var distToHydrant = userLatLng.distanceTo(hydrantLatLng);
                    var distToBike = distToBikeLane(userLatLng);

                    if (distToHydrant < 20) {
                        alertText.innerHTML = 'PULL FORWARD! <br>You are too close to a Fire Hydrant ($100 Fine)';
                        alertBanner.classList.add('show');
                        isHazard = true;
                    } else if (distToBike < 25) {
                        alertText.innerHTML = 'DO NOT STOP! <br>You are in a Protected Bike Lane ($200 Fine)';
                        alertBanner.classList.add('show');
                        isHazard = true;
                    }

                    if (!isHazard) {
                        alertBanner.classList.remove('show');
                    }
                },
                function(error) {
                    showToast('Location access denied. Please enable Location Services.');
                    btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Start Live GPS Guardian';
                    btn.classList.remove('active-gps');
                    document.getElementById('gpsAlertBanner').classList.remove('show');
                    if (userMarker) { mapInstance.removeLayer(userMarker); userMarker = null; }
                    gpsWatchId = null;
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
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
                'hidden_sign': 'To the Screening Officer,\\n\\nI respectfully request cancellation of this parking infraction notice. The regulatory signage at the location was completely obscured by overgrown foliage/construction materials, rendering the parking restrictions illegible to a reasonable person.\\n\\nI have attached photographic evidence of the sign obstruction taken at the time of the infraction.\\n\\nThank you for your consideration.',
                'wrong_data': 'To the Screening Officer,\\n\\nI respectfully request cancellation under Section 1.0 (Incorrect Data). Upon reviewing the parking infraction notice, I have identified that the officer recorded incorrect information (licence plate number/date/time/location), rendering this notice legally invalid.\\n\\nPlease review the attached documentation.\\n\\nThank you for your consideration.',
                'broken_meter': 'To the Screening Officer,\\n\\nI respectfully request cancellation of this infraction. I attempted to pay for parking at the location, however the Green P pay station was malfunctioning and would not accept payment. I have attached a photograph of the error screen on the machine.\\n\\nThank you for your consideration.',
                'valid_permit': 'To the Screening Officer,\\n\\nI respectfully request cancellation under Section 3.1 (Valid Permit). At the time of the infraction, I held a valid City of Toronto On-Street Residential Parking Permit for this area, which was properly displayed.\\n\\nPlease see the attached copy of my valid permit.\\n\\nThank you for your consideration.'
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
                    new Notification('DriveSafe TO', {
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

                var existing = document.getElementById('lawyerBanner');
                if (existing) existing.remove();
                var highSeverity = /stunt|plate.?den|denial|impaired|dui|careless|dangerous|red.?light|bike.?lane|\$[2-9]\d{2}|\$[1-9]\d{3}/i.test(text);
                if (highSeverity) {
                    var banner = document.createElement('div');
                    banner.id = 'lawyerBanner';
                    banner.className = 'lawyer-banner';

                    var bannerText = document.createElement('div');
                    bannerText.className = 'lawyer-banner-text';
                    bannerText.innerHTML = '<i class="fa-solid fa-scale-balanced" style="margin-right:6px;"></i>This may be a lawyer case \u2014 see Legal tab for free consultations.';
                    banner.appendChild(bannerText);

                    var bannerActions = document.createElement('div');
                    bannerActions.className = 'lawyer-banner-actions';

                    var goBtn = document.createElement('button');
                    goBtn.className = 'lawyer-banner-go';
                    goBtn.textContent = 'See Legal Tab';
                    goBtn.onclick = function() { switchTab('legal', document.querySelectorAll('.nav-btn')[4]); };
                    bannerActions.appendChild(goBtn);

                    var dismissBtn = document.createElement('button');
                    dismissBtn.className = 'lawyer-banner-dismiss';
                    dismissBtn.title = 'Dismiss';
                    dismissBtn.textContent = '\u00d7';
                    dismissBtn.onclick = function() { banner.remove(); };
                    bannerActions.appendChild(dismissBtn);

                    banner.appendChild(bannerActions);
                    resultEl.before(banner);
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

        function submitReport(issueType) {
            var overlay = document.getElementById('loadingOverlay');
            overlay.classList.add('show');

            if (!('geolocation' in navigator)) {
                overlay.classList.remove('show');
                showToast('Geolocation is not supported by your browser');
                return;
            }

            navigator.geolocation.getCurrentPosition(
                function(position) {
                    document.getElementById('issueTypeInput').value = issueType;
                    document.getElementById('latInput').value = position.coords.latitude;
                    document.getElementById('lngInput').value = position.coords.longitude;
                    document.getElementById('reportForm').submit();
                },
                function(error) {
                    overlay.classList.remove('show');
                    showToast('Could not get your location. Please enable GPS.');
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
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

        function analyseTicket() {
            var text = (document.getElementById('advisorInput').value || '').toLowerCase();
            var resultEl = document.getElementById('advisorResult');
            var severityEl = document.getElementById('advisorSeverity');
            var actionEl = document.getElementById('advisorAction');
            var reasonEl = document.getElementById('advisorReason');

            if (!text.trim()) {
                showToast('Please describe your ticket first');
                return;
            }

            var urgent = /stunt|impaired|dui|criminal|dangerous driving|fail to remain|hit.?and.?run|100\s*km|over 50|50\s*(km|over)|60\s*(km|over)/i.test(text);
            var serious = /careless|school zone|construction zone|red light camera|cell phone|handheld|bike lane|40\s*(km|over)|45\s*(km|over)|photo radar|plate den/i.test(text);

            var severity, action, reason, cssClass, highlights;

            if (urgent) {
                severity = 'Urgent — Get a Lawyer Now';
                cssClass = 'advisor-result-urgent';
                if (/stunt/i.test(text)) {
                    action = 'Retain a traffic defence lawyer immediately';
                    reason = 'Stunt Driving (50+ km/h over or aggressive manoeuvres) carries an automatic 30-day licence suspension, vehicle impoundment, and fines up to $10,000. A conviction can lead to criminal charges. You must contest this.';
                    highlights = ['firm-xcopper', 'firm-xpolice', 'firm-hwylaw'];
                } else if (/impaired|dui/i.test(text)) {
                    action = 'Contact a criminal defence lawyer today';
                    reason = 'DUI / Impaired Driving is a criminal offence in Canada. A conviction means a criminal record, mandatory driving suspension, and significant fines. You need an experienced criminal HTA lawyer.';
                    highlights = ['firm-hwylaw', 'firm-xpolice', 'firm-xcopper'];
                } else {
                    action = 'Retain a traffic defence lawyer immediately';
                    reason = 'This charge carries serious consequences including potential licence suspension, vehicle impoundment, criminal record, or insurance surcharge. Do not pay — contest it with legal representation.';
                    highlights = ['firm-xcopper', 'firm-hwylaw', 'firm-xpolice'];
                }
            } else if (serious) {
                severity = 'Serious — Consider a Paralegal';
                cssClass = 'advisor-result-serious';
                if (/careless/i.test(text)) {
                    action = 'Hire a paralegal or traffic lawyer';
                    reason = 'Careless Driving carries 6 demerit points and fines up to $2,000. It can be reduced to a lesser charge by an experienced paralegal or lawyer.';
                    highlights = ['firm-xcops', 'firm-pointts', 'firm-trafficexperts'];
                } else if (/red light|photo radar/i.test(text)) {
                    action = 'A paralegal can often get this reduced or dismissed';
                    reason = 'Red light camera and photo radar tickets affect your insurance. A licensed paralegal can often challenge the evidence or negotiate a reduced fine.';
                    highlights = ['firm-ottlegal', 'firm-xcops', 'firm-streetlegal'];
                } else if (/bike lane/i.test(text)) {
                    action = 'A paralegal can contest this ticket';
                    reason = 'Bike lane infractions carry fines of $150–$500 and can impact your driving record. A paralegal may be able to have it dismissed or reduced.';
                    highlights = ['firm-streetlegal', 'firm-xcops', 'firm-ottlegal'];
                } else {
                    action = 'Consider hiring a paralegal to contest this';
                    reason = 'This offence carries demerit points or a significant fine that could impact your insurance. A paralegal can often negotiate a reduction or withdrawal.';
                    highlights = ['firm-xcops', 'firm-pointts', 'firm-trafficexperts'];
                }
            } else {
                severity = 'Minor — You Can Handle This';
                cssClass = 'advisor-result-minor';
                action = 'Pay the fine or contest it yourself online';
                reason = 'This appears to be a minor infraction with no demerit points or low risk to your insurance. You can pay at toronto.ca or request a trial by mail. A paralegal may still save you money on larger fines.';
                highlights = ['firm-streetlegal', 'firm-ottlegal'];
            }

            resultEl.className = 'advisor-result show ' + cssClass;
            severityEl.textContent = severity;
            actionEl.textContent = action;
            reasonEl.textContent = reason;

            document.querySelectorAll('.firm-card').forEach(function(el) {
                el.classList.remove('firm-card-highlight');
            });
            if (highlights && highlights.length) {
                setTimeout(function() {
                    highlights.forEach(function(id, i) {
                        var el = document.getElementById(id);
                        if (el) {
                            el.classList.add('firm-card-highlight');
                            if (i === 0) {
                                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }
                            setTimeout(function() { el.classList.remove('firm-card-highlight'); }, 3000);
                        }
                    });
                }, 400);
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
        if (params.get('reported') === '1') {
            showToast('Hazard reported! Pin added to map.');
            switchTab('hotspots', document.querySelectorAll('.nav-btn')[3]);
        }
        if (params.has('saved') || params.has('deleted') || params.has('reported')) {
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
        'PRODID:-//DriveSafe TO//EN',
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
    reports_json = json.dumps(reports_data)
    return render_template_string(HTML_TEMPLATE,
        profile=users_data['profile'],
        reminders=reminders,
        profile_saved=profile_saved,
        reports=reports_data,
        reports_json=reports_json
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

@app.route('/report_311', methods=['POST'])
def handle_311_report():
    issue_type = request.form.get('issue_type', '').strip()
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    if issue_type and lat and lng:
        try:
            reports_data.append({
                "type": issue_type,
                "lat": float(lat),
                "lng": float(lng),
                "status": "Logged in Community App"
            })
        except (ValueError, TypeError):
            pass
    return redirect('/?reported=1')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
