# ADR-0009: Separación auth/network

**Fecha:** 2026-04-23  
**Estado:** ✅ Aceptado  

## Contexto

Auth offline-first requiere sincronización entre: estado de conectividad, validez del token, y reachability del backend. Acoplar todo generaba bugs difíciles de rastrear.

## Decisión

Tres servicios independientes:
- `ConnectivityPlusService`: conectividad de red (WiFi/datos)
- `HttpBackendReachabilityService`: reachability del backend (HEAD /health)
- `NetworkStatusResolver`: computa estado efectivo combinando ambos

AuthController escucha cambios de red pero NO bloquea operaciones. Cada repositorio decide su estrategia según conectividad.

## Consecuencias

- Auth y network desacoplados
- Cada repositorio implementa su propia lógica offline/online
- Sin falsos positivos (red OK pero backend caído, o viceversa)
- Recuperación automática al volver la conectividad
