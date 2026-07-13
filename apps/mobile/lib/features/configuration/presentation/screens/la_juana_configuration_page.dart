import 'package:flutter/material.dart';
import 'package:material_symbols_icons/symbols.dart';

import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/reservation_rules/presentation/pages/reservation_rules_page.dart';
import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/presentation/screens/ai_configuration_page.dart';
import 'package:mobile/features/configuration/presentation/screens/business_location_page.dart';
import 'package:mobile/features/configuration/presentation/screens/payment_methods_page.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';

class LaJuanaConfigurationPage extends StatelessWidget {
  const LaJuanaConfigurationPage({
    super.key,
    required this.module,
    required this.catalogsModule,
    required this.authController,
  });

  final LaJuanaConfigurationModule module;
  final CatalogsModule catalogsModule;
  final AuthController authController;

  void _open(BuildContext context, Widget page) =>
      Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));

  Widget _leadingIcon(BuildContext context, IconData icon) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Icon(
        icon,
        size: 22,
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
    child: ListView(
      children: [
        AppSectionHeader(
          eyebrow: 'Más',
          title: 'Configuración de La Juana',
          subtitle:
              'Administra reservas, inteligencia artificial, pagos y ubicación.',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => Navigator.pop(context),
          ),
        ),
        const SizedBox(height: 20),
        AppEntityRowCard(
          title: 'Reglas de reserva',
          subtitle: 'Anticipación, vencimiento, edades y comprobantes',
          leading: _leadingIcon(context, Symbols.event_note),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(
            context,
            ReservationRulesPage(
              module: catalogsModule,
              authController: authController,
            ),
          ),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Configuración de IA',
          subtitle: 'Servicios y rutas de respaldo del asistente',
          leading: _leadingIcon(context, Symbols.psychology),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(context, AiConfigurationPage(module: module)),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Métodos de pago',
          subtitle: 'Consignación bancaria y enlace Bold',
          leading: _leadingIcon(context, Symbols.payments),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(context, PaymentMethodsPage(module: module)),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Ubicación del negocio',
          subtitle: 'Dirección, indicaciones y punto en el mapa',
          leading: _leadingIcon(context, Symbols.location_on_rounded),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(context, BusinessLocationPage(module: module)),
        ),
      ],
    ),
  );
}
