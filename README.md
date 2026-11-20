# Smart Canteen Management System

A complete canteen ordering system: customers browse the menu, order food and track their orders; canteen staff manage the menu, orders, customers and sales reports from an admin dashboard.

* **Frontend:** HTML, CSS, vanilla JavaScript (no frameworks, no build step, no CDN – works offline)
* **Backend:** Python Flask REST API (JSON)
* **Database:** SQLite (a single file, created automatically)

---

## 1. Features

**Customer**
* Home page with personalised greeting, live statistics (chefs, menu items, customer rating, average preparation time), categories, popular dishes, offers and footer
* Menu with search, category filter, veg / non-veg filter, price sorting and "available only" filter
* Cart (quantity +/-, remove, subtotal, tax, total) – prices and availability are re-checked against the server
* Checkout (student ID, phone, Dine-in / Takeaway, **Cash** or **Demo UPI**) – creates a real database order
* Orders page with status filter, full order details, status timeline, cancel (while Pending) and star rating (after Completed). Auto-refreshes every 20 s
* Profile: edit details, change password, logout
* Registration / login with validation, hashed passwords and server-side sessions

**Admin** (separate login at `/admin/login.html`)
* Dashboard: total orders, revenue, customers, menu items, pending and completed orders, recent orders, status breakdown, top sellers
* Menu management: add / edit / delete items, image upload, change prices, enable/disable availability, manage categories
* Order management: view all orders, details, search, filter by status, update status (guided workflow) and cancel
* Customer management: search, details, order history, disable/enable accounts, delete customers without orders
* Reports: daily (14 days), weekly (8 weeks), monthly (12 months) revenue charts, most popular items, total sales

## 2. Technology stack
| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (ES2017+, `fetch`) |
| Backend | Python 3.9+, Flask 3 |
| Database | SQLite 3 (parameterised queries only) |
| Passwords | PBKDF2-SHA256 (Werkzeug) |

## 3. Folder structure
```
smart-canteen/
├── frontend/                 # static site (HTML/CSS/JS/images)
│   ├── index.html login.html register.html menu.html cart.html
│   ├── checkout.html orders.html profile.html
│   ├── admin/                # login, dashboard, manage-menu, manage-orders, manage-users, reports
│   ├── css/                  # style.css auth.css dashboard.css responsive.css
│   ├── js/                   # config.js main.js auth.js menu.js cart.js orders.js admin.js
│   └── assets/images/        # bundled food illustrations, logo, hero
├── backend/
│   ├── app.py                # Flask app factory
│   ├── config.py             # settings (environment variables / .env)
│   ├── database.py           # SQLite connection + schema creation
│   ├── models.py             # schema, constants, serialisers
│   ├── utils.py              # validation, auth decorators, uploads, rate limiting
│   ├── routes/               # auth.py menu.py orders.py admin.py
│   ├── tests/test_api.py     # 27 automated API tests
│   ├── uploads/              # uploaded food images
│   └── requirements.txt
├── database/init_db.py       # creates tables, sample menu, admin account
├── tools/make_images.py      # (optional) regenerates the bundled SVG images
├── .env.example  .gitignore  README.md
├── run.py                    # starts the server
└── start-windows.bat         # one-click setup + start for Windows
```
`config.js`, `utils.py`, `start-windows.bat` and the tests are small additions to the requested layout.

## 4. Installation (Windows)

You need **Python 3.9 or newer** from <https://www.python.org/downloads/> (tick *“Add python.exe to PATH”* in the installer).

**Quick way:** double-click `start-windows.bat`. It creates `.env`, a virtual environment, installs Flask and starts the server. Skip to section 7.

**Manual way** (Command Prompt, inside the project folder):
```bat
py -m venv venv
venv\Scripts\activate
pip install -r backend\requirements.txt
copy .env.example .env
```
(PowerShell: use `venv\Scripts\Activate.ps1`; if scripts are blocked run `Set-ExecutionPolicy -Scope Process RemoteSigned` first.)
macOS / Linux: `python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt && cp .env.example .env`.

## 5. Configure `.env` (safely)
Open `.env` and set at least:
```
SECRET_KEY=<paste output of: python -c "import secrets; print(secrets.token_hex(32))">
ADMIN_EMAIL=admin@smartcanteen.local
ADMIN_PASSWORD=<your own strong password>
```
* `.env` is listed in `.gitignore` – **never commit it**.
* If `SECRET_KEY` is empty a random key is generated once into `backend/instance/secret_key` (development only).
* Other options: `PORT`, `HOST`, `TAX_RATE` (default 0.05), `CANTEEN_CHEFS`, `SESSION_COOKIE_SECURE`, `CORS_ORIGINS` – see `.env.example`.

## 6. Initialise the database
```bat
python database/init_db.py            :: tables + sample menu + admin account
python database/init_db.py --demo     :: also adds 3 demo customers and ~45 sample orders
```
`python run.py` does this automatically on start-up, so this step is optional. It is safe to run repeatedly: the sample menu is only added to an empty database and the admin account only if no admin exists.

**Admin credentials:** the account is created from `ADMIN_EMAIL` / `ADMIN_PASSWORD`.
* If you copied `.env.example` unchanged, the demo login is `admin@smartcanteen.local` / `ChangeMe@123` — **change it before anyone else can reach the site** (edit `.env` *before the first start*; the admin is only created once. To change it later, log in and use your admin profile via the API `POST /api/change-password`, or delete `database/canteen.db` and start again to recreate).
* If `ADMIN_PASSWORD` is empty, a random password is generated and printed **once** in the console.
* Demo customers (only with `--demo`): `demo.student@smartcanteen.local` / `Demo@12345` – use for testing only.

## 7. Start the application
```bat
python run.py
```
Open:
* Customer site: <http://127.0.0.1:5000/>
* Admin login: <http://127.0.0.1:5000/admin/login.html>
* API health check: <http://127.0.0.1:5000/api/health>

Flask serves both the API and the `frontend/` folder on the same origin, which is the simplest setup (no CORS issues).

### Running frontend and backend separately
1. Start the backend: `python run.py` (API on port 5000).
2. Serve the `frontend` folder from any static server **over http**, e.g. `cd frontend && python -m http.server 5500`, then open <http://localhost:5500/>.
3. `frontend/js/config.js` points to `http://<same host name>:5000`. If your API is elsewhere put its URL into `FIXED_API_BASE`, and add the frontend origin to `CORS_ORIGINS` in `.env` (localhost / 127.0.0.1 on any port are allowed by default).
4. Use the same host name for both (`localhost` with `localhost`, or `127.0.0.1` with `127.0.0.1`) – session cookies are not shared between different host names. Opening the HTML files directly via `file://` is **not supported** (browsers do not send login cookies from `file://`).

## 8. API documentation
All endpoints live under `/api`, use JSON (menu create/update also accept `multipart/form-data` for the image) and return `{"error": "...", "details": {field: message}}` with a suitable HTTP status on failure (400 validation, 401 not logged in, 403 forbidden, 404 not found, 409 conflict, 413 too large, 429 too many login attempts).

**Authentication**
| Method & path | Access | Description |
|---|---|---|
| POST `/register` | public | `name, email, phone, student_id, password, confirm_password` → creates customer, logs in (201) |
| POST `/login` | public | `email, password, role?` (`"admin"` for the admin page). Sets session cookie |
| POST `/logout` | any | Ends the session |
| GET `/profile` | logged in | Current user |
| PUT `/profile` | logged in | Update `name, email, phone, student_id` |
| POST `/change-password` | logged in | `current_password, new_password, confirm_password` |

**Menu**
| Method & path | Access | Description |
|---|---|---|
| GET `/menu` | public | Query: `q, category, veg=veg|nonveg, available=1, popular=1, sort=name|popular|price_asc|price_desc, limit`. Returns `items`, `count`, `tax_rate` |
| GET `/menu/<id>` | public | One item |
| POST `/menu` | admin | `name, description, price, category_id, prep_time, is_veg, is_available, is_popular, image` |
| PUT `/menu/<id>` | admin | Any subset of the fields above (+ `remove_image`) |
| DELETE `/menu/<id>` | admin | Delete (past orders keep their item names and prices) |
| GET `/categories` | public | Categories with item counts |
| POST / PUT / DELETE `/categories[/<id>]` | admin | Manage categories (delete only when empty) |
| GET `/stats` | public | Chefs, menu item count, average rating, average preparation minutes |

**Orders**
| Method & path | Access | Description |
|---|---|---|
| POST `/orders` | customer | `items:[{menu_item_id, quantity}], order_type (Dine-in/Takeaway), payment_method (Cash/Demo UPI), customer_name, student_id, phone, upi_id (Demo UPI only), notes`. Prices are always taken from the database |
| GET `/orders` | logged in | Customer: own orders. Admin: all orders, filters `status`, `q` (order no., name, student ID, phone) |
| GET `/orders/<id>` | owner / admin | Order with items |
| PUT `/orders/<id>/status` | admin; customer may cancel own *Pending* order | `status` |
| POST `/orders/<id>/rating` | customer | `rating` 1–5, only for Completed orders, once |

Status workflow: Pending → Confirmed → Preparing → Ready for Pickup → Completed; any open status can go to Cancelled. Completed and Cancelled are final.

**Admin**
| Method & path | Description |
|---|---|
| GET `/admin/dashboard` | KPIs, status breakdown, recent orders, top sellers |
| GET `/admin/customers?q=` | Customers with order count and total spent |
| GET `/admin/customers/<id>` | Customer details + order history |
| PUT `/admin/customers/<id>` | `{"is_active": true/false}` – disable/enable account |
| DELETE `/admin/customers/<id>` | Only when the customer has no orders |
| GET `/admin/reports` | daily / weekly / monthly revenue, popular items, total sales |

## 9. Database
Tables: `users`, `categories`, `menu_items`, `orders`, `order_items` (primary keys, foreign keys with `PRAGMA foreign_keys=ON`, `created_at` timestamps, CHECK constraints). Order lines store a snapshot of item name and price, so editing or deleting a menu item never changes history. Timestamps are stored in the server's local time.

## 10. Security measures
* Passwords hashed with PBKDF2-SHA256; never returned by the API
* Server-side validation of every input; parameterised SQL only; `LIKE` wildcards escaped
* Role-based authorisation (`admin` / `customer`); customers cannot read other customers' orders (404)
* Signed session cookie: `HttpOnly`, `SameSite=Lax`, 8-hour lifetime, optional `Secure`
* Origin check on state-changing requests (CSRF defence in depth), CORS limited to local/allow-listed origins
* Login throttling (5 failed attempts / 10 minutes per IP + e-mail); generic "invalid email or password" message
* Uploads: extension + size (2 MB) + real file-signature check, random file names, SVG not accepted
* Secrets only from environment variables; HTML output escaped in the frontend; strict Content-Security-Policy on pages served by Flask; JSON errors without stack traces

## 11. Testing
```bat
python -m unittest discover -s backend/tests -v
```
27 tests cover registration, login (valid / invalid / lock-out / admin rules), password change, menu loading and filters, menu management and uploads, cart-to-order placement, price tampering, availability, status workflow, privacy between customers, customer management, reports and security headers. The UI was additionally exercised end-to-end in a real browser (Chromium): registration, login, menu filters, cart, checkout, orders, profile, admin menu/orders/customers/reports and mobile layouts.

## 12. Known limitations (documented on purpose)
* **Payments are simulated.** "Demo UPI" only validates the format of a UPI ID and records `Paid (Demo)`; Cash orders become `Paid` when the order is marked Completed. No payment provider is contacted.
* **Special offers** on the home page are informational shortcuts to categories – there is no discount/coupon engine.
* **Chefs count** is a setting (`CANTEEN_CHEFS`), not a database table. **Customer rating** is the average of ratings customers give to completed orders ("New" until the first rating). **Average preparation time** is measured from completed orders of the last 30 days, falling back to menu preparation estimates.
* **Revenue** counts every order that is not Cancelled (tax included).
* The cart is stored in the browser (localStorage) and cleared on logout.
* No e-mail features (password reset by e-mail, receipts) and no real-time push – the orders page polls every 20 s.
* SQLite and Flask's built-in server suit a single canteen / local use. For production use a WSGI server (e.g. waitress), HTTPS and `SESSION_COOKIE_SECURE=true`.

## 13. Troubleshooting
| Problem | Fix |
|---|---|
| `python` is not recognised | Reinstall Python with “Add to PATH”, or use `py` instead of `python` |
| `ModuleNotFoundError: flask` | Activate the venv (`venv\Scripts\activate`) and run `pip install -r backend\requirements.txt` |
| Port 5000 already in use | Set `PORT=5001` in `.env` (when Flask serves the frontend nothing else changes; for a separate frontend also update `FIXED_API_BASE` in `js/config.js`) |
| Page says “Cannot reach the server” | Backend not running, or wrong API address in `js/config.js` |
| Login works but you are logged out immediately (separate frontend) | Use the same host name for frontend and API (`localhost` + `localhost`) and `http://`, not `file://` |
| Forgot admin password | Stop the server, delete `database/canteen.db`, set `ADMIN_PASSWORD` in `.env`, start again (this also deletes all data) |
| Images not showing after upload | Check that `backend/uploads` is writable |
| “Too many failed attempts” | Wait 10 minutes or restart the server |
