# KcartBot Setup Instructions

## Prerequisites

- **Python** 3.11 or 3.12 (not 3.13)
- **Node.js** 18 or higher
- **Docker** and Docker Compose
- **Google Gemini API Key** - [Get it here](https://makersuite.google.com/app/apikey)
- **Runware API Key** (Free) - [Get it here](https://runware.ai/)

**Make sure you are inside KcartBot-chipchip- directory**

---

## Setup Steps

```bash
# Make sure you are inside KcartBot-chipchip- directory
# 1. Deactivate any active virtual environment
deactivate 2>/dev/null || true

# 2. Check if you have Python 3.12 (Python 3.11 also works)
python3.12 --version

# If not found, install Python 3.11 or 3.12:

# macOS:
brew install python@3.12


# 3. Recreate virtual environment with Python 3.12
cd backend
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Restart Docker
cd ..
docker-compose down -v
docker-compose up -d

# 6. Setup environment (add your API keys)
cd backend

# Create .env file with your API keys (get them from the links above)
nano .env

# Add these lines (replace with your actual API keys):
# GOOGLE_API_KEY='your_google_gemini_api_key_here'
# RUNWARE_API_KEY='your_runware_api_key_here'
# Save and exit (Ctrl+O, Enter, Ctrl+X)

# 7. Setup database
# Remove old SQLite database if it exists
rm -f db.sqlite3

python manage.py makemigrations
python manage.py migrate

# Load sample data (ignore timezone warnings, just wait until it finishes)
python scripts/data_loading/load_relational_data.py
python scripts/data_loading/load_vector_data.py
```

---

## Starting the Application

Follow the following to start the app:

**Terminal 1 - Start Backend:**
```bash
# Make sure you're in backend/ directory with venv activated
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

**Terminal 2 - Start Frontend:**

Open a new terminal and make sure you're in KcartBot-chipchip- directory:

```bash
cd frontend
npm install
npm run dev
```

**Access the app:** http://localhost:5173

