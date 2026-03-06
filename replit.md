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
- Dashboard with profile (name + license plate), deadline ROI calculator, and fine reminders with due dates
- Deadline ROI Calculator: enter a base fine amount and see how Toronto late fees escalate ($15.39 address search + $32.10 late payment + $32.10 plate denial = $79.59 total penalties)
- Reminders show status badges (Upcoming, Today, Overdue)
- Calendar integration: Google Calendar link (opens pre-filled event) and .ics file download (works with Apple Calendar, Outlook, etc.)
- .ics files include VALARM reminders (1 day before and day-of)
- Services tab with 3 sections: Parking Violations, Speed & Red Light Cameras, Court Services
- Hotspots tab with Leaflet.js interactive map showing simulated Toronto enforcement hotspots as a heatmap (uses leaflet.heat plugin, dark CartoDB basemap)
- All external links open in new tabs to official Toronto portals
- 3-tab bottom navigation bar (Dashboard, Services, Hotspots)
- Toast notifications on save/delete actions
- Refined dark mode with vibrant color palette (DM Sans + JetBrains Mono typography), layered surface cards, gradient top borders, SVG icons

## External Dependencies (CDN)
- Leaflet.js 1.9.4 (map rendering)
- leaflet.heat (heatmap layer plugin)
- Google Fonts (DM Sans, JetBrains Mono)

## Routes
- `GET /` - Main page
- `POST /save-profile` - Save name and license plate
- `POST /add-reminder` - Add a fine reminder
- `POST /delete-reminder` - Delete a reminder by index
- `GET /calendar/ics/<index>` - Download .ics calendar file for a reminder
