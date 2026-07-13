import 'package:flutter/material.dart';
import 'package:mobile/features/notifications/presentation/controllers/notifications_controller.dart';
import 'package:mobile/features/notifications/infrastructure/notification_background_service.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_switch_row.dart';

const _preferenceLabels = <String, String>{
  'reservation_created': 'Nuevas reservas',
  'reservation_confirmed': 'Reservas confirmadas',
  'reservation_status_changed': 'Cambios de estado',
  'reservation_updated': 'Ediciones de reservas',
  'reservation_cancelled': 'Cancelaciones',
  'payment_proof_registered': 'Comprobantes de pago',
  'participant_form_completed': 'Formularios de participantes',
  'human_review_requested': 'Solicitudes de atención humana',
  'whatsapp_message_unattended': 'WhatsApp sin asistente',
  'configuration_changed': 'Cambios de configuración',
  'assignment_changed': 'Asignaciones',
  'tomorrow_services_summary': 'Resumen de servicios de mañana',
  'whatsapp_delivery_failed': 'Fallos de envío WhatsApp',
};

class NotificationsSettingsPage extends StatefulWidget {
  const NotificationsSettingsPage({
    super.key,
    required this.controller,
  });

  final NotificationsController controller;

  @override
  State<NotificationsSettingsPage> createState() =>
      _NotificationsSettingsPageState();
}

class _NotificationsSettingsPageState extends State<NotificationsSettingsPage> {
  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      widget.controller.loadPreferences();
    });
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onChanged);
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _toggleBackground(bool enabled) async {
    widget.controller.setBackgroundPollingEnabled(enabled);
    if (!NotificationBackgroundService.supportsBackgroundNotifications) {
      return;
    }
    if (enabled) {
      await NotificationBackgroundService.registerPeriodic();
    } else {
      await NotificationBackgroundService.cancel();
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final prefs = controller.preferences?.preferences ?? const <String, bool>{};
    final bgSupported =
        NotificationBackgroundService.supportsBackgroundNotifications;

    return Scaffold(
      appBar: AppBar(title: const Text('Notificaciones')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 24, 24, 32),
        children: [
          const AppSectionHeader(
            eyebrow: 'Dispositivo',
            title: 'Alertas locales',
          ),
          const SizedBox(height: 16),
          AppSwitchRow(
            title: 'Notificaciones en segundo plano',
            subtitle: bgSupported
                ? 'Puede consumir más batería.'
                : 'Solo disponible en Android e iOS. Usa la app en primer plano.',
            value: controller.backgroundPollingEnabled && bgSupported,
            onChanged: bgSupported ? _toggleBackground : null,
          ),
          const SizedBox(height: 28),
          const AppSectionHeader(
            eyebrow: 'Preferencias',
            title: 'Que recibir',
          ),
          const SizedBox(height: 16),
          if (controller.preferencesLoading)
            const Padding(
              padding: EdgeInsets.only(top: 24),
              child: AppCenteredLoader(fill: false),
            )
          else if (controller.errorMessage != null &&
              controller.preferences == null)
            AppStatusBanner(
              title: 'Error al cargar',
              message: controller.errorMessage!,
              tone: AppStatusBannerTone.danger,
              icon: Icons.error_outline_rounded,
              badgeLabel: 'Error',
              onTap: controller.loadPreferences,
            )
          else
            ..._preferenceLabels.entries.map((entry) {
              final enabled = prefs[entry.key] ?? true;
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: AppSwitchRow(
                  title: entry.value,
                  value: enabled,
                  onChanged: (value) =>
                      controller.setPreference(entry.key, value),
                ),
              );
            }),
        ],
      ),
    );
  }
}
