import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

/// Pantalla de carga compartida para bootstrap y reconexion de sesion.
/// Solo muestra el logo y un spinner, sin badges ni texto de estado.
class SessionLoadingView extends StatelessWidget {
  const SessionLoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Theme.of(context).colorScheme.surface,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            SizedBox(
              width: 220,
              height: 220 / (1600 / 567),
              child: SvgPicture.asset(
                'assets/branding/lajuana-banner.svg',
                fit: BoxFit.contain,
                colorFilter: ColorFilter.mode(
                  Theme.of(context).colorScheme.onSurface,
                  BlendMode.srcIn,
                ),
              ),
            ),
            const SizedBox(height: 16),
            const SizedBox(
              height: 28,
              width: 28,
              child: CircularProgressIndicator(strokeWidth: 2.5),
            ),
          ],
        ),
      ),
    );
  }
}
