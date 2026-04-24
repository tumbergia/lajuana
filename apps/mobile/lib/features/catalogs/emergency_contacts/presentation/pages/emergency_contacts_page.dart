import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../../../app/widgets/app_badge.dart';
import '../../../../../app/widgets/app_button.dart';
import '../../../../../app/widgets/app_centered_loader.dart';
import '../../../../../app/widgets/app_entity_row_card.dart';
import '../../../../../app/widgets/app_section_header.dart';
import '../../../../auth/presentation/auth_controller.dart';
import '../../../catalogs_module.dart';
import '../controllers/emergency_contacts_controller.dart';

class EmergencyContactsPage extends StatefulWidget {
  const EmergencyContactsPage({
    super.key,
    required this.module,
    required this.authController,
  });

  final CatalogsModule module;
  final AuthController authController;

  @override
  State<EmergencyContactsPage> createState() => _EmergencyContactsPageState();
}

class _EmergencyContactsPageState extends State<EmergencyContactsPage> {
  late final EmergencyContactsController _controller;

  @override
  void initState() {
    super.initState();
    _controller = EmergencyContactsController(
      repository: widget.module.emergencyContacts,
      catalogsRepository: widget.module.repository,
    );
    _controller.loadLocalThenRefresh();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _call(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (!await canLaunchUrl(uri)) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final isLoadingAny =
            _controller.isInitialLoading || _controller.isRefreshing;
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppSectionHeader(
                eyebrow: 'Catalogos',
                title: 'Contactos de emergencia',
                trailing: Wrap(
                  spacing: 8,
                  children: [
                    AppButton(
                      label: _controller.isRefreshing
                          ? 'Actualizando...'
                          : 'Actualizar',
                      icon: Icons.refresh_rounded,
                      variant: AppButtonVariant.ghost,
                      onPressed: _controller.isRefreshing
                          ? null
                          : () => _controller.refreshFromServer(),
                    ),
                    AppButton(
                      label: 'Volver',
                      icon: Icons.arrow_back_rounded,
                      variant: AppButtonVariant.ghost,
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: isLoadingAny
                    ? const AppCenteredLoader()
                    : ListView(
                        children: [
                          if (_controller.error != null)
                            AppEntityRowCard(
                              title: 'No se pudieron cargar contactos',
                              subtitle: _controller.error!,
                              selected: true,
                            )
                          else if (_controller.items.isEmpty)
                            const AppEntityRowCard(
                              title: 'Sin contactos disponibles',
                              subtitle: 'No hay registros para mostrar',
                              selected: true,
                            )
                          else
                            ..._controller.items.asMap().entries.map((entry) {
                              final index = entry.key;
                              final item = entry.value;
                              return Padding(
                                padding: EdgeInsets.only(
                                  bottom: index == _controller.items.length - 1
                                      ? 0
                                      : 10,
                                ),
                                child: AppEntityRowCard(
                                  title: item.name,
                                  subtitle: item.description,
                                  badge: AppBadge(
                                    label: item.phoneNumber,
                                    tone: item.isPrimary
                                        ? AppBadgeTone.warning
                                        : AppBadgeTone.neutral,
                                    uppercase: false,
                                  ),
                                  trailing: const Icon(
                                    Icons.call_outlined,
                                    size: 18,
                                  ),
                                  onTap: () => _call(item.phoneNumber),
                                ),
                              );
                            }),
                        ],
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
