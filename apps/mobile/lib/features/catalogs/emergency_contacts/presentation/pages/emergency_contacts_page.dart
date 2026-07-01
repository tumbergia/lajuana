import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/emergency_contacts/presentation/controllers/emergency_contacts_controller.dart';

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

class _EmergencyContactsPageState extends State<EmergencyContactsPage>
    with RefreshableState {
  late final EmergencyContactsController _controller;

  @override
  Future<void> onRefresh() => _controller.refreshFromServer();

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
                trailing: AppButton(
                  label: 'Volver',
                  icon: Icons.arrow_back_rounded,
                  variant: AppButtonVariant.ghost,
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ),
              const SizedBox(height: 12),
              Expanded(
                child: isLoadingAny
                    ? const RefreshableViewport(child: AppCenteredLoader())
                    : ListView(
                        physics: const AlwaysScrollableScrollPhysics(),
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
