# AgriKonnect Django Project Changes

This rebuilt backend keeps your current apps and database structure, but upgrades the farmer project/batch/profit API used by the Flutter app.

## Improved farmer project APIs

Existing endpoints still work:

- `GET/POST /api/farmers/projects/`
- `GET/PUT/PATCH/DELETE /api/farmers/projects/{id}/`
- `GET/POST /api/farmers/batches/`
- `GET/POST /api/farmers/project-inputs/`
- `GET/POST /api/farmers/project-revenues/`
- `GET/POST /api/farmers/expenses/`
- `GET/POST /api/farmers/sales/`

## New/updated endpoints

- `GET /api/farmers/projects/performance/`
  - Mobile friendly project cards with farm name, status labels, revenue, costs, profit, ROI, margin, batch counts and progress.

- `GET /api/farmers/projects/{id}/report/`
  - Full project report: project details, batches, recent expenses, recent sales, recent inputs, recent revenues, cost categories, monthly sales and monthly inputs.

- `POST /api/farmers/projects/{id}/close/`
  - Marks a project as completed.

- `GET /api/farmers/batches/performance/`
  - Mobile friendly batch cards with stock, harvested quantity, sold quantity, revenue, expenses and profit.

- `GET /api/farmers/batches/{id}/profit-summary/`
  - Detailed batch profit report with ROI and profit margin.

- `GET /api/farmers/analytics/profit/`
  - Whole-farm profit dashboard: total revenue, total cost, net profit, ROI, profit margin, top projects and top batches.

- `GET /api/farmers/analytics/profit-trend/`
  - Monthly revenue/cost/profit trend.

- `GET /api/farmers/analytics/profit-trend/?project=<project_id>`
  - Monthly trend for one project.

## Query filters added

Projects:

- `?status=active`
- `?project_type=poultry`
- `?farm=<farm_id>`
- `?q=broilers`

Batches:

- `?status=active`
- `?project=<project_id>`
- `?farm=<farm_id>`
- `?q=batch`

## Files changed

- `farmers_api/serializers.py`
- `farmers_api/views.py`
- `farmers_api/urls.py`

## Deployment

On the server:

```bash
cd /var/www/agrikonnect
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
sudo systemctl restart gunicorn
sudo nginx -t && sudo systemctl reload nginx
```

No new database migration is required because this update uses your existing project, batch, expense, input and revenue models.
