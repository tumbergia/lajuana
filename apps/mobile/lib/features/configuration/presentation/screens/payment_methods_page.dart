import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile/shared/input_validation.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_switch_row.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

class PaymentMethodsPage extends StatefulWidget {
  const PaymentMethodsPage({super.key, required this.module});

  final LaJuanaConfigurationModule module;

  @override
  State<PaymentMethodsPage> createState() => _PaymentMethodsPageState();
}

class _PaymentMethodsPageState extends State<PaymentMethodsPage>
    with RefreshableState {
  final bank = TextEditingController();
  final type = TextEditingController();
  final number = TextEditingController();
  final holder = TextEditingController();
  final holderId = TextEditingController();
  final note = TextEditingController();
  final boldUrl = TextEditingController();
  final boldFee = TextEditingController();
  final boldNote = TextEditingController();

  bool manual = true;
  bool bold = false;
  bool loading = true;
  bool saving = false;
  bool editing = false;
  String? error;
  String? loadError;

  @override
  Future<void> onRefresh() => _load();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [
      bank,
      type,
      number,
      holder,
      holderId,
      note,
      boldUrl,
      boldFee,
      boldNote,
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  String _friendlyError(Object e) =>
      e is ConfigurationApiFailure ? e.message : 'No se pudo cargar la configuración.';

  void _apply(PaymentConfiguration v) {
    bank.text = v.bank;
    type.text = v.accountType;
    number.text = v.accountNumber;
    holder.text = v.holderName;
    holderId.text = v.holderId;
    note.text = v.transferNote;
    boldUrl.text = v.boldUrl ?? '';
    boldFee.text = v.boldFee.toString();
    boldNote.text = v.boldNote;
    manual = v.manualEnabled;
    bold = v.boldEnabled;
  }

  Future<void> _load() async {
    setState(() {
      loadError = null;
      if (!editing) loading = true;
    });
    try {
      final v = await widget.module.api.getPayments();
      if (!mounted) return;
      setState(() {
        _apply(v);
        loading = false;
        error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loadError = _friendlyError(e);
        loading = false;
      });
    }
  }

  Future<void> _cancelEdit() async {
    setState(() {
      editing = false;
      error = null;
      loading = true;
    });
    await _load();
  }

  Future<void> _save() async {
    if (manual) {
      if (bank.text.trim().isEmpty ||
          type.text.trim().isEmpty ||
          number.text.trim().isEmpty ||
          holder.text.trim().isEmpty) {
        setState(() {
          error =
              'Completa banco, tipo de cuenta, número y titular para consignación.';
        });
        return;
      }
    }
    if (bold) {
      final fee = InputValidation.parseDecimal(boldFee.text);
      if (boldUrl.text.trim().isEmpty) {
        setState(() {
          error = 'El enlace de Bold es obligatorio si Bold está activo.';
        });
        return;
      }
      if (!InputValidation.isValidHttpUrl(boldUrl.text)) {
        setState(() {
          error =
              'El enlace de Bold debe ser una URL válida que empiece por http:// o https://.';
        });
        return;
      }
      if (fee == null || fee < 0 || fee > 100) {
        setState(() {
          error = 'La comisión Bold debe ser un número entre 0 y 100.';
        });
        return;
      }
    }

    setState(() {
      saving = true;
      error = null;
    });
    try {
      final fee = InputValidation.parseDecimal(boldFee.text) ?? 7;
      final v = await widget.module.api.updatePayments({
        'manual_transfer_enabled': manual,
        'account_bank': bank.text.trim(),
        'account_type': type.text.trim(),
        'account_number': number.text.trim(),
        'account_holder_name': holder.text.trim(),
        'account_holder_id': holderId.text.trim(),
        'transfer_note': note.text.trim(),
        'bold_enabled': bold,
        'bold_checkout_url': boldUrl.text.trim().isEmpty
            ? null
            : boldUrl.text.trim(),
        'bold_surcharge_percent': fee,
        'bold_note': boldNote.text.trim(),
      });
      if (!mounted) return;
      setState(() {
        _apply(v);
        saving = false;
        editing = false;
      });
      showAppToast(context, message: 'Métodos de pago actualizados.');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = _friendlyError(e);
        saving = false;
      });
    }
  }

  Widget _sectionTitle(BuildContext context, String text) {
    final theme = Theme.of(context);
    return Text(
      text.toUpperCase(),
      style: theme.textTheme.labelLarge?.copyWith(
        color: theme.colorScheme.onSurfaceVariant,
        fontWeight: FontWeight.w800,
        letterSpacing: 1.4,
      ),
    );
  }

  Widget _leadingIcon(IconData icon) {
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
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Configuración de La Juana',
            title: 'Métodos de pago',
            subtitle: 'El bot mostrará únicamente los métodos activos.',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.pop(context),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: loading
                ? const RefreshableViewport(child: AppCenteredLoader())
                : ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (loadError != null) ...[
                        AppStatusBanner(
                          title: 'No se pudo cargar',
                          message: loadError!,
                          tone: AppStatusBannerTone.danger,
                          icon: Icons.error_outline_rounded,
                        ),
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Reintentar',
                          expanded: true,
                          onPressed: _load,
                        ),
                      ] else if (!editing) ...[
                        AppEntityRowCard(
                          title: 'Consignación bancaria',
                          subtitle: manual
                              ? [
                                  if (bank.text.trim().isNotEmpty) bank.text.trim(),
                                  if (number.text.trim().isNotEmpty)
                                    number.text.trim(),
                                  if (holder.text.trim().isNotEmpty)
                                    holder.text.trim(),
                                ].join(' · ').ifEmpty('Activa')
                              : 'Desactivada',
                          leading: _leadingIcon(Symbols.account_balance),
                          selected: true,
                        ),
                        const SizedBox(height: 10),
                        AppEntityRowCard(
                          title: 'Bold',
                          subtitle: bold
                              ? 'Activo · comisión ${boldFee.text.trim()}%'
                              : 'Desactivado',
                          leading: _leadingIcon(Symbols.link),
                        ),
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Editar',
                          icon: Icons.edit_rounded,
                          expanded: true,
                          onPressed: () => setState(() => editing = true),
                        ),
                      ] else ...[
                        AppSwitchRow(
                          title: 'Aceptar consignación bancaria',
                          value: manual,
                          onChanged: (v) => setState(() => manual = v),
                        ),
                        if (manual) ...[
                          const SizedBox(height: 8),
                          _sectionTitle(context, 'Consignación'),
                          const SizedBox(height: 8),
                          AppTextField(controller: bank, label: 'Banco'),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: type,
                            label: 'Tipo de cuenta',
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: number,
                            label: 'Número de cuenta',
                            inputKind: AppTextInputKind.integer,
                          ),
                          const SizedBox(height: 10),
                          AppTextField(controller: holder, label: 'Titular'),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: holderId,
                            label: 'Documento del titular',
                            inputKind: AppTextInputKind.integer,
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: note,
                            label: 'Instrucciones para el cliente',
                            maxLines: 3,
                          ),
                        ],
                        const SizedBox(height: 12),
                        AppSwitchRow(
                          title: 'Aceptar pagos con Bold',
                          value: bold,
                          onChanged: (v) => setState(() => bold = v),
                        ),
                        if (bold) ...[
                          const SizedBox(height: 8),
                          _sectionTitle(context, 'Bold'),
                          const SizedBox(height: 8),
                          AppTextField(
                            controller: boldUrl,
                            label: 'Enlace fijo de pago Bold',
                            inputKind: AppTextInputKind.url,
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: boldFee,
                            label: 'Comisión adicional (%)',
                            inputKind: AppTextInputKind.decimal,
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: boldNote,
                            label: 'Nota para el cliente',
                            maxLines: 2,
                          ),
                        ],
                        if (error != null) ...[
                          const SizedBox(height: 12),
                          AppStatusBanner(
                            title: 'No se pudo guardar',
                            message: error!,
                            tone: AppStatusBannerTone.danger,
                            icon: Icons.error_outline_rounded,
                          ),
                        ],
                        const SizedBox(height: 12),
                        AppButton(
                          label: saving ? 'Guardando...' : 'Guardar',
                          expanded: true,
                          onPressed: saving ? null : _save,
                        ),
                        const SizedBox(height: 8),
                        AppButton(
                          label: 'Cancelar',
                          expanded: true,
                          variant: AppButtonVariant.secondary,
                          onPressed: saving ? null : _cancelEdit,
                        ),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

extension on String {
  String ifEmpty(String fallback) => isEmpty ? fallback : this;
}
