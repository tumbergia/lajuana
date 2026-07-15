# Auditoría semántica — métricas Leads → Analítica

**Fecha:** 2026-07-14  
**Fuente:** `apps/api/app/services/analytics_service.py` (estado pre-overhaul)

Leyenda de clasificación:

| Código | Significado |
|--------|-------------|
| **C** | Conservar (como módulo o breakdown) |
| **B** | Combinar en un módulo v2 |
| **R** | Renombrar (etiqueta incorrecta o poco clara) |
| **N2** | Mover a vista secundaria (Nivel 2 / catálogo) |
| **E** | Eliminar del producto principal |
| **X** | Corregir fórmula / semántica |

## Correcciones obligatorias

| Problema | Corrección |
|----------|------------|
| `ing_total` titulado "Ingreso total facturado" usa `quoted_total_amount` | Renombrar a **Valor cotizado**; nunca "facturado" ni "cobrado" |
| `vol_conversion` = completadas / total | **Bloqueada**: no es conversión comercial defendible. Sustituir por distribución de estados |
| `ori_top_pais` describe "país de origen" sin filtrar por periodo ni estado | Filtrar participantes de reservas **confirmadas/completadas** en el periodo; etiqueta "país de residencia" |
| Totales sin periodo | Todo módulo v2 lleva `period` explícito |
| `ori_top_pais` / `ori_top_pct` / `ori_top_5` duplican el mismo ranking | Consolidar en `top_countries` |
| `value: str` como fuente numérica | `primary_value.raw` tipado |

## Módulos bloqueados (datos inexistentes)

| Concepto | Motivo |
|----------|--------|
| Ingreso cobrado | `PaymentProofDocument` no tiene monto; solo estado |
| Tasa de conversión comercial | Sin historial de embudo por cohorte / etapa |
| Capacidad operativa de schedule | No existe `ScheduleDocument`; ocupación redefinida vs cupo de experiencia |

---

## Categoría `accion` — Pendientes de acción

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `vol_contact` | Nuevos leads | B + R | `action_center` (ítem: contactos nuevos) |
| `vol_quoted` | Cotizadas | B | `action_center` / `reservation_status` |
| `vol_pending_payment` | Pendientes de pago | B | `action_center` |
| `vol_payment_received` | Pago recibido | B | `action_center` |
| `pay_received` | Comprobantes por verificar | B | `action_center` + `payment_status` |
| `pay_pending` | Comprobantes pendientes | B | `action_center` + `payment_status` |
| `par_pending` | Formularios pendientes | B + X | `participant_readiness` (solo confirmadas próximas: esperados − completos) |
| `op_asignaciones` | Asignaciones activas | N2 | Detalle operativo / catálogo |

## Categoría `reservas` — Embudo

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `vol_activas` | Reservas activas | B | `reservation_status` |
| `vol_confirmed` | Confirmadas | B | `reservation_status` + `reservation_trend` |
| `vol_completed` | Completadas | B | `reservation_status` |
| `vol_cancelled` | Canceladas | B | `reservation_status` |
| `vol_conversion` | Tasa de conversión | E + X | Bloqueada; no exponer % engañoso |
| `vol_total` | Total reservas | N2 | Breakdown de `reservation_status` con periodo |

## Categoría `dinero`

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `ing_total` | Ingreso total facturado | R + X | **Valor cotizado** (Nivel 2); no en Inicio por defecto |
| `ing_avg_reserva` | Promedio por reserva | N2 | Derivado de valor cotizado |
| `ing_confirmed` | Ingreso de confirmadas/completadas | R | **Ingresos comprometidos** → `confirmed_value_trend` |
| `ing_avg_participante` | Ticket promedio por participante | N2 | Derivado |
| `pay_verified` | Comprobantes verificados | B | `payment_status` |
| `pay_rejected` | Comprobantes rechazados | B | `payment_status` + `action_center` |
| `pay_verification_rate` | Tasa de verificación | N2 | Breakdown de `payment_status` |
| `pay_total` | Total comprobantes | N2 | Breakdown |

## Categoría `eq_operacion`

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `eq_available` | Disponibles | B | `equine_availability` |
| `eq_in_service` | En servicio | B | `equine_availability` |
| `eq_resting` | En descanso | B | `equine_availability` |
| `eq_unavailable` | No disponibles | B | `equine_availability` |
| `eq_workload` | Carga laboral semanal | C + R | `equine_workload` (carga de mulas/equinos) |

## Categoría `eq_salud`

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `eq_injured` | Lesionados | B | `equine_care_alerts` / disponibilidad |
| `eq_open_injuries` | Lesiones recientes | B | `equine_care_alerts` |
| `eq_overdue_care` | Cuidados vencidos | C | `equine_care_alerts` (crítico) |
| `eq_due_soon` | Cuidados próximos | C | `equine_care_alerts` |
| `eq_health_7d` | Eventos de salud (7 días) | N2 | Detalle de alertas |
| `eq_high_severity` | Severidad alta/crítica | B | `equine_care_alerts` |

## Categoría `personas`

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `par_completed` | Formularios completados | B | `participant_readiness` |
| `par_completion_rate` | Tasa de completitud | N2 | Derivado de readiness |
| `ori_top_pais` | Principal país de origen | B + R + X | `top_countries` |
| `ori_top_pct` | Concentración top país | B | `top_countries` (share) |
| `par_total` | Total participantes | N2 / E | Inventario lento |
| `par_avg_age` | Edad promedio | E / N2 | Bajo valor operativo |
| `par_top_level` | Nivel más común | N2 | Catálogo |
| `ori_total_paises` | Países representados | N2 | Contador en `top_countries` |
| `ori_top_5` | Top 5 países | B | `top_countries` |

## Categoría `catalogo`

| ID | Título actual | Clasificación | Destino v2 |
|----|---------------|---------------|------------|
| `eq_total` | Total equinos | N2 | Inventario |
| `eq_horses` / `eq_mules` / `eq_donkeys` | Por especie | N2 | Inventario |
| `exp_total` / `exp_published` / `exp_routes` / `exp_experiences` / `exp_private` | Catálogo | N2 | Inventario |
| `exp_top` | Más reservada | B + X | `top_experiences` (solo confirmadas/completadas en periodo) |
| `op_asignaciones_total` / `op_finalizadas` | Asignaciones | N2 | Operativo |
| `op_usuarios` / `op_usuarios_total` | Usuarios | E | No es analítica de negocio operativa |

## Módulos v2 iniciales (mapeo)

| Module ID | Título de negocio | Visualización | Fuente |
|-----------|-------------------|---------------|--------|
| `action_center` | Tareas pendientes | `action_list` | Pendientes críticos |
| `reservation_trend` | Tendencia de reservas | `line` / `sparkline` | `created_at` en periodo |
| `reservation_status` | Estado de las reservas | `donut` / `bar` | Conteos por `status` |
| `confirmed_value_trend` | Ingresos comprometidos | `line` / `kpi` | `quoted_total_amount` confirmadas+completadas |
| `payment_status` | Comprobantes de pago | `donut` | `PaymentProofDocument.status` |
| `top_experiences` | Experiencias más reservadas | `ranking` / `bar` | Confirmadas+completadas |
| `occupancy` | Ocupación de próximas salidas | `progress` / `ranking` | Participantes vs cupo experiencia |
| `top_countries` | Países de los visitantes | `ranking` | Participantes de confirmadas/completadas |
| `participant_readiness` | Preparación de participantes | `progress` / `kpi` | Esperados − completos |
| `equine_availability` | Disponibilidad equina | `donut` | `operational_status` |
| `equine_workload` | Carga de trabajo equina | `ranking` / `kpi` | Asignaciones / `workload_last_7_days` |
| `equine_care_alerts` | Alertas de cuidados | `action_list` | `next_due_at`, lesiones, severidad |

## Equivalencia legacy → módulo (migración de pins)

| Lead ID legacy | Module ID v2 |
|----------------|--------------|
| `ing_confirmed` | `confirmed_value_trend` |
| `vol_confirmed` / `vol_activas` / `vol_completed` | `reservation_trend` o `reservation_status` |
| `exp_top` | `top_experiences` |
| `ori_top_pais` / `ori_top_5` / `ori_top_pct` | `top_countries` |
| `par_pending` / `par_completed` | `participant_readiness` |
| `eq_available` / `eq_in_service` | `equine_availability` |
| `eq_workload` | `equine_workload` |
| `eq_overdue_care` / `eq_due_soon` / `eq_injured` | `equine_care_alerts` |
| `pay_received` / `pay_pending` / `vol_pending_payment` | `payment_status` / `action_center` |
| `ing_total` | (sin equivalencia Inicio; valor cotizado Nivel 2) |
| `vol_conversion` | (sin equivalencia; bloqueada) |
