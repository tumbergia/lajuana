# Implementation Plan: Admin CRUD Tools

## Context
Add 15 new admin tools to the MCP registry so the administrator can manage the entire system via `POST /api/v1/admin/ask`.

## Slices

### Slice 1: Admin Experience Tools (4 tools)
- `admin_create_experience`
- `admin_update_experience`
- `admin_list_experiences_admin`
- `admin_deactivate_experience`

### Slice 2: Admin User Tools (4 tools)
- `admin_list_users`
- `admin_create_user`
- `admin_update_user`
- `admin_deactivate_user`

### Slice 3: Admin Schedule Tools (4 tools)
- `admin_create_schedule`
- `admin_update_schedule`
- `admin_list_schedules_admin`
- `admin_deactivate_schedule`

### Slice 4: Admin Config Tools (3 tools)
- `admin_get_system_config`
- `admin_update_reservation_rules`
- `admin_get_payment_instructions`

### Slice 5: Integration & Wiring
- tool_contracts.py: new Pydantic contracts
- tools/__init__.py: exports
- mcp/__init__.py: registry registrations
- policy.py: add to ADMIN_TOOLS
- planner.py: mention new admin tools in prompt

## Evidence
- All policy tests pass
- All new tools registered in registry
- Admin can use all tools from `admin_api` channel
- Client cannot use admin tools from `whatsapp` channel

## Risks
- Service layer already exists, so risk is low
- Need to ensure HumanReviewRequestDocument is registered in DB init
- Need to validate tool_contracts don't conflict with existing schemas