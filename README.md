# Automatic Resume Builder

Professional Flask web application for creating, editing, saving and exporting resumes.

## Important: GitHub is for the source code
GitHub Pages cannot run a Flask/Python backend. Upload this repository to GitHub, then deploy the same repository to a Python hosting service such as Render.

## Run locally

### Windows PowerShell / CMD
```bash
py -m pip install -r requirements.txt
py app.py
```
Open: http://127.0.0.1:5000

### Linux / macOS
```bash
python3 -m pip install -r requirements.txt
python3 app.py
```
Open: http://127.0.0.1:5000

## Deploy on Render
1. Push this project to GitHub.
2. In Render, create **New + Web Service**.
3. Connect your GitHub repository.
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Create/deploy the service.
7. Open the Render URL.

A `render.yaml` is included for configuration.

## Features
- Sign up / Login / Logout
- User-specific resume history
- Create, edit, preview and delete resumes
- PDF download
- Dashboard user/resume statistics
- SQLite local database

## Note about production data
SQLite is included for the college/demo project. On some cloud hosts, local files can be reset during redeploys/restarts. For permanent multi-user production data, use a managed PostgreSQL database and persistent file/email storage.

Set `SECRET_KEY` as an environment variable in production.
