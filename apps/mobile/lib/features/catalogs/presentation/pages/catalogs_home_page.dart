import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/reservation_rules/presentation/pages/reservation_rules_page.dart';
import 'package:mobile/features/catalogs/schedules/presentation/pages/schedules_page.dart';

class CatalogsHomePage extends StatelessWidget {
  const CatalogsHomePage({
    super.key,
    required this.module,
    required this.authController,
  });

  final CatalogsModule module;
  final AuthController authController;

  bool get _isAdmin => authController.currentUser?.role == 'admin';

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Mas',
            title: 'Catalogos',
            subtitle: 'Disponibilidad, reglas y referencias operativas',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 20),
          AppEntityRowCard(
            title: 'Fechas operativas',
            subtitle: 'Control de cupos y estados por salida',
            trailing: const Icon(Icons.chevron_right_rounded, size: 18),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => SchedulesPage(
                    module: module,
                    authController: authController,
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 10),
          if (_isAdmin) ...[
            AppEntityRowCard(
              title: 'Reglas de reserva',
              subtitle: 'Configuracion operativa y anticipacion minima',
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => ReservationRulesPage(
                      module: module,
                      authController: authController,
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
