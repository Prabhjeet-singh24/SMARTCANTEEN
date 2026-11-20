import os

# Render provides the port in the PORT environment variable (typically 10000 on Render)
port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"

workers = 2
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
