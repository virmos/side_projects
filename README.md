## Orders Service (FastAPI)

Simple FastAPI backend to manage customer orders (order header + order lines).

### Quickstart

1. Create virtualenv and install dependencies

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash/PowerShell
pip install -r requirements.txt
```

2. Run the server

```bash
uvicorn api.app:app --reload
```

3. Open docs at `http://127.0.0.1:8000/docs`.

### Endpoints

- POST `/orders`: Create an order with lines
- GET `/orders/{id}`: Retrieve full order
- GET `/orders`: List orders (skip, limit)
- PUT `/orders/{id}`: Update order (optionally replace lines)
- DELETE `/orders/{id}`: Delete order

### Sample payload

```json
{
  "customer_id": 456,
  "order_date": "2025-08-05",
  "status": "pending",
  "lines": [
    { "product_id": 1001, "quantity": 2, "unit_price": 25.50 },
    { "product_id": 1002, "quantity": 1, "unit_price": 15.00 }
  ]
}
```

### Security considerations

- SQL Injection: Use SQLAlchemy ORM with bound parameters; never concatenate raw SQL. Pydantic schemas validate and coerce input types.
- Authorization: Example `get_current_user_id` stub plus per-order check to ensure only owners can read/update/delete. Extend for admin roles as needed.
- Validation & Sanitization: Pydantic schemas enforce numeric ranges, date format, and allowed `status` values. Reject invalid inputs with 422.

### Persistence

- Default DB is SQLite `orders.db`. Override with `DATABASE_URL` env var (e.g., `postgresql+psycopg2://user:pass@host/db`).


