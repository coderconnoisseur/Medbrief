# Project Setup Guide

This project runs a FastAPI application. Follow the steps below to get started.

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>

2.**Create and activate a virtual environment**

On Windows (PowerShell):
```bash
python -m venv venv
.\venv\Scripts\activate
```
On macOS/Linux:

    python3 -m venv venv
    source venv/bin/activate

3. **Install dependencies**
```bash
pip install -r requirements.txt
```
4. **Run the application**
```bash
uvicorn app.main:app --reload
```
The app will be available at:
👉 http://127.0.0.1:8000
