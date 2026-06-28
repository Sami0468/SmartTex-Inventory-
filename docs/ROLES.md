# Roles & Permissions

SmartTex Inventory uses role-based access control (RBAC) with four roles. **Admin** always has full access to every action regardless of the table below — the matrix shows the *additional* roles permitted for each action.

| Module / Action | Admin | Inventory Manager | Production Manager | Sales Manager |
|---|:---:|:---:|:---:|:---:|
| **Dashboard** — view | ✅ | ✅ | ✅ | ✅ |
| **AI Assistant** — use chat & insights | ✅ | ✅ | ✅ | ✅ |
| **Fabrics** — view, search | ✅ | ✅ | ✅ | ✅ |
| **Fabrics** — add / edit / adjust stock / transfer | ✅ | ✅ | — | — |
| **Fabrics** — delete (deactivate) | ✅ | — | — | — |
| **Warehouses** — view | ✅ | ✅ | ✅ | ✅ |
| **Warehouses** — add / edit | ✅ | ✅ | — | — |
| **Warehouses** — delete | ✅ | — | — | — |
| **Suppliers** — view | ✅ | ✅ | ✅ | ✅ |
| **Suppliers** — add / edit / purchase orders / payments | ✅ | ✅ | — | — |
| **Suppliers** — delete | ✅ | — | — | — |
| **Production Orders** — view | ✅ | ✅ | ✅ | ✅ |
| **Production Orders** — create / update status | ✅ | — | ✅ | — |
| **Workers** — view | ✅ | ✅ | ✅ | ✅ |
| **Workers** — add / edit / attendance / payroll | ✅ | — | ✅ | — |
| **Workers** — delete | ✅ | — | — | — |
| **Customers** — view | ✅ | ✅ | ✅ | ✅ |
| **Customers** — add / edit | ✅ | — | — | ✅ |
| **Customers** — delete | ✅ | — | — | — |
| **Sales / Invoices** — view | ✅ | ✅ | ✅ | ✅ |
| **Sales / Invoices** — create / record payment | ✅ | — | — | ✅ |
| **Reports** — view & export (all types) | ✅ | ✅ | ✅ | ✅ |
| **Notifications** — view own | ✅ | ✅ | ✅ | ✅ |
| **Team Chat** — read & post in shared channel | ✅ | ✅ | ✅ | ✅ |
| **History** — view & restore deleted items | ✅ | — | — | — |
| **Audit Logs** — view | ✅ | — | — | — |

## Design Rationale

- **Viewing is broad, editing is narrow.** Every role can see the full picture (dashboard, reports, all module listings) since cross-functional visibility helps a factory run smoothly — a Sales Manager benefits from seeing live stock, and a Production Manager benefits from seeing sales demand.
- **Deletion is Admin-only everywhere.** Deactivating a fabric, supplier, warehouse, customer, or worker affects historical reporting and financial records, so it's reserved for the Admin role.
- **Audit Logs are Admin-only.** This is the accountability layer of the system; if other roles could view it, the value as an independent record is weakened.
- **Deletion is reversible.** Every delete is a soft-delete: the record is hidden from active lists and dropdowns everywhere, but stays fully intact — including in any past invoice, purchase order, or production order that references it — and can be restored from the **History** page (Admin only) at any time. Nothing is ever permanently erased through the UI.
- **Each Manager role owns their domain end-to-end.** Inventory Manager controls fabric/supplier/warehouse data; Production Manager controls production orders, workers, attendance, and payroll; Sales Manager controls customers and sales invoices.

## Changing a User's Role

Currently, role is set at registration (`Register` page) and can be amended directly in the database by an Admin:

```sql
UPDATE users SET role = 'Production Manager' WHERE username = 'someuser';
```

A self-service "manage users" admin panel is a natural extension point — see `app/blueprints/auth/routes.py` for where to add it.
