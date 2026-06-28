# Route Reference

SmartTex Inventory is a server-rendered Flask application (not a JSON API), so these are page/form routes rather than a REST API — useful if you're extending the app, writing integration tests, or building automation against it. All routes except `/login`, `/register`, `/forgot-password`, and `/reset-password/<token>` require an authenticated session.

The one true JSON endpoint is the AI Assistant's `/ai/chat/ask`, documented separately below.

## Authentication

| Method | Route | Description |
|---|---|---|
| GET, POST | `/login` | Sign in |
| GET, POST | `/register` | Create account (choose role) |
| GET | `/logout` | End session |
| GET, POST | `/forgot-password` | Request password reset link |
| GET, POST | `/reset-password/<token>` | Set new password via emailed/generated token |
| GET, POST | `/change-password` | Change password while logged in |
| GET, POST | `/profile` | View/edit own profile |

## Dashboard

| Method | Route | Description |
|---|---|---|
| GET | `/` | Main dashboard — KPIs and charts |

## Fabrics (Inventory)

| Method | Route | Description |
|---|---|---|
| GET | `/fabrics/` | List, search, filter fabrics |
| GET, POST | `/fabrics/add` | Add new fabric *(Admin, Inventory Manager)* |
| GET | `/fabrics/<id>` | Fabric detail, movement history, QR/barcode |
| GET, POST | `/fabrics/<id>/edit` | Edit fabric specs/pricing *(Admin, Inventory Manager)* |
| POST | `/fabrics/<id>/delete` | Deactivate fabric *(Admin)* |
| POST | `/fabrics/<id>/adjust` | Record stock movement (IN/OUT/ADJUSTMENT/DAMAGE) *(Admin, Inventory Manager)* |
| POST | `/fabrics/<id>/transfer` | Transfer stock to another warehouse *(Admin, Inventory Manager)* |
| POST | `/fabrics/<id>/restore` | Restore a deleted fabric back to active *(Admin)* |

## Suppliers

| Method | Route | Description |
|---|---|---|
| GET | `/suppliers/` | List suppliers |
| GET, POST | `/suppliers/add` | Add supplier *(Admin, Inventory Manager)* |
| GET | `/suppliers/<id>` | Supplier detail, purchase history |
| GET, POST | `/suppliers/<id>/edit` | Edit supplier *(Admin, Inventory Manager)* |
| POST | `/suppliers/<id>/delete` | Deactivate supplier *(Admin)* |
| POST | `/suppliers/<id>/restore` | Restore a deleted supplier back to active *(Admin)* |
| GET, POST | `/suppliers/<id>/purchase-orders/new` | Create purchase order *(Admin, Inventory Manager)* |
| GET | `/suppliers/purchase-orders/<po_id>` | Purchase order detail |
| POST | `/suppliers/purchase-orders/<po_id>/status` | Update PO status; "Received" auto-adds stock *(Admin, Inventory Manager)* |
| POST | `/suppliers/purchase-orders/<po_id>/payment` | Record a payment *(Admin, Inventory Manager)* |

## Warehouses

| Method | Route | Description |
|---|---|---|
| GET | `/warehouses/` | List warehouses with utilization |
| GET, POST | `/warehouses/add` | Add warehouse *(Admin, Inventory Manager)* |
| GET | `/warehouses/<id>` | Warehouse detail, fabrics stored |
| GET, POST | `/warehouses/<id>/edit` | Edit warehouse *(Admin, Inventory Manager)* |
| POST | `/warehouses/<id>/delete` | Deactivate warehouse *(Admin)* |
| POST | `/warehouses/<id>/restore` | Restore a deleted warehouse back to active *(Admin)* |

## Production

| Method | Route | Description |
|---|---|---|
| GET | `/production/` | List production orders, filter by status |
| GET, POST | `/production/new` | Create production order; reserves fabric *(Admin, Production Manager)* |
| GET | `/production/<id>` | Production order detail |
| POST | `/production/<id>/update` | Update status/usage/waste; auto-consumes reserved fabric *(Admin, Production Manager)* |

## Workers

| Method | Route | Description |
|---|---|---|
| GET | `/workers/` | List workers, filter by department |
| GET, POST | `/workers/add` | Add worker *(Admin, Production Manager)* |
| GET | `/workers/<id>` | Worker detail, attendance, payroll |
| GET, POST | `/workers/<id>/edit` | Edit worker *(Admin, Production Manager)* |
| POST | `/workers/<id>/delete` | Deactivate worker *(Admin)* |
| POST | `/workers/<id>/restore` | Restore a deleted worker back to active *(Admin)* |
| POST | `/workers/<id>/attendance` | Mark/update attendance for a date *(Admin, Production Manager)* |
| POST | `/workers/<id>/payroll` | Generate payroll for a month *(Admin, Production Manager)* |
| POST | `/workers/payroll/<payroll_id>/mark-paid` | Mark a payroll record as paid *(Admin, Production Manager)* |

## Customers

| Method | Route | Description |
|---|---|---|
| GET | `/customers/` | List customers |
| GET, POST | `/customers/add` | Add customer *(Admin, Sales Manager)* |
| GET | `/customers/<id>` | Customer detail, purchase history |
| GET, POST | `/customers/<id>/edit` | Edit customer *(Admin, Sales Manager)* |
| POST | `/customers/<id>/delete` | Deactivate customer *(Admin)* |
| POST | `/customers/<id>/restore` | Restore a deleted customer back to active *(Admin)* |

## Sales

| Method | Route | Description |
|---|---|---|
| GET | `/sales/` | List sales orders (paginated) |
| GET, POST | `/sales/new` | Create invoice; validates & deducts stock *(Admin, Sales Manager)* |
| GET | `/sales/<id>` | Invoice detail |
| GET | `/sales/<id>/pdf` | Download invoice as PDF |
| POST | `/sales/<id>/payment` | Record a payment *(Admin, Sales Manager)* |

## Reports

| Method | Route | Description |
|---|---|---|
| GET | `/reports/` | Report hub |
| GET | `/reports/<type>` | View report on-screen. `<type>` ∈ `inventory, suppliers, warehouses, sales, production, employees, financial` |
| GET | `/reports/<type>/export/<fmt>` | Export report. `<fmt>` ∈ `pdf, excel, csv` |

## Notifications

| Method | Route | Description |
|---|---|---|
| GET | `/notifications/` | List own notifications |
| POST | `/notifications/<id>/read` | Mark one as read |
| POST | `/notifications/mark-all-read` | Mark all as read |

## Team Chat

| Method | Route | Description |
|---|---|---|
| GET | `/team-chat/` | Shared channel UI — all messages, newest at bottom |
| POST | `/team-chat/post` | **JSON-returning form endpoint.** Body: `body=<text>`. Returns `{"ok": true, "message": {...}}` |
| GET | `/team-chat/poll?after_id=<id>` | **JSON endpoint.** Returns messages with `id > after_id`, used for 3-second auto-refresh |

## History

| Method | Route | Description |
|---|---|---|
| GET | `/history/` | All deleted items across every module, with Restore actions *(Admin only)* |
| GET | `/history/?type=<key>` | Filter by type. `<key>` ∈ `fabrics, suppliers, warehouses, workers, customers` |

Restoring uses each module's own `/restore` route (see above) — the History page is a read view that links into them.

## Audit Logs

| Method | Route | Description |
|---|---|---|
| GET | `/audit/` | List system audit logs, filter by module *(Admin only)* |

## AI Assistant

| Method | Route | Description |
|---|---|---|
| GET | `/ai/chat` | Chat UI |
| POST | `/ai/chat/ask` | **JSON endpoint.** Body: `{"question": "..."}` → Returns `{"answer": str, "data": object\|null}` |
| GET | `/ai/insights` | Forecasting, reorder, anomaly detection, supplier ranking dashboard |

### Example: calling the chat endpoint programmatically

```bash
curl -X POST http://localhost:5000/ai/chat/ask \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token from a logged-in session>" \
  --cookie "session=<your session cookie>" \
  -d '{"question": "Which fabric is low in stock?"}'
```

```json
{
  "answer": "2 fabric(s) are low in stock:\n• Soft Polyester Blend (FB-0003): 31.5m available, threshold 100m\n• Chiffon Georgette (FB-0008): 30.0m available, threshold 80m",
  "data": [
    {"fabric_code": "FB-0003", "name": "Soft Polyester Blend", "available": 31.5, "threshold": 100.0},
    {"fabric_code": "FB-0008", "name": "Chiffon Georgette", "available": 30.0, "threshold": 80.0}
  ]
}
```

Supported question patterns (case-insensitive substring matching): stock availability, low stock, supplier performance, monthly/total sales summary, damaged stock. Unmatched questions return a helpful suggestion list rather than a guess.
