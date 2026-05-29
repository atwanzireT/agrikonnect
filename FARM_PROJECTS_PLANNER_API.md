# AgriKonnect Farmer Project Planner API

This upgrade lets a farmer manage projects under each farm, for example poultry, cattle, goats, crops, fish farming, or beekeeping. It also lets the farmer plan activities, track input costs, record project revenue, and monitor whether expected profit is increasing or reducing.

## Run the migration

```bash
python manage.py makemigrations
python manage.py migrate
```

A ready migration is included:

```text
farms/migrations/0004_farm_projects_planner_profit_tracking.py
```

## New models

### FarmProject
Represents a business project under a farm.

Important fields:

- `farm`
- `name`
- `project_type`: `crop`, `poultry`, `cattle`, `goats`, `piggery`, `fish`, `beekeeping`, `other`
- `start_date`
- `expected_end_date`
- `status`: `planned`, `active`, `paused`, `completed`, `cancelled`
- `expected_revenue`
- `expected_cost`
- `target_quantity`
- `target_unit`

Computed values:

- `planned_profit = expected_revenue - expected_cost`
- `actual_cost = total project inputs`
- `actual_revenue = total project revenue`
- `estimated_profit = actual_revenue - actual_cost`
- `projected_profit = expected_revenue - actual_cost`
- `cost_variance = expected_cost - actual_cost`

### ProjectPlannedActivity
Used for planning and tracking activities such as vaccination, feeding, spraying, labour, land preparation, etc.

### ProjectInputRecord
Used for tracking inputs such as drugs, feeds, labour, transport, fertilizer, chemicals, seed, equipment, etc.

### ProjectRevenueRecord
Used for recording revenue from the project.

## New API endpoints

All endpoints require:

```http
Authorization: Token <token>
```

### Projects

```http
GET    /api/farmers/projects/
POST   /api/farmers/projects/
GET    /api/farmers/projects/<id>/
PATCH  /api/farmers/projects/<id>/
DELETE /api/farmers/projects/<id>/
GET    /api/farmers/projects/<id>/profit-summary/
```

Example create project:

```json
{
  "farm": "FARM_UUID",
  "name": "Poultry batch 1",
  "project_type": "poultry",
  "description": "First batch of broilers",
  "start_date": "2026-05-23",
  "expected_end_date": "2026-07-23",
  "status": "active",
  "expected_revenue": "3500000",
  "expected_cost": "2200000",
  "target_quantity": "300",
  "target_unit": "birds"
}
```

### Planned activities

```http
GET    /api/farmers/project-plans/
POST   /api/farmers/project-plans/
PATCH  /api/farmers/project-plans/<id>/
DELETE /api/farmers/project-plans/<id>/
GET    /api/farmers/planner/
```

Example:

```json
{
  "project": "PROJECT_UUID",
  "farm": "FARM_UUID",
  "title": "Vaccinate chicks",
  "activity_type": "other",
  "planned_date": "2026-05-30",
  "status": "todo",
  "estimated_cost": "50000",
  "assigned_to": "Farm worker"
}
```

### Project inputs

```http
GET    /api/farmers/project-inputs/
POST   /api/farmers/project-inputs/
PATCH  /api/farmers/project-inputs/<id>/
DELETE /api/farmers/project-inputs/<id>/
GET    /api/farmers/input-trends/
```

Example input:

```json
{
  "project": "PROJECT_UUID",
  "farm": "FARM_UUID",
  "category": "drugs",
  "item_name": "Vaccine",
  "quantity": "2",
  "unit": "bottle",
  "unit_cost": "25000",
  "record_date": "2026-05-30",
  "supplier_name": "Agrovet"
}
```

The server calculates:

```text
total_cost = quantity × unit_cost
```

### Project revenues

```http
GET    /api/farmers/project-revenues/
POST   /api/farmers/project-revenues/
PATCH  /api/farmers/project-revenues/<id>/
DELETE /api/farmers/project-revenues/<id>/
```

Example revenue:

```json
{
  "project": "PROJECT_UUID",
  "farm": "FARM_UUID",
  "description": "Sold mature broilers",
  "quantity": "250",
  "unit": "birds",
  "price_per_unit": "15000",
  "revenue_date": "2026-07-23",
  "buyer_name": "Kasese buyer"
}
```

The server calculates:

```text
amount = quantity × price_per_unit
```

## Offline sync support

The existing sync endpoint now includes these keys:

```json
{
  "projects": [],
  "project_plans": [],
  "project_inputs": [],
  "project_revenues": []
}
```

Endpoint:

```http
POST /api/farmers/sync/
```

## Profit monitoring logic

The mobile app can use:

```http
GET /api/farmers/projects/<id>/profit-summary/
```

To show:

- Expected revenue
- Expected cost
- Planned profit
- Actual input costs
- Actual revenue
- Estimated profit
- Projected profit
- Cost variance
- Input costs grouped by category
- Monthly increase/decrease of inputs
- Activity progress

For input increase/decrease across all projects or one project:

```http
GET /api/farmers/input-trends/
GET /api/farmers/input-trends/?project=PROJECT_UUID
```
