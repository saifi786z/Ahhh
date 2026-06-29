#!/bin/bash

echo "🚀 Starting UPI Giveaway 2026 Bot..."
echo "====================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directory if not exists
mkdir -p bot_data

# Start bot
echo "✅ Starting bot..."
python bot.py
