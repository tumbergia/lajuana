import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experiences_controller.dart';
import 'package:mobile/features/catalogs/experiences/presentation/widgets/experience_card.dart';
import 'experience_detail_page.dart';
import 'experience_form_page.dart';

class ExperiencesPage extends StatefulWidget {
  const ExperiencesPage({
    super.key,
    required this.module,
    required this.authController,
  });

  final CatalogsModule module;
  final AuthController authController;

  @override
  State<ExperiencesPage> createState() => _ExperiencesPageState();
}

class _ExperiencesPageState extends State<ExperiencesPage> {
  late final ExperiencesController _controller;

  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

  @override
  void initState() {
    super.initState();
    _controller = ExperiencesController(
      repository: widget.module.experiences,
      catalogsRepository: widget.module.repository,
    );
    _controller.loadLocalThenRefresh();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _openCreate() async {
    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ExperienceFormPage(
          module: widget.module,
          authController: widget.authController,
        ),
      ),
    );
    await _controller.loadLocalThenRefresh(refreshServer: false);
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final isLoadingAny =
            _controller.isInitialLoading ||
            _controller.isRefreshing ||
            _controller.isSyncing;
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppSectionHeader(
                eyebrow: 'Catalogos',
                title: 'Experiencias',
                subtitle: 'Catalogo operativo para reservas',
                trailing: Wrap(
                  spacing: 8,
                  children: [
                    AppButton(
                      label: 'Sync',
                      icon: Icons.sync_rounded,
                      variant: AppButtonVariant.ghost,
                      onPressed: _controller.isSyncing
                          ? null
                          : () => _controller.syncNow(),
                    ),
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
              if (_isAdmin)
                AppButton(
                  label: 'Crear experiencia',
                  icon: Icons.add_rounded,
                  expanded: true,
                  onPressed: _openCreate,
                ),
              if (_isAdmin) const SizedBox(height: 12),
              Expanded(
                child: isLoadingAny
                    ? const AppCenteredLoader()
                    : ListView(
                        children: [
                          if (_controller.error != null)
                            AppEntityRowCard(
                              title: 'No se pudieron cargar experiencias',
                              subtitle: _controller.error!,
                              selected: true,
                            )
                          else if (_controller.items.isEmpty)
                            const AppEntityRowCard(
                              title: 'Sin experiencias',
                              subtitle: 'No hay registros disponibles',
                              selected: true,
                            )
                          else
                            ..._controller.items.asMap().entries.map((entry) {
                              final index = entry.key;
                              final experience = entry.value;
                              return Padding(
                                padding: EdgeInsets.only(
                                  bottom: index == _controller.items.length - 1
                                      ? 0
                                      : 10,
                                ),
                                child: ExperienceCard(
                                  experience: experience,
                                  onTap: () async {
                                    await Navigator.of(context).push(
                                      MaterialPageRoute<void>(
                                        builder: (_) => ExperienceDetailPage(
                                          module: widget.module,
                                          authController: widget.authController,
                                          experienceId: experience.id,
                                        ),
                                      ),
                                    );
                                    await _controller.loadLocalThenRefresh(
                                      refreshServer: false,
                                    );
                                  },
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
