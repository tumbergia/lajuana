# Cómo desplegar La Juana

El release oficial consta de dos artefactos independientes:

- una imagen OCI del API, desplegada primero;
- un Android App Bundle (`.aab`) firmado para Google Play y APKs firmadas para distribución directa.

No publiques desde un árbol con cambios sin commit. Todo release debe corresponder a un tag `vX.Y.Z` y conservar sus checksums.

## 1. Requisitos

- Flutter 3.41.7.
- JDK 21.
- Docker con BuildKit.
- MongoDB administrado o con copias de seguridad verificadas.
- Dominio HTTPS para el API.
- URL HTTPS pública de la política de privacidad.
- Cuenta de Google Play y acceso al entorno `production` de GitHub Actions.

El identificador actual es `co.lajuana.app`. Debe confirmarse antes de registrar la aplicación en Play Console; después de la primera publicación se considera permanente.

## 2. Firma Android

Genera una clave de carga una sola vez y almacénala en un gestor de secretos:

```bash
keytool -genkeypair -v -keystore upload-keystore.jks -alias upload -keyalg RSA -keysize 4096 -validity 10000
```

Para compilar localmente, crea `apps/mobile/android/key.properties` (está ignorado por Git):

```properties
storePassword=<secret>
keyPassword=<secret>
keyAlias=upload
storeFile=C:/ruta/absoluta/upload-keystore.jks
```

El build release falla deliberadamente si la firma no está configurada. Nunca uses la clave debug para un artefacto oficial.

Configura estos secretos en el environment `production` de GitHub:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`
- `PRODUCTION_API_BASE_URL`
- `PRIVACY_POLICY_URL`
- `MAP_TILE_URL` (opcional, recomendado para producción)

Convierte el keystore a Base64 sin saltos de línea antes de guardarlo como secreto.

## 3. API

Construcción reproducible:

```bash
docker build -t lajuana-api:local apps/api
```

Para desplegar una imagen publicada:

```bash
cd deploy
cp .env.production.example .env.production
# Completa secretos y fija LAJUANA_API_IMAGE a un tag inmutable.
docker compose -f compose.production.yml pull
docker compose -f compose.production.yml up -d
```

El contenedor escucha solamente en `127.0.0.1:8000` del host. El TLS debe terminar en el proxy o balanceador del entorno.

Cada tag `vX.Y.Z` construye y publica `ghcr.io/<owner>/lajuana-api:X.Y.Z`. Los pull requests solo validan que la imagen compile.

## 4. Android

Compilación local firmada:

```bash
cd apps/mobile
flutter pub get
flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://api.example.com/api/v1 \
  --dart-define=PRIVACY_POLICY_URL=https://example.com/privacidad \
  --build-name=1.0.0 \
  --build-number=1
```

Para APKs firmadas por arquitectura:

```bash
flutter build apk --release --split-per-abi \
  --dart-define=API_BASE_URL=https://api.example.com/api/v1 \
  --dart-define=PRIVACY_POLICY_URL=https://example.com/privacidad \
  --build-name=1.0.0 \
  --build-number=1
```

La URL del API y la política son obligatorias y deben usar HTTPS. El workflow `Android signed release` genera AAB, APKs y `SHA256SUMS.txt` desde un tag o una ejecución manual.

## 5. Orden de promoción

1. Ejecutar CI completa en `develop`.
2. Crear copia de seguridad de MongoDB y registrar el punto de restauración.
3. Desplegar el API en staging con un tag inmutable.
4. Ejecutar los smoke checks de abajo.
5. Promover la misma imagen a producción.
6. Subir el AAB al track interno de Play Console.
7. Probar instalación, login, sincronización, notificación, foto y voz en dispositivos reales.
8. Promover a prueba cerrada y luego a producción.

## 6. Smoke checks

```bash
curl --fail https://api.example.com/api/v1/health
curl --fail --request POST https://api.example.com/api/v1/auth/login \
  --header "Content-Type: application/json" \
  --data '{"email":"<release-test-user>","password":"<secret>"}'
```

Comprobar además:

- salud de MongoDB y espacio de almacenamiento;
- errores 5xx, latencia y reinicios del contenedor;
- login y refresh token;
- sincronización offline/online;
- carga y lectura de comprobantes/fotos;
- notificaciones en segundo plano;
- voz y permisos de micrófono;
- diseño según `docs/guides/RESPONSIVE_QA.md`.

Detén la promoción ante fallos de salud, aumento sostenido de 5xx, pérdida de datos, imposibilidad de autenticar o sincronización inconsistente.

## 7. Rollback

API:

```bash
cd deploy
# Cambia LAJUANA_API_IMAGE al tag anterior conocido como estable.
docker compose -f compose.production.yml pull
docker compose -f compose.production.yml up -d
curl --fail https://api.example.com/api/v1/health
```

Si hubo una migración incompatible, restaura primero el backup documentado. No reviertas datos sin confirmar el alcance exacto.

Android no permite instalar una versión con `versionCode` inferior. En Play Console, detén el rollout; si ya se distribuyó, publica una corrección basada en el commit estable con un `build-number` mayor.

## 8. Checklist Play Console

- [ ] Cuenta e identidad verificadas.
- [ ] Play App Signing habilitado.
- [ ] Ficha, icono, screenshots y datos de contacto.
- [ ] Política de privacidad publicada y accesible desde la app.
- [ ] Data safety consistente con autenticación, fotos, voz y notificaciones.
- [ ] Clasificación de contenido y audiencia objetivo.
- [ ] Credenciales de revisión funcionales.
- [ ] Prueba cerrada requerida completada, si aplica a la cuenta.
- [ ] `versionCode` superior al último publicado.
- [ ] AAB y checksums archivados junto al tag.

