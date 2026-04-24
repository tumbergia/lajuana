import 'package:flutter/material.dart';

class AppTermHelp extends StatelessWidget {
  const AppTermHelp({super.key, required this.title, required this.message});

  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(999),
        onTap: () {
          showDialog<void>(
            context: context,
            builder: (dialogContext) {
              return AlertDialog(
                title: Text(title),
                content: Text(message),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(dialogContext).pop(),
                    child: const Text('Entendido'),
                  ),
                ],
              );
            },
          );
        },
        child: Container(
          width: 22,
          height: 22,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(color: scheme.outlineVariant),
          ),
          child: Icon(
            Icons.question_mark_rounded,
            size: 14,
            color: scheme.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
