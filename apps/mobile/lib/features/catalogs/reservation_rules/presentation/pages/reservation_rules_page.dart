import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_switch_row.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/reservation_rules/presentation/controllers/reservation_rules_controller.dart';

class ReservationRulesPage extends StatefulWidget {
  const ReservationRulesPage({
    super.key,
    required this.module,
    required this.authController,
  });

  final CatalogsModule module;
  final AuthController authController;

  @override
  State<ReservationRulesPage> createState() => _ReservationRulesPageState();
}

class _ReservationRulesPageState extends State<ReservationRulesPage>
    with RefreshableState {
  late final ReservationRulesController _controller;
  final TextEditingController _minDaysCtrl = TextEditingController();
  final TextEditingController _ttlCtrl = TextEditingController();
  final TextEditingController _minAgeCtrl = TextEditingController();
  final TextEditingController _maxAgeCtrl = TextEditingController();
  bool _requirePaymentProof = true;
  bool _editing = false;
  bool _saving = false;
  String? _error;

  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

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
  Future<void> onRefresh() => _controller.refreshFromServer();

  @override
  void initState() {
    super.initState();
    _controller = ReservationRulesController(
      repository: widget.module.reservationRules,
      catalogsRepository: widget.module.repository,
    );
    _controller.addListener(_syncFormFromController);
    _controller.loadLocalThenRefresh();
  }

  @override
  void dispose() {
    _controller.removeListener(_syncFormFromController);
    _controller.dispose();
    _minDaysCtrl.dispose();
    _ttlCtrl.dispose();
    _minAgeCtrl.dispose();
    _maxAgeCtrl.dispose();
    super.dispose();
  }

  void _syncFormFromController({bool force = false}) {
    final rules = _controller.rules;
    if (rules == null) return;
    if (_editing && !force) return;
    _minDaysCtrl.text = rules.minDaysInAdvance.toString();
    _requirePaymentProof = rules.requirePaymentProofForConfirmation;
    _ttlCtrl.text = rules.reservationDraftTtlMinutes.toString();
    _minAgeCtrl.text = rules.minAge.toString();
    _maxAgeCtrl.text = rules.maxAge.toString();
  }

  Future<void> _save() async {
    final minDays = int.tryParse(_minDaysCtrl.text.trim());
    final ttl = int.tryParse(_ttlCtrl.text.trim());
    final minAge = int.tryParse(_minAgeCtrl.text.trim());
    final maxAge = int.tryParse(_maxAgeCtrl.text.trim());
    if (minDays == null ||
        minDays < 0 ||
        ttl == null ||
        ttl < 5 ||
        ttl > 20000 ||
        minAge == null ||
        maxAge == null ||
        minAge < 0 ||
        minAge > maxAge) {
      setState(() {
        _error =
            'Revisa anticipación, vencimiento (5–20000 min, hasta ~2 semanas) y rango de edades.';
      });
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await _controller.update(
        minDaysInAdvance: minDays,
        requirePaymentProofForConfirmation: _requirePaymentProof,
        reservationDraftTtlMinutes: ttl,
        minAge: minAge,
        maxAge: maxAge,
      );
      if (!mounted) return;
      setState(() {
        _editing = false;
      });
      showAppToast(context, message: 'Reglas de reserva actualizadas.');
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      if (mounted) {
        setState(() {
          _saving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final rules = _controller.rules;
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
                eyebrow: 'Configuración de La Juana',
                title: 'Reglas de reserva',
                subtitle: _isAdmin
                    ? 'Cambios aplican sobre reservas futuras'
                    : 'Solo lectura para tu rol',
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
                              title: 'No se pudieron cargar reglas',
                              subtitle: _controller.error!,
                              selected: true,
                            )
                          else if (rules != null && !_editing) ...[
                            AppEntityRowCard(
                              title: 'Anticipación mínima',
                              subtitle: '${rules.minDaysInAdvance} días',
                              leading: _leadingIcon(Symbols.calendar_month),
                              selected: true,
                            ),
                            const SizedBox(height: 10),
                            AppEntityRowCard(
                              title: 'Vencimiento de pre-reserva',
                              subtitle:
                                  '${rules.reservationDraftTtlMinutes} minutos',
                              leading: _leadingIcon(Symbols.timer),
                            ),
                            const SizedBox(height: 10),
                            AppEntityRowCard(
                              title: 'Edades permitidas',
                              subtitle:
                                  '${rules.minAge} a ${rules.maxAge} años',
                              leading: _leadingIcon(Symbols.groups),
                            ),
                            const SizedBox(height: 10),
                            AppEntityRowCard(
                              title: 'Comprobante requerido',
                              subtitle: rules.requirePaymentProofForConfirmation
                                  ? 'Sí'
                                  : 'No',
                              leading: _leadingIcon(Symbols.receipt_long),
                            ),
                            if (_isAdmin) ...[
                              const SizedBox(height: 12),
                              AppButton(
                                label: 'Editar',
                                icon: Icons.edit_rounded,
                                expanded: true,
                                onPressed: () {
                                  _syncFormFromController(force: true);
                                  setState(() {
                                    _editing = true;
                                    _error = null;
                                  });
                                },
                              ),
                            ],
                          ] else if (rules != null && _editing) ...[
                            AppTextField(
                              controller: _minDaysCtrl,
                              label: 'Mínimo de días',
                              inputKind: AppTextInputKind.integer,
                            ),
                            const SizedBox(height: 10),
                            AppTextField(
                              controller: _ttlCtrl,
                              label: 'Vencimiento de pre-reserva (minutos)',
                              hintText: '5–20000 (hasta ~2 semanas)',
                              inputKind: AppTextInputKind.integer,
                            ),
                            const SizedBox(height: 10),
                            AppTextField(
                              controller: _minAgeCtrl,
                              label: 'Edad mínima',
                              inputKind: AppTextInputKind.integer,
                            ),
                            const SizedBox(height: 10),
                            AppTextField(
                              controller: _maxAgeCtrl,
                              label: 'Edad máxima',
                              inputKind: AppTextInputKind.integer,
                            ),
                            const SizedBox(height: 10),
                            AppSwitchRow(
                              title: 'Requerir comprobante para confirmar',
                              value: _requirePaymentProof,
                              onChanged: (value) {
                                setState(() {
                                  _requirePaymentProof = value;
                                });
                              },
                            ),
                            if (_error != null) ...[
                              const SizedBox(height: 12),
                              AppBadge(
                                label: _error!,
                                tone: AppBadgeTone.danger,
                                uppercase: false,
                              ),
                            ],
                            const SizedBox(height: 12),
                            AppButton(
                              label: _saving ? 'Guardando...' : 'Guardar',
                              expanded: true,
                              onPressed: _saving ? null : _save,
                            ),
                            const SizedBox(height: 8),
                            AppButton(
                              label: 'Cancelar',
                              expanded: true,
                              variant: AppButtonVariant.secondary,
                              onPressed: _saving
                                  ? null
                                  : () {
                                      setState(() {
                                        _editing = false;
                                        _error = null;
                                      });
                                      _syncFormFromController(force: true);
                                    },
                            ),
                          ],
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
