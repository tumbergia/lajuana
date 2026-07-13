import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/reservation_rules/presentation/pages/reservation_rules_page.dart';

class CatalogsHomePage extends StatefulWidget {
  const CatalogsHomePage({
    super.key,
    required this.module,
    required this.authController,
  });

  final CatalogsModule module;
  final AuthController authController;

  @override
  State<CatalogsHomePage> createState() => _CatalogsHomePageState();
}

class _CatalogsHomePageState extends State<CatalogsHomePage>
    with RefreshableState {
  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

  @override
  Future<void> onRefresh() => widget.module.repository.autoSync();

  @override
  Widget build(BuildContext context) {
    return RefreshableViewport(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Más',
            title: 'Catálogos',
            subtitle: 'Disponibilidad, reglas y referencias operativas',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 20),
          if (_isAdmin) ...[
            AppEntityRowCard(
              title: 'Reglas de reserva',
              subtitle: 'Configuración operativa y anticipación mínima',
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => ReservationRulesPage(
                      module: widget.module,
                      authController: widget.authController,
                    ),
                  ),
                );
              },
            ),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}
