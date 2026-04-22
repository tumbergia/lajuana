# Arquitectura API

## Estado actual

El backend esta en fase funcional v1 centrada en el agregado `Reservation`.
Hoy centraliza:

- bootstrap de FastAPI y lifecycle;
- configuracion por entorno y reglas persistentes de reserva;
- routing principal versionado;
- contrato uniforme de errores de API;
- autenticacion JWT (`access + refresh`);
- vertical de dominio: `Auth`, `Experience`, `Schedule`, `Reservation`, `Participant`, `PaymentProof`, `AppConfig`.

## Capas vigentes

- `api/`: routers (entrada HTTP)
- `schemas/`: contratos request/response
- `services/`: reglas de negocio y casos de uso
- `documents/`: persistencia Beanie/Mongo
- `core/`: config, seguridad, db, errores transversales

## Reglas de implementacion

- La validacion de negocio critica vive en `services/`.
- Los routers no contienen reglas de confirmacion/disponibilidad/pagos.
- No se exponen documentos Beanie como contrato publico directo.
- `Reservation` es el agregado central de operacion.

## Versionado

El versionado de API se resuelve en rutas (`/api/v1/...`) usando configuracion.
No se versiona por carpetas (no `api/v1/` en filesystem).

## Decisiones vigentes v1

- Confirmacion de reserva solo via backend con validaciones de:
  - transicion de estado explicita,
  - anticipacion minima configurable,
  - disponibilidad real de cupos,
  - pago/comprobante segun configuracion.
- No se almacenan binarios en MongoDB; `PaymentProof` guarda metadatos + `storage_key`.
- `UserRole` incluye `guide` desde v1 para compatibilidad hacia S2.

## Fuera de alcance v1

- modulos operativos extendidos (`Equine`, `Saddle`, `Assignment`, `ServiceLog`, `Provider`, `Policy`) como dominio completo;
- firma digital legal final, facturacion final, importadores masivos.
