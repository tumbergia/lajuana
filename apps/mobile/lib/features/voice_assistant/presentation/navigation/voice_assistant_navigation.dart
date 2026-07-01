import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/presentation/pages/experience_detail_page.dart';
import 'package:mobile/features/equines/presentation/screens/equine_detail_screen.dart';
import 'package:mobile/features/equines/presentation/screens/equine_timeline_screen.dart';
import 'package:mobile/features/providers/infrastructure/mappers/provider_mapper.dart'
    as provider_mapper;
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_detail_sheet.dart';
import 'package:mobile/features/providers/providers_module.dart';
import 'package:mobile/features/reservations/presentation/screens/reservation_detail_shell_screen.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/saddles/infrastructure/mappers/saddle_mapper.dart'
    as saddle_mapper;
import 'package:mobile/features/saddles/presentation/models/saddle_view_models.dart';
import 'package:mobile/features/saddles/saddles_module.dart';
import 'package:mobile_domain/src/equines/equine_event_repository.dart';
import 'package:mobile_domain/src/equines/equine_repository.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';

/// Dependencias y acciones de navegación desde resultados del asistente de voz.
class VoiceAssistantNavigation {
  const VoiceAssistantNavigation({
    required this.authController,
    required this.equineRepository,
    required this.equineEventRepository,
    this.reservationsModule,
    this.catalogsModule,
    this.saddlesModule,
    this.providersModule,
    this.assignmentsModule,
  });

  final AuthController authController;
  final EquineRepository equineRepository;
  final EquineEventRepository equineEventRepository;
  final ReservationsModule? reservationsModule;
  final CatalogsModule? catalogsModule;
  final SaddlesModule? saddlesModule;
  final ProvidersModule? providersModule;
  final AssignmentsModule? assignmentsModule;

  void openReservation(
    BuildContext context,
    String reservationId, {
    ReservationDetailSubroute? initialSubroute,
  }) {
    if (reservationsModule == null) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ReservationDetailShellScreen(
          reservationId: reservationId,
          reservationsModule: reservationsModule,
          catalogsModule: catalogsModule,
          authController: authController,
          assignmentsModule: assignmentsModule,
          initialSubroute: initialSubroute,
        ),
      ),
    );
  }

  void openEquine(BuildContext context, String equineId) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => EquineDetailScreen(
          equineId: equineId,
          repository: equineRepository,
          userRole: authController.currentUser?.role,
        ),
      ),
    );
  }

  void openEquineTimeline(
    BuildContext context, {
    required String equineId,
    required String equineName,
  }) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => EquineTimelineScreen(
          equineId: equineId,
          equineName: equineName,
          repository: equineRepository,
          eventRepository: equineEventRepository,
        ),
      ),
    );
  }

  void openExperience(BuildContext context, String experienceId) {
    final module = catalogsModule;
    if (module == null) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ExperienceDetailPage(
          module: module,
          authController: authController,
          experienceId: experienceId,
        ),
      ),
    );
  }

  Future<void> openProviderDetail(
    BuildContext context, {
    required String providerId,
    required String name,
    required String slug,
    required String type,
    required String status,
    required bool isActive,
  }) async {
    final repository = providersModule?.repository;
    if (repository == null) return;

    final stub = ProviderRecord(
      id: providerId,
      name: name,
      slug: slug,
      type: type,
      status: status,
      isActive: isActive,
    );

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => ProviderDetailSheet(
        provider: stub,
        loadDetails: () async {
          final full = await repository.getProviderById(providerId);
          return provider_mapper.listItemToRecord(full);
        },
        onEdit: () => Navigator.of(context).pop(),
        onDeactivate: () => Navigator.of(context).pop(),
        onReactivate: () => Navigator.of(context).pop(),
      ),
    );
  }

  Future<void> openSaddleDetail(
    BuildContext context, {
    required String saddleId,
    String? fallbackCode,
    String? fallbackName,
    bool? fallbackAvailable,
  }) async {
    final repository = saddlesModule?.repository;
    SaddleRecord? saddle;

    if (repository != null) {
      try {
        saddle = saddle_mapper.listItemToRecord(await repository.getSaddleById(saddleId));
      } catch (_) {
        saddle = null;
      }
    }

    saddle ??= SaddleRecord(
      id: saddleId,
      code: fallbackCode ?? 'Montura',
      name: fallbackName ?? 'Sin nombre',
      isAvailable: fallbackAvailable ?? true,
    );

    if (!context.mounted) return;
    await _showSaddleActionsSheet(context, saddle);
  }

  Future<void> _showSaddleActionsSheet(
    BuildContext context,
    SaddleRecord saddle,
  ) async {
    final scheme = Theme.of(context).colorScheme;
    await showModalBottomSheet<void>(
      context: context,
      backgroundColor: scheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
      ),
      builder: (ctx) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Symbols.airline_seat_legroom_extra,
                size: 40,
                color: scheme.primary,
              ),
              const SizedBox(height: 12),
              Text(
                saddle.code,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                saddle.name,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                    ),
              ),
              const SizedBox(height: 8),
              AppBadge(
                label: saddle.statusLabel,
                tone: saddle.statusTone,
                uppercase: false,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: AppButton(
                  label: 'Cerrar',
                  variant: AppButtonVariant.secondary,
                  onPressed: () => Navigator.of(ctx).pop(),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
