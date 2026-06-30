import 'package:flutter/material.dart';

/// Toast flotante del sistema de diseño (SnackBar estilizado).
void showAppToast(
  BuildContext context, {
  required String message,
  bool isError = false,
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
