import 'package:flutter/material.dart';

/// Confirmación / feedback con el SnackBar simple de la app.
void showAppToast(
  BuildContext context, {
  required String message,
  bool isError = false,
}) {
  if (!context.mounted) return;
  final messenger = ScaffoldMessenger.of(context);
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(
    SnackBar(
      content: Text(message),
      duration: Duration(milliseconds: isError ? 3600 : 2600),
    ),
  );
}
