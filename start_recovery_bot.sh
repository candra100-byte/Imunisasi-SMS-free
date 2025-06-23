
#!/bin/bash

# Startup script for Recovery Bot
# Usage: ./start_recovery_bot.sh

echo "Starting Recovery Bot for Sistem Imunisasi Lombok Tengah..."

# Set environment variables if needed
export FLASK_APP=app.py
export FLASK_ENV=production

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
fi

# Install dependencies if needed
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Dependencies installed"
fi

# Start the recovery bot
echo "Starting recovery bot..."
python3 system_recovery_bot.py

echo "Recovery bot stopped"
