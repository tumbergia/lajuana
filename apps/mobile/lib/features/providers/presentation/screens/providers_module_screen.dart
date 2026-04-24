import 'package:flutter/material.dart';

import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_entity_row_card.dart';

/// Placeholder hasta conectar catálogo real de proveedores.
class ProvidersModuleScreen extends StatelessWidget {
  const ProvidersModuleScreen({super.key, this.showHeader = true});

  /// Si es false, la cabecera la aporta la pantalla contenedora (evita duplicar ruta).
  final bool showHeader;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: showHeader
          ? const EdgeInsets.fromLTRB(24, 24, 24, 24)
          : EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (showHeader) ...const [
            AppSectionHeader(
              eyebrow: 'Proveedores',
              title: 'Catalogo operativo',
              subtitle: 'Se cargara por demanda desde almacen local y sync',
            ),
            SizedBox(height: 20),
          ],
          const AppEntityRowCard(
            title: 'Sin datos aun',
            subtitle: 'Este modulo se habilitara en una iteracion posterior',
            selected: true,
          ),
        ],
      ),
    );
  }
}
