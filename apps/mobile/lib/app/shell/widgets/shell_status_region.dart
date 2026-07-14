import 'package:flutter/material.dart';

import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';

/// Banners globales de sesión y conectividad (solo presentación).
///
/// La sincronización ya no se muestra aquí: corre en segundo plano y reintenta
/// sola (ver `OutboxRepository.autoSync`). El aviso de "servidor no alcanzable"
/// se emite como toast superior desde el shell, no como banner persistente.
/// "Sin enlace de red" y "Sesión local" tampoco viven aquí: son el mismo
/// ícono compacto de conectividad en el `AppTopBar` (ver `AuthenticatedShell`),
/// no banners que ocupen espacio — ambos significan lo mismo para el usuario:
/// "no hay conexión completa con el servidor ahora mismo".
class ShellStatusRegion extends StatelessWidget {
  const ShellStatusRegion({
    super.key,
    required this.controller,
  });

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final banners = _bannersFor(controller);
        if (banners.isEmpty) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              for (int i = 0; i < banners.length; i++) ...[
                banners[i],
                if (i != banners.length - 1) const SizedBox(height: 10),
              ],
            ],
          ),
        );
      },
    );
  }

  static List<Widget> _bannersFor(AuthController c) {
    final banners = <Widget>[];
    final authState = c.authState;
    final ns = c.networkStatus;

    if (ns.linkType == LinkType.mobile &&
        ns.backendReachability == BackendReachability.reachable) {
      banners.add(
        const AppStatusBanner(
          title: 'Red movil',
          message:
              'Conectado por datos. Puede haber mas latencia en algunas acciones.',
          tone: AppStatusBannerTone.info,
          icon: Icons.signal_cellular_alt_rounded,
          badgeLabel: 'Datos',
        ),
      );
    }

    if (authState == LocalAuthState.refreshRequired ||
        authState == LocalAuthState.invalid) {
      banners.add(
        AppStatusBanner(
          title: 'Sesion requiere validacion',
          message:
              'Verifica internet y actualiza sesion para habilitar acciones.',
          tone: AppStatusBannerTone.danger,
          icon: Icons.warning_amber_rounded,
          badgeLabel: 'Atencion',
          onTap: c.isLoading ? null : () => c.refreshRequested(),
        ),
      );
    }

    return banners;
  }
}
