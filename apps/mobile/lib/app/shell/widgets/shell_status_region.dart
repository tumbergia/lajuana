import 'package:flutter/material.dart';

import '../../../features/auth/domain/auth_enums.dart';
import '../../../features/auth/infrastructure/connectivity/network_models.dart';
import '../../../features/auth/presentation/auth_controller.dart';
import '../../widgets/app_status_banner.dart';

/// Banners globales de sesión, conectividad y sync (solo presentación).
class ShellStatusRegion extends StatelessWidget {
  const ShellStatusRegion({super.key, required this.controller});

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

    if (ns.linkType == LinkType.offline) {
      banners.add(
        const AppStatusBanner(
          title: 'Sin enlace de red',
          message:
              'No hay Wi‑Fi ni datos. El modo local sigue disponible si aplica.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.wifi_off_rounded,
          badgeLabel: 'Sin enlace',
        ),
      );
    } else if (ns.backendReachability == BackendReachability.unreachable) {
      banners.add(
        const AppStatusBanner(
          title: 'Servidor no alcanzable',
          message:
              'Hay red en el dispositivo, pero el backend no respondio. Revisa URL o que el API este en marcha.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.cloud_off_rounded,
          badgeLabel: 'Backend',
        ),
      );
    } else if (ns.linkType == LinkType.mobile &&
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

    if (c.hasPendingSync) {
      banners.add(
        const AppStatusBanner(
          title: 'Cambios pendientes',
          message: 'Hay actualizaciones locales esperando envio al backend.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.sync_problem_rounded,
          badgeLabel: 'Pendiente',
        ),
      );
    }

    if (c.isOfflineRestricted) {
      banners.add(
        const AppStatusBanner(
          title: 'Sesion local',
          message:
              'Acciones criticas online-only estan temporalmente bloqueadas.',
          tone: AppStatusBannerTone.info,
          icon: Icons.lock_clock_outlined,
          badgeLabel: 'Modo local',
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
