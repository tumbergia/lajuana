import 'package:flutter/material.dart';

import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile/features/reservations/presentation/screens/reservation_detail_shell_screen.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_date_leading.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';

import '../helpers/voice_date_format.dart';
import '../helpers/voice_display_labels.dart';
import '../navigation/voice_assistant_navigation.dart';
import 'voice_result_entity_row.dart';

class VoiceResultItem {
  const VoiceResultItem({
    required this.title,
    required this.subtitle,
    this.statusLabel,
    this.statusTone = AppBadgeTone.neutral,
    this.onTap,
    this.leading,
  });

  final String title;
  final String subtitle;
  final String? statusLabel;
  final AppBadgeTone statusTone;
  final VoidCallback? onTap;
  final Widget? leading;
}

class VoiceStructuredResult {
  const VoiceStructuredResult({required this.summary, required this.items});

  final String summary;
  final List<VoiceResultItem> items;
}

/// Convierte `tool_output` en resumen + filas navegables para tools de listado admin.
class VoiceResultPresenter {
  static VoiceStructuredResult? present({
    required String? toolName,
    required Map<String, dynamic> toolOutput,
    required VoiceAssistantNavigation navigation,
    required BuildContext hostContext,
    required VoidCallback closeSheet,
  }) {
    if (toolName == null || toolName.isEmpty) return null;

    void navigate(VoidCallback action) {
      closeSheet();
      action();
    }

    return switch (toolName) {
      'admin_list_reservations' => _reservations(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_equines' => _equines(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_providers' => _providers(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_saddles' => _saddles(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_experiences_admin' => _experiences(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_equine_events' => _equineEvents(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_available_saddles_for_reservation' => _availableSaddles(
        toolOutput,
        navigation,
        hostContext,
        navigate,
      ),
      'admin_list_users' => _users(toolOutput),
      'admin_list_human_review_requests' => _humanReviews(toolOutput),
      'admin_list_schedules_admin' => _schedules(toolOutput),
      _ => null,
    };
  }

  static VoiceStructuredResult _reservations(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'reservations');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'reserva',
        plural: 'reservas',
      ),
      items: items.map((item) {
        final id = voiceString(item, 'reservation_id');
        final experience = voiceString(item, 'experience_name');
        final holder = voiceString(item, 'holder_name');
        final code = voiceString(item, 'code');
        final date = formatVoiceDate(voiceString(item, 'requested_date'));
        final status = voiceString(item, 'status');

        final title = experience ?? holder ?? code ?? 'Reserva';
        final subtitleParts = <String>[
          if (holder != null && experience != null) holder,
          date,
          if (code != null && title != code) code,
        ];

        return VoiceResultItem(
          title: title,
          subtitle: subtitleParts.join(' · '),
          statusLabel: voiceReservationStatusLabel(status),
          statusTone: voiceReservationStatusTone(status),
          leading: ReservationDateLeading(
            requestedDate: voiceString(item, 'requested_date'),
          ),
          onTap: id == null
              ? null
              : () =>
                    navigate(() => navigation.openReservation(hostContext, id)),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _equines(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'equines');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'equino',
        plural: 'equinos',
      ),
      items: items.map((item) {
        final id = voiceString(item, 'equine_id');
        final name = voiceString(item, 'name') ?? 'Equino';
        final breed = voiceString(item, 'breed');
        final isAvailable = item['is_available'] == true;
        final subtitleParts = <String>[
          if (breed != null) breed,
          voiceAvailabilityLabel(isAvailable),
        ];

        return VoiceResultItem(
          title: name,
          subtitle: subtitleParts.join(' · '),
          statusLabel: voiceAvailabilityLabel(isAvailable),
          statusTone: voiceAvailabilityTone(isAvailable),
          onTap: id == null
              ? null
              : () => navigate(() => navigation.openEquine(hostContext, id)),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _providers(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'providers');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'proveedor',
        plural: 'proveedores',
      ),
      items: items.map((item) {
        final id = voiceString(item, 'provider_id');
        final name = voiceString(item, 'name') ?? 'Proveedor';
        final type = voiceString(item, 'type') ?? '';
        final status = voiceString(item, 'status') ?? '';
        final slug = voiceString(item, 'slug') ?? '';
        final isActive = item['is_active'] != false;

        return VoiceResultItem(
          title: name,
          subtitle: providerTypeLabel(type),
          statusLabel: providerStatusLabel(status),
          statusTone: isActive ? AppBadgeTone.success : AppBadgeTone.neutral,
          onTap: id == null
              ? null
              : () => navigate(
                  () => navigation.openProviderDetail(
                    hostContext,
                    providerId: id,
                    name: name,
                    slug: slug,
                    type: type,
                    status: status,
                    isActive: isActive,
                  ),
                ),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _saddles(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'saddles');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'montura',
        plural: 'monturas',
      ),
      items: items.map((item) {
        final id = voiceString(item, 'saddle_id');
        final code = voiceString(item, 'code') ?? 'Montura';
        final name = voiceString(item, 'name');
        final isAvailable = item['is_available'] == true;

        return VoiceResultItem(
          title: code,
          subtitle: name ?? voiceAvailabilityLabel(isAvailable),
          statusLabel: voiceAvailabilityLabel(isAvailable),
          statusTone: voiceAvailabilityTone(isAvailable),
          onTap: id == null
              ? null
              : () => navigate(
                  () => navigation.openSaddleDetail(
                    hostContext,
                    saddleId: id,
                    fallbackCode: code,
                    fallbackName: name,
                    fallbackAvailable: isAvailable,
                  ),
                ),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _experiences(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'experiences');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'experiencia',
        plural: 'experiencias',
      ),
      items: items.map((item) {
        final id = voiceString(item, 'experience_id');
        final name = voiceString(item, 'name') ?? 'Experiencia';
        final status = voiceString(item, 'status');
        final price = item['starting_price'];
        final priceLabel = price is num ? voiceMoneyCop(price.toInt()) : null;
        final isActive = item['is_active'] != false;

        final subtitleParts = <String>[
          if (priceLabel != null && priceLabel.isNotEmpty) priceLabel,
          if (!isActive) 'Inactiva',
        ];

        return VoiceResultItem(
          title: name,
          subtitle: subtitleParts.isEmpty
              ? voiceExperienceStatusLabel(status)
              : subtitleParts.join(' · '),
          statusLabel: voiceExperienceStatusLabel(status),
          statusTone: isActive ? AppBadgeTone.primary : AppBadgeTone.neutral,
          onTap: id == null
              ? null
              : () =>
                    navigate(() => navigation.openExperience(hostContext, id)),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _equineEvents(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'events');
    final total = voiceOutputTotal(toolOutput);
    final equineId = voiceString(toolOutput, 'equine_id');
    final equineName = voiceString(toolOutput, 'equine_name') ?? 'Equino';

    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'evento',
        plural: 'eventos',
      ),
      items: items.map((item) {
        final title = voiceString(item, 'title') ?? 'Evento';
        final eventType = voiceString(item, 'event_type');
        final happenedAt = formatVoiceDateTime(
          voiceString(item, 'happened_at'),
        );
        final subtitleParts = <String>[
          voiceEquineEventTypeLabel(eventType),
          happenedAt,
        ];

        return VoiceResultItem(
          title: title,
          subtitle: subtitleParts.join(' · '),
          onTap: equineId == null
              ? null
              : () => navigate(
                  () => navigation.openEquineTimeline(
                    hostContext,
                    equineId: equineId,
                    equineName: equineName,
                  ),
                ),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _availableSaddles(
    Map<String, dynamic> toolOutput,
    VoiceAssistantNavigation navigation,
    BuildContext hostContext,
    void Function(VoidCallback action) navigate,
  ) {
    final items = voiceOutputList(toolOutput, 'saddles');
    final total = voiceOutputTotal(toolOutput);
    final reservationId = voiceString(toolOutput, 'reservation_id');

    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'montura disponible',
        plural: 'monturas disponibles',
      ),
      items: items.map((item) {
        final saddleId = voiceString(item, 'saddle_id');
        final code = voiceString(item, 'code') ?? 'Montura';
        final name = voiceString(item, 'name');
        final isAvailable = item['is_available'] == true;
        final blockReason = voiceString(item, 'block_reason');

        final subtitleParts = <String>[
          if (name != null) name,
          if (blockReason != null) blockReason,
        ];

        return VoiceResultItem(
          title: code,
          subtitle: subtitleParts.isEmpty
              ? voiceAvailabilityLabel(isAvailable)
              : subtitleParts.join(' · '),
          statusLabel: voiceAvailabilityLabel(isAvailable),
          statusTone: voiceAvailabilityTone(isAvailable),
          onTap: reservationId == null
              ? (saddleId == null
                    ? null
                    : () => navigate(
                        () => navigation.openSaddleDetail(
                          hostContext,
                          saddleId: saddleId,
                          fallbackCode: code,
                          fallbackName: name,
                          fallbackAvailable: isAvailable,
                        ),
                      ))
              : () => navigate(
                  () => navigation.openReservation(
                    hostContext,
                    reservationId,
                    initialSubroute: ReservationDetailSubroute.asignaciones,
                  ),
                ),
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _users(Map<String, dynamic> toolOutput) {
    final items = voiceOutputList(toolOutput, 'users');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'usuario',
        plural: 'usuarios',
      ),
      items: items.map((item) {
        final name = voiceString(item, 'full_name') ?? 'Usuario';
        final email = voiceString(item, 'email');
        final role = voiceString(item, 'role');
        final isActive = item['is_active'] != false;

        return VoiceResultItem(
          title: name,
          subtitle: email ?? '',
          statusLabel: voiceUserRoleLabel(role),
          statusTone: isActive ? AppBadgeTone.primary : AppBadgeTone.neutral,
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _humanReviews(Map<String, dynamic> toolOutput) {
    final items = voiceOutputList(toolOutput, 'requests');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'revisión',
        plural: 'revisiones',
      ),
      items: items.map((item) {
        final summary = voiceString(item, 'summary') ?? 'Revisión humana';
        final priority = voiceString(item, 'priority');
        final status = voiceString(item, 'status');
        final createdAt = formatVoiceDateTime(voiceString(item, 'created_at'));

        return VoiceResultItem(
          title: summary,
          subtitle: createdAt,
          statusLabel: voiceReviewPriorityLabel(priority),
          statusTone: switch (priority?.toLowerCase()) {
            'high' || 'urgent' => AppBadgeTone.danger,
            'medium' => AppBadgeTone.warning,
            _ => AppBadgeTone.neutral,
          },
        );
      }).toList(),
    );
  }

  static VoiceStructuredResult _schedules(Map<String, dynamic> toolOutput) {
    final items = voiceOutputList(toolOutput, 'schedules');
    final total = voiceOutputTotal(toolOutput);
    return VoiceStructuredResult(
      summary: voiceListSummary(
        total: total,
        singular: 'horario',
        plural: 'horarios',
      ),
      items: items.map((item) {
        final date = formatVoiceDate(voiceString(item, 'scheduled_date'));
        final time = formatVoiceTime(voiceString(item, 'start_time'));
        final available = item['available_slots'];
        final capacity = item['capacity_total'];
        final status = voiceString(item, 'status');

        final subtitleParts = <String>[
          if (time.isNotEmpty) time,
          if (available is num && capacity is num) '$available/$capacity cupos',
        ];

        return VoiceResultItem(
          title: date,
          subtitle: subtitleParts.join(' · '),
          statusLabel: voiceScheduleStatusLabel(status),
          statusTone: AppBadgeTone.primary,
        );
      }).toList(),
    );
  }
}

/// Lista de filas estructuradas para el sheet del asistente.
class VoiceStructuredResultList extends StatelessWidget {
  const VoiceStructuredResultList({super.key, required this.items});

  final List<VoiceResultItem> items;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final item in items)
          VoiceResultEntityRow(
            title: item.title,
            subtitle: item.subtitle,
            statusLabel: item.statusLabel,
            statusTone: item.statusTone,
            onTap: item.onTap,
            leading: item.leading,
          ),
      ],
    );
  }
}
