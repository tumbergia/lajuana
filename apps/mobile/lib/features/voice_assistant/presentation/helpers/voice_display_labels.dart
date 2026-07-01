import 'package:mobile/features/reservations/domain/models/reservation_status.dart';
import 'package:mobile/features/reservations/presentation/helpers/reservation_status_labels.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';

/// Convierte snake_case técnico en texto legible como último recurso.
String humanizeSnakeCase(String? value) {
  if (value == null || value.trim().isEmpty) return 'Sin dato';
  return value
      .trim()
      .replaceAll('_', ' ')
      .split(' ')
      .map((part) {
        if (part.isEmpty) return part;
        return '${part[0].toUpperCase()}${part.substring(1).toLowerCase()}';
      })
      .join(' ');
}

String voiceReservationStatusLabel(String? status) {
  if (status == null || status.trim().isEmpty) return 'Sin estado';
  return reservationStatusLabel(parseReservationStatus(status));
}

AppBadgeTone voiceReservationStatusTone(String? status) {
  final parsed = parseReservationStatus(status);
  return switch (parsed) {
    ReservationStatus.confirmed ||
    ReservationStatus.completed =>
      AppBadgeTone.success,
    ReservationStatus.pendingPayment ||
    ReservationStatus.preReserved ||
    ReservationStatus.quoted =>
      AppBadgeTone.warning,
    ReservationStatus.cancelled ||
    ReservationStatus.expired =>
      AppBadgeTone.danger,
    ReservationStatus.paymentReceived => AppBadgeTone.primary,
    _ => AppBadgeTone.neutral,
  };
}

String voicePaymentStatusLabel(String? status) =>
    paymentStatusLabel(status);

String voiceAvailabilityLabel(bool isAvailable) =>
    isAvailable ? 'Disponible' : 'No disponible';

AppBadgeTone voiceAvailabilityTone(bool isAvailable) =>
    isAvailable ? AppBadgeTone.success : AppBadgeTone.neutral;

String voiceUserRoleLabel(String? role) {
  return switch (role?.toLowerCase()) {
    'admin' => 'Administrador',
    'guide' => 'Guía',
    'unassigned' => 'Sin rol',
    _ => humanizeSnakeCase(role),
  };
}

String voiceExperienceStatusLabel(String? status) {
  return switch (status?.toLowerCase()) {
    'draft' => 'Borrador',
    'published' => 'Publicada',
    'archived' => 'Archivada',
    _ => humanizeSnakeCase(status),
  };
}

String voiceReviewPriorityLabel(String? priority) {
  return switch (priority?.toLowerCase()) {
    'low' => 'Baja',
    'medium' => 'Media',
    'high' => 'Alta',
    'urgent' => 'Urgente',
    _ => humanizeSnakeCase(priority),
  };
}

String voiceReviewStatusLabel(String? status) {
  return switch (status?.toLowerCase()) {
    'open' => 'Abierta',
    'in_progress' => 'En progreso',
    'resolved' => 'Resuelta',
    'closed' => 'Cerrada',
    _ => humanizeSnakeCase(status),
  };
}

String voiceScheduleStatusLabel(String? status) {
  return switch (status?.toLowerCase()) {
    'open' => 'Abierto',
    'closed' => 'Cerrado',
    'cancelled' => 'Cancelado',
    'full' => 'Completo',
    _ => humanizeSnakeCase(status),
  };
}

String voiceEquineEventTypeLabel(String? eventType) =>
    humanizeSnakeCase(eventType);

String voiceListSummary({
  required int total,
  required String singular,
  required String plural,
}) {
  if (total == 0) return 'No se encontraron $plural.';
  if (total == 1) return '1 $singular encontrado.';
  return '$total $plural encontrados.';
}

int voiceOutputTotal(Map<String, dynamic> toolOutput) {
  final total = toolOutput['total'];
  if (total is int) return total;
  if (total is num) return total.toInt();
  return 0;
}

List<Map<String, dynamic>> voiceOutputList(
  Map<String, dynamic> toolOutput,
  String key,
) {
  final raw = toolOutput[key];
  if (raw is! List) return const [];
  return raw
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList();
}

String? voiceString(Map<String, dynamic> map, String key) {
  final value = map[key];
  if (value == null) return null;
  final text = value.toString().trim();
  return text.isEmpty ? null : text;
}

String voiceMoneyCop(int? amount) {
  if (amount == null) return '';
  final text = amount.toString().replaceAllMapped(
        RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
        (m) => '${m[1]}.',
      );
  return 'Desde \$$text';
}
