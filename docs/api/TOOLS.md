# MCP Tools

Model Context Protocol tools — registered by `app/ai/mcp/__init__.py`. Each tool is a Python async function callable by the AI assistant (Gemini planner).

Registration: tools are defined in `app/ai/mcp/tools/`, imported by `tools/__init__.py`, then registered in a single `_TOOLS` dict in `mcp/__init__.py`. Adding a new tool is a single-line change.

All tools log their execution to `ToolCallLogDocument` (trace_id, latency, status, input/output).

---

## Client-Facing Tools

### Catalog & Discovery

| Tool | Description |
|------|-------------|
| `list_experiences` | List active experiences with summaries, prices, tags |
| `get_experience_detail` | Get full detail for a single experience by ID or query (name, alias, tag) |
| `get_public_business_rules` | Return business rules, restrictions, alcohol policy, disclaimer |
| `check_experience_availability` | Check if a date has available slots for an experience; returns blocking reasons |
| `list_available_schedules` | List available dates for an experience on a given date range (day-lock model) |
| `suggest_alternative_dates` | Suggest nearby available dates when the requested date is full |
| `quote_experience` | Calculate official pricing for a participant count, returns tier breakdown |

### Client Reservation Management

| Tool | Description |
|------|-------------|
| `create_reservation_draft` | Create a pre-reservation draft with quote snapshot and payment instructions |
| `get_reservation_public_summary` | Get public reservation summary by code + phone (status, dates, amounts) |
| `get_reservation_status_by_phone` | Look up reservation status by holder phone number |
| `cancel_reservation` | Cancel own reservation by code + phone (only if payment pending) |
| `update_reservation_date` | Change reservation date by code + phone + new date |
| `update_reservation_participants` | Change participant count by code + phone |
| `attach_payment_proof_to_reservation` | Attach a payment proof to a reservation by code + phone |
| `request_human_review` | Create a human review request (escalation from AI chat) |
| `generate_participant_form_link` | Generate a temporary form link for participants of a confirmed reservation |
| `get_participant_form_status` | Check participant form status (registered count, limit, remaining) |

---

## Admin Tools

### Equine Health & Service

| Tool | Description |
|------|-------------|
| `admin_add_equine_health_event` | Log a health event for an equine (injury, treatment, checkup) |
| `admin_close_service_execution` | Complete a reservation (CONFIRMED → COMPLETED), logs closure |
| `admin_get_logistics_checklist` | Generate a pre-service checklist for a reservation (participants, assignments, policies, equines) |
| `admin_get_equine_workload` | Show workload (upcoming assignments) for one or more equines |
| `admin_update_equine_availability` | Set an equine as available/unavailable with a reason |

### Reports & Analytics

| Tool | Description |
|------|-------------|
| `admin_get_sales_summary` | Sales summary grouped by reservation status for a date range |
| `admin_get_reservation_funnel` | Reservation funnel counts by stage (contact → completed) |
| `admin_get_channel_performance` | Performance metrics by acquisition channel |
| `admin_get_occupancy_report` | Occupancy report by reservation date range |
| `admin_get_equine_workload_report` | Detailed workload report across all equines |

### Admin CRUD — Experiences

| Tool | Description |
|------|-------------|
| `admin_create_experience` | Create a new experience with pricing tiers, inclusions, duration |
| `admin_update_experience` | Update experience fields |
| `admin_list_experiences_admin` | List all experiences (including inactive) |
| `admin_deactivate_experience` | Deactivate an experience |

### Admin CRUD — Users

| Tool | Description |
|------|-------------|
| `admin_list_users` | List all internal users |
| `admin_create_user` | Create a new internal user |
| `admin_update_user` | Update user fields |
| `admin_deactivate_user` | Deactivate a user |

### Admin CRUD — Equines

| Tool | Description |
|------|-------------|
| `admin_list_equines` | List equines with availability and filters |
| `admin_create_equine` | Create a new equine |
| `admin_update_equine` | Update equine fields |
| `admin_get_equine` | Get full equine detail |
| `admin_deactivate_equine` | Deactivate an equine |

### Admin CRUD — Reservations

| Tool | Description |
|------|-------------|
| `admin_list_reservations` | List reservations with filters (status, date, limit) |
| `admin_get_reservation_detail` | Get full reservation detail |
| `admin_confirm_reservation` | Confirm a reservation (admin action) |
| `admin_cancel_reservation` | Cancel a reservation (admin action) |

### Admin CRUD — Participants

| Tool | Description |
|------|-------------|
| `admin_get_participant` | Get full participant detail with emergency contact |
| `admin_update_participant` | Update participant fields |

### Admin CRUD — Payment Proofs

| Tool | Description |
|------|-------------|
| `admin_get_payment_proof` | Get payment proof by ID or reservation ID |
| `admin_approve_payment` | Approve payment proof → triggers notification + form link generation |
| `admin_reject_payment_proof` | Reject a payment proof with reason |
| `admin_unverify_payment_proof` | Unverify (reverse verification) |
| `admin_unreject_payment_proof` | Unreject (reverse rejection) |

### Admin — System

| Tool | Description |
|------|-------------|
| `admin_get_system_config` | Get reservation rules and payment instructions |
| `admin_update_reservation_rules` | Update min_days_in_advance, require_payment_proof, draft TTL |
| `admin_get_payment_instructions` | Get bank account details for transfers |
| `admin_list_human_review_requests` | List open human review requests with filters |

---

## Guide Tools

| Tool | Description |
|------|-------------|
| `guide_create_service_log` | Log a service event (arrival, checkpoint, closure, note) for a reservation |
| `guide_report_incident` | Report an incident with severity level during service |
| `send_post_service_message` | Send a "thank you" post-service message to the customer |

---

## Automation Tools

| Tool | Description |
|------|-------------|
| `schedule_birthday_automation` | Schedule automated birthday greetings for customers |
| `schedule_visit_anniversary_automation` | Schedule automated visit anniversary messages for returning customers |

---

## Tool Architecture

All tools follow a consistent pattern:

1. Accept `**kwargs` with typed parameters extracted from Gemini's tool call
2. Validate input using Pydantic schemas (`tool_contracts.py`)
3. Execute business logic against the domain services / Beanie documents
4. Return a typed output Pydantic model, serialized to dict
5. Log execution to `ToolCallLogDocument` (always in `finally` block)

Errors are surfaced via `ToolBlockingReason` objects (code + message + optional details), not exceptions — the AI can then explain the block to the user.

### Adding a new tool

1. Define input/output schemas in `app/ai/mcp/tool_contracts.py`
2. Implement the tool function in `app/ai/mcp/tools/<module>.py`
3. Import and add to `_TOOLS` dict in `app/ai/mcp/__init__.py`
4. Add to `__all__` in `app/ai/mcp/tools/__init__.py`
