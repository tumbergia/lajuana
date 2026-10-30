import 'package:flutter/material.dart';

/// Card que muestra el estado de pago con fondo tintado según el estado.
class PaymentStatusCard extends StatelessWidget {
  const PaymentStatusCard({
    super.key,
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final String label;
  final Color backgroundColor;
  final Color foregroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          Icon(Icons.receipt_long_rounded, size: 18, color: foregroundColor),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label.toUpperCase(),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: foregroundColor,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                'Estado de pago',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: foregroundColor.withValues(alpha: 0.88),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
