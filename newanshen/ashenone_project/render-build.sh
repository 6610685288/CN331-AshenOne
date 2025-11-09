#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# 1. ติดตั้ง Python dependencies
pip install -r requirements.txt

# 2. Collect static files (รวบรวม Static Files ไปยัง STATIC_ROOT)
python manage.py collectstatic --no-input

# 3. Apply database migrations (รัน migrate)
python manage.py migrate