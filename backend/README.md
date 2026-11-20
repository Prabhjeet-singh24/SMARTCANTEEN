# Smart Canteen – Backend

Flask + SQLite REST API. See the full documentation (endpoints, security, troubleshooting) in the main `README.md`.

```
pip install -r backend/requirements.txt
copy .env.example .env      (then edit SECRET_KEY / ADMIN_PASSWORD)
python run.py               (creates the database on first start; API on http://127.0.0.1:5000/api)
python -m unittest discover -s backend/tests -v
```
Without the `frontend/` folder next to it the server runs as API only (`/api/health` to check).
