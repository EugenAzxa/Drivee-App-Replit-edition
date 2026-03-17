# DriveSafe TO

## Overview
A mobile-friendly Flask web app for managing Toronto traffic fines. Features an Apple/iOS-native dark mode UI with true black background and clean card design.

## Stack
- Python 3.11
- Flask 3.x
- Gunicorn (production server)
- In-memory data storage

## Structure
- `main.py` - Single-file Flask application with embedded HTML template

## Running
The app runs on port 5000 via `python main.py` (dev) or `gunicorn --bind=0.0.0.0:5000 main:app` (production).

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
- Hotspots tab with GPS Guardian Proximity Scanner (live geolocation tracking detects $200 bike lane and $100 fire hydrant fine zones, red alert banner on proximity), 311 Community Hazard Reporter (4 report types: Broken Meter, Hidden Sign, Pothole, Bike Lane Blocked — GPS-located, stored server-side, shown as blue markers on map), and Leaflet.js interactive map showing simulated Toronto enforcement hotspots as a heatmap (uses leaflet.heat plugin, dark CartoDB basemap) plus bike lane polyline and hydrant markers
- All external links open in new tabs to official Toronto portals
- Guide tab: step-by-step walkthrough of all app features (8 steps), shown as the default landing page with a "Get Started" button
- Legal tab: Toronto traffic defence firm directory (8 real firms: X-Copper, X-COPS, POINTTS, OTT Legal, X-Police, Street Legal, Traffic Ticket Experts, HWY-LAW) with firm type badges, specialty pills, price ranges, "Email Firm" mailto links, and "Visit Website" links; AI Ticket Advisor with rule-based keyword analyser for severity (Minor/Serious/Urgent) and recommendation; lawyer case banner auto-shown on Dashboard after OCR scan if high-severity keywords detected
- 5-tab iOS-style full-width bottom tab bar (Guide, Dashboard, Services, Hotspots, Legal) with Font Awesome icons
- Toast notifications on save/delete actions

## Design System (Apple/iOS Native)
- True black background (#000000)
- iOS dark gray cards (#1C1C1E) — solid, no glassmorphism, no borders
- Apple Electric Blue accent (#0A84FF)
- Apple system font stack: -apple-system, BlinkMacSystemFont, SF Pro Text
- JetBrains Mono for ticket numbers and plates
- Solid-color buttons (no gradients) with opacity 0.8 active state
- Full-width bottom nav bar (flush to bottom, blur backdrop, 0.5px top border)
- 12px/16px border-radius, no card borders, 4px-24px box-shadows
- prefers-reduced-motion accessibility support
- Color palette: Blue #0A84FF, Purple #BF5AF2, Teal #64D2FF, Rose #FF453A, Amber #FFD60A, Green #30D158, Orange #FF9F0A

## External Dependencies (CDN)
- Leaflet.js 1.9.4 (map rendering)
- leaflet.heat (heatmap layer plugin)
- Tesseract.js 4.0.1 (client-side OCR for ticket scanning)
- Font Awesome 6.5.1 (icon library)
- Google Fonts (JetBrains Mono)

## Routes
- `GET /` - Main page
- `POST /save-profile` - Save name and license plate
- `POST /add-reminder` - Add a fine reminder
- `POST /delete-reminder` - Delete a reminder by index
- `GET /calendar/ics/<index>` - Download .ics calendar file for a reminder
- `POST /report_311` - Submit a community hazard report (type, lat, lng)
