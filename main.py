from flask import Flask, render_template_string, request, redirect, url_for, jsonify, Response
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import json
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
    <meta name="theme-color" content="#000000">
    <title>Drivee | Professional</title>
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

        /* ── Full-screen hero map ── */
        #map {
            height: calc(100svh - var(--safe-top) - var(--safe-bottom) - 162px);
            min-height: 420px;
            border-radius: 0;
            border: none;
            z-index: 1;
            display: block;
        }
        .map-hero-section {
            position: relative;
            margin: -4px -16px 16px;
        }
        @media (max-width: 480px) {
            .map-hero-section { margin: -4px -14px 14px; }
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
            right: 12px;
            z-index: 800;
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: rgba(255,255,255,0.95);
            border: none;
            box-shadow: 0 2px 12px rgba(0,0,0,0.18);
            color: var(--blue);
            font-size: 17px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .map-gps-fab:active { transform: scale(0.92); }
        .map-gps-fab.active-gps { background: var(--blue); color: #fff; }
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
    </style>
</head>
<body>
    <div id="loadingOverlay" class="loading-overlay">
        <i class="fa-solid fa-satellite-dish fa-spin"></i>
        <span>Grabbing GPS Coordinates...</span>
    </div>

    <div id="toast" class="toast"></div>

    <div class="app">
        <div class="top-search-bar">
            <div class="search-input-wrap">
                <i class="fa-solid fa-magnifying-glass search-icon"></i>
                <input type="text" class="search-input" placeholder="Find parking near..." readonly onclick="switchTab('hotspots', document.querySelectorAll('.nav-btn')[3])">
            </div>
            <button class="search-bell" onclick="switchTab('dashboard', document.querySelectorAll('.nav-btn')[1])" title="Reminders">
                <i class="fa-solid fa-bell"></i>
                {% if reminders %}<span class="bell-badge">{{ reminders|length }}</span>{% endif %}
            </button>
            <button class="search-profile" onclick="switchTab('dashboard', document.querySelectorAll('.nav-btn')[1])" title="Profile">
                <i class="fa-solid fa-user"></i>
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
                    <a href="https://www.ontario.ca/page/traffic-ticket" target="_blank" rel="noopener" class="service-link svc-amber">
                        <div class="svc-icon">&#x1F6A8;</div>
                        <span class="svc-text">Speed Violation — Pay or Dispute</span>
                        <span class="svc-arrow">&#x203A;</span>
                    </a>
                    <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/courts/pay-a-fine-at-court/" target="_blank" rel="noopener" class="service-link svc-teal">
                        <div class="svc-icon">&#x1F4B8;</div>
                        <span class="svc-text">Pay a Fine at Court</span>
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
                <a href="https://apps.apple.com/ca/app/green-p-parking/id983111045" target="_blank" rel="noopener" class="green-p-link" style="margin-top:14px;">
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
            </div>

            <div class="card card-blue card-7">
                <div class="card-label label-blue"><i class="fa-solid fa-flag-usa"></i> Got a Ticket in the USA?</div>
                <p class="card-desc">Quick links to pay or dispute US parking tickets and toll violations from any state.</p>
                <div class="service-list">
                    <a href="https://www.dmv.org/traffic-tickets/" target="_blank" rel="noopener" class="service-link svc-blue">
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

            <div class="map-hero-section">
                <div id="map"></div>

                <button class="map-gps-fab" onclick="startGPSGuardian()" id="gpsBtn" title="GPS Guardian">
                    <i class="fa-solid fa-satellite-dish"></i>
                </button>

                <div id="mapLoadStatus" class="map-load-status"></div>

                <div class="map-float-controls">
                    <div class="map-float-layers">
                        <button class="layer-toggle active" id="toggleParking" onclick="toggleLayer('parking')" style="color:#16a34a;">
                            <span class="toggle-dot" style="background:#16a34a;"></span> Parking
                        </button>
                        <button class="layer-toggle active" id="toggleEV" onclick="toggleLayer('ev')" style="color:#8b5cf6;">
                            <span class="toggle-dot" style="background:#8b5cf6;"></span> EV Charging
                        </button>
                        <button class="layer-toggle active" id="toggleBike" onclick="toggleLayer('bike')" style="color:#10b981;">
                            <span class="toggle-dot" style="background:#10b981;"></span> Bike Lanes
                        </button>
                        <button class="layer-toggle active" id="toggleHydrant" onclick="toggleLayer('hydrant')" style="color:#f59e0b;">
                            <span class="toggle-dot" style="background:#f59e0b;"></span> Hydrants
                        </button>
                        <button class="layer-toggle active" id="toggleHeat" onclick="toggleLayer('heat')" style="color:#ef4444;">
                            <span class="toggle-dot" style="background:#ef4444;"></span> Hotspots
                        </button>
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
            <a href="https://www.toronto.ca/services-payments/tickets-fines-penalties/parking-violations/" target="_blank" rel="noopener" class="nav-fab" title="Pay Ticket">
                <i class="fa-solid fa-receipt"></i>
            </a>
        </div>
    </nav>

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
                <div class="chat-msg-bubble">Hi! I am Drivee AI. Ask me anything about Toronto parking tickets, fines, disputes, or traffic law. How can I help you today?</div>
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
            <button class="chat-suggestion" onclick="sendSuggestion(this)">How much are late fees in Toronto?</button>
            <button class="chat-suggestion" onclick="sendSuggestion(this)">Can I contest a red light camera fine?</button>
        </div>
        <div class="chat-input-row">
            <textarea class="chat-input" id="chatInput" placeholder="Ask about tickets, fines, disputes..." rows="1"
                onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendChat();}"
                oninput="this.style.height='auto';this.style.height=Math.min(this.scrollHeight,100)+'px'"></textarea>
            <button class="chat-send" id="chatSendBtn" onclick="sendChat()">
                <i class="fa-solid fa-paper-plane"></i>
            </button>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script>
        var mapInstance = null;
        var bikeGeoLayer = null;
        var hydrantGroup = null;
        var heatLayerRef = null;
        var evGroup = null;
        var parkingGroup = null;
        var bikeLayerOn = true;
        var hydrantLayerOn = true;
        var heatLayerOn = true;
        var evLayerOn = true;
        var parkingLayerOn = true;

        function initMap() {
            if (mapInstance) {
                mapInstance.invalidateSize();
                return;
            }
            mapInstance = L.map('map', { zoomControl: true }).setView([43.6532, -79.3832], 13);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
                maxZoom: 19,
                subdomains: 'abcd'
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

            heatLayerRef = L.heatLayer(hotspots, {
                radius: 32,
                blur: 22,
                maxZoom: 16,
                gradient: { 0.2: '#bfdbfe', 0.4: '#93c5fd', 0.6: '#fde68a', 0.8: '#fb923c', 1.0: '#ef4444' }
            }).addTo(mapInstance);

            loadBikeLanesLayer();
            loadHydrantsLayer();
            loadEVStationsLayer();
            loadParkingLayer();

            var hazardIcon = L.divIcon({
                className: 'custom-icon',
                html: '<i class="fa-solid fa-location-dot" style="color: #0A84FF; font-size: 32px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.5));"></i>',
                iconSize: [32, 32],
                iconAnchor: [16, 32]
            });

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
                var marker = L.marker([report.lat, report.lng], {icon: avIcon}).addTo(mapInstance);
                marker.bindPopup('<b>' + name + '</b><br>' + report.type + '<br><span style="color:#8E8E93;font-size:12px;">' + report.status + '</span>');
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
                btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i>';
                btn.classList.remove('active-gps');
                btn.title = 'Start GPS Guardian';
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
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            btn.classList.add('active-gps');
            btn.title = 'Guardian Active — tap to stop';

            gpsWatchId = navigator.geolocation.watchPosition(
                function(position) {
                    btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i>';

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
                    btn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i>';
                    btn.classList.remove('active-gps');
                    document.getElementById('gpsAlertBanner').classList.remove('show');
                    if (userMarker) { mapInstance.removeLayer(userMarker); userMarker = null; }
                    gpsWatchId = null;
                },
                { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
            );
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

        function openReportPanel(issueType) {
            currentReportType = issueType;
            document.getElementById('reportPanelTitle').textContent = issueType + ' — AI Email Draft';
            var savedName = localStorage.getItem('drivee_name') || '';
            document.getElementById('reporterName').value = savedName;
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
                addAvatarMarkerToMap(lat, lng, name, color, currentReportType);
                document.getElementById('issueTypeInput').value = currentReportType;
                document.getElementById('latInput').value = lat;
                document.getElementById('lngInput').value = lng;
                document.getElementById('reporterNameInput').value = name;
                document.getElementById('reporterColorInput').value = color;
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

        function addAvatarMarkerToMap(lat, lng, name, color, issueType) {
            var initials = name.split(' ').filter(function(w){return w.length>0;}).map(function(w){return w[0].toUpperCase();}).join('').slice(0,2) || '?';
            var avIcon = L.divIcon({
                className: '',
                html: '<div class="report-avatar" style="background:' + color + ';">' + initials + '</div>',
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });
            var marker = L.marker([lat, lng], {icon: avIcon}).addTo(mapInstance);
            marker.bindPopup('<b>' + name + '</b><br>' + issueType + '<br><span style="color:#8E8E93;font-size:12px;">Just now</span>');
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

        /* ── Map layer loaders ─────────────────────────────────── */

        async function loadBikeLanesLayer() {
            var statusEl = document.getElementById('mapLoadStatus');
            if (statusEl) { statusEl.textContent = 'Loading cycling network from toronto.ca\u2026'; statusEl.style.display = 'block'; }
            try {
                var pkgResp = await fetch('https://ckan0.cf.opendata.inter.toronto.ca/api/3/action/package_show?id=cycling-network');
                var pkg = await pkgResp.json();
                var resources = (pkg.result || {}).resources || [];
                var geoRes = resources.find(function(r) {
                    var fmt = (r.format || '').toLowerCase();
                    var nm = (r.name || '').toLowerCase();
                    var url = (r.url || '').toLowerCase();
                    return fmt === 'geojson' || nm.indexOf('4326') >= 0 || url.indexOf('geojson') >= 0;
                });
                if (geoRes) {
                    if (statusEl) statusEl.textContent = 'Fetching ' + (geoRes.name || 'bike lanes') + '\u2026';
                    var geoResp = await fetch(geoRes.url);
                    var geoData = await geoResp.json();
                    bikeGeoLayer = L.geoJSON(geoData, {
                        style: function(feature) {
                            var p = feature.properties || {};
                            var type = (p.INFRA_HIGHORDER || '').toLowerCase();
                            var color = (type.indexOf('protect') >= 0) ? '#059669' :
                                        (type.indexOf('trail') >= 0 || type.indexOf('path') >= 0) ? '#7c3aed' : '#2563eb';
                            return { color: color, weight: 2.5, opacity: 0.9 };
                        },
                        onEachFeature: function(feature, layer) {
                            var p = feature.properties || {};
                            var name = p.STREETNAME || 'Cycling Route';
                            var type = p.INFRA_HIGHORDER || 'Bike Lane';
                            layer.bindPopup('<b>🚲 ' + name + '</b><br>' + type + '<br><span style="color:#FF453A;font-weight:600">$200 Fine Zone</span>');
                        }
                    });
                    if (bikeLayerOn) bikeGeoLayer.addTo(mapInstance);
                    if (statusEl) { statusEl.textContent = 'Cycling network loaded from toronto.ca'; setTimeout(function() { statusEl.style.display = 'none'; }, 3000); }
                    return;
                }
            } catch(e) {
                console.warn('Toronto Open Data bike lanes failed, using fallback:', e);
            }
            bikeGeoLayer = drawFallbackBikeLanes();
            if (bikeLayerOn) bikeGeoLayer.addTo(mapInstance);
            if (statusEl) { statusEl.textContent = 'Cycling routes loaded (offline data)'; setTimeout(function() { statusEl.style.display = 'none'; }, 2000); }
        }

        function drawFallbackBikeLanes() {
            var routes = [
                { coords: [[43.6655,-79.4165],[43.6655,-79.3960],[43.6655,-79.3720],[43.6655,-79.3330]], name: 'Bloor St W', type: 'Protected Bike Lane' },
                { coords: [[43.6615,-79.4050],[43.6615,-79.3800],[43.6615,-79.3620]], name: 'Harbord St', type: 'Bike Lane' },
                { coords: [[43.6510,-79.4080],[43.6510,-79.3850],[43.6510,-79.3600]], name: 'College St', type: 'Bike Lane' },
                { coords: [[43.6485,-79.4050],[43.6485,-79.3840],[43.6485,-79.3600]], name: 'Wellesley St', type: 'Protected Bike Lane' },
                { coords: [[43.6390,-79.4090],[43.6390,-79.3880],[43.6390,-79.3680]], name: 'Queen St W', type: 'Bike Lane' },
                { coords: [[43.6360,-79.4080],[43.6360,-79.3880],[43.6360,-79.3700]], name: 'Richmond St', type: 'Protected Bike Lane' },
                { coords: [[43.6345,-79.4060],[43.6345,-79.3860],[43.6345,-79.3700]], name: 'Adelaide St', type: 'Protected Bike Lane' },
                { coords: [[43.6540,-79.3885],[43.6480,-79.3880],[43.6420,-79.3885]], name: 'Sherbourne St', type: 'Protected Bike Lane' },
                { coords: [[43.6600,-79.3890],[43.6540,-79.3890],[43.6480,-79.3890]], name: 'Jarvis St', type: 'Bike Lane' },
                { coords: [[43.6720,-79.4050],[43.6650,-79.4010],[43.6590,-79.3970]], name: 'Davenport Rd', type: 'Multi-use Trail' },
                { coords: [[43.6380,-79.3800],[43.6280,-79.3810],[43.6200,-79.3820]], name: 'Lakeshore Trail', type: 'Multi-use Trail' },
                { coords: [[43.6600,-79.4250],[43.6540,-79.4250],[43.6480,-79.4250]], name: 'Shaw St', type: 'Bike Lane' },
                { coords: [[43.6428,-79.4000],[43.6428,-79.3800],[43.6428,-79.3600]], name: 'Dundas St W', type: 'Bike Lane' },
            ];
            var group = L.layerGroup();
            routes.forEach(function(route) {
                var color = (route.type.toLowerCase().indexOf('protect') >= 0) ? '#059669' :
                            (route.type.toLowerCase().indexOf('trail') >= 0) ? '#7c3aed' : '#2563eb';
                L.polyline(route.coords, { color: color, weight: 3, opacity: 0.9 })
                 .bindPopup('<b>\U0001F6B2 ' + route.name + '</b><br><span style="color:#059669;font-weight:600;">' + route.type + '</span><br><span style="color:#dc2626;font-weight:600">$200 Fine Zone</span>')
                 .addTo(group);
            });
            return group;
        }

        function loadHydrantsLayer() {
            hydrantGroup = L.layerGroup();
            var hydrantIcon = L.divIcon({
                className: '',
                html: '<div style="width:10px;height:10px;border-radius:50%;background:#f59e0b;border:2px solid #92400e;box-shadow:0 1px 3px rgba(0,0,0,0.3);"></div>',
                iconSize: [10, 10],
                iconAnchor: [5, 5]
            });
            var step = 0.0030;
            var latS = 43.637, latE = 43.678, lngS = -79.423, lngE = -79.351;
            for (var lat = latS; lat < latE; lat += step) {
                for (var lng = lngS; lng < lngE; lng += step * 1.4) {
                    var rLat = lat + (Math.random() - 0.5) * step * 0.5;
                    var rLng = lng + (Math.random() - 0.5) * step * 0.5;
                    L.marker([rLat, rLng], { icon: hydrantIcon })
                     .bindPopup('<b style="color:#92400e;">Fire Hydrant</b><br><span style="color:#6b7280;font-size:12px;">3 m no-parking clearance required</span><br><span style="color:#dc2626;font-weight:700;font-size:13px;">$100 Fine</span>')
                     .addTo(hydrantGroup);
                }
            }
            if (hydrantLayerOn) hydrantGroup.addTo(mapInstance);
        }

        async function loadEVStationsLayer() {
            evGroup = L.layerGroup();
            var evIcon = L.divIcon({
                className: '',
                html: '<div style="width:22px;height:22px;border-radius:50%;background:#8b5cf6;border:2.5px solid #fff;box-shadow:0 2px 6px rgba(139,92,246,0.5);display:flex;align-items:center;justify-content:center;font-size:11px;color:#fff;font-weight:800;">EV</div>',
                iconSize: [22, 22],
                iconAnchor: [11, 11]
            });

            var evStations = [
                { lat: 43.6482, lng: -79.3992, name: 'CF Sherway Gardens', addr: '25 The West Mall', ports: 8, network: 'ChargePoint', free: false },
                { lat: 43.6426, lng: -79.3866, name: 'Scotiabank Arena Garage', addr: '40 Bay St', ports: 6, network: 'Tesla', free: false },
                { lat: 43.6677, lng: -79.4000, name: 'Yorkdale Mall', addr: '3401 Dufferin St', ports: 12, network: 'Tesla Supercharger', free: false },
                { lat: 43.7730, lng: -79.3383, name: 'Fairview Mall', addr: '1800 Sheppard Ave E', ports: 4, network: 'ChargePoint', free: false },
                { lat: 43.6461, lng: -79.3798, name: 'Union Station Garage', addr: '65 Front St W', ports: 4, network: 'Flo', free: false },
                { lat: 43.6617, lng: -79.3804, name: 'City Hall Garage', addr: '100 Queen St W', ports: 6, network: 'Flo', free: false },
                { lat: 43.7245, lng: -79.3427, name: 'North York Civic Centre', addr: '5100 Yonge St', ports: 8, network: 'Flo', free: true },
                { lat: 43.6531, lng: -79.4056, name: 'Exhibition Place', addr: '200 Princes Blvd', ports: 10, network: 'ChargePoint', free: false },
                { lat: 43.6441, lng: -79.3997, name: 'Metro Toronto Convention Ctr', addr: '255 Front St W', ports: 6, network: 'ChargePoint', free: false },
                { lat: 43.7070, lng: -79.3980, name: 'Downsview Park', addr: '35 Carl Hall Rd', ports: 4, network: 'Flo', free: true },
                { lat: 43.6480, lng: -79.4120, name: 'Liberty Village Parking', addr: '171 East Liberty St', ports: 4, network: 'ChargePoint', free: false },
                { lat: 43.6590, lng: -79.3450, name: 'Corktown Common', addr: '155 Bayview Ave', ports: 3, network: 'Flo', free: true },
                { lat: 43.6720, lng: -79.3880, name: 'Ryerson University', addr: '350 Victoria St', ports: 5, network: 'ChargePoint', free: false },
                { lat: 43.6980, lng: -79.4230, name: 'Humber College North', addr: '205 Humber College Blvd', ports: 6, network: 'Flo', free: false },
                { lat: 43.7630, lng: -79.5240, name: 'Etobicoke Civic Centre', addr: '399 The West Mall', ports: 4, network: 'Flo', free: true },
                { lat: 43.6800, lng: -79.5580, name: 'Mimico GO Station', addr: '55 Superior Ave', ports: 3, network: 'Petro-Canada RECHARGE', free: false },
                { lat: 43.7190, lng: -79.2720, name: 'Scarborough Town Centre', addr: '300 Borough Dr', ports: 8, network: 'Tesla', free: false },
                { lat: 43.7714, lng: -79.2510, name: 'Agincourt GO', addr: '4100 Sheppard Ave E', ports: 4, network: 'Petro-Canada RECHARGE', free: false },
                { lat: 43.6350, lng: -79.3500, name: 'Leslieville Charging Hub', addr: '905 Queen St E', ports: 4, network: 'Flo', free: false },
                { lat: 43.6553, lng: -79.4645, name: 'High Park P-Lot', addr: '1873 Bloor St W', ports: 3, network: 'Flo', free: true }
            ];

            try {
                var pkgResp = await fetch('https://ckan0.cf.opendata.inter.toronto.ca/api/3/action/package_show?id=electric-vehicle-charging-stations');
                var pkg = await pkgResp.json();
                var resources = (pkg.result || {}).resources || [];
                var geoRes = resources.find(function(r) {
                    var fmt = (r.format || '').toLowerCase();
                    return fmt === 'geojson' || fmt === 'json' || (r.url || '').toLowerCase().indexOf('geojson') >= 0;
                });
                if (geoRes) {
                    var geoResp = await fetch(geoRes.url);
                    var geoData = await geoResp.json();
                    var features = geoData.features || [];
                    if (features.length > 0) {
                        features.forEach(function(f) {
                            var coords = (f.geometry || {}).coordinates || [];
                            if (coords.length < 2) return;
                            var p = f.properties || {};
                            var name = p.STATION_NAME || p.NAME || p.name || 'EV Charging Station';
                            var addr = p.ADDRESS || p.address || '';
                            var ports = p.EV_LEVEL2_EVSE_NUM || p.EVSE_COUNT || p.ports || '?';
                            var network = p.EV_NETWORK || p.NETWORK || 'City of Toronto';
                            L.marker([coords[1], coords[0]], { icon: evIcon })
                             .bindPopup('<b style="color:#7c3aed;">\u26A1 ' + name + '</b><br><span style="color:#374151;font-size:12px;">' + addr + '</span><br>Ports: <b>' + ports + '</b> &bull; ' + network)
                             .addTo(evGroup);
                        });
                        if (evLayerOn) evGroup.addTo(mapInstance);
                        return;
                    }
                }
            } catch(e) {}

            evStations.forEach(function(s) {
                var freeLabel = s.free ? '<span style="color:#059669;font-weight:600;">Free to use</span>' : '<span style="color:#374151;">Paid / App required</span>';
                L.marker([s.lat, s.lng], { icon: evIcon })
                 .bindPopup('<b style="color:#7c3aed;">\u26A1 ' + s.name + '</b><br><span style="color:#6b7280;font-size:12px;">' + s.addr + '</span><br>Ports: <b>' + s.ports + '</b><br>Network: ' + s.network + '<br>' + freeLabel)
                 .addTo(evGroup);
            });
            if (evLayerOn) evGroup.addTo(mapInstance);
        }

        function loadParkingLayer() {
            parkingGroup = L.layerGroup();
            var spots = [
                { lat: 43.6533, lng: -79.3832, name: 'Nathan Phillips Square', rate: '$3.50/hr', max: '3 hrs', hours: 'Mon-Sun 7am-10pm', count: 31, tier: 'orange' },
                { lat: 43.6485, lng: -79.3835, name: 'Harbour Square', rate: '$4.00/hr', max: '2 hrs', hours: 'Mon-Sun 8am-10pm', count: 12, tier: 'orange' },
                { lat: 43.6611, lng: -79.3805, name: 'Dundas Square P-Lot', rate: '$3.00/hr', max: '2 hrs', hours: 'Mon-Sat 8am-9pm', count: 0, tier: 'red' },
                { lat: 43.6540, lng: -79.4055, name: 'Strachan Ave Green P', rate: '$2.50/hr', max: '4 hrs', hours: 'Mon-Sat 8am-9pm', count: 18, tier: 'green' },
                { lat: 43.6438, lng: -79.3872, name: 'Front St W Green P', rate: '$3.50/hr', max: '2 hrs', hours: 'Mon-Sun 8am-midnight', count: 12, tier: 'orange' },
                { lat: 43.6620, lng: -79.3900, name: 'Gerrard St E Lot', rate: '$2.00/hr', max: '4 hrs', hours: 'Mon-Fri 8am-6pm', count: 89, tier: 'green' },
                { lat: 43.6490, lng: -79.3978, name: 'Rees St Green P', rate: '$3.00/hr', max: '2 hrs', hours: 'Mon-Sun 7am-10pm', count: 2, tier: 'orange' },
                { lat: 43.6560, lng: -79.3740, name: 'George St Green P', rate: '$2.50/hr', max: '3 hrs', hours: 'Mon-Sat 8am-9pm', count: 45, tier: 'green' },
                { lat: 43.6388, lng: -79.4010, name: 'Dufferin St Lot', rate: '$2.00/hr', max: '4 hrs', hours: 'Mon-Fri 7am-7pm', count: 28, tier: 'green' },
                { lat: 43.6680, lng: -79.4100, name: 'Dufferin-Bloor Green P', rate: '$2.50/hr', max: '3 hrs', hours: 'Mon-Sat 8am-9pm', count: 7, tier: 'green' },
                { lat: 43.6432, lng: -79.4000, name: 'Queen-Bathurst Lot', rate: '$2.50/hr', max: '3 hrs', hours: 'Mon-Sat 8am-9pm', count: 25, tier: 'green' },
                { lat: 43.6700, lng: -79.3680, name: 'Sherbourne-Bloor', rate: '$2.00/hr', max: '3 hrs', hours: 'Mon-Sat 8am-8pm', count: 55, tier: 'green' },
                { lat: 43.6580, lng: -79.4200, name: 'Dovercourt-College', rate: '$1.75/hr', max: 'No limit', hours: 'Mon-Sat 8am-8pm', count: 6, tier: 'green' },
                { lat: 43.6348, lng: -79.3450, name: 'Riverside Green P', rate: '$1.50/hr', max: 'No limit', hours: 'Mon-Fri 8am-6pm', count: 3, tier: 'orange' },
                { lat: 43.6510, lng: -79.3600, name: 'Berkeley St Lot', rate: '$2.25/hr', max: '3 hrs', hours: 'Mon-Sat 8am-8pm', count: 12, tier: 'orange' }
            ];
            spots.forEach(function(s) {
                var bg = s.tier === 'green' ? '#16a34a' : s.tier === 'orange' ? '#d97706' : '#dc2626';
                var size = s.count > 50 ? 42 : s.count > 10 ? 36 : 30;
                var fontSize = s.count > 50 ? 14 : s.count > 10 ? 13 : 12;
                var icon = L.divIcon({
                    className: '',
                    html: '<div style="width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:' + bg + ';border:2.5px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.25);display:flex;align-items:center;justify-content:center;font-size:' + fontSize + 'px;color:#fff;font-weight:800;font-family:-apple-system,sans-serif;">' + s.count + '</div>',
                    iconSize: [size, size],
                    iconAnchor: [size/2, size/2]
                });
                var availLabel = s.count === 0 ? '<span style="color:#dc2626;font-weight:600;">Full</span>' :
                                 s.count < 5 ? '<span style="color:#d97706;font-weight:600;">Only ' + s.count + ' spots</span>' :
                                 '<span style="color:#16a34a;font-weight:600;">' + s.count + ' spots available</span>';
                L.marker([s.lat, s.lng], { icon: icon })
                 .bindPopup('<b style="color:#1f2937;">' + s.name + '</b><br>' + availLabel + '<br><span style="color:#374151;font-size:12px;">' + s.hours + '</span><br>Rate: <b style="color:#0A84FF;">' + s.rate + '</b> &bull; Max: ' + s.max)
                 .addTo(parkingGroup);
            });
            if (parkingLayerOn) parkingGroup.addTo(mapInstance);
        }

        function toggleLayer(type) {
            if (type === 'bike') {
                bikeLayerOn = !bikeLayerOn;
                if (bikeGeoLayer) {
                    if (bikeLayerOn) bikeGeoLayer.addTo(mapInstance);
                    else mapInstance.removeLayer(bikeGeoLayer);
                }
                document.getElementById('toggleBike').classList.toggle('active', bikeLayerOn);
            } else if (type === 'hydrant') {
                hydrantLayerOn = !hydrantLayerOn;
                if (hydrantGroup) {
                    if (hydrantLayerOn) hydrantGroup.addTo(mapInstance);
                    else mapInstance.removeLayer(hydrantGroup);
                }
                document.getElementById('toggleHydrant').classList.toggle('active', hydrantLayerOn);
            } else if (type === 'heat') {
                heatLayerOn = !heatLayerOn;
                if (heatLayerRef) {
                    if (heatLayerOn) heatLayerRef.addTo(mapInstance);
                    else mapInstance.removeLayer(heatLayerRef);
                }
                document.getElementById('toggleHeat').classList.toggle('active', heatLayerOn);
            } else if (type === 'ev') {
                evLayerOn = !evLayerOn;
                if (evGroup) {
                    if (evLayerOn) evGroup.addTo(mapInstance);
                    else mapInstance.removeLayer(evGroup);
                }
                document.getElementById('toggleEV').classList.toggle('active', evLayerOn);
            } else if (type === 'parking') {
                parkingLayerOn = !parkingLayerOn;
                if (parkingGroup) {
                    if (parkingLayerOn) parkingGroup.addTo(mapInstance);
                    else mapInstance.removeLayer(parkingGroup);
                }
                document.getElementById('toggleParking').classList.toggle('active', parkingLayerOn);
            }
        }

        /* ─────────────────────────────────────────────────────── */

        async function performLegalScan(event) {
            var file = event.target.files[0];
            if (!file) return;
            var statusEl = document.getElementById('legalScanStatus');
            var verdictEl = document.getElementById('legalVerdict');
            statusEl.className = 'scan-status loading';
            statusEl.textContent = 'AI is reading your ticket\u2026';
            verdictEl.className = 'legal-verdict';

            try {
                var dataUrl = await fileToDataURL(file);
                var result = await Tesseract.recognize(dataUrl, 'eng');
                var rawText = result.data.text || '';
                var textUpper = rawText.toUpperCase();

                var fineMatch = rawText.match(/\$\s*(\d+(?:\.\d{2})?)/);
                var fineAmount = fineMatch ? parseFloat(fineMatch[1]) : 0;

                var urgent = /STUNT|IMPAIRED|DUI|CRIMINAL CODE|DANGEROUS DRIVING|FAIL TO REMAIN|HIT.?AND.?RUN|RACING|STREET RACING/.test(textUpper);
                var serious = /CARELESS|SCHOOL ZONE|CONSTRUCTION ZONE|RED LIGHT CAMERA|CELL PHONE|HANDHELD|BIKE LANE|PHOTO RADAR|PLATE DENIED|FOLLOW TOO CLOSE|SEATBELT|SEAT BELT|NO INSURANCE|INSURANCE/.test(textUpper) || fineAmount >= 200;

                var badge, headline, detail, cssClass, showCTA;

                if (urgent) {
                    badge = 'Get a Lawyer — Serious Consequences';
                    headline = 'Do NOT pay this ticket';
                    detail = 'This charge may result in criminal charges, licence suspension, vehicle impoundment, or a permanent record. Paying is an admission of guilt. Contact a traffic lawyer today — free consultation with any firm below.';
                    cssClass = 'verdict-lawyer';
                    showCTA = true;
                } else if (serious) {
                    badge = 'Get a Paralegal — Worth Fighting';
                    headline = 'This ticket is worth contesting';
                    detail = 'This charge carries demerit points or a significant fine that could raise your insurance premium for 3+ years. A licensed paralegal can often get it reduced or withdrawn. Free consultation — see firms below.';
                    cssClass = 'verdict-paralegal';
                    showCTA = true;
                } else if (fineAmount >= 100) {
                    badge = 'Consider a Paralegal';
                    headline = 'High fine — may be worth fighting';
                    detail = 'A fine this size is worth a free 15-minute paralegal consult. They can often reduce or dismiss it, saving you more than their fee. See the firms listed below.';
                    cssClass = 'verdict-paralegal';
                    showCTA = true;
                } else if (fineAmount > 0 && fineAmount < 100) {
                    badge = 'Pay It — Not Worth Fighting';
                    headline = 'Small fine, easiest to pay';
                    detail = 'This is a low-value infraction with minimal impact on your record. Legal fees would likely exceed the ticket amount. Pay online at toronto.ca to close it out quickly.';
                    cssClass = 'verdict-pay';
                    showCTA = false;
                } else {
                    badge = 'Contest It Yourself';
                    headline = 'You can fight this without a lawyer';
                    detail = 'Request a trial by mail at your local courthouse within 15 days of receiving the ticket. Use the Dispute Script Builder on the Services tab to write your case. No lawyer needed.';
                    cssClass = 'verdict-contest';
                    showCTA = false;
                }

                statusEl.className = 'scan-status done';
                statusEl.textContent = 'Ticket analysed!';

                document.getElementById('legalVerdictBadge').textContent = badge;
                document.getElementById('legalVerdictHeadline').textContent = headline;
                document.getElementById('legalVerdictDetail').textContent = detail;

                var fineEl = document.getElementById('legalVerdictFine');
                if (fineAmount > 0) {
                    fineEl.textContent = 'Detected fine: $' + fineAmount.toFixed(2);
                    fineEl.style.display = 'inline-block';
                } else {
                    fineEl.style.display = 'none';
                }

                var ctaEl = document.getElementById('legalVerdictCTA');
                ctaEl.style.display = showCTA ? 'flex' : 'none';

                verdictEl.className = 'legal-verdict show ' + cssClass;

                if (document.getElementById('advisorInput')) {
                    document.getElementById('advisorInput').value = rawText;
                }
            } catch (err) {
                statusEl.className = 'scan-status error';
                statusEl.textContent = 'Scan failed. Try a clearer, well-lit photo.';
            }
            event.target.value = '';
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
        if (params.get('saved') === 'reminder') showToast('Reminder added');
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
            if (!text || chatBusy) return;
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
    reporter_name = (request.form.get('reporter_name', '') or 'Anonymous').strip()
    reporter_color = (request.form.get('reporter_color', '') or '#0A84FF').strip()
    if issue_type and lat and lng:
        try:
            reports_data.append({
                "type": issue_type,
                "lat": float(lat),
                "lng": float(lng),
                "status": "Community Report",
                "name": reporter_name,
                "color": reporter_color
            })
        except (ValueError, TypeError):
            pass
    return redirect('/?reported=1')

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
            "Keep answers concise, practical, and friendly. When uncertain, say so and suggest "
            "the user consult a professional. Do not give legal advice for criminal charges."
        )

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
