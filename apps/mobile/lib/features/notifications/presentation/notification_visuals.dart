import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';

class NotificationVisuals {
  const NotificationVisuals({
    required this.label,
    required this.tone,
    required this.icon,
  });

  final String label;
  final AppBadgeTone tone;
  final IconData icon;
}

NotificationVisuals notificationVisuals(
  String eventType, {
  String body = '',
}) {
  final looksCancelled = body.toLowerCase().contains('cancel');
  return switch (eventType) {
    'reservation_cancelled' => const NotificationVisuals(
        label: 'Cancelación',
        tone: AppBadgeTone.danger,
        icon: Symbols.event_busy,
      ),
    'reservation_status_changed' when looksCancelled => const NotificationVisuals(
        label: 'Cancelación',
        tone: AppBadgeTone.danger,
        icon: Symbols.event_busy,
      ),
    'reservation_created' => const NotificationVisuals(
        label: 'Nueva reserva',
        tone: AppBadgeTone.primary,
        icon: Symbols.event,
      ),
    'reservation_confirmed' => const NotificationVisuals(
        label: 'Confirmada',
        tone: AppBadgeTone.primary,
        icon: Symbols.event,
      ),
    'reservation_status_changed' => const NotificationVisuals(
        label: 'Cambio de estado',
        tone: AppBadgeTone.primary,
        icon: Symbols.event,
      ),
    'reservation_updated' => const NotificationVisuals(
        label: 'Actualizada',
        tone: AppBadgeTone.primary,
        icon: Symbols.event,
      ),
    'payment_proof_registered' => const NotificationVisuals(
        label: 'Pago',
        tone: AppBadgeTone.warning,
        icon: Symbols.receipt_long,
      ),
    'participant_form_completed' => const NotificationVisuals(
        label: 'Participante',
        tone: AppBadgeTone.success,
        icon: Symbols.person_check,
      ),
    'human_review_requested' => const NotificationVisuals(
        label: 'Atención humana',
        tone: AppBadgeTone.primary,
        icon: Symbols.support_agent,
      ),
    'whatsapp_message_unattended' => const NotificationVisuals(
        label: 'WhatsApp',
        tone: AppBadgeTone.primary,
        icon: Symbols.chat,
      ),
    'whatsapp_delivery_failed' => const NotificationVisuals(
        label: 'Fallo WhatsApp',
        tone: AppBadgeTone.danger,
        icon: Symbols.error,
      ),
    'configuration_changed' => const NotificationVisuals(
        label: 'Configuración',
        tone: AppBadgeTone.neutral,
        icon: Symbols.settings,
      ),
    'assignment_changed' => const NotificationVisuals(
        label: 'Asignaciones',
        tone: AppBadgeTone.primary,
        icon: Symbols.assignment,
      ),
    'tomorrow_services_summary' => const NotificationVisuals(
        label: 'Reservas mañana',
        tone: AppBadgeTone.warning,
        icon: Symbols.wb_sunny,
      ),
    _ => const NotificationVisuals(
        label: 'Notificación',
        tone: AppBadgeTone.neutral,
        icon: Symbols.notifications,
      ),
  };
}

/// API timestamps are UTC; naive values (no Z/+00:00) must be treated as UTC
/// or they look "in the future" in west-of-UTC timezones and always show
/// "Hace un momento".
DateTime _notificationInstant(DateTime value) {
  if (value.isUtc) return value;
  return DateTime.utc(
    value.year,
    value.month,
    value.day,
    value.hour,
    value.minute,
    value.second,
    value.millisecond,
    value.microsecond,
  );
}

String formatRelativeTime(DateTime value, {DateTime? now}) {
  final local = _notificationInstant(value).toLocal();
  final reference = (now ?? DateTime.now()).toLocal();
  var diff = reference.difference(local);
  if (diff.isNegative) diff = Duration.zero;
  if (diff.inSeconds < 60) return 'Hace un momento';
  if (diff.inMinutes < 60) return 'Hace ${diff.inMinutes} min';
  if (diff.inHours < 24) return 'Hace ${diff.inHours} h';
  if (diff.inDays == 1) return 'Ayer';
  if (diff.inDays < 7) return 'Hace ${diff.inDays} días';
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)} ${two(local.hour)}:${two(local.minute)}';
}

String whatsappDigits(String? phone) {
  if (phone == null || phone.trim().isEmpty) return '';
  return phone.replaceAll(RegExp(r'\D'), '');
}

/// Prefer explicit contactPhone; fall back to phone prefix in body ("+57…: msg").
String? resolveNotificationPhone({
  String? contactPhone,
  String body = '',
}) {
  if (whatsappDigits(contactPhone).isNotEmpty) return contactPhone!.trim();
  final match = RegExp(r'^(\+?\d[\d\s\-]{6,})\s*:').firstMatch(body.trim());
  final candidate = match?.group(1)?.trim();
  if (candidate != null && whatsappDigits(candidate).isNotEmpty) {
    return candidate;
  }
  return null;
}

bool isWhatsAppPrimaryEvent(String eventType) {
  return eventType == 'whatsapp_message_unattended' ||
      eventType == 'human_review_requested' ||
      eventType == 'whatsapp_delivery_failed';
}

/// Solid tile + contrasting glyph. Neutral/ghost go black-on-surface punch.
({Color background, Color foreground}) notificationIconColors(
  BuildContext context,
  AppBadgeTone tone,
) {
  final scheme = Theme.of(context).colorScheme;
  if (tone == AppBadgeTone.neutral || tone == AppBadgeTone.ghost) {
    return (background: scheme.onSurface, foreground: scheme.surface);
  }
  final colors = appBadgeToneColors(context, tone);
  return (background: colors.background, foreground: colors.foreground);
}

