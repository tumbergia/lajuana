import 'package:flutter/material.dart';

import '../../../home/home_page.dart';
import '../../domain/auth_enums.dart';
import '../../infrastructure/remote/auth_api_client.dart';
import '../auth_controller.dart';

class AuthenticatedHomeScreen extends StatelessWidget {
  const AuthenticatedHomeScreen({
    super.key,
    required this.controller,
    this.contactsApiClient,
    this.onCallRequested,
  });

  final AuthController controller;
  final AuthApiClient? contactsApiClient;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final showReconnectOverlay =
            controller.isLoading &&
            controller.authState == LocalAuthState.signedInLocalUnverified &&
            controller.connectivityState == ConnectivityState.online;

        return Stack(
          children: [
            HomePage(
              controller: controller,
              contactsApiClient: contactsApiClient,
              onCallRequested: onCallRequested,
            ),
            if (showReconnectOverlay) ...[
              const Positioned.fill(
                child: ModalBarrier(dismissible: false, color: Colors.black54),
              ),
              const Positioned.fill(child: _ReconnectLoadingView()),
            ],
          ],
        );
      },
    );
  }
}

class _ReconnectLoadingView extends StatelessWidget {
  const _ReconnectLoadingView();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Container(
        width: 280,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHigh,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: scheme.outlineVariant),
        ),
        child: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 24,
              height: 24,
              child: CircularProgressIndicator(strokeWidth: 2.4),
            ),
            SizedBox(height: 12),
            Text('Reconectando sesion...', textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
