# For gunicorn
# Run command: gunicorn app:app -c g_config.py

bind = "0.0.0.0:8000"
workers = 5