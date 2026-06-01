# Implementation Handoff: Admin CRUD Tools

## Completed Slices

### Slice 1: Admin Experience Tools (4 tools)
- `admin_create_experience` — Crea experiencia usando `ExperienceService.create()`
- `admin_update_experience` — Actualiza experiencia usando `ExperienceService.update()`
- `admin_list_experiences_admin` — Lista experiencias usando `ExperienceService.list()`
- `admin_deactivate_experience` — Desactiva experiencia usando `ExperienceService.deactivate()`

### Slice 2: Admin User Tools (4 tools)
- `admin_list_users` — Lista usuarios usando `UserService.list_users()`
- `admin_create_user` — Crea usuario usando `UserService.create_user()`
- `admin_update_user` — Actualiza usuario usando `UserService.update_user()`
- `admin_deactivate_user` — Desactiva usuario usando `UserService.soft_delete_user()`

### Slice 3: Admin Schedule Tools (4 tools)
- `admin_create_schedule` — Crea schedule usando `ScheduleService.create()`
- `admin_update_schedule` — Actualiza schedule usando `ScheduleService.update()`
- `admin_list_schedules_admin` — Lista schedules usando `ScheduleService.list()`
- `admin_deactivate_schedule` — Desactiva schedule usando `ScheduleService.deactivate()`

### Slice 4: Admin Config Tools (3 tools)
- `admin_get_system_config` — Obtiene reglas de reserva + instrucciones de pago
- `admin_update_reservation_rules` — Actualiza reglas usando `ConfigService.update_reservation_rules()`
- `admin_get_payment_instructions` — Obtiene datos bancarios configurados

### Slice 5: Integration & Wiring
- `tool_contracts.py` — 15 nuevos contratos Pydantic Input/Output
- `tools/__init__.py` — Imports y exports de las nuevas tools
- `tools/__init__.py` — Reemplazo de stubs: `get_experience_detail`, `get_public_business_rules`, `request_human_review`
- `mcp/__init__.py` — Registro de 15 nuevas tools en el registry (total: 44)
- `policy.py` — Nuevas tools añadidas a ADMIN_TOOLS, READ_TOOLS, LIMITED_WRITE_TOOLS, WRITE_TOOLS
- `planner.py` — Reglas anti-admin intent (previamente implementado)

## Tests Run

- `test_tool_policy.py` — 18 tests, todos pasan
- `test_tool_policy_quote.py` — 6 tests, todos pasan
- `test_reservation_draft_service.py` — 10 tests, todos pasan
- Verificación manual: 15 nuevas admin tools permitidas desde `admin_api`, bloqueadas desde `whatsapp`

## Changed Contracts

- Nuevo documento: `HumanReviewRequestDocument` (colección `human_review_requests`)
- Nuevos contratos en `tool_contracts.py`:
  - `AdminCreateExperienceOutput`, `AdminUpdateExperienceOutput`, `AdminListExperiencesOutput`, `AdminDeactivateExperienceOutput`
  - `AdminListUsersOutput`, `AdminCreateUserOutput`, `AdminUpdateUserOutput`, `AdminDeactivateUserOutput`
  - `AdminListSchedulesOutput`, `AdminCreateScheduleOutput`, `AdminUpdateScheduleOutput`, `AdminDeactivateScheduleOutput`
  - `AdminGetSystemConfigOutput`, `AdminUpdateReservationRulesOutput`, `AdminGetPaymentInstructionsOutput`
- `collections.py` — añadido `HUMAN_REVIEW_REQUESTS`
- `db.py` — registrado `HumanReviewRequestDocument` en `init_beanie`

## Evidence

```
Total tools registered: 44
Admin tools: 25
```

## Known Risks

- Las nuevas tools administrativas no tienen tests unitarios propios (solo tests de policy). Los servicios subyacentes ya están testeados vía endpoints HTTP.
- `request_human_review` ahora crea documentos reales en MongoDB. Asegurar que la colección existe en producción.
- `get_experience_detail` y `get_public_business_rules` ahora son implementaciones reales (no stubs).

## Next Workflow
verify-work