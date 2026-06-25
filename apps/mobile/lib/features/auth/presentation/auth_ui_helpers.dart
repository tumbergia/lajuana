import 'package:flutter/material.dart';

import 'package:mobile_ui/mobile_ui.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';

AppBadge connectivityBadge(NetworkStatus status) {
  if (status.linkType == LinkType.offline) {
    return const AppBadge(
      label: 'Sin enlace de red',
      tone: AppBadgeTone.danger,
      uppercase: false,
    );
  }
  if (status.backendReachability == BackendReachability.unreachable) {
    return const AppBadge(
      label: 'Servidor no disponible',
      tone: AppBadgeTone.warning,
      uppercase: false,
    );
  }
  if (status.backendReachability == BackendReachability.unknown) {
    return const AppBadge(
      label: 'Red activa',
      tone: AppBadgeTone.neutral,
      uppercase: false,
    );
  }
  if (status.linkType == LinkType.mobile) {
    return const AppBadge(
      label: 'Conectado (datos)',
      tone: AppBadgeTone.success,
      uppercase: false,
    );
  }
  return const AppBadge(
    label: 'Conectado al servidor',
    tone: AppBadgeTone.success,
    uppercase: false,
  );
}

AppBadge authStateBadge(LocalAuthState state) {
  switch (state) {
    case LocalAuthState.signedInVerified:
      return const AppBadge(
        label: 'Sesión verificada',
        tone: AppBadgeTone.success,
        uppercase: false,
      );
    case LocalAuthState.signedInLocalUnverified:
      return const AppBadge(
        label: 'Modo local',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    case LocalAuthState.refreshRequired:
      return const AppBadge(
        label: 'Requiere internet',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    case LocalAuthState.invalid:
      return const AppBadge(
        label: 'Tu sesión expiró',
        tone: AppBadgeTone.danger,
        uppercase: false,
      );
    case LocalAuthState.signedOut:
      return const AppBadge(
        label: 'Sin sesión',
        tone: AppBadgeTone.neutral,
        uppercase: false,
      );
  }
}

void showAuthToast(
  BuildContext context, {
  required String message,
  required bool isError,
}) {
  showAppToast(context, message: message, isError: isError);
}
