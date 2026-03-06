# Toronto Fine Tracker

## Overview
A Flask web application for tracking Toronto parking/traffic fines and setting payment reminders.

## Stack
- Python 3.11
- Flask 3.x
- In-memory data storage (list)

## Structure
- `main.py` - Single-file Flask application with embedded HTML template

## Running
The app runs on port 5000 via `python main.py`.

## Features
- Add ticket reminders with name, license plate, ticket number, and due date
- View saved reminders on the dashboard
- Link to official Toronto payment portal
