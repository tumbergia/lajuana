import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile/features/providers/presentation/models/provider_view_models.dart';
import 'package:mobile/features/providers/presentation/utils/phone_country.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_catalog_contact_actions.dart';

class ProviderDetailSheet extends StatefulWidget {
  const ProviderDetailSheet({
    super.key,
    required this.provider,
    required this.loadDetails,
    this.onEdit,
    this.onDeactivate,
    this.onReactivate,
  });

  final ProviderRecord provider;
  final Future<ProviderRecord> Function() loadDetails;
  final VoidCallback? onEdit;
  final VoidCallback? onDeactivate;
  final VoidCallback? onReactivate;

  @override
  State<ProviderDetailSheet> createState() => _ProviderDetailSheetState();
}

class _ProviderDetailSheetState extends State<ProviderDetailSheet> {
  ProviderRecord? _details;
  var _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final details = await widget.loadDetails();
      if (!mounted) return;
      setState(() {
        _details = details;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _details = widget.provider;
        _loading = false;
        _error = 'No se pudieron cargar todos los detalles.';
      });
    }
  }

  ProviderRecord get _provider => _details ?? widget.provider;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final provider = _provider;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Symbols.handshake, size: 36, color: scheme.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        provider.name,
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        provider.subtitle,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: scheme.onSurfaceVariant,
                            ),
                      ),
                    ],
                  ),
                ),
                AppBadge(
                  label: provider.statusLabel,
                  tone: provider.statusTone,
                  uppercase: false,
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (_loading) const AppCenteredLoader(fill: false),
            if (!_loading) ...[
              if (_error != null) ...[
                Text(
                  _error!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: scheme.error,
                      ),
                ),
                const SizedBox(height: 12),
              ],
              _DetailSection(
                title: 'Contacto',
                children: [
                  _detailRow('Nombre', provider.contactName),
                  _detailRow('Correo', provider.email),
                  _detailRow(
                    'Telefono / WhatsApp',
                    formatPhoneForDisplay(provider.whatsappPhone),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ProviderCatalogContactActions(
                email: provider.email,
                whatsappPhone: provider.whatsappPhone,
              ),
              const SizedBox(height: 16),
              _DetailSection(
                title: 'Operacion',
                children: [
                  _detailRow('Tipo', provider.typeLabel),
                  _detailRow('Estado', provider.statusLabel),
                  _detailRow('Ubicacion', provider.locationLabel),
                  if (provider.serviceCategories.isNotEmpty)
                    _detailRow(
                      'Categorias',
                      provider.serviceCategories.join(', '),
                    ),
                ],
              ),
              const SizedBox(height: 16),
              _DetailSection(
                title: 'Notas',
                children: [
                  _detailRow('Tarifa', provider.tariffNotes),
                  _detailRow('Capacidad', provider.capacityNotes),
                  _detailRow('Operativas', provider.operationalNotes),
                  _detailRow('Origen', provider.sourceNotes),
                ],
              ),
              const SizedBox(height: 24),
              if (widget.onEdit != null) ...[
                AppButton(
                  label: 'Editar',
                  icon: Icons.edit_rounded,
                  expanded: true,
                  onPressed: () {
                    Navigator.of(context).pop();
                    widget.onEdit!();
                  },
                ),
                const SizedBox(height: 10),
              ],
              if (provider.isInactive && widget.onReactivate != null)
                AppButton(
                  label: 'Reactivar',
                  icon: Icons.restore_rounded,
                  variant: AppButtonVariant.secondary,
                  expanded: true,
                  onPressed: () {
                    Navigator.of(context).pop();
                    widget.onReactivate!();
                  },
                )
              else if (!provider.isInactive && widget.onDeactivate != null)
                AppButton(
                  label: 'Desactivar',
                  icon: Icons.delete_outline_rounded,
                  variant: AppButtonVariant.secondary,
                  expanded: true,
                  onPressed: () {
                    Navigator.of(context).pop();
                    widget.onDeactivate!();
                  },
                ),
              if (widget.onEdit != null ||
                  widget.onDeactivate != null ||
                  widget.onReactivate != null)
                const SizedBox(height: 10),
              AppButton(
                label: 'Cerrar',
                icon: Icons.close_rounded,
                variant: AppButtonVariant.secondary,
                expanded: true,
                onPressed: () => Navigator.of(context).pop(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget? _detailRow(String label, String? value) {
    if (value == null || value.trim().isEmpty || value == '—') {
      return null;
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AppEntityRowCard(
        title: label,
        subtitle: value,
      ),
    );
  }
}

class _DetailSection extends StatelessWidget {
  const _DetailSection({
    required this.title,
    required this.children,
  });

  final String title;
  final List<Widget?> children;

  @override
  Widget build(BuildContext context) {
    final visible = children.whereType<Widget>().toList(growable: false);
    if (visible.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                letterSpacing: 1.2,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
        ),
        const SizedBox(height: 8),
        ...visible,
      ],
    );
  }
}
