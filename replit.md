# TO Fine Tracker

## Overview
A mobile-friendly Flask web app for managing Toronto traffic fines. Features a dark mode UI with glassmorphism effects and neon accent colors.

## Stack
- Python 3.11
- Flask 3.x
- In-memory data storage

## Structure
- `main.py` - Single-file Flask application with embedded HTML template

## Running
The app runs on port 5000 via `python main.py`.

## Features
- Dashboard with AI ticket scanner, profile, deadline ROI calculator, and fine reminders with due dates
- 24h Deadline Alerts: browser notification permission banner at top of Dashboard; requests Notification API permission, shows green "Active" state when granted, sends confirmation notification
- AI Ticket Scanner: uses Tesseract.js OCR (v4.0.1 from CDN) to photograph physical parking tickets and extract Ontario plate numbers (ABCD 123 format) and dates; auto-fills the Add Fine Reminder form
- Deadline ROI Calculator: enter a base fine amount and see how Toronto late fees escalate ($15.39 address search + $32.10 late payment + $32.10 plate denial = $79.59 total penalties)
- Reminders show status badges (Upcoming, Today, Overdue)
- Calendar integration: Google Calendar link (opens pre-filled event) and .ics file download (works with Apple Calendar, Outlook, etc.)
- .ics files include VALARM reminders (1 day before and day-of)
- Services tab with 6 sections: Parking Violations, Speed & Red Light Cameras, Court Services, Street Parking Checker, Vehicle Towed finder, Dispute Script Builder
- Street Parking Checker: dropdown for 4 Toronto areas (Queen St W, Bloor/Yorkville, Kensington, Front St) showing rates, enforcement hours, free parking times, rush hour warnings, plus Green P app link
- Dispute Script Builder: 4 pre-written legal dispute templates (hidden sign, wrong data, broken meter, valid permit) with copy-to-clipboard
- Vehicle Towed link: direct link to Toronto Police towing services
- Hotspots tab with GPS Guardian Proximity Scanner (live geolocation tracking detects $200 bike lane and $100 fire hydrant fine zones, red pulsing alert banner on proximity) and Leaflet.js interactive map showing simulated Toronto enforcement hotspots as a heatmap (uses leaflet.heat plugin, dark CartoDB basemap) plus bike lane polyline and hydrant markers
- All external links open in new tabs to official Toronto portals
- Guide tab: step-by-step walkthrough of all app features, shown as the default landing page with a "Get Started" button
- 4-tab floating pill-shaped bottom navigation bar (Guide, Dashboard, Services, Hotspots) with Font Awesome icons
- Toast notifications on save/delete actions
- Dark mode glassmorphism design: backdrop-filter blur on cards, gradient header, box-shadows, staggered entrance animations, cubic-bezier button transitions
- Font Awesome 6.5.1 icons throughout (nav bar, card labels, buttons)
- Pulsing red "Find Towed Car" danger button with urgency animation
- Solid-color action buttons (green for Green P, red for towed car, gradient for scan/save)
- prefers-reduced-motion accessibility support
- DM Sans + JetBrains Mono typography, gradient top borders on cards

## External Dependencies (CDN)
- Leaflet.js 1.9.4 (map rendering)
- leaflet.heat (heatmap layer plugin)
- Tesseract.js 4.0.1 (client-side OCR for ticket scanning)
- Font Awesome 6.5.1 (icon library)
- Google Fonts (DM Sans, JetBrains Mono)

## Routes
- `GET /` - Main page
- `POST /save-profile` - Save name and license plate
- `POST /add-reminder` - Add a fine reminder
- `POST /delete-reminder` - Delete a reminder by index
- `GET /calendar/ics/<index>` - Download .ics calendar file for a reminder
