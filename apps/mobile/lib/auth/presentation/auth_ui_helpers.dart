import 'package:flutter/material.dart';

import '../../app/widgets/app_badge.dart';
import '../domain/auth_enums.dart';

AppBadge connectivityBadge(ConnectivityState state) {
  switch (state) {
    case ConnectivityState.online:
      return const AppBadge(
        label: 'Sesión verificada',
        tone: AppBadgeTone.success,
        uppercase: false,
      );
    case ConnectivityState.unstable:
      return const AppBadge(
        label: 'Modo local',
        tone: AppBadgeTone.warning,
        uppercase: false,
      );
    case ConnectivityState.offline:
      return const AppBadge(
        label: 'Sin conexión',
        tone: AppBadgeTone.danger,
        uppercase: false,
      );
  }
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
  final scheme = Theme.of(context).colorScheme;
  final bgColor = isError ? scheme.errorContainer : scheme.secondaryContainer;
  final fgColor = isError
      ? scheme.onErrorContainer
      : scheme.onSecondaryContainer;
  final icon = isError ? Icons.error_outline : Icons.check_circle_outline;

  final messenger = ScaffoldMessenger.of(context);
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(
    SnackBar(
      behavior: SnackBarBehavior.floating,
      margin: const EdgeInsets.fromLTRB(16, 0, 16, 20),
      backgroundColor: bgColor,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      duration: Duration(milliseconds: isError ? 3600 : 2600),
      content: Row(
        children: [
          Icon(icon, size: 18, color: fgColor),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: TextStyle(color: fgColor, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    ),
  );
}
