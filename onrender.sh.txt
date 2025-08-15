#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
# Render automatically uses pip and requirements.txt if available.
# This line ensures it's explicitly run.
pip install -r requirements.txt

# Run database migrations
# This applies any changes from your Django models to the PostgreSQL database.
python manage.py migrate

# Collect static files
# This gathers all your CSS, JavaScript, and image files into a single directory
# so WhiteNoise can serve them efficiently in production.
# --noinput: Prevents prompts, making it run automatically.
# --clear: Clears existing static files before collecting new ones.
python manage.py collectstatic --noinput --clear
