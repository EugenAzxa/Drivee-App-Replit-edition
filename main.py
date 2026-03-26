from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import json
import re
from openai import OpenAI

# do not change this unless explicitly requested by the user
_openai_client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key')

users_data = {
    'profile': {'name': '', 'plate': ''},
    'reminders': []
}

reports_data = [
    {"type": "Pothole", "lat": 43.650, "lng": -79.390, "status": "Pending 311", "name": "Alex T.", "color": "#0A84FF"},
    {"type": "Broken Meter", "lat": 43.652, "lng": -79.383, "status": "Pending 311", "name": "Sara M.", "color": "#30D158"},
    {"type": "Hidden Sign", "lat": 43.648, "lng": -79.396, "status": "Pending 311", "name": "James K.", "color": "#BF5AF2"}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="theme-color" content="#0A84FF">
    <title>Drivee | Professional</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚗</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous"/>
    <script src="https://unpkg.com/tesseract.js@v4.0.1/dist/tesseract.min.js"></script>
    <style>
        *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

        :root {
            --bg-root: #F0F4FF;
            --bg-surface: #FFFFFF;
            --bg-elevated: #F3F7F3;
            --bg-input: #F0F4F0;
            --border: rgba(0,0,0,0.08);
            --border-focus: rgba(10,132,255,0.35);
            --text-primary: #1A1A1A;
            --text-secondary: #6B7280;
            --text-tertiary: #9CA3AF;
            --blue: #2563EB;
            --blue-vivid: #2563EB;
            --blue-subtle: rgba(37,99,235,0.10);
            --blue-glow: rgba(37,99,235,0.16);
            --purple: #7C3AED;
            --purple-subtle: rgba(124,58,237,0.10);
            --purple-glow: rgba(124,58,237,0.16);
            --teal: #0891B2;
            --teal-subtle: rgba(8,145,178,0.10);
            --teal-glow: rgba(8,145,178,0.16);
            --rose: #DC2626;
            --rose-subtle: rgba(220,38,38,0.10);
            --rose-glow: rgba(220,38,38,0.16);
            --amber: #D97706;
            --amber-subtle: rgba(217,119,6,0.12);
            --amber-glow: rgba(217,119,6,0.16);
            --green: #0A84FF;
            --green-vivid: #3B9EFF;
            --green-subtle: rgba(10,132,255,0.12);
            --green-glow: rgba(10,132,255,0.18);
            --orange: #EA580C;
            --orange-subtle: rgba(234,88,12,0.12);
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
            padding: 0 16px;
            padding-top: calc(var(--safe-top) + 80px);
            padding-bottom: calc(var(--safe-bottom) + 110px);
        }

        /* ── Top Search Bar ── */
        .top-search-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 90;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: calc(var(--safe-top) + 10px) 16px 10px;
            max-width: 460px;
            margin: 0 auto;
            background: var(--bg-root);
        }
        .search-input-wrap {
            flex: 1;
            position: relative;
            display: flex;
            align-items: center;
        }
        .search-icon {
            position: absolute;
            left: 14px;
            color: var(--text-tertiary);
            font-size: 14px;
            pointer-events: none;
        }
        .search-input {
            width: 100%;
            padding: 12px 14px 12px 38px;
            background: #FFFFFF;
            border: 1.5px solid var(--border);
            border-radius: 50px;
            color: var(--text-secondary);
            font-size: 15px;
            font-family: var(--font);
            font-weight: 400;
            outline: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            cursor: pointer;
        }
        .search-bell {
            position: relative;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 1.5px solid var(--border);
            color: var(--text-secondary);
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        }
        .bell-badge {
            position: absolute;
            top: -2px;
            right: -2px;
            background: var(--rose);
            color: #fff;
            font-size: 9px;
            font-weight: 700;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid var(--bg-root);
        }
        .search-profile {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #FFFFFF;
            border: 1.5px solid var(--border);
            color: var(--text-secondary);
            font-size: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        }

        /* ── Legacy header (hidden) ── */
        .header { display: none; }

        .card {
            background: var(--bg-surface);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            animation: slideUp 0.5s ease-out both;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 16px rgba(0,0,0,0.07), 0 1px 4px rgba(0,0,0,0.05);
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
            background: #FFFFFF;
            border: 1.5px solid var(--border);
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
            box-shadow: 0 0 0 2px var(--green);
            border-color: var(--green);
        }
        .field input[type="date"] { color-scheme: light; }
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
            background: var(--green);
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
            background: #FFFFFF;
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
            background: var(--green-subtle);
            color: var(--green);
        }
        .cal-sync-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font);
            border: none;
            background: linear-gradient(135deg, #eaf3ff 0%, #d6eaff 100%);
            color: var(--blue);
            cursor: pointer;
            transition: box-shadow 0.15s, transform 0.1s;
            -webkit-tap-highlight-color: transparent;
        }
        .cal-sync-btn:active { transform: scale(0.96); }
        .cal-sync-btn svg { width: 13px; height: 13px; flex-shrink: 0; }
        .cal-sheet-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.45);
            z-index: 9000;
            display: flex;
            align-items: flex-end;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.25s;
        }
        .cal-sheet-overlay.open {
            opacity: 1;
            pointer-events: all;
        }
        .cal-sheet {
            background: #fff;
            border-radius: 22px 22px 0 0;
            width: 100%;
            max-width: 480px;
            padding: 20px 20px 36px;
            transform: translateY(100%);
            transition: transform 0.3s cubic-bezier(.32,1,.22,1);
        }
        .cal-sheet-overlay.open .cal-sheet {
            transform: translateY(0);
        }
        .cal-sheet-drag {
            width: 40px; height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin: 0 auto 18px;
        }
        .cal-sheet-title {
            font-size: 17px;
            font-weight: 700;
            color: var(--text-primary);
            text-align: center;
            margin-bottom: 6px;
        }
        .cal-sheet-sub {
            font-size: 13px;
            color: var(--text-secondary);
            text-align: center;
            margin-bottom: 20px;
        }
        .cal-sheet-options {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .cal-sheet-opt {
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 14px 16px;
            border-radius: 14px;
            border: none;
            cursor: pointer;
            font-family: var(--font);
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            background: #f5f7fa;
            text-decoration: none;
            transition: background 0.15s, transform 0.1s;
            -webkit-tap-highlight-color: transparent;
        }
        .cal-sheet-opt:active { transform: scale(0.97); }
        .cal-sheet-opt-icon {
            width: 40px; height: 40px;
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 22px;
            flex-shrink: 0;
        }
        .cal-opt-phone .cal-sheet-opt-icon { background: #eaf3ff; }
        .cal-opt-gcal .cal-sheet-opt-icon { background: #fff3ea; }
        .cal-sheet-opt-sub {
            font-size: 12px;
            font-weight: 400;
            color: var(--text-secondary);
            margin-top: 1px;
        }
        .cal-sheet-cancel {
            display: block;
            width: 100%;
            margin-top: 14px;
            padding: 14px;
            border-radius: 14px;
            border: none;
            background: #f5f7fa;
            font-family: var(--font);
            font-size: 15px;
            font-weight: 600;
            color: var(--text-secondary);
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
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
            padding-bottom: var(--safe-bottom);
            pointer-events: none;
        }
        .nav-inner {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 10px 16px 14px;
            max-width: 460px;
            margin: 0 auto;
            pointer-events: none;
        }
        .nav-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            flex: 1;
            background: #FFFFFF;
            border-radius: 50px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.14), 0 1px 6px rgba(0,0,0,0.08);
            padding: 7px 10px;
            pointer-events: all;
        }
        .nav-btn {
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: 6px;
            cursor: pointer;
            border: none;
            background: none;
            color: var(--text-secondary);
            font-family: var(--font);
            font-size: 13px;
            font-weight: 500;
            flex: 1;
            padding: 9px 6px;
            border-radius: 40px;
            transition: all 0.22s cubic-bezier(0.34,1.56,0.64,1);
            white-space: nowrap;
        }
        .nav-btn.active {
            background: var(--green);
            color: #fff;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(10,132,255,0.35);
        }
        .nav-btn i {
            font-size: 15px;
            display: block;
            flex-shrink: 0;
        }
        .nav-btn svg {
            width: 15px;
            height: 15px;
            flex-shrink: 0;
        }
        .nav-label {
            display: none;
        }
        .nav-btn.active .nav-label {
            display: inline;
        }
        .nav-fab {
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: var(--green);
            color: #fff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            box-shadow: 0 4px 16px rgba(10,132,255,0.4);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            flex-shrink: 0;
            pointer-events: all;
            text-decoration: none;
        }
        .nav-fab:active {
            transform: scale(0.93);
            box-shadow: 0 2px 8px rgba(10,132,255,0.35);
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
            background: #FFFFFF;
            border: none;
            color: var(--green);
            box-shadow: 0 6px 24px rgba(0,0,0,0.15);
        }
        .toast.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }

        /* ── Embedded map with fullscreen option ── */
        #map {
            height: 420px;
            border-radius: 18px;
            border: none;
            z-index: 1;
            display: block;
        }
        .map-hero-section {
            position: relative;
            margin: 0 0 16px;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.10);
        }
        /* Fullscreen state */
        .map-hero-section.map-is-fullscreen {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: 4000;
            margin: 0;
            border-radius: 0;
            overflow: hidden;
        }
        .map-hero-section.map-is-fullscreen #map {
            height: 100% !important;
            border-radius: 0;
        }
        .map-float-controls {
            position: absolute;
            bottom: 12px;
            left: 0;
            right: 0;
            z-index: 800;
            padding: 0 10px;
            pointer-events: none;
        }
        .map-float-layers {
            display: flex;
            gap: 6px;
            flex-wrap: nowrap;
            overflow-x: auto;
            background: rgba(255,255,255,0.94);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 22px;
            padding: 8px 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.14);
            scrollbar-width: none;
            pointer-events: all;
        }
        .map-float-layers::-webkit-scrollbar { display: none; }
        .map-float-layers .layer-toggle {
            white-space: nowrap;
            flex-shrink: 0;
            background: transparent;
            border-color: transparent;
            padding: 5px 10px;
        }
        .map-float-layers .layer-toggle.active {
            background: rgba(10,132,255,0.08);
            border-color: rgba(10,132,255,0.2);
        }
        .map-load-status {
            position: absolute;
            bottom: 68px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 900;
            background: rgba(255,255,255,0.9);
            backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 5px 14px;
            font-size: 11px;
            color: var(--text-secondary);
            display: none;
            white-space: nowrap;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .map-gps-fab {
            position: absolute;
            top: 12px;
            left: 12px;
            z-index: 800;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.95);
            border: none;
            box-shadow: 0 2px 12px rgba(0,0,0,0.18);
            color: var(--blue);
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .map-gps-fab:active { transform: scale(0.92); }
        .map-gps-fab.active-gps { background: var(--blue); color: #fff; }
        .map-expand-btn {
            position: absolute;
            top: 12px;
            right: 12px;
            z-index: 800;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.95);
            border: none;
            box-shadow: 0 2px 12px rgba(0,0,0,0.18);
            color: #374151;
            font-size: 15px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .map-expand-btn:active { transform: scale(0.92); }
        .map-is-fullscreen .map-expand-btn { color: var(--blue); }
        .map-caption {
            text-align: center;
            font-size: 12px;
            color: var(--text-tertiary);
            margin-top: 10px;
            line-height: 1.5;
            display: none;
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
        .leaflet-container { background: #f0f4ff !important; }
        .map-layer-toggles {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            margin: 12px 0 6px;
        }
        .layer-toggle {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 6px 12px;
            border-radius: 20px;
            border: 1.5px solid #e5e7eb;
            background: #f9fafb;
            color: #6b7280;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            transition: all 0.2s;
        }
        .layer-toggle.active {
            background: #fff;
            border-color: currentColor;
            color: inherit;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }
        .toggle-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        /* Parking neighborhood grid */
        .parking-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 12px;
        }
        .parking-card {
            background: #fff;
            border: 1.5px solid var(--border);
            border-radius: 14px;
            padding: 12px 14px;
            cursor: pointer;
            transition: all 0.18s;
            position: relative;
            overflow: hidden;
        }
        .parking-card:active { transform: scale(0.97); }
        .parking-card.selected {
            border-color: var(--blue);
            background: rgba(10,132,255,0.04);
            box-shadow: 0 0 0 3px rgba(10,132,255,0.12);
        }
        .parking-card-area {
            font-size: 11px;
            font-weight: 700;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 3px;
        }
        .parking-card-rate {
            font-size: 22px;
            font-weight: 800;
            color: var(--blue);
            font-family: var(--font-mono);
            line-height: 1;
        }
        .parking-card-unit {
            font-size: 11px;
            color: var(--text-tertiary);
            font-weight: 500;
        }
        .parking-card-name {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-primary);
            margin-top: 5px;
            line-height: 1.3;
        }
        .parking-detail-panel {
            background: rgba(10,132,255,0.04);
            border: 1.5px solid rgba(10,132,255,0.15);
            border-radius: 14px;
            padding: 16px;
            margin-top: 12px;
            display: none;
            animation: fadeIn 0.2s ease;
        }
        .parking-detail-panel.show { display: block; }
        .parking-detail-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .parking-detail-row {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(10,132,255,0.08);
            font-size: 13px;
        }
        .parking-detail-row:last-child { border-bottom: none; }
        .parking-detail-label {
            color: var(--text-tertiary);
            font-weight: 500;
            min-width: 60px;
            flex-shrink: 0;
        }
        .parking-detail-value {
            color: var(--text-primary);
            font-weight: 500;
            flex: 1;
        }
        .parking-detail-value.warn { color: var(--rose); font-weight: 600; }
        .parking-detail-value.free { color: #059669; font-weight: 600; }
        .parking-detail-value.cost { color: var(--blue); font-weight: 700; font-family: var(--font-mono); }

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
            background-color: #FFFFFF;
            border: 1.5px solid var(--border);
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
            background: rgba(10,132,255,0.05);
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
            border: 1.5px solid var(--border);
            background: #FFFFFF;
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
            background: #FFFFFF;
            border: 1.5px solid var(--border);
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
            box-shadow: 0 0 0 2px var(--green);
            border-color: var(--green);
        }
        .copy-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-top: 10px;
            padding: 8px 16px;
            border-radius: var(--radius);
            border: none;
            background: var(--green-subtle);
            color: var(--green);
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
        .firm-promo {
            margin-top: 12px;
            padding: 9px 12px;
            background: var(--green-subtle);
            border-radius: 8px;
            font-size: 12px;
            color: var(--green);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 7px;
            line-height: 1.4;
        }
        .firm-promo strong {
            font-weight: 700;
            font-family: var(--font-mono);
            letter-spacing: 0.5px;
        }
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

        /* Legal ticket scanner verdict */
        .legal-verdict {
            display: none;
            margin-top: 14px;
            padding: 16px;
            border-radius: var(--radius);
        }
        .legal-verdict.show { display: block; animation: fadeIn 0.25s ease; }
        .legal-verdict-badge {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.9px;
            margin-bottom: 7px;
        }
        .verdict-headline {
            font-size: 19px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
            margin-bottom: 8px;
            line-height: 1.2;
        }
        .verdict-fine-pill {
            display: inline-block;
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 6px;
            background: var(--bg-elevated);
            color: var(--text-secondary);
            margin-bottom: 10px;
        }
        .verdict-detail {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.55;
            margin-bottom: 14px;
        }
        .verdict-cta {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            transition: opacity 0.15s;
        }
        .verdict-cta:active { opacity: 0.8; }
        .verdict-pay { background: var(--green-subtle); }
        .verdict-pay .legal-verdict-badge { color: var(--green); }
        .verdict-contest { background: var(--blue-subtle); }
        .verdict-contest .legal-verdict-badge { color: var(--blue); }
        .verdict-paralegal { background: var(--amber-subtle); }
        .verdict-paralegal .legal-verdict-badge { color: var(--amber); }
        .verdict-paralegal .verdict-cta { background: var(--amber); color: #000; }
        .verdict-lawyer { background: var(--rose-subtle); }
        .verdict-lawyer .legal-verdict-badge { color: var(--rose); }
        .verdict-lawyer .verdict-cta { background: var(--rose); color: #fff; }

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

        /* Report email panel */
        .report-email-panel {
            display: none;
            margin-top: 14px;
            padding: 14px;
            background: var(--bg-elevated);
            border-radius: 10px;
            animation: fadeIn 0.2s ease;
        }
        .report-email-panel.show { display: block; }
        .report-email-panel-title {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .report-ai-label {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .report-name-input {
            width: 100%;
            background: var(--bg-surface);
            border: 1.5px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 13px;
            font-family: var(--font);
            color: var(--text-primary);
            box-sizing: border-box;
            margin-bottom: 8px;
        }
        .report-email-textarea {
            width: 100%;
            min-height: 120px;
            background: var(--bg-surface);
            border: 1.5px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 11.5px;
            font-family: var(--font);
            color: var(--text-primary);
            resize: none;
            box-sizing: border-box;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        .report-email-actions { display: flex; gap: 7px; flex-wrap: wrap; }
        .report-email-btn {
            flex: 1;
            min-width: 110px;
            padding: 9px 10px;
            border-radius: 9px;
            border: none;
            font-size: 11.5px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            transition: opacity 0.15s;
        }
        .report-email-btn:active { opacity: 0.8; }
        .report-btn-311 { background: var(--blue); color: #fff; }
        .report-btn-greenp { background: var(--green); color: #fff; }
        .report-btn-police { background: var(--rose); color: #fff; }
        .report-btn-cycling { background: var(--purple); color: #fff; }
        .report-pin-btn {
            width: 100%;
            margin-top: 10px;
            padding: 11px;
            border-radius: 9px;
            border: none;
            background: var(--purple);
            color: #fff;
            font-size: 13px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: opacity 0.15s;
        }
        .report-pin-btn:active { opacity: 0.8; }
        /* Photo upload */
        .report-photo-row {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0 6px;
        }
        .report-photo-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 14px;
            border-radius: 9px;
            border: 1.5px dashed rgba(10,132,255,0.4);
            background: rgba(10,132,255,0.06);
            color: var(--blue);
            font-size: 13px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            transition: all 0.15s;
            white-space: nowrap;
        }
        .report-photo-btn:active { opacity: 0.75; }
        .report-photo-btn.has-photo {
            border-style: solid;
            background: rgba(10,132,255,0.10);
        }
        .report-photo-status {
            font-size: 12px;
            color: var(--text-secondary);
            flex: 1;
        }
        .report-photo-status.analyzing { color: var(--blue); }
        .report-photo-status.done { color: var(--green); }
        .report-photo-preview {
            position: relative;
            display: none;
            margin-bottom: 10px;
        }
        .report-photo-preview img {
            width: 100%;
            max-height: 180px;
            object-fit: cover;
            border-radius: 10px;
            border: 1.5px solid rgba(0,0,0,0.08);
        }
        .report-photo-remove {
            position: absolute;
            top: 6px; right: 6px;
            width: 26px; height: 26px;
            border-radius: 50%;
            background: rgba(0,0,0,0.55);
            color: #fff;
            border: none;
            font-size: 13px;
            cursor: pointer;
            display: flex; align-items: center; justify-content: center;
        }
        /* Popup photo */
        .report-popup-photo {
            width: 100%;
            max-width: 220px;
            border-radius: 8px;
            margin-top: 7px;
            display: block;
        }
        /* Avatar markers on map */
        .report-avatar {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            font-size: 12px;
            font-weight: 700;
            color: #fff;
            border: 2px solid rgba(255,255,255,0.35);
            box-shadow: 0 2px 8px rgba(0,0,0,0.55);
            font-family: var(--font);
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
        .gps-guardian-section {
            background: #fff;
            border-radius: 16px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        }
        .gps-guardian-info {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 14px;
        }
        .gps-guardian-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: rgba(10,132,255,0.10);
            color: var(--blue);
            font-size: 19px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .gps-guardian-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }
        .gps-guardian-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
        }

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

        /* ── AI Chat Panel ── */
        .chat-fab {
            position: fixed;
            bottom: calc(var(--safe-bottom) + 90px);
            right: 18px;
            z-index: 110;
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: var(--blue);
            color: #fff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 4px 18px rgba(10,132,255,0.45);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .chat-fab:active { transform: scale(0.93); }
        .chat-fab .chat-fab-dot {
            position: absolute;
            top: -1px;
            right: -1px;
            width: 13px;
            height: 13px;
            background: #fff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chat-fab .chat-fab-dot::after {
            content: '';
            width: 7px;
            height: 7px;
            background: var(--green);
            border-radius: 50%;
        }
        .chat-overlay {
            display: none;
            position: fixed;
            inset: 0;
            z-index: 150;
            background: rgba(0,0,0,0.3);
            backdrop-filter: blur(2px);
        }
        .chat-overlay.open { display: block; }
        .chat-panel {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%) translateY(100%);
            z-index: 160;
            width: min(460px, 100vw);
            height: 75vh;
            max-height: 620px;
            background: #fff;
            border-radius: 24px 24px 0 0;
            box-shadow: 0 -8px 40px rgba(0,0,0,0.18);
            display: flex;
            flex-direction: column;
            transition: transform 0.38s cubic-bezier(0.22,1,0.36,1);
            overflow: hidden;
        }
        .chat-panel.open {
            transform: translateX(-50%) translateY(0);
        }
        .chat-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 18px 20px 14px;
            border-bottom: 1px solid var(--border);
            flex-shrink: 0;
        }
        .chat-header-icon {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: var(--blue-subtle);
            color: var(--blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            flex-shrink: 0;
        }
        .chat-header-text { flex: 1; min-width: 0; }
        .chat-header-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.2px;
        }
        .chat-header-sub {
            font-size: 11px;
            color: var(--text-tertiary);
            margin-top: 1px;
        }
        .chat-close {
            background: var(--bg-elevated);
            border: none;
            color: var(--text-secondary);
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            flex-shrink: 0;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px 16px 8px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            scroll-behavior: smooth;
        }
        .chat-msg {
            display: flex;
            gap: 8px;
            animation: slideUp 0.2s ease;
        }
        .chat-msg.user { flex-direction: row-reverse; }
        .chat-msg-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            flex-shrink: 0;
            margin-top: 2px;
        }
        .chat-msg.bot .chat-msg-avatar { background: var(--blue-subtle); color: var(--blue); }
        .chat-msg.user .chat-msg-avatar { background: var(--bg-elevated); color: var(--text-secondary); }
        .chat-msg-bubble {
            max-width: 82%;
            padding: 10px 14px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.5;
        }
        .chat-msg.bot .chat-msg-bubble {
            background: var(--bg-elevated);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
        }
        .chat-msg.user .chat-msg-bubble {
            background: var(--blue);
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .chat-typing {
            display: none;
            align-items: center;
            gap: 4px;
            padding: 10px 14px;
            background: var(--bg-elevated);
            border-radius: 18px;
            border-bottom-left-radius: 4px;
            width: fit-content;
        }
        .chat-typing.show { display: flex; }
        .chat-typing span {
            width: 6px;
            height: 6px;
            background: var(--text-tertiary);
            border-radius: 50%;
            animation: typingBounce 1.2s infinite;
        }
        .chat-typing span:nth-child(2) { animation-delay: 0.2s; }
        .chat-typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-5px); }
        }
        .chat-suggestions {
            display: flex;
            gap: 6px;
            padding: 0 16px 8px;
            overflow-x: auto;
            flex-shrink: 0;
            scrollbar-width: none;
        }
        .chat-suggestions::-webkit-scrollbar { display: none; }
        .chat-suggestion {
            white-space: nowrap;
            padding: 6px 12px;
            border-radius: 20px;
            border: 1.5px solid var(--border);
            background: #fff;
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            font-family: var(--font);
            transition: all 0.15s;
            flex-shrink: 0;
        }
        .chat-suggestion:hover, .chat-suggestion:active {
            border-color: var(--blue);
            color: var(--blue);
            background: var(--blue-subtle);
        }
        .chat-input-row {
            display: flex;
            align-items: flex-end;
            gap: 10px;
            padding: 12px 16px calc(var(--safe-bottom) + 14px);
            border-top: 1px solid var(--border);
            flex-shrink: 0;
        }
        .chat-input {
            flex: 1;
            padding: 10px 14px;
            background: var(--bg-elevated);
            border: 1.5px solid var(--border);
            border-radius: 22px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: var(--font);
            outline: none;
            resize: none;
            max-height: 100px;
            min-height: 40px;
            line-height: 1.4;
            transition: border-color 0.2s;
        }
        .chat-input:focus { border-color: var(--blue); }
        .chat-send {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--blue);
            color: #fff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
            transition: opacity 0.2s, transform 0.15s;
        }
        .chat-send:disabled { opacity: 0.45; cursor: not-allowed; }
        .chat-send:not(:disabled):active { transform: scale(0.93); }
    
        /* ── Splash Screen ── */
        #splashScreen {
            position: fixed;
            inset: 0;
            z-index: 99999;
            background: #0A84FF;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            pointer-events: all;
            animation: splashExit 0.5s ease 2.0s forwards;
        }
        #splashScreen.hidden { display: none; }
        .splash-inner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            animation: splashContentIn 0.65s cubic-bezier(0.34, 1.56, 0.64, 1) 0.15s both;
        }
        .splash-car-wrap {
            width: 88px;
            height: 88px;
            background: rgba(255,255,255,0.18);
            border-radius: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 22px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.18);
        }
        .splash-car-icon {
            font-size: 48px;
            line-height: 1;
        }
        .splash-wordmark {
            font-size: 46px;
            font-weight: 800;
            color: #fff;
            letter-spacing: -1.5px;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
            line-height: 1;
            margin-bottom: 10px;
        }
        .splash-tagline {
            font-size: 15px;
            color: rgba(255,255,255,0.78);
            font-weight: 500;
            letter-spacing: 0.2px;
            font-family: -apple-system, sans-serif;
            animation: splashTagIn 0.5s ease 0.55s both;
        }
        .splash-dots {
            display: flex;
            gap: 7px;
            margin-top: 52px;
            animation: splashTagIn 0.5s ease 0.8s both;
        }
        .splash-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: rgba(255,255,255,0.5);
            animation: dotPulse 1.1s ease infinite;
        }
        .splash-dot:nth-child(2) { animation-delay: 0.18s; }
        .splash-dot:nth-child(3) { animation-delay: 0.36s; }
        @keyframes splashExit {
            0% { opacity: 1; transform: scale(1); }
            100% { opacity: 0; transform: scale(1.04); pointer-events: none; }
        }
        @keyframes splashContentIn {
            from { opacity: 0; transform: translateY(28px) scale(0.88); }
            to   { opacity: 1; transform: translateY(0)   scale(1); }
        }
        @keyframes splashTagIn {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes dotPulse {
            0%, 100% { opacity: 0.4; transform: scale(0.85); }
            50%       { opacity: 1;   transform: scale(1.15); }
        }

        /* ── Install Guide Sheet ── */
        #installSheetOverlay {
            position: fixed;
            inset: 0;
            z-index: 99998;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: flex-end;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.28s ease;
        }
        #installSheetOverlay.open {
            opacity: 1;
            pointer-events: all;
        }
        #installSheet {
            background: #fff;
            border-radius: 26px 26px 0 0;
            width: 100%;
            max-width: 480px;
            padding: 12px 24px calc(28px + env(safe-area-inset-bottom, 0px));
            transform: translateY(100%);
            transition: transform 0.38s cubic-bezier(0.32, 1, 0.22, 1);
        }
        #installSheetOverlay.open #installSheet {
            transform: translateY(0);
        }
        .install-drag {
            width: 44px; height: 5px;
            background: #e0e0e0;
            border-radius: 3px;
            margin: 0 auto 20px;
        }
        .install-app-row {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 18px;
        }
        .install-app-icon {
            width: 58px;
            height: 58px;
            border-radius: 14px;
            background: #0A84FF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            flex-shrink: 0;
            box-shadow: 0 4px 16px rgba(10,132,255,0.3);
        }
        .install-app-name {
            font-size: 20px;
            font-weight: 800;
            color: #111;
            letter-spacing: -0.4px;
        }
        .install-app-sub {
            font-size: 13px;
            color: #6b7280;
            margin-top: 2px;
        }
        .install-steps {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 20px;
        }
        .install-step {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            background: #f8fafc;
            border-radius: 14px;
        }
        .install-step-num {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #0A84FF;
            color: #fff;
            font-size: 13px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .install-step-text {
            font-size: 14px;
            color: #374151;
            font-weight: 500;
            line-height: 1.35;
        }
        .install-step-text strong {
            color: #111;
            font-weight: 700;
        }
        .install-got-it {
            width: 100%;
            padding: 16px;
            background: #0A84FF;
            color: #fff;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 700;
            font-family: -apple-system, sans-serif;
            cursor: pointer;
            transition: opacity 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .install-got-it:active { opacity: 0.85; }
        .install-later {
            display: block;
            text-align: center;
            margin-top: 12px;
            font-size: 14px;
            color: #9ca3af;
            cursor: pointer;
            padding: 4px;
            -webkit-tap-highlight-color: transparent;
        }
    
        /* ── AI Search Bar ── */
        .top-search-bar {
            gap: 8px;
        }
        .ai-search-wrap {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 0;
            min-width: 0;
        }
        .ai-search-row {
            display: flex;
            align-items: center;
            background: #FFFFFF;
            border: 1.5px solid var(--border);
            border-radius: 50px;
            padding: 0 6px 0 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.07);
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .ai-search-row:focus-within {
            border-color: #0A84FF;
            box-shadow: 0 0 0 3px rgba(10,132,255,0.12), 0 2px 10px rgba(0,0,0,0.07);
        }
        .ai-search-icon {
            color: #0A84FF;
            font-size: 13px;
            flex-shrink: 0;
            margin-right: 8px;
        }
        .ai-search-input {
            flex: 1;
            border: none;
            background: transparent;
            color: var(--text-primary);
            font-size: 15px;
            font-family: var(--font);
            font-weight: 400;
            outline: none;
            padding: 12px 0;
            min-width: 0;
        }
        .ai-search-input::placeholder { color: var(--text-tertiary); }
        .ai-search-send {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: #0A84FF;
            color: #fff;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            flex-shrink: 0;
            transition: opacity 0.15s, transform 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .ai-search-send:active { opacity: 0.8; transform: scale(0.93); }
        .ai-chip-row {
            display: flex;
            gap: 7px;
            margin-top: 8px;
            overflow-x: auto;
            padding-bottom: 2px;
            scrollbar-width: none;
        }
        .ai-chip-row::-webkit-scrollbar { display: none; }
        .ai-chip {
            flex-shrink: 0;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(10,132,255,0.10);
            color: #0A84FF;
            border: none;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            white-space: nowrap;
            transition: background 0.15s, transform 0.1s;
            -webkit-tap-highlight-color: transparent;
        }
        .ai-chip:active { background: rgba(10,132,255,0.2); transform: scale(0.96); }

        /* ── Support Sheet ── */
        .support-overlay {
            position: fixed;
            inset: 0;
            z-index: 9900;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: flex-end;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.28s ease;
        }
        .support-overlay.open {
            opacity: 1;
            pointer-events: all;
        }
        .support-sheet {
            background: #fff;
            border-radius: 26px 26px 0 0;
            width: 100%;
            max-width: 480px;
            padding: 12px 24px calc(32px + env(safe-area-inset-bottom, 0px));
            transform: translateY(100%);
            transition: transform 0.38s cubic-bezier(0.32, 1, 0.22, 1);
        }
        .support-overlay.open .support-sheet {
            transform: translateY(0);
        }
        .support-drag {
            width: 44px; height: 5px;
            background: #e0e0e0;
            border-radius: 3px;
            margin: 0 auto 20px;
        }
        .support-heart-anim {
            text-align: center;
            font-size: 52px;
            margin-bottom: 12px;
            animation: heartBeat 1.2s ease-in-out infinite;
        }
        @keyframes heartBeat {
            0%, 100% { transform: scale(1); }
            14%       { transform: scale(1.15); }
            28%       { transform: scale(1); }
            42%       { transform: scale(1.1); }
            70%       { transform: scale(1); }
        }
        .support-title {
            font-size: 22px;
            font-weight: 800;
            color: #111;
            text-align: center;
            letter-spacing: -0.4px;
            margin-bottom: 8px;
        }
        .support-desc {
            font-size: 14px;
            color: #6b7280;
            text-align: center;
            line-height: 1.55;
            margin-bottom: 18px;
        }
        .support-bullet {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
            color: #374151;
            line-height: 1.4;
        }
        .support-bullet:last-of-type { border-bottom: none; }
        .support-bullet-icon {
            font-size: 18px;
            flex-shrink: 0;
            margin-top: 1px;
        }
        .support-gofundme-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            width: 100%;
            padding: 16px;
            margin-top: 18px;
            background: linear-gradient(135deg, #00b964 0%, #009d52 100%);
            color: #fff;
            border: none;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 700;
            font-family: var(--font);
            cursor: pointer;
            text-decoration: none;
            transition: opacity 0.15s, transform 0.1s;
            -webkit-tap-highlight-color: transparent;
        }
        .support-gofundme-btn:active { opacity: 0.9; transform: scale(0.98); }
        .support-close-link {
            display: block;
            text-align: center;
            margin-top: 12px;
            font-size: 14px;
            color: #9ca3af;
            cursor: pointer;
            padding: 4px;
            -webkit-tap-highlight-color: transparent;
        }

        /* ── Dispute AI Email ── */
        .dispute-divider {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 16px 0 12px;
            color: var(--text-tertiary);
            font-size: 12px;
            font-weight: 500;
        }
        .dispute-divider::before,
        .dispute-divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border);
        }
        .dispute-ai-label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .dispute-send-row {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .dispute-send-btn {
            flex: 1;
            min-width: 80px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 5px;
            padding: 10px 8px;
            background: #f8fafc;
            border: 1.5px solid var(--border);
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            font-family: var(--font);
            color: var(--text-secondary);
            text-decoration: none;
            cursor: pointer;
            text-align: center;
            transition: border-color 0.15s, background 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .dispute-send-btn i { font-size: 18px; color: #0A84FF; }
        .dispute-send-btn:active { background: rgba(10,132,255,0.06); border-color: #0A84FF; }
        .dispute-copy-email-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 12px;
            background: var(--green-subtle);
            color: var(--green);
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            margin-top: 10px;
            -webkit-tap-highlight-color: transparent;
        }
        .dispute-ai-building {
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 14px;
        }

        /* ── Guide Contact Banner ── */
        .guide-contact-card {
            background: linear-gradient(135deg, #0A84FF 0%, #1E6FDB 100%);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            text-align: center;
            color: #fff;
        }
        .guide-contact-title {
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.3px;
            margin-bottom: 6px;
        }
        .guide-contact-sub {
            font-size: 13px;
            opacity: 0.85;
            margin-bottom: 14px;
        }
        .guide-contact-email-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 11px 20px;
            background: rgba(255,255,255,0.22);
            border: 1.5px solid rgba(255,255,255,0.45);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            font-weight: 700;
            text-decoration: none;
            transition: background 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .guide-contact-email-btn:active { background: rgba(255,255,255,0.35); }

        /* ── AI Nav Suggestion Chips in Chat ── */
        .chat-nav-chip-row {
            display: flex;
            gap: 7px;
            flex-wrap: wrap;
            margin-top: 8px;
            padding: 0 44px;
        }
        .chat-nav-chip {
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(10,132,255,0.1);
            color: #0A84FF;
            border: none;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font);
            cursor: pointer;
            white-space: nowrap;
            transition: background 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .chat-nav-chip:active { background: rgba(10,132,255,0.2); }
    
        /* ---- Chat photo button ---- */
        .chat-photo-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: #f0f4ff;
            color: #0A84FF;
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
            transition: background 0.15s;
            -webkit-tap-highlight-color: transparent;
        }
        .chat-photo-btn:active { background: rgba(10,132,255,0.18); }
        .chat-photo-preview-wrap {
            padding: 6px 12px 0;
            display: flex;
            gap: 8px;
        }
        .chat-photo-thumb {
            position: relative;
            width: 64px;
            height: 64px;
            border-radius: 10px;
            overflow: hidden;
            flex-shrink: 0;
            border: 1.5px solid var(--border);
        }
        .chat-photo-thumb img { width: 100%; height: 100%; object-fit: cover; }
        .chat-photo-thumb-remove {
            position: absolute; top: 2px; right: 2px;
            width: 18px; height: 18px;
            border-radius: 50%;
            background: rgba(0,0,0,0.65);
            color: #fff; border: none;
            font-size: 10px; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
        }
        .chat-msg-photo {
            max-width: 200px;
            border-radius: 10px;
            margin-bottom: 4px;
            display: block;
        }
</style>
    <link rel="manifest" href="/manifest.json">
    <meta name="apple-mobile-web-app-title" content="Drivee">
    <link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='22' fill='%230A84FF'/><text x='50' y='68' font-size='52' text-anchor='middle' font-family='-apple-system,sans-serif' font-weight='900' fill='white'>D</text></svg>">
</head>
<body>
    <div id="splashScreen">
        <div class="splash-inner">
            <div class="splash-car-wrap">
                <span class="splash-car-icon">🚗</span>
            </div>
            <div class="splash-wordmark">Drivee</div>
            <div class="splash-tagline">Toronto Parking &amp; Fines Manager</div>
            <div class="splash-dots">
                <div class="splash-dot"></div>
                <div class="splash-dot"></div>
                <div class="splash-dot"></div>
            </div>
        </div>
    </div>

    <div id="installSheetOverlay" onclick="handleInstallOverlayClick(event)">
        <div id="installSheet">
            <div class="install-drag"></div>
            <div class="install-app-row">
                <div class="install-app-icon">🚗</div>
                <div>
                    <div class="install-app-name">Drivee</div>
                    <div class="install-app-sub">Add to your Home Screen</div>
                </div>
            </div>
            <div class="install-steps" id="installSteps"></div>
            <button class="install-got-it" onclick="dismissInstall()">Got it — Thanks!</button>
            <span class="install-later" onclick="closeInstallSheet()">Maybe later</span>
        </div>
    </div>

    <div id="loadingOverlay" class="loading-overlay">
        <i class="fa-solid fa-satellite-dish fa-spin"></i>
        <span>Grabbing GPS Coordinates...</span>
    </div>

    <div id="toast" class="toast"></div>

    <div class="app">
        <div class="top-search-bar">
            <div class="ai-search-wrap">
                <div class="ai-search-row">
                    <i class="fa-solid fa-sparkles ai-search-icon"></i>
                    <input type="text" id="aiSearchInput" class="ai-search-input"
                           placeholder="Ask Drivee AI anything..."
                           oninput="onAiSearchInput(this.value)"
                           onkeydown="if(event.key==='Enter'&&this.value.trim()){sendAiSearch();event.preventDefault()}">
                    <button class="ai-search-send" id="aiSearchSendBtn" onclick="sendAiSearch()" style="opacity:0;pointer-events:none">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
                <div class="ai-chip-row">
                    <button class="ai-chip" onclick="aiChipAction('ticket')">&#x1F3AB; Got a ticket?</button>
                    <button class="ai-chip" onclick="aiChipAction('parking')">&#x1F17F; Free parking</button>
                    <button class="ai-chip" onclick="aiChipAction('pay')">&#x1F4B3; Pay a fine</button>
                    <button class="ai-chip" onclick="aiChipAction('dispute')">&#x2696; Dispute it</button>
                    <button class="ai-chip" onclick="aiChipAction('towed')">&#x1F697; Car towed?</button>
                    <button class="ai-chip" onclick="aiChipAction('report')">&#x2709; Report a problem</button>
                </div>
            </div>
            <button class="search-bell" onclick="switchTab('dashboard', document.querySelectorAll('.nav-btn')[1])" title="Reminders">
                <i class="fa-solid fa-bell"></i>
                {% if reminders %}<span class="bell-badge">{{ reminders|length }}</span>{% endif %}
            </button>
        </div>

        <div id="tab-guide" class="tab active">
            <div class="card card-blue card-1">
                <div class="card-label label-blue"><i class="fa-solid fa-book-open"></i> How to Use This App</div>
                <p class="card-desc">Welcome to Drivee — your all-in-one Toronto parking and traffic fine manager. Here is a quick walkthrough of everything you can do.</p>

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
                        <div class="guide-title">Find Free Drop-off Spots</div>
                        <div class="guide-desc">The Map tab shows 25 real free street parking spots across Toronto — from Cabbagetown to Leslieville, Roncesvalles to the Danforth. Tap any pin to see the address, schedule, max stay, and parking rules.</div>
                        <span class="guide-tab-ref guide-tab-hot">Map</span>
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

            <div class="guide-contact-card">
                <div class="guide-contact-title">&#x1F4AC; Questions or Problems?</div>
                <div class="guide-contact-sub">We are here to help. Reach out to the Drivee team directly for support, feedback, or bug reports.</div>
                <a href="mailto:drivee.canada@gmail.com" class="guide-contact-email-btn">
                    <i class="fa-solid fa-envelope"></i> drivee.canada@gmail.com
                </a>
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
                                <button class="cal-sync-btn" onclick="openCalSheet('/calendar/ics/{{ loop.index0 }}','{{ r.gcal_url }}','{{ r.ticket_num }}','{{ r.due_date_display }}')">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                                    Sync to Calendar
                                </button>
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
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/pay-your-provincial-offence/" target="_blank" rel="noopener" class="service-link svc-amber">
                        <div class="svc-icon">&#x1F6A8;</div>
                        <span class="svc-text">Speed Violation — Pay or Dispute</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>

                </div>
            </div>

            <div class="card card-green card-4">
                <div class="card-label label-green"><i class="fa-solid fa-square-parking"></i> Street Parking Rates</div>
                <p class="card-desc">Tap any neighbourhood to see the hourly rate, enforcement hours, and tow warnings.</p>
                <div class="parking-grid" id="parkingGrid">
                    <div class="parking-card" onclick="showParkingDetail('queen_west', this)">
                        <div class="parking-card-area">Downtown</div>
                        <div class="parking-card-rate">$3.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Queen St W</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('bloor_yorkville', this)">
                        <div class="parking-card-area">Yorkville</div>
                        <div class="parking-card-rate">$4.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Bloor St W</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('kensington', this)">
                        <div class="parking-card-area">West End</div>
                        <div class="parking-card-rate">$2.25</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Kensington Market</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('front_st', this)">
                        <div class="parking-card-area">Entertainment</div>
                        <div class="parking-card-rate">$5.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Front St (Arena)</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('king_west', this)">
                        <div class="parking-card-area">King West</div>
                        <div class="parking-card-rate">$3.50</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">King St W</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('financial', this)">
                        <div class="parking-card-area">Financial</div>
                        <div class="parking-card-rate">$4.50</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Bay St / King St E</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('chinatown', this)">
                        <div class="parking-card-area">Chinatown</div>
                        <div class="parking-card-rate">$2.50</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Spadina / Dundas</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('annex', this)">
                        <div class="parking-card-area">The Annex</div>
                        <div class="parking-card-rate">$2.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Bloor W / Bathurst</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('distillery', this)">
                        <div class="parking-card-area">Distillery</div>
                        <div class="parking-card-rate">$4.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Distillery District</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('little_italy', this)">
                        <div class="parking-card-area">Little Italy</div>
                        <div class="parking-card-rate">$2.25</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">College St W</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('greektown', this)">
                        <div class="parking-card-area">Greektown</div>
                        <div class="parking-card-rate">$2.50</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Danforth Ave</div>
                    </div>
                    <div class="parking-card" onclick="showParkingDetail('leslieville', this)">
                        <div class="parking-card-area">Leslieville</div>
                        <div class="parking-card-rate">$2.00</div>
                        <div class="parking-card-unit">/ hour</div>
                        <div class="parking-card-name">Queen St E</div>
                    </div>
                </div>
                <div class="parking-detail-panel" id="parkingDetailPanel">
                    <div class="parking-detail-title"><i class="fa-solid fa-circle-info" style="color:var(--blue);"></i> <span id="pdName"></span></div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Rate</span>
                        <span class="parking-detail-value cost" id="pdRate"></span>
                    </div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Hours</span>
                        <span class="parking-detail-value" id="pdHours"></span>
                    </div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Max Stay</span>
                        <span class="parking-detail-value" id="pdMax"></span>
                    </div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Free After</span>
                        <span class="parking-detail-value free" id="pdFree"></span>
                    </div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Rush Hour</span>
                        <span class="parking-detail-value warn" id="pdRush"></span>
                    </div>
                    <div class="parking-detail-row">
                        <span class="parking-detail-label">Tip</span>
                        <span class="parking-detail-value" id="pdTip" style="color:var(--text-secondary);font-size:12px;"></span>
                    </div>
                </div>
                <a href="https://apps.apple.com/ca/app/green-p/id429679356" target="_blank" rel="noopener" class="green-p-link" style="margin-top:14px;">
                    <i class="fa-solid fa-mobile-screen"></i> Open Green P App
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

                <div class="dispute-divider"><span>or write your own</span></div>

                <div class="dispute-ai-label"><i class="fa-solid fa-pen-to-square"></i> Describe Your Situation</div>
                <textarea id="disputeOwnIssue" class="dispute-textarea" placeholder="e.g. I got a ticket on King St but there was no visible sign. The sign was covered by a tree branch. I have photos..." style="min-height:90px"></textarea>

                <button class="btn btn-blue" onclick="buildDisputeEmailAI()" style="margin-top:10px;font-size:15px;">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Build Email with AI
                </button>

                <div id="disputeEmailSection" style="display:none; margin-top:16px;">
                    <div class="dispute-ai-label"><i class="fa-solid fa-envelope-open-text"></i> Your AI-Generated Dispute Email</div>
                    <textarea id="disputeEmailText" class="dispute-textarea" style="min-height:220px; font-size:13px;"></textarea>
                    <button class="dispute-copy-email-btn" onclick="copyDisputeEmail()">
                        <i class="fa-solid fa-copy"></i> Copy Email
                    </button>
                    <div class="dispute-ai-label" style="margin-top:14px;"><i class="fa-solid fa-paper-plane"></i> Send this email to:</div>
                    <div class="dispute-send-row">
                        <a class="dispute-send-btn" id="dspBtnParking" href="mailto:parkingoperations@toronto.ca" target="_blank">
                            <i class="fa-solid fa-square-parking"></i>
                            <span>Parking Office</span>
                        </a>
                        <a class="dispute-send-btn" id="dspBtnCourt" href="mailto:courtservices@toronto.ca" target="_blank">
                            <i class="fa-solid fa-gavel"></i>
                            <span>POA Court</span>
                        </a>
                        <a class="dispute-send-btn" id="dspBtnPolice" href="mailto:traffic.services@tps.ca" target="_blank">
                            <i class="fa-solid fa-shield-halved"></i>
                            <span>Police</span>
                        </a>
                        <a class="dispute-send-btn" id="dspBtnGreenP" href="mailto:customerservice@greenp.com" target="_blank">
                            <i class="fa-solid fa-charging-station"></i>
                            <span>Green P</span>
                        </a>
                    </div>
                </div>
            </div>

            <div class="card card-blue card-7">
                <div class="card-label label-blue"><i class="fa-solid fa-flag-usa"></i> Got a Ticket in the USA?</div>
                <p class="card-desc">Quick links to pay or dispute US parking tickets and toll violations from any state.</p>
                <div class="service-list">
                    <a href="https://www.cvb.uscourts.gov/pay-ticket/online-payment-federal-tickets" target="_blank" rel="noopener" class="service-link svc-blue">
                        <div class="svc-icon">&#x1F17F;</div>
                        <span class="svc-text">Pay US Parking Ticket (All States)</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.usa.gov/traffic-tickets" target="_blank" rel="noopener" class="service-link svc-teal">
                        <div class="svc-icon">&#x1F1FA;&#x1F1F8;</div>
                        <span class="svc-text">USA.gov — Find Your State Portal</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.e-zpassiag.com" target="_blank" rel="noopener" class="service-link svc-purple">
                        <div class="svc-icon">&#x1F6E3;</div>
                        <span class="svc-text">E-ZPass Toll Violations (18 States)</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.platepass.com" target="_blank" rel="noopener" class="service-link svc-amber">
                        <div class="svc-icon">&#x1F697;</div>
                        <span class="svc-text">PlatePass — Rental Car Toll Bills</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.sunpass.com/en/tollpayment/tollPayment.shtml" target="_blank" rel="noopener" class="service-link svc-green">
                        <div class="svc-icon">&#x2600;</div>
                        <span class="svc-text">SunPass — Florida Toll Roads</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.txtag.org/txTag/en/index.shtml" target="_blank" rel="noopener" class="service-link svc-rose">
                        <div class="svc-icon">&#x2B50;</div>
                        <span class="svc-text">TxTag — Texas Toll Roads</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                </div>
                <p style="text-align:center; font-size:11px; margin-top:10px; color:var(--text-secondary);">Canadian plates are tracked on US toll systems. Unpaid tolls can block cross-border vehicle registration.</p>
            </div>
        </div>

        <div id="tab-hotspots" class="tab">
            <div id="gpsAlertBanner" class="gps-alert">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="gpsAlertText">WARNING!</span>
            </div>

            <div class="gps-guardian-section">
                <div class="gps-guardian-info">
                    <div class="gps-guardian-icon"><i class="fa-solid fa-satellite-dish"></i></div>
                    <div>
                        <div class="gps-guardian-title">GPS Guardian</div>
                        <div class="gps-guardian-desc">Tracks your real-time location and highlights the nearest free street parking spots on the map — so you can find real free parking near you without circling the block.</div>
                    </div>
                </div>
                <button class="btn-gps" onclick="startGPSGuardian()" id="gpsBtn">
                    <i class="fa-solid fa-satellite-dish"></i> Enable GPS Guardian
                </button>
            </div>

            <div class="map-hero-section" id="mapHeroSection">
                <div id="map"></div>

                <button class="map-expand-btn" onclick="toggleMapFullscreen()" id="mapExpandBtn" title="Fullscreen map">
                    <i class="fa-solid fa-expand" id="mapExpandIcon"></i>
                </button>

                <div id="mapLoadStatus" class="map-load-status"></div>

                <div class="map-float-controls">
                    <div class="map-float-layers" style="pointer-events:none;gap:8px;padding:8px 14px;">
                        <span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:#15803d;">
                            <span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#16a34a;flex-shrink:0;"></span>
                            Free Street Parking
                        </span>
                        <span style="color:#d1d5db;font-size:10px;">|</span>
                        <span style="display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:#b45309;">
                            <span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:#b45309;flex-shrink:0;"></span>
                            Time Limit
                        </span>
                        <span style="color:#d1d5db;font-size:10px;">|</span>
                        <span id="spotCountBadge" style="background:#f3f4f6;color:#374151;border-radius:8px;padding:1px 7px;font-size:10px;font-weight:700;">25 spots</span>
                    </div>
                </div>
            </div>

            <div class="card card-purple card-3">
                <div class="card-label label-purple"><i class="fa-solid fa-bullhorn"></i> Report an Issue</div>
                <p class="card-desc" style="margin-bottom: 4px;">Tap a problem type — AI drafts your 311 email instantly. Send it directly, then pin your report on the community map with your name.</p>
                <div class="report-count"><i class="fa-solid fa-map-pin"></i> {{ reports|length }} community reports on the map</div>
                <div class="report-grid">
                    <button class="report-btn" onclick="openReportPanel('Broken Meter')">
                        <i class="fa-solid fa-plug-circle-xmark"></i>
                        Broken Meter
                    </button>
                    <button class="report-btn" onclick="openReportPanel('Hidden Sign')">
                        <i class="fa-solid fa-eye-slash"></i>
                        Hidden Sign
                    </button>
                    <button class="report-btn" onclick="openReportPanel('Pothole')">
                        <i class="fa-solid fa-road"></i>
                        Pothole
                    </button>
                    <button class="report-btn" onclick="openReportPanel('Bike Lane Blocked')">
                        <i class="fa-solid fa-bicycle"></i>
                        Bike Lane Block
                    </button>
                </div>

                <div id="reportEmailPanel" class="report-email-panel">
                    <div class="report-email-panel-title">
                        <i class="fa-solid fa-robot" style="color:var(--purple);"></i>
                        <span id="reportPanelTitle">AI Email Draft</span>
                    </div>
                    <input type="text" id="reporterName" class="report-name-input" placeholder="Your name (shown on map pin)">

                    <input type="file" id="reportPhotoInput" accept="image/*" capture="environment" style="display:none" onchange="onReportPhotoSelected(this)">
                    <div class="report-photo-row">
                        <button class="report-photo-btn" id="reportPhotoBtnLabel" type="button" onclick="document.getElementById('reportPhotoInput').click()">
                            <i class="fa-solid fa-camera"></i> Add Photo
                        </button>
                        <span class="report-photo-status" id="reportPhotoStatus"></span>
                    </div>
                    <div class="report-photo-preview" id="reportPhotoPreview">
                        <img id="reportPhotoThumb" src="" alt="Issue photo">
                        <button class="report-photo-remove" onclick="clearReportPhoto()" title="Remove photo">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>

                    <div class="report-ai-label"><i class="fa-solid fa-wand-magic-sparkles"></i> AI-drafted — edit freely before sending</div>
                    <textarea id="reportEmailBody" class="report-email-textarea"></textarea>
                    <div class="report-email-actions" id="reportEmailButtons"></div>
                    <button class="report-pin-btn" onclick="pinAndSubmitReport()">
                        <i class="fa-solid fa-map-pin"></i> Pin on Community Map
                    </button>
                </div>

                <form id="reportForm" action="/report_311" method="POST" style="display:none;">
                    <input type="hidden" name="issue_type" id="issueTypeInput">
                    <input type="hidden" name="lat" id="latInput">
                    <input type="hidden" name="lng" id="lngInput">
                    <input type="hidden" name="reporter_name" id="reporterNameInput">
                    <input type="hidden" name="reporter_color" id="reporterColorInput">
                    <input type="hidden" name="photo_data" id="photoDataInput">
                </form>
            </div>
        </div>

        <div id="tab-legal" class="tab">

            <div class="card card-1" id="legalScanCard">
                <div class="card-label label-rose"><i class="fa-solid fa-camera"></i> Scan Ticket — AI Verdict</div>
                <p class="card-desc">Photograph any Toronto traffic or parking ticket. AI reads it in seconds and tells you exactly what to do: pay up, fight it yourself, or get legal help.</p>
                <button class="scan-btn" onclick="document.getElementById('legalTicketUpload').click()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                    Photograph My Ticket
                </button>
                <input type="file" id="legalTicketUpload" accept="image/*" capture="environment" style="display:none" onchange="performLegalScan(event)">
                <div id="legalScanStatus" class="scan-status"></div>
                <div id="legalVerdict" class="legal-verdict">
                    <div class="legal-verdict-badge" id="legalVerdictBadge"></div>
                    <div class="verdict-headline" id="legalVerdictHeadline"></div>
                    <div class="verdict-fine-pill" id="legalVerdictFine" style="display:none;"></div>
                    <div class="verdict-detail" id="legalVerdictDetail"></div>
                    <button class="verdict-cta" id="legalVerdictCTA" style="display:none;" onclick="scrollToFirms()">
                        <i class="fa-solid fa-building-columns"></i> See Matched Law Firms Below
                    </button>
                </div>
            </div>

            <div class="card card-2">
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
                <div class="firm-price">Free consultation &middot; From $350&ndash;$900</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">DUI</span>
                    <span class="specialty-pill">Careless Driving</span>
                    <span class="specialty-pill">Criminal</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@xcopper.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.xcopper.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card card-3 firm-card" id="firm-xcops">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">X-COPS Traffic Ticket Fighters</div>
                <div class="firm-price">Free consultation &middot; From $200&ndash;$600</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Red Light Camera</span>
                    <span class="specialty-pill">Parking Tickets</span>
                    <span class="specialty-pill">Careless Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@x-cops.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.x-cops.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card card-4 firm-card" id="firm-pointts">
                <div class="firm-type-badge firm-type-mixed">Lawyer &amp; Paralegal</div>
                <div class="firm-name">POINTTS Advisory Services</div>
                <div class="firm-price">Free consultation &middot; From $250&ndash;$700</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">School Zone</span>
                    <span class="specialty-pill">Careless Driving</span>
                    <span class="specialty-pill">Insurance Impact</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:toronto@pointts.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.pointts.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card card-5 firm-card" id="firm-ottlegal">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">OTT Legal — Ontario Traffic Tickets</div>
                <div class="firm-price">Free consultation &middot; From $200&ndash;$550</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Red Light Camera</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Parking</span>
                    <span class="specialty-pill">HOV Lane</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@ontariotraffictickets.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.ontariotraffictickets.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card card-6 firm-card" id="firm-xpolice">
                <div class="firm-type-badge firm-type-lawyer">Lawyer</div>
                <div class="firm-name">X-Police / Fight Your Ticket</div>
                <div class="firm-price">Free consultation &middot; From $300&ndash;$800</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">DUI / Impaired</span>
                    <span class="specialty-pill">Criminal HTA</span>
                    <span class="specialty-pill">Careless Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:help@xpolice.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.xpolice.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card firm-card" id="firm-streetlegal">
                <div class="firm-type-badge firm-type-paralegal">Paralegal</div>
                <div class="firm-name">Street Legal Paralegal Services</div>
                <div class="firm-price">Free consultation &middot; From $150&ndash;$500</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Bike Lane</span>
                    <span class="specialty-pill">Parking Tickets</span>
                    <span class="specialty-pill">Cell Phone</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@street-legal.ca?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.street-legal.ca" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card firm-card" id="firm-trafficexperts">
                <div class="firm-type-badge firm-type-mixed">Lawyer &amp; Paralegal</div>
                <div class="firm-name">Traffic Ticket Experts</div>
                <div class="firm-price">Free consultation &middot; From $200&ndash;$650</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">All HTA Charges</span>
                    <span class="specialty-pill">Speeding</span>
                    <span class="specialty-pill">Stunt Driving</span>
                    <span class="specialty-pill">Red Light</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@trafficticket.legal?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.trafficticket.legal" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

            <div class="card firm-card" id="firm-hwylaw">
                <div class="firm-type-badge firm-type-lawyer">Lawyer</div>
                <div class="firm-name">HWY-LAW Criminal Defence</div>
                <div class="firm-price">Free consultation &middot; From $400&ndash;$1,200</div>
                <div class="specialty-pills">
                    <span class="specialty-pill">DUI / Impaired</span>
                    <span class="specialty-pill">Criminal HTA</span>
                    <span class="specialty-pill">Dangerous Driving</span>
                    <span class="specialty-pill">Stunt Driving</span>
                </div>
                <div class="firm-actions">
                    <a class="firm-btn firm-btn-email" href="mailto:info@hwy-law.com?subject=Traffic%20Ticket%20Defence%20Inquiry%20%E2%80%93%20Drivee&body=Hi%2C%20I%27m%20reaching%20out%20via%20Drivee%20about%20my%20traffic%20ticket.%20Please%20apply%20my%20Drivee%20code%3A%20DRIVEE%20(5%E2%80%9310%25%20off%20your%20fee)."><i class="fa-solid fa-envelope"></i> Email Firm</a>
                    <a class="firm-btn firm-btn-web" href="https://www.hwy-law.com" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> Visit Website</a>
                </div>
                <div class="firm-promo"><i class="fa-solid fa-tag"></i> Email via Drivee with code <strong>DRIVEE</strong> &mdash; get 5&ndash;10% off your fee</div>
            </div>

        </div>
    </div>

    <nav class="nav">
        <div class="nav-inner">
            <div class="nav-pill">
                <button class="nav-btn active" onclick="switchTab('guide', this)">
                    <i class="fa-solid fa-circle-question"></i>
                    <span class="nav-label">Guide</span>
                </button>
                <button class="nav-btn" onclick="switchTab('dashboard', this)">
                    <i class="fa-solid fa-house"></i>
                    <span class="nav-label">Dashboard</span>
                </button>
                <button class="nav-btn" onclick="switchTab('services', this)">
                    <i class="fa-solid fa-credit-card"></i>
                    <span class="nav-label">Services</span>
                </button>
                <button class="nav-btn" onclick="switchTab('hotspots', this)">
                    <i class="fa-solid fa-map-location-dot"></i>
                    <span class="nav-label">Map</span>
                </button>
                <button class="nav-btn" onclick="switchTab('legal', this)">
                    <i class="fa-solid fa-gavel"></i>
                    <span class="nav-label">Legal</span>
                </button>
            </div>
            <button class="nav-fab" onclick="openSupportSheet()" title="Support Drivee">
                <i class="fa-solid fa-handshake-angle"></i>
            </button>
        </div>
    </nav>

    <!-- Support Sheet -->
    <div class="support-overlay" id="supportOverlay" onclick="handleSupportOverlayClick(event)">
        <div class="support-sheet">
            <div class="support-drag"></div>
            <div class="support-heart-anim">&#x1F917;</div>
            <div class="support-title">Support Drivee</div>
            <div class="support-desc">Drivee is a community-driven project built to help Toronto drivers navigate fines, parking, and traffic law. Your support keeps us running and growing.</div>
            <div class="support-bullet">
                <span class="support-bullet-icon">&#x1F697;</span>
                <div><strong>Smarter parking tools</strong> &mdash; better maps, real-time alerts, and AI-powered guidance for every driver.</div>
            </div>
            <div class="support-bullet">
                <span class="support-bullet-icon">&#x2696;</span>
                <div><strong>Legal resource expansion</strong> &mdash; partnerships with paralegals to offer free dispute consultations for drivers who can&rsquo;t afford one.</div>
            </div>
            <div class="support-bullet">
                <span class="support-bullet-icon">&#x1F30D;</span>
                <div><strong>Expand beyond Toronto</strong> &mdash; bring Drivee to Ottawa, Vancouver, Calgary, and across Canada.</div>
            </div>
            <a href="https://www.gofundme.com" target="_blank" rel="noopener" class="support-gofundme-btn" onclick="closeSupportSheet()">
                <i class="fa-solid fa-heart"></i> Donate on GoFundMe
            </a>
            <span class="support-close-link" onclick="closeSupportSheet()">Maybe later</span>
        </div>
    </div>

    <!-- AI Chat FAB -->
    <button class="chat-fab" onclick="toggleChat()" title="Ask Drivee AI">
        <i class="fa-solid fa-robot"></i>
        <div class="chat-fab-dot"></div>
    </button>

    <!-- AI Chat Overlay -->
    <div class="chat-overlay" id="chatOverlay" onclick="toggleChat()"></div>

    <!-- AI Chat Panel -->
    <div class="chat-panel" id="chatPanel">
        <div class="chat-header">
            <div class="chat-header-icon"><i class="fa-solid fa-robot"></i></div>
            <div class="chat-header-text">
                <div class="chat-header-title">Drivee AI</div>
                <div class="chat-header-sub">Powered by ChatGPT &bull; Toronto traffic specialist</div>
            </div>
            <button class="chat-close" onclick="toggleChat()"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="chat-msg bot">
                <div class="chat-msg-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="chat-msg-bubble">Hi! I am Drivee AI &#x2728; Ask me anything about Toronto parking tickets, fines, disputes, or traffic law &mdash; or use the chips above to jump straight to what you need. How can I help today?</div>
            </div>
            <div class="chat-msg bot" id="chatTypingRow" style="display:none;">
                <div class="chat-msg-avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="chat-typing show" id="chatTyping">
                    <span></span><span></span><span></span>
                </div>
            </div>
        </div>
        <div class="chat-suggestions" id="chatSuggestions">
            <button class="chat-suggestion" onclick="sendSuggestion(this)">How do I dispute a parking ticket?</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">What happens if I miss the deadline?</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">Do I need a lawyer for stunt driving?</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">I want to report a problem with the app</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">How much are late fees in Toronto?</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">Can I contest a red light camera fine?</button>
        </div>
        <div id="chatPhotoPreviewWrap" class="chat-photo-preview-wrap" style="display:none"></div>
        <div class="chat-input-row">
            <button class="chat-photo-btn" onclick="document.getElementById('chatPhotoInput').click()" title="Send a photo">
                <i class="fa-solid fa-camera"></i>
            </button>
            <input type="file" id="chatPhotoInput" accept="image/*" capture="environment" style="display:none" onchange="onChatPhotoSelected(event)">
            <textarea class="chat-input" id="chatInput" placeholder="Ask about your ticket or send a photo..." rows="1"
                onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat();}"
                oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,100)+'px'"></textarea>
            <button class="chat-send" id="chatSendBtn" onclick="sendChat()">
                <i class="fa-solid fa-paper-plane"></i>
            </button>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <script>
        var mapInstance = null;
        var freeDropoffGroup = null;

        function initMap() {
            if (mapInstance) {
                mapInstance.invalidateSize();
                return;
            }
            mapInstance = L.map('map', { zoomControl: true }).setView([43.6532, -79.3832], 15);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
                maxZoom: 19,
                subdomains: 'abcd'
            }).addTo(mapInstance);

            loadFreeDropoffLayer();

            var liveReports = {{ reports_json|safe }};
            liveReports.forEach(function(report) {
                var name = report.name || 'Community';
                var color = report.color || '#0A84FF';
                var initials = name.split(' ').filter(function(w){return w.length>0;}).map(function(w){return w[0].toUpperCase();}).join('').slice(0,2) || '?';
                var avIcon = L.divIcon({
                    className: '',
                    html: '<div class="report-avatar" style="background:' + color + ';">' + initials + '</div>',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                });
                var photoHtml = report.photo ? '<img src="' + report.photo + '" class="report-popup-photo">' : '';
                var marker = L.marker([report.lat, report.lng], {icon: avIcon}).addTo(mapInstance);
                marker.bindPopup('<b>' + name + '</b><br>' + report.type + '<br><span style="color:#8E8E93;font-size:12px;">' + report.status + '</span>' + photoHtml);
            });
        }

        var userMarker = null;
        var gpsWatchId = null;

        // Expanded proximity data matching the real map layers
        var hydrantPositions = [
            L.latLng(43.6485,-79.3950), L.latLng(43.6490,-79.3870), L.latLng(43.6470,-79.3910),
            L.latLng(43.6510,-79.3830), L.latLng(43.6530,-79.3790), L.latLng(43.6550,-79.3750),
            L.latLng(43.6460,-79.4010), L.latLng(43.6440,-79.3960), L.latLng(43.6420,-79.3920),
            L.latLng(43.6500,-79.4050), L.latLng(43.6520,-79.4000), L.latLng(43.6570,-79.3870),
            L.latLng(43.6590,-79.3840), L.latLng(43.6610,-79.3820), L.latLng(43.6630,-79.3800),
            L.latLng(43.6390,-79.3890), L.latLng(43.6370,-79.3850), L.latLng(43.6350,-79.3820),
            L.latLng(43.6480,-79.3810), L.latLng(43.6500,-79.3770), L.latLng(43.6520,-79.3740)
        ];
        var hydrantLatLng = hydrantPositions[0]; // backward compat

        var bikeLaneSegments = [
            [L.latLng(43.6655,-79.4165), L.latLng(43.6655,-79.3960)],
            [L.latLng(43.6655,-79.3960), L.latLng(43.6655,-79.3720)],
            [L.latLng(43.6655,-79.3720), L.latLng(43.6655,-79.3330)],
            [L.latLng(43.6615,-79.4050), L.latLng(43.6615,-79.3620)],
            [L.latLng(43.6510,-79.4080), L.latLng(43.6510,-79.3600)],
            [L.latLng(43.6485,-79.4050), L.latLng(43.6485,-79.3600)],
            [L.latLng(43.6360,-79.4080), L.latLng(43.6360,-79.3700)],
            [L.latLng(43.6345,-79.4060), L.latLng(43.6345,-79.3700)],
            [L.latLng(43.6540,-79.3885), L.latLng(43.6420,-79.3885)],
            [L.latLng(43.6600,-79.3890), L.latLng(43.6480,-79.3890)]
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
                btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Enable GPS Guardian';
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
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Locating\u2026';
            btn.classList.add('active-gps');

            gpsWatchId = navigator.geolocation.watchPosition(
                function(position) {
                    btn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Guardian Active \u2014 Tap to Stop';

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
                    btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Enable GPS Guardian';
                    btn.classList.remove('active-gps');
                    document.getElementById('gpsAlertBanner').classList.remove('show');
                    if (userMarker) { mapInstance.removeLayer(userMarker); userMarker = null; }
                    gpsWatchId = null;
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
        }

        function toggleMapFullscreen() {
            var section = document.getElementById('mapHeroSection');
            var icon = document.getElementById('mapExpandIcon');
            var isFs = section.classList.toggle('map-is-fullscreen');
            icon.className = isFs ? 'fa-solid fa-compress' : 'fa-solid fa-expand';
            document.body.style.overflow = isFs ? 'hidden' : '';
            if (mapInstance) { setTimeout(function() { mapInstance.invalidateSize(); }, 80); }
        }

        function showParkingDetail(key, el) {
            var db = {
                'queen_west':    { name: 'Queen St W (Spadina–Bathurst)', rate: '$3.00 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: '3:30–6:30 PM Mon–Fri — WILL TOW', tip: 'Side streets off Queen W often have free 1-hr spots in evenings.' },
                'bloor_yorkville':{ name: 'Bloor St W — Yorkville', rate: '$4.00 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '2 hours', free: 'Daily after 9:00 PM', rush: '3:30–6:30 PM Mon–Fri — WILL TOW', tip: 'Green P on Bellair St is slightly cheaper than curbside.' },
                'kensington':    { name: 'Kensington Market', rate: '$2.25 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: 'None', tip: 'Augusta Ave has free spots before 9am on weekdays.' },
                'front_st':      { name: 'Front St (Scotiabank Arena)', rate: '$5.00 / hr (event: $20 flat)', hours: 'Mon–Sun 8am–Midnight', max: '4 hours', free: 'After Midnight', rush: '3:30–6:30 PM Mon–Fri — WILL TOW', tip: 'Green P garages on Bremner Blvd are cheaper on event nights.' },
                'king_west':     { name: 'King St W', rate: '$3.50 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '2 hours', free: 'Daily after 9:00 PM', rush: '3:30–6:30 PM Mon–Fri — WILL TOW', tip: 'King St is a transit priority corridor — metered spots are limited.' },
                'financial':     { name: 'Bay St / King St E', rate: '$4.50 / hr', hours: 'Mon–Fri 7am–6pm only', max: '2 hours', free: 'Weekends + after 6 PM weekdays', rush: '7–9 AM & 3:30–6:30 PM Mon–Fri — WILL TOW', tip: 'Most spots disappear to rush-hour restrictions on weekday mornings.' },
                'chinatown':     { name: 'Spadina Ave / Dundas St W', rate: '$2.50 / hr', hours: 'Mon\u2013Sat 8am\u20139pm, Sun 1pm\u20139pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: '3:30\u20136:30 PM Mon\u2013Fri', tip: 'Side streets near Kensington have free residential spots before 9am.' },
                'annex':         { name: 'Bloor St W / Bathurst Area', rate: '$2.00 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: 'None', tip: 'Residential side streets require area permits; check signs carefully.' },
                'distillery':    { name: 'Distillery District', rate: '$4.00 / hr', hours: 'Mon–Sun 8am–Midnight', max: '4 hours', free: 'After Midnight', rush: 'None', tip: 'Cherry St Green P lot is ~30% cheaper than surface parking inside.' },
                'little_italy':  { name: 'College St W (Little Italy)', rate: '$2.25 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: 'None', tip: 'Clinton St south of College has free on-street parking most evenings.' },
                'greektown':     { name: 'Danforth Ave (Greektown)', rate: '$2.50 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: 'None', tip: 'Side streets like Gough Ave have free 3-hr parking with no permit needed.' },
                'leslieville':   { name: 'Queen St E (Leslieville)', rate: '$2.00 / hr', hours: 'Mon–Sat 8am–9pm, Sun 1pm–9pm', max: '3 hours', free: 'Daily after 9:00 PM', rush: 'None', tip: 'Broadview Ave has free 2-hour parking on the east side in the evenings.' }
            };
            var d = db[key];
            if (!d) return;
            document.querySelectorAll('.parking-card').forEach(function(c) { c.classList.remove('selected'); });
            el.classList.add('selected');
            document.getElementById('pdName').textContent = d.name;
            document.getElementById('pdRate').textContent = d.rate;
            document.getElementById('pdHours').textContent = d.hours;
            document.getElementById('pdMax').textContent = d.max;
            document.getElementById('pdFree').textContent = d.free;
            document.getElementById('pdRush').textContent = d.rush;
            document.getElementById('pdTip').textContent = d.tip;
            var panel = document.getElementById('parkingDetailPanel');
            panel.classList.add('show');
            panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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
                    new Notification('Drivee', {
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
                var scanSucceeded = !!(scannedPlate || scannedDate);
                var highSeverity = /stunt|plate.?den|denial|impaired|dui|careless|dangerous|red.?light|bike.?lane|\$[2-9]\d{2}|\$[1-9]\d{3}/i.test(text);
                if (scanSucceeded && highSeverity) {
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

        var currentReportType = '';
        var currentReportLat = null;
        var currentReportLng = null;
        var reportAvatarColors = ['#0A84FF','#30D158','#BF5AF2','#FF453A','#FFD60A','#FF9F0A','#5E5CE6'];

        var reportPhotoBase64 = '';
        var reportPhotoDescription = '';

        function openReportPanel(issueType) {
            currentReportType = issueType;
            document.getElementById('reportPanelTitle').textContent = issueType + ' — AI Email Draft';
            var savedName = localStorage.getItem('drivee_name') || '';
            document.getElementById('reporterName').value = savedName;
            clearReportPhoto();
            buildEmailButtons(issueType);
            var panel = document.getElementById('reportEmailPanel');
            panel.classList.add('show');
            if ('geolocation' in navigator) {
                navigator.geolocation.getCurrentPosition(
                    function(pos) {
                        currentReportLat = pos.coords.latitude;
                        currentReportLng = pos.coords.longitude;
                        generateReportEmail(issueType, pos.coords.latitude.toFixed(5) + ', ' + pos.coords.longitude.toFixed(5));
                    },
                    function() { generateReportEmail(issueType, 'Toronto (location unavailable)'); },
                    { enableHighAccuracy: true, timeout: 8000 }
                );
            } else {
                generateReportEmail(issueType, 'Toronto');
            }
            setTimeout(function() { panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, 100);
        }

        function generateReportEmail(issueType, location) {
            var today = new Date().toLocaleDateString('en-CA');
            var name = (document.getElementById('reporterName').value || 'A Drivee User').trim();
            var nl = String.fromCharCode(10);
            function body311(subject, greeting, detail, action) {
                return [subject, '', greeting, '', detail, '', action, '', 'Reported via Drivee Community App.', '', 'Thank you,', name].join(nl);
            }
            var bodies = {
                'Broken Meter': body311(
                    'Subject: Broken Parking Meter — ' + location,
                    'Dear Toronto Parking Authority,',
                    'I am writing to report a broken parking meter at ' + location + ', observed on ' + today + '. The meter appears to be malfunctioning (screen blank, card reader not responding, or unable to issue a receipt). This creates an unfair situation for drivers who may receive tickets despite attempting to pay.',
                    'Please arrange for inspection and repair at your earliest convenience. If a ticket was issued due to the broken meter, I request it be reviewed accordingly.'
                ),
                'Hidden Sign': body311(
                    'Subject: Hidden or Obscured Parking Sign — ' + location,
                    'Dear Toronto 311,',
                    'I am writing to report a parking sign that is hidden, obscured, or missing at ' + location + ', observed on ' + today + '. The sign may be blocked by overgrown vegetation, vandalism, or physical damage, making it impossible for drivers to see parking restrictions.',
                    'Please arrange for inspection and correction at your earliest convenience.'
                ),
                'Pothole': body311(
                    'Subject: Pothole / Road Damage — ' + location,
                    'Dear Toronto 311,',
                    'I am writing to report a pothole or significant road damage at ' + location + ', observed on ' + today + '. The damage poses a safety risk to vehicles, cyclists, and pedestrians.',
                    'Please arrange for inspection and repair at your earliest convenience.'
                ),
                'Bike Lane Blocked': body311(
                    'Subject: Bike Lane Obstruction — ' + location,
                    'Dear Toronto 311,',
                    'I am writing to report a blocked or obstructed bike lane at ' + location + ', observed on ' + today + '. A vehicle or other obstruction is forcing cyclists into active traffic and creating a dangerous situation.',
                    'Please arrange for enforcement or removal at your earliest convenience.'
                )
            };
            var emailText = bodies[issueType] || body311(
                'Subject: Community Issue — ' + location,
                'Dear Toronto 311,',
                'I am writing to report a ' + issueType + ' at ' + location + ', observed on ' + today + '.',
                'Please arrange for inspection at your earliest convenience.'
            );
            if (reportPhotoDescription) {
                var photoNote = nl + 'Photo evidence: ' + reportPhotoDescription;
                var lines = emailText.split(nl);
                var insertAt = lines.length - 4;
                lines.splice(insertAt < 0 ? 0 : insertAt, 0, photoNote);
                emailText = lines.join(nl);
            }
            document.getElementById('reportEmailBody').value = emailText;
        }

        document.addEventListener('input', function(e) {
            if (e.target && e.target.id === 'reporterName' && currentReportType) {
                generateReportEmail(currentReportType, currentReportLat ? currentReportLat.toFixed(5) + ', ' + currentReportLng.toFixed(5) : 'Toronto');
            }
        });

        function buildEmailButtons(issueType) {
            var c = document.getElementById('reportEmailButtons');
            c.innerHTML = '';
            function makeBtn(label, email, cls, icon) {
                var b = document.createElement('button');
                b.className = 'report-email-btn ' + cls;
                b.innerHTML = '<i class="fa-solid ' + icon + '"></i> ' + label;
                b.onclick = function() { sendReportEmail(email); };
                c.appendChild(b);
            }
            makeBtn('Email 311', '311@toronto.ca', 'report-btn-311', 'fa-envelope');
            if (issueType === 'Broken Meter') {
                makeBtn('Email Green P', 'customerservice@greenp.com', 'report-btn-greenp', 'fa-square-parking');
                makeBtn('Police Enforcement', 'tpsparkingcomplaints@torontopolice.on.ca', 'report-btn-police', 'fa-shield-halved');
            } else if (issueType === 'Bike Lane Blocked') {
                makeBtn('Email Cycling', 'cycling@toronto.ca', 'report-btn-cycling', 'fa-bicycle');
            }
        }

        function clearReportPhoto() {
            reportPhotoBase64 = '';
            reportPhotoDescription = '';
            document.getElementById('reportPhotoInput').value = '';
            document.getElementById('reportPhotoThumb').src = '';
            document.getElementById('reportPhotoPreview').style.display = 'none';
            var btn = document.getElementById('reportPhotoBtnLabel');
            btn.classList.remove('has-photo');
            btn.innerHTML = '<i class="fa-solid fa-camera"></i> Add Photo';
            var st = document.getElementById('reportPhotoStatus');
            st.textContent = '';
            st.className = 'report-photo-status';
        }

        function onReportPhotoSelected(input) {
            var file = input.files && input.files[0];
            if (!file) return;
            var reader = new FileReader();
            reader.onload = function(e) {
                var img = new Image();
                img.onload = function() {
                    var MAX = 640;
                    var w = img.width, h = img.height;
                    if (w > MAX || h > MAX) {
                        if (w > h) { h = Math.round(h * MAX / w); w = MAX; }
                        else { w = Math.round(w * MAX / h); h = MAX; }
                    }
                    var canvas = document.createElement('canvas');
                    canvas.width = w; canvas.height = h;
                    canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                    var dataUrl = canvas.toDataURL('image/jpeg', 0.75);
                    reportPhotoBase64 = dataUrl.split(',')[1];
                    document.getElementById('reportPhotoThumb').src = dataUrl;
                    document.getElementById('reportPhotoPreview').style.display = 'block';
                    var btn = document.getElementById('reportPhotoBtnLabel');
                    btn.classList.add('has-photo');
                    btn.innerHTML = '<i class="fa-solid fa-camera-rotate"></i> Change Photo';
                    analyzeReportPhoto(reportPhotoBase64);
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }

        function analyzeReportPhoto(base64) {
            if (!base64 || !currentReportType) return;
            var st = document.getElementById('reportPhotoStatus');
            st.textContent = 'AI analyzing photo\u2026';
            st.className = 'report-photo-status analyzing';
            fetch('/api/analyze-photo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo: base64, issue_type: currentReportType })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.description) {
                    reportPhotoDescription = data.description;
                    st.textContent = 'Photo analyzed \u2714';
                    st.className = 'report-photo-status done';
                    var loc = currentReportLat ? currentReportLat.toFixed(5) + ', ' + currentReportLng.toFixed(5) : 'Toronto';
                    generateReportEmail(currentReportType, loc);
                } else {
                    st.textContent = '';
                    st.className = 'report-photo-status';
                }
            })
            .catch(function() {
                st.textContent = 'Could not analyze photo';
                st.className = 'report-photo-status';
            });
        }

        function sendReportEmail(toEmail) {
            var nl = String.fromCharCode(10);
            var body = document.getElementById('reportEmailBody').value;
            var lines = body.split(nl);
            var subject = lines[0].replace(/^Subject:\s*/i, '').trim();
            var emailBody = lines.slice(2).join(nl).trim();
            window.open('mailto:' + toEmail + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(emailBody), '_blank');
            showToast('Email app opened — review and send!');
        }

        function pinAndSubmitReport() {
            var name = (document.getElementById('reporterName').value || 'Anonymous').trim();
            var color = reportAvatarColors[(name.charCodeAt(0) || 65) % reportAvatarColors.length];
            var doSubmit = function(lat, lng) {
                initMap();
                var photoDataUrl = reportPhotoBase64 ? 'data:image/jpeg;base64,' + reportPhotoBase64 : '';
                addAvatarMarkerToMap(lat, lng, name, color, currentReportType, photoDataUrl);
                document.getElementById('issueTypeInput').value = currentReportType;
                document.getElementById('latInput').value = lat;
                document.getElementById('lngInput').value = lng;
                document.getElementById('reporterNameInput').value = name;
                document.getElementById('reporterColorInput').value = color;
                document.getElementById('photoDataInput').value = reportPhotoBase64 ? 'data:image/jpeg;base64,' + reportPhotoBase64 : '';
                document.getElementById('reportForm').submit();
            };
            if (currentReportLat && currentReportLng) {
                doSubmit(currentReportLat, currentReportLng);
            } else {
                navigator.geolocation.getCurrentPosition(
                    function(p) { doSubmit(p.coords.latitude, p.coords.longitude); },
                    function() { showToast('Could not get your location. Please enable GPS.'); },
                    { enableHighAccuracy: true, timeout: 10000 }
                );
            }
        }

        function addAvatarMarkerToMap(lat, lng, name, color, issueType, photoDataUrl) {
            var initials = name.split(' ').filter(function(w){return w.length>0;}).map(function(w){return w[0].toUpperCase();}).join('').slice(0,2) || '?';
            var avIcon = L.divIcon({
                className: '',
                html: '<div class="report-avatar" style="background:' + color + ';">' + initials + '</div>',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            var photoHtml = photoDataUrl ? '<img src="' + photoDataUrl + '" class="report-popup-photo">' : '';
            var marker = L.marker([lat, lng], {icon: avIcon}).addTo(mapInstance);
            marker.bindPopup('<b>' + name + '</b><br>' + issueType + '<br><span style="color:#8E8E93;font-size:12px;">Just now</span>' + photoHtml);
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

        /* ── Free 20-min drop-off spots ─────────────────────────── */

        function loadFreeDropoffLayer() {
            freeDropoffGroup = L.layerGroup();
            var spots = [
                {lat:43.6581,lng:-79.3644,addr:'321 Shuter St',area:'Cabbagetown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'},
                {lat:43.6619,lng:-79.3688,addr:'Spruce St at Oak St',area:'Cabbagetown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6609,lng:-79.3664,addr:'Sackville St at Winchester St',area:'Cabbagetown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6634,lng:-79.3668,addr:'Amelia St at Ontario St',area:'Cabbagetown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6532,lng:-79.3618,addr:'First Ave at King St E',area:'Corktown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'},
                {lat:43.6514,lng:-79.3590,addr:'Bright St at Queen St E',area:'Corktown',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6606,lng:-79.3336,addr:'Booth Ave at Queen St E',area:'Leslieville',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6603,lng:-79.3304,addr:'Munro St at Queen St E',area:'Leslieville',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6614,lng:-79.3272,addr:'Victor Ave at Queen St E',area:'Leslieville',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6626,lng:-79.3322,addr:'Larchmount Ave, Leslieville',area:'Leslieville',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'},
                {lat:43.6596,lng:-79.3354,addr:'Coady Ave, South Riverdale',area:'South Riverdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6662,lng:-79.3530,addr:'Browning Ave, Riverdale',area:'Riverdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'},
                {lat:43.6476,lng:-79.4316,addr:'Fern Ave, Roncesvalles',area:'Roncesvalles',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6447,lng:-79.4355,addr:'Marion St at Howard Park',area:'Roncesvalles',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6441,lng:-79.4332,addr:'Garden Ave, Parkdale',area:'Parkdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6461,lng:-79.4334,addr:'Marmaduke St, Parkdale',area:'Parkdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6449,lng:-79.4288,addr:'Brock Ave at Queen W',area:'Parkdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'1 hr',rules:'1 hour maximum parking rule applies'},
                {lat:43.6428,lng:-79.4280,addr:'Close Ave, Parkdale',area:'Parkdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6489,lng:-79.4183,addr:'Manning Ave at Dundas W',area:'Trinity-Bellwoods',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'},
                {lat:43.6519,lng:-79.4162,addr:'Clinton St at College St',area:'Little Italy',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'2 hrs',rules:'2 hour maximum parking rule applies'},
                {lat:43.6503,lng:-79.4146,addr:'Crawford St at Bloor W',area:'Little Italy',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6512,lng:-79.4148,addr:'Beatrice St, Trinity-Bellwoods',area:'Trinity-Bellwoods',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6768,lng:-79.3534,addr:'Forman Ave at Danforth Ave',area:'Danforth',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6681,lng:-79.3483,addr:'Standish Ave, Riverdale',area:'Riverdale',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'No limit',rules:'Residential street, free of charge'},
                {lat:43.6773,lng:-79.2988,addr:'Kenilworth Ave at Kingston Rd',area:'Upper Beach',schedule:'Mon \u2013 Sun',hours:'All day',maxStay:'3 hrs',rules:'3 hour maximum parking rule applies'}
            ];
            spots.forEach(function(s) {
                var isLimited = (s.maxStay !== 'No limit');
                var bg = isLimited ? '#16a34a' : '#15803d';
                var timeLabel = isLimited ? s.maxStay.replace(' hrs','H').replace(' hr','H') : '\u221e';
                var icon = L.divIcon({
                    className: '',
                    html: '<div style="position:relative;width:38px;height:50px;">'
                        + '<div style="width:36px;height:36px;border-radius:50%;background:' + bg + ';border:3px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.28);display:flex;align-items:center;justify-content:center;">'
                        + '<span style="color:#fff;font-size:18px;font-weight:900;font-family:-apple-system,sans-serif;line-height:1;">P</span>'
                        + '</div>'
                        + '<div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);background:' + bg + ';color:#fff;font-size:8px;font-weight:800;font-family:-apple-system,sans-serif;border-radius:3px;padding:1px 5px;white-space:nowrap;border:1.5px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,0.2);">'
                        + timeLabel + ' FREE'
                        + '</div>'
                        + '</div>',
                    iconSize: [38, 50],
                    iconAnchor: [19, 50]
                });
                var popup = '<div style="font-family:-apple-system,sans-serif;min-width:220px;padding:4px 2px;">'
                    + '<div style="display:inline-flex;align-items:center;gap:5px;background:#dcfce7;border-radius:6px;padding:4px 10px;margin-bottom:10px;">'
                    + '<span style="width:8px;height:8px;border-radius:50%;background:#16a34a;display:inline-block;flex-shrink:0;"></span>'
                    + '<span style="font-size:12px;font-weight:700;color:#15803d;">Free of charge</span>'
                    + '</div>'
                    + '<div style="font-size:14px;font-weight:700;color:#111827;margin-bottom:2px;">' + s.addr + '</div>'
                    + '<div style="font-size:12px;color:#6b7280;margin-bottom:10px;">' + s.area + ', Toronto</div>'
                    + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:8px;background:#f9fafb;border-radius:8px;margin-bottom:8px;">'
                    + '<div><div style="font-size:9px;text-transform:uppercase;color:#9ca3af;font-weight:600;letter-spacing:0.5px;margin-bottom:2px;">Schedule</div>'
                    + '<div style="font-size:12px;font-weight:700;color:#111827;">' + s.schedule + '</div>'
                    + '<div style="font-size:11px;color:#6b7280;">' + s.hours + '</div></div>'
                    + '<div><div style="font-size:9px;text-transform:uppercase;color:#9ca3af;font-weight:600;letter-spacing:0.5px;margin-bottom:2px;">Max Stay</div>'
                    + '<div style="font-size:12px;font-weight:700;color:' + (isLimited ? '#b45309' : '#15803d') + ';">' + s.maxStay + '</div></div>'
                    + '</div>'
                    + '<div style="font-size:11px;color:#6b7280;padding:0 2px;margin-bottom:8px;">' + s.rules + '</div>'
                    + '<a href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(s.addr + ', Toronto, ON') + '" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:5px;background:#f0f9ff;border:1px solid #bae6fd;border-radius:6px;padding:7px;font-size:12px;font-weight:600;color:#0369a1;text-decoration:none;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"></polygon></svg>View on Google Maps</a>'
                    + '</div>';
                (function(spot) {
                    var marker = L.marker([spot.lat, spot.lng], { icon: icon });
                    marker.bindPopup(popup, { maxWidth: 260 });
                    marker.on('click', function() {
                        mapInstance.flyTo([spot.lat, spot.lng], 18, { animate: true, duration: 0.6 });
                    });
                    marker.addTo(freeDropoffGroup);
                })(s);
            });
            freeDropoffGroup.addTo(mapInstance);
            var countEl = document.getElementById('spotCountBadge');
            if (countEl) countEl.textContent = spots.length + ' spots';
        }
        function scrollToFirms() {
            var firstFirm = document.querySelector('.firm-card');
            if (firstFirm) firstFirm.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
        if (params.get('saved') === 'reminder') {
            showToast('Reminder added');
            setTimeout(function() { autoTriggerCalSync(); }, 500);
        }
        if (params.get('deleted') === '1') showToast('Reminder deleted');
        if (params.get('reported') === '1') {
            showToast('Hazard reported! Pin added to map.');
            switchTab('hotspots', document.querySelectorAll('.nav-btn')[3]);
        }
        if (params.has('saved') || params.has('deleted') || params.has('reported')) {
            history.replaceState(null, '', '/');
        }

        // ── Drivee AI Chat ──
        var chatOpen = false;
        var chatHistory = [];
        var chatBusy = false;

        function toggleChat() {
            chatOpen = !chatOpen;
            document.getElementById('chatPanel').classList.toggle('open', chatOpen);
            document.getElementById('chatOverlay').classList.toggle('open', chatOpen);
            if (chatOpen) {
                setTimeout(function() {
                    document.getElementById('chatInput').focus();
                }, 380);
            }
        }

        function sendSuggestion(btn) {
            var text = btn.textContent.trim();
            document.getElementById('chatSuggestions').style.display = 'none';
            sendChatMessage(text);
        }

        function sendChat() {
            var input = document.getElementById('chatInput');
            var text = input.value.trim();
            if (chatBusy) return;
            if (chatPendingPhoto) {
                var photo = chatPendingPhoto;
                chatPendingPhoto = null;
                var wrap = document.getElementById('chatPhotoPreviewWrap');
                if (wrap) { wrap.innerHTML = ''; wrap.style.display = 'none'; }
                input.value = '';
                input.style.height = 'auto';
                input.placeholder = 'Ask about your ticket or send a photo...';
                document.getElementById('chatSuggestions').style.display = 'none';
                sendChatWithPhoto(text, photo);
                return;
            }
            if (!text) return;
            input.value = '';
            input.style.height = 'auto';
            document.getElementById('chatSuggestions').style.display = 'none';
            sendChatMessage(text);
        }

        function appendChatMsg(role, text) {
            var msgs = document.getElementById('chatMessages');
            var typingRow = document.getElementById('chatTypingRow');
            var div = document.createElement('div');
            div.className = 'chat-msg ' + role;
            var icon = role === 'bot' ? 'fa-robot' : 'fa-user';
            div.innerHTML = '<div class="chat-msg-avatar"><i class="fa-solid ' + icon + '"></i></div>'
                + '<div class="chat-msg-bubble">' + text.replace(/\\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') + '</div>';
            msgs.insertBefore(div, typingRow);
            msgs.scrollTop = msgs.scrollHeight;
        }

        function sendChatMessage(text) {
            if (chatBusy) return;
            chatBusy = true;
            appendChatMsg('user', text);
            chatHistory.push({ role: 'user', content: text });

            var typingRow = document.getElementById('chatTypingRow');
            typingRow.style.display = 'flex';
            var msgs = document.getElementById('chatMessages');
            msgs.scrollTop = msgs.scrollHeight;

            var sendBtn = document.getElementById('chatSendBtn');
            sendBtn.disabled = true;

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                typingRow.style.display = 'none';
                if (data.reply) {
                    appendChatMsg('bot', data.reply);
                    addChatNavChips(data.reply);
                    chatHistory.push({ role: 'assistant', content: data.reply });
                } else {
                    appendChatMsg('bot', data.error || 'Sorry, something went wrong. Please try again.');
                }
            })
            .catch(function() {
                typingRow.style.display = 'none';
                appendChatMsg('bot', 'Connection error. Please check your internet and try again.');
            })
            .finally(function() {
                chatBusy = false;
                sendBtn.disabled = false;
                msgs.scrollTop = msgs.scrollHeight;
            });
        }
    </script>

    <!-- Calendar Sync Bottom Sheet -->
    <div class="cal-sheet-overlay" id="calSheetOverlay" onclick="closeCalSheet(event)">
        <div class="cal-sheet">
            <div class="cal-sheet-drag"></div>
            <div class="cal-sheet-title">Sync to Calendar</div>
            <div class="cal-sheet-sub" id="calSheetSub">Add this reminder to your calendar</div>
            <div class="cal-sheet-options">
                <button class="cal-sheet-opt cal-opt-phone" id="calSheetPhoneBtn" onclick="calSyncPhone()">
                    <div class="cal-sheet-opt-icon">&#x1F4F1;</div>
                    <div>
                        <div>Phone Calendar</div>
                        <div class="cal-sheet-opt-sub">iOS Calendar, Samsung Calendar &amp; more</div>
                    </div>
                </button>
                <a class="cal-sheet-opt cal-opt-gcal" id="calSheetGcalBtn" href="#" target="_blank" rel="noopener" onclick="closeCalSheetNow()">
                    <div class="cal-sheet-opt-icon">&#x1F4C5;</div>
                    <div>
                        <div>Google Calendar</div>
                        <div class="cal-sheet-opt-sub">Opens in Google Calendar on the web</div>
                    </div>
                </a>
            </div>
            <button class="cal-sheet-cancel" onclick="closeCalSheetNow()">Not Now</button>
        </div>
    </div>
    <script>
        var _calIcsUrl = '';
        var _calGcalUrl = '';
        function openCalSheet(icsUrl, gcalUrl, ticketNum, dueDisplay) {
            _calIcsUrl = icsUrl;
            _calGcalUrl = gcalUrl;
            var sub = document.getElementById('calSheetSub');
            if (ticketNum && dueDisplay) {
                sub.textContent = ticketNum + ' \u2014 Due ' + dueDisplay;
            } else {
                sub.textContent = 'Add this reminder to your calendar';
            }
            document.getElementById('calSheetGcalBtn').href = gcalUrl;
            document.getElementById('calSheetOverlay').classList.add('open');
        }
        function closeCalSheetNow() {
            document.getElementById('calSheetOverlay').classList.remove('open');
        }
        function closeCalSheet(e) {
            if (e.target === document.getElementById('calSheetOverlay')) closeCalSheetNow();
        }
        function calSyncPhone() {
            closeCalSheetNow();
            window.location.href = _calIcsUrl;
        }
        function autoTriggerCalSync() {
            var reminders = document.querySelectorAll('.reminder');
            if (!reminders.length) return;
            var last = reminders[reminders.length - 1];
            var btn = last.querySelector('.cal-sync-btn');
            if (btn) btn.click();
        }

        // ── Splash Screen + Install Guide ────────────────────────────
        (function() {
            var splash = document.getElementById('splashScreen');
            if (!splash) return;

            var splashDone = false;
            function onSplashDone() {
                if (splashDone) return;
                splashDone = true;
                splash.style.display = 'none';
                checkInstallPrompt();
            }

            // Primary: CSS animationend
            splash.addEventListener('animationend', function(e) {
                if (e.animationName === 'splashExit') onSplashDone();
            });

            // Fallback: in case animationend never fires (e.g. reduced-motion, old browser)
            setTimeout(onSplashDone, 3200);
        })();

        function checkInstallPrompt() {
            var isStandalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) || !!navigator.standalone;
            if (isStandalone) return;
            if (localStorage.getItem('drivee_install_dismissed')) return;

            var ua = navigator.userAgent || '';
            var isIOS = (/iPad|iPhone|iPod/.test(ua) && !window.MSStream) ||
                    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
            var isAndroid = /Android/.test(ua);
            if (!isIOS && !isAndroid) return;

            var stepsEl = document.getElementById('installSteps');
            if (!stepsEl) return;

            if (isIOS) {
                stepsEl.innerHTML =
                    '<div class="install-step"><div class="install-step-num">1</div><div class="install-step-text">Open this page in <strong>Safari</strong> (not Chrome or other browsers)</div></div>' +
                    '<div class="install-step"><div class="install-step-num">2</div><div class="install-step-text">Tap the <strong>Share</strong> button &#9633;&#8593; at the bottom of the screen</div></div>' +
                    '<div class="install-step"><div class="install-step-num">3</div><div class="install-step-text">Scroll down and tap <strong>Add to Home Screen</strong></div></div>' +
                    '<div class="install-step"><div class="install-step-num">4</div><div class="install-step-text">Tap <strong>Add</strong> — Drivee will appear on your home screen like a real app!</div></div>';
            } else {
                stepsEl.innerHTML =
                    '<div class="install-step"><div class="install-step-num">1</div><div class="install-step-text">Tap the <strong>three dots</strong> &#8942; menu in Chrome (top right)</div></div>' +
                    '<div class="install-step"><div class="install-step-num">2</div><div class="install-step-text">Tap <strong>Add to Home screen</strong> or <strong>Install App</strong></div></div>' +
                    '<div class="install-step"><div class="install-step-num">3</div><div class="install-step-text">Tap <strong>Install</strong> — Drivee will appear on your home screen!</div></div>';
            }

            var overlay = document.getElementById('installSheetOverlay');
            if (overlay) {
                setTimeout(function() { overlay.classList.add('open'); }, 350);
            }
        }

        function closeInstallSheet() {
            var overlay = document.getElementById('installSheetOverlay');
            if (overlay) overlay.classList.remove('open');
        }

        function dismissInstall() {
            localStorage.setItem('drivee_install_dismissed', '1');
            closeInstallSheet();
        }

        function handleInstallOverlayClick(e) {
            if (e.target === document.getElementById('installSheetOverlay')) {
                closeInstallSheet();
            }
        }

        // ── AI Search Bar ─────────────────────────────────────────────
        function onAiSearchInput(val) {
            var btn = document.getElementById('aiSearchSendBtn');
            if (val && val.trim()) {
                btn.style.opacity = '1';
                btn.style.pointerEvents = 'auto';
            } else {
                btn.style.opacity = '0';
                btn.style.pointerEvents = 'none';
            }
        }

        function sendAiSearch() {
            var input = document.getElementById('aiSearchInput');
            var text = (input.value || '').trim();
            if (!text) return;
            input.value = '';
            onAiSearchInput('');
            input.blur();
            if (!chatOpen) toggleChat();
            setTimeout(function() {
                document.getElementById('chatSuggestions').style.display = 'none';
                sendChatMessage(text);
            }, chatOpen ? 0 : 420);
        }

        var aiChipMessages = {
            'ticket': 'I just got a parking ticket in Toronto. What should I do? What are my options?',
            'parking': 'Where can I find free street parking in Toronto right now?',
            'pay': 'How do I pay my parking fine or camera violation in Toronto?',
            'dispute': 'How do I dispute a parking ticket or camera fine in Toronto? What is the process?',
            'towed': 'My car was towed in Toronto. How do I find it and what are the fees?',
            'report': 'I want to report a problem or send feedback about the Drivee app. My email is drivee.canada@gmail.com'
        };

        var aiChipNavActions = {
            'parking': function() { switchTab('hotspots', document.querySelectorAll('.nav-btn')[3]); },
            'pay': function() { switchTab('services', document.querySelectorAll('.nav-btn')[2]); },
            'dispute': function() { switchTab('services', document.querySelectorAll('.nav-btn')[2]); }
        };

        function aiChipAction(type) {
            if (aiChipNavActions[type] && !chatOpen) {
                aiChipNavActions[type]();
                if (type !== 'parking') {
                    setTimeout(function() {
                        if (!chatOpen) toggleChat();
                        setTimeout(function() {
                            document.getElementById('chatSuggestions').style.display = 'none';
                            sendChatMessage(aiChipMessages[type]);
                        }, 420);
                    }, 300);
                }
            } else {
                if (!chatOpen) toggleChat();
                setTimeout(function() {
                    document.getElementById('chatSuggestions').style.display = 'none';
                    sendChatMessage(aiChipMessages[type] || type);
                }, chatOpen ? 0 : 420);
            }
        }

        // ── Chat nav chips from AI response ───────────────────────────
        var navKeywords = [
            { words: ['services tab', 'services section', 'pay fine', 'pay your fine', 'payment portal', 'dispute script'],
              label: 'Go to Services →', tab: 'services', idx: 2 },
            { words: ['map tab', 'parking map', 'free parking', 'street parking', 'hotspot'],
              label: 'Open Map →', tab: 'hotspots', idx: 3 },
            { words: ['dashboard', 'add reminder', 'set reminder', 'scan ticket'],
              label: 'Go to Dashboard →', tab: 'dashboard', idx: 1 },
            { words: ['legal tab', 'find a lawyer', 'paralegal', 'traffic lawyer', 'defence firm'],
              label: 'Find Legal Help →', tab: 'legal', idx: 4 }
        ];

        function addChatNavChips(text) {
            var lower = text.toLowerCase();
            var chips = [];
            navKeywords.forEach(function(kw) {
                if (kw.words.some(function(w) { return lower.indexOf(w) !== -1; })) {
                    chips.push(kw);
                }
            });
            if (!chips.length) return;
            var msgs = document.getElementById('chatMessages');
            var typingRow = document.getElementById('chatTypingRow');
            var row = document.createElement('div');
            row.className = 'chat-nav-chip-row';
            chips.forEach(function(kw) {
                var btn = document.createElement('button');
                btn.className = 'chat-nav-chip';
                btn.textContent = kw.label;
                btn.onclick = function() {
                    if (!chatOpen) toggleChat();
                    else toggleChat();
                    setTimeout(function() {
                        switchTab(kw.tab, document.querySelectorAll('.nav-btn')[kw.idx]);
                    }, 100);
                };
                row.appendChild(btn);
            });
            msgs.insertBefore(row, typingRow);
            msgs.scrollTop = msgs.scrollHeight;
        }

        // ── Support Sheet ──────────────────────────────────────────────
        function openSupportSheet() {
            document.getElementById('supportOverlay').classList.add('open');
        }
        function closeSupportSheet() {
            document.getElementById('supportOverlay').classList.remove('open');
        }
        function handleSupportOverlayClick(e) {
            if (e.target === document.getElementById('supportOverlay')) closeSupportSheet();
        }

        // ── Dispute AI Email Builder ───────────────────────────────────
        function buildDisputeEmailAI() {
            var issue = (document.getElementById('disputeOwnIssue').value || '').trim();
            if (!issue) { showToast('Please describe your situation first'); return; }

            var emailSection = document.getElementById('disputeEmailSection');
            var emailText = document.getElementById('disputeEmailText');
            emailSection.style.display = 'block';
            emailText.value = 'Building your email with AI...';
            emailText.style.color = '#9ca3af';
            updateDisputeMailtoLinks('Building email...');

            fetch('/api/dispute-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ issue: issue })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.email) {
                    emailText.value = data.email;
                    emailText.style.color = '';
                    updateDisputeMailtoLinks(data.email);
                    emailSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    showToast('Email built! Copy or tap to send.');
                } else {
                    emailText.value = data.error || 'Unable to build email. Please try again.';
                    emailText.style.color = '#dc2626';
                }
            })
            .catch(function() {
                emailText.value = 'Network error. Please check your connection.';
                emailText.style.color = '#dc2626';
            });
        }

        function updateDisputeMailtoLinks(body) {
            var subject = encodeURIComponent('Parking Infraction Dispute');
            var bodyEnc = encodeURIComponent(body);
            var emails = {
                'dspBtnParking': 'parkingoperations@toronto.ca',
                'dspBtnCourt':   'courtservices@toronto.ca',
                'dspBtnPolice':  'traffic.services@tps.ca',
                'dspBtnGreenP':  'customerservice@greenp.com'
            };
            Object.keys(emails).forEach(function(id) {
                var el = document.getElementById(id);
                if (el) el.href = 'mailto:' + emails[id] + '?subject=' + subject + '&body=' + bodyEnc;
            });
        }

        function copyDisputeEmail() {
            var ta = document.getElementById('disputeEmailText');
            if (!ta || !ta.value || ta.value.indexOf('Building') === 0) {
                showToast('Email not ready yet'); return;
            }
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(ta.value).then(function() {
                    showToast('Email copied to clipboard');
                });
            } else {
                ta.select();
                document.execCommand('copy');
                showToast('Email copied to clipboard');
            }
        }

        // ---- Legal tab: AI photo scan --------------------------------
        async function performLegalScan(event) {
            var file = event.target.files[0];
            if (!file) return;
            var statusEl = document.getElementById('legalScanStatus');
            var verdictEl = document.getElementById('legalVerdict');
            statusEl.className = 'scan-status loading';
            statusEl.textContent = 'AI is analysing your ticket...';
            verdictEl.classList.remove('show');
            try {
                var dataUrl = await fileToDataURL(file);
                var b64 = dataUrl.split(',')[1];
                var res = await fetch('/api/analyze-ticket-photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ photo: b64 })
                });
                var data = await res.json();
                if (data.error) throw new Error(data.error);
                var cssMap = { pay: 'verdict-pay', contest: 'verdict-contest', paralegal: 'verdict-paralegal', lawyer: 'verdict-lawyer' };
                var badgeMap = { pay: '✓ Just Pay It', contest: '⚖️ Contest It Yourself', paralegal: 'Get a Paralegal', lawyer: '⚠️ Get a Lawyer' };
                verdictEl.className = 'legal-verdict show ' + (cssMap[data.verdict] || 'verdict-contest');
                document.getElementById('legalVerdictBadge').textContent = badgeMap[data.verdict] || data.verdict;
                document.getElementById('legalVerdictHeadline').textContent = data.headline || '';
                var finePill = document.getElementById('legalVerdictFine');
                if (data.fine) { finePill.textContent = data.fine; finePill.style.display = ''; }
                else { finePill.style.display = 'none'; }
                document.getElementById('legalVerdictDetail').textContent = data.detail || '';
                document.getElementById('legalVerdictCTA').style.display = data.show_firms ? '' : 'none';
                statusEl.className = 'scan-status done';
                statusEl.textContent = 'Analysis complete!';
            } catch (err) {
                statusEl.className = 'scan-status error';
                statusEl.textContent = 'Analysis failed. Try a clearer, well-lit photo.';
            }
            event.target.value = '';
        }

        // ---- Chat panel: photo upload --------------------------------
        var chatPendingPhoto = null;

        async function onChatPhotoSelected(event) {
            var file = event.target.files[0];
            if (!file) return;
            var dataUrl = await fileToDataURL(file);
            chatPendingPhoto = dataUrl.split(',')[1];
            var wrap = document.getElementById('chatPhotoPreviewWrap');
            wrap.innerHTML = '';
            wrap.style.display = 'flex';
            var thumb = document.createElement('div');
            thumb.className = 'chat-photo-thumb';
            var img = document.createElement('img');
            img.src = dataUrl;
            var rm = document.createElement('button');
            rm.className = 'chat-photo-thumb-remove';
            rm.textContent = '×';
            rm.onclick = function() {
                chatPendingPhoto = null;
                wrap.innerHTML = ''; wrap.style.display = 'none';
                event.target.value = '';
            };
            thumb.appendChild(img); thumb.appendChild(rm);
            wrap.appendChild(thumb);
            document.getElementById('chatInput').focus();
        }

        function sendChatWithPhoto(text, photoB64) {
            if (chatBusy) return;
            chatBusy = true;
            var msgs = document.getElementById('chatMessages');
            var typingRow = document.getElementById('chatTypingRow');
            var userMsg = text || 'Please analyse this photo and tell me what to do about this ticket.';
            var div = document.createElement('div');
            div.className = 'chat-msg user';
            div.innerHTML = '<div class="chat-msg-avatar"><i class="fa-solid fa-user"></i></div>'
                + '<div class="chat-msg-bubble"><img src="data:image/jpeg;base64,' + photoB64 + '" class="chat-msg-photo"><br>' + (text || '[Photo sent]') + '</div>';
            msgs.insertBefore(div, typingRow);
            chatHistory.push({ role: 'user', content: userMsg + ' [photo attached]' });
            typingRow.style.display = 'flex';
            msgs.scrollTop = msgs.scrollHeight;
            document.getElementById('chatSendBtn').disabled = true;
            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory, photo: photoB64 })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                typingRow.style.display = 'none';
                if (data.reply) {
                    appendChatMsg('bot', data.reply);
                    addChatNavChips(data.reply);
                    chatHistory.push({ role: 'assistant', content: data.reply });
                } else {
                    appendChatMsg('bot', data.error || 'Sorry, something went wrong.');
                }
            })
            .catch(function() {
                typingRow.style.display = 'none';
                appendChatMsg('bot', 'Connection error. Please try again.');
            })
            .finally(function() {
                chatBusy = false;
                document.getElementById('chatSendBtn').disabled = false;
                msgs.scrollTop = msgs.scrollHeight;
            });
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
        'PRODID:-//Drivee//EN',
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

@app.route('/manifest.json')
def manifest():
    data = {
        "name": "Drivee",
        "short_name": "Drivee",
        "description": "Toronto parking & traffic fine manager",
        "start_url": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "theme_color": "#0A84FF",
        "background_color": "#F0F4FF",
        "icons": [
            {
                "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><rect width='512' height='512' rx='115' fill='%230A84FF'/><text x='256' y='360' font-size='280' text-anchor='middle' font-family='-apple-system,sans-serif' font-weight='900' fill='white'>D</text></svg>",
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable"
            }
        ]
    }
    return Response(json.dumps(data), mimetype='application/manifest+json',
                    headers={'Cache-Control': 'public, max-age=86400'})


@app.route('/favicon.ico')
def favicon():
    return '', 204

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
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Content-Type': 'text/calendar; charset=utf-8; method=PUBLISH'
            }
        )
    return redirect('/')

@app.route('/report_311', methods=['POST'])
def handle_311_report():
    issue_type = request.form.get('issue_type', '').strip()
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    reporter_name = (request.form.get('reporter_name', '') or 'Anonymous').strip()
    reporter_color = (request.form.get('reporter_color', '') or '#0A84FF').strip()
    photo_data = request.form.get('photo_data', '').strip()
    if issue_type and lat and lng:
        try:
            entry = {
                "type": issue_type,
                "lat": float(lat),
                "lng": float(lng),
                "status": "Community Report",
                "name": reporter_name,
                "color": reporter_color
            }
            if photo_data:
                entry["photo"] = photo_data
            reports_data.append(entry)
        except (ValueError, TypeError):
            pass
    return redirect('/?reported=1')


@app.route('/api/dispute-email', methods=['POST'])
def dispute_email():
    try:
        data = request.get_json(force=True) or {}
        issue = (data.get('issue') or '').strip()
        if not issue:
            return jsonify({'error': 'No issue description provided'}), 400

        prompt = (
            "You are a professional legal letter writer helping a Toronto driver dispute a parking or traffic infraction. "
            "Write a formal, polite dispute email based on the following situation described by the driver:\n\n"
            + issue + "\n\n"
            "The email should:\n"
            "- Start with 'To the Screening Officer,' or 'To Whom It May Concern,'\n"
            "- Clearly state they are requesting cancellation of the infraction notice\n"
            "- Explain the grounds for dispute based on the driver's description\n"
            "- Mention any evidence they may have (photos, permit, witnesses)\n"
            "- Be professional, concise (3-5 paragraphs), and factual\n"
            "- End with 'Respectfully,' and leave a blank for their name and date\n"
            "Do not include placeholders like [YOUR NAME] in the body — just leave 'Respectfully,' at the end."
        )

        response = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=600
        )
        email_text = response.choices[0].message.content or ""
        return jsonify({'email': email_text})
    except Exception as e:
        err = str(e)
        if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
            return jsonify({'error': 'Cloud budget exceeded. Please try again later.'}), 429
        return jsonify({'error': 'AI service unavailable. Please try again.'}), 500


@app.route('/api/analyze-ticket-photo', methods=['POST'])
def analyze_ticket_photo():
    try:
        data = request.get_json(force=True) or {}
        photo_b64 = data.get('photo', '')
        if not photo_b64:
            return jsonify({'error': 'No photo provided'}), 400
        prompt = (
            'You are a Toronto traffic legal expert. Analyse this parking or traffic ticket photo.\n'
            'Return ONLY valid JSON (no markdown, no explanation) with these exact fields:\n'
            '{\n'
            '  "verdict": "pay" | "contest" | "paralegal" | "lawyer",\n'
            '  "headline": "short action phrase max 8 words",\n'
            '  "fine": "amount visible e.g. $150.00 or empty string",\n'
            '  "detail": "2-3 sentences of advice based on what you see",\n'
            '  "show_firms": true or false\n'
            '}\n'
            'Verdict guide:\n'
            '- pay: minor parking fine under $100, clear infraction\n'
            '- contest: unclear signage, procedural error, equipment fault\n'
            '- paralegal: demerit point offence, fine $150+, camera ticket\n'
            '- lawyer: stunt driving, DUI, criminal charge, fine $500+\n'
            'Set show_firms true for paralegal or lawyer verdicts.'
        )
        response = _openai_client.chat.completions.create(
            model='gpt-4o',
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + photo_b64}}
                ]
            }],
            max_completion_tokens=400
        )
        raw = response.choices[0].message.content or '{}'
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return jsonify(parsed)
        return jsonify({'error': 'Could not parse AI response'}), 500
    except Exception as e:
        err = str(e)
        if 'FREE_CLOUD_BUDGET_EXCEEDED' in err:
            return jsonify({'error': 'Budget exceeded'}), 429
        return jsonify({'error': 'AI service unavailable'}), 500

@app.route('/api/analyze-photo', methods=['POST'])
def analyze_photo():
    try:
        data = request.get_json(force=True) or {}
        photo_b64 = data.get('photo', '')
        issue_type = data.get('issue_type', 'street issue')
        if not photo_b64:
            return jsonify({'description': ''}), 400
        response = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "This is a photo of a " + issue_type + " reported on a Toronto street. In 1-2 concise sentences, describe what you see in a way useful for a 311 report to the City of Toronto. Be specific about visible damage, obstruction, or hazard."},
                    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + photo_b64}}
                ]
            }],
            max_completion_tokens=120
        )
        description = response.choices[0].message.content or ""
        return jsonify({'description': description})
    except Exception as e:
        err = str(e)
        if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
            return jsonify({'error': 'Budget exceeded'}), 429
        return jsonify({'description': '', 'error': 'Photo analysis unavailable'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True) or {}
        messages = data.get('messages', [])
        if not messages:
            return jsonify({'error': 'No messages'}), 400

        system_prompt = (
            "You are Drivee AI — a friendly, knowledgeable assistant specializing in Toronto "
            "parking tickets, traffic fines, and driving violations in Ontario, Canada. "
            "You help users understand their tickets, know their rights, dispute fines, "
            "find payment options, understand late fees, and decide whether to contest or pay. "
            "You know Toronto bylaws, the Highway Traffic Act (HTA), POA courts, Green P parking, "
            "and can recommend when to hire a paralegal or traffic lawyer. "
            "The Drivee app has these tabs: Dashboard (profile, ticket scanner, reminders, deadline calculator), "
            "Services (pay/dispute parking tickets, camera fines, court services, Green P parking rates, dispute script builder), "
            "Map (free street parking spots across Toronto), and Legal (traffic lawyers and paralegals). "
            "When relevant, mention which tab or section can help the user. "
            "Keep answers concise, practical, and friendly. When uncertain, say so and suggest "
            "the user consult a professional. Do not give legal advice for criminal charges. "
            "If a user wants to report a problem with the app or give feedback, tell them to email drivee.canada@gmail.com."
        )

        photo_b64 = data.get('photo', '')

        # If photo provided, replace last user message with vision content
        if photo_b64 and messages:
            last = messages[-1]
            if last.get('role') == 'user':
                vision_content = [
                    {'type': 'text', 'text': last.get('content', 'Please analyse this ticket photo.')},
                    {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + photo_b64}}
                ]
                messages = messages[:-1] + [{'role': 'user', 'content': vision_content}]

        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=full_messages,
            max_completion_tokens=800
        )
        reply = response.choices[0].message.content or ""
        return jsonify({'reply': reply})
    except Exception as e:
        err = str(e)
        if "FREE_CLOUD_BUDGET_EXCEEDED" in err:
            return jsonify({'error': 'Cloud budget exceeded. Please check your Replit credits.'}), 429
        return jsonify({'error': 'AI service unavailable. Please try again.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
