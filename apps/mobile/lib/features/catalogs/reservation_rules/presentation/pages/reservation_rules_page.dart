import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
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
  bool _requirePaymentProof = true;
  bool _editing = false;
  bool _saving = false;
  String? _error;

  bool get _isAdmin => widget.authController.currentUser?.role == 'admin';

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
    super.dispose();
  }

  void _syncFormFromController() {
    final rules = _controller.rules;
    if (rules == null) return;
    if (_editing) return;
    _minDaysCtrl.text = rules.minDaysInAdvance.toString();
    _requirePaymentProof = rules.requirePaymentProofForConfirmation;
  }

  Future<void> _save() async {
    final minDays = int.tryParse(_minDaysCtrl.text.trim());
    if (minDays == null || minDays < 0) {
      setState(() {
        _error = 'Los dias minimos deben ser >= 0.';
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
      );
      if (!mounted) return;
      setState(() {
        _editing = false;
      });
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
                eyebrow: 'Catalogos',
                title: 'Reglas de reserva',
                subtitle: _isAdmin
                    ? 'Cambios aplican sobre reservas futuras'
                    : 'Solo lectura para tu rol',
                trailing: Wrap(
                  spacing: 8,
                  children: [
                    AppButton(
                      label: _controller.isSyncing
                          ? 'Sincronizando...'
                          : 'Sync',
                      icon: Icons.sync_rounded,
                      variant: AppButtonVariant.ghost,
                      onPressed: _controller.isSyncing
                          ? null
                          : () => _controller.syncNow(),
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
                          else if (rules != null) ...[
                            AppEntityRowCard(
                              title: 'Anticipacion minima',
                              subtitle: '${rules.minDaysInAdvance} dias',
                              selected: true,
                            ),
                            const SizedBox(height: 10),
                            AppEntityRowCard(
                              title: 'Comprobante requerido',
                              subtitle: rules.requirePaymentProofForConfirmation
                                  ? 'Si'
                                  : 'No',
                            ),
                            if (_isAdmin) ...[
                              const SizedBox(height: 12),
                              if (!_editing)
                                AppButton(
                                  label: 'Editar regla',
                                  icon: Icons.edit_rounded,
                                  expanded: true,
                                  onPressed: () {
                                    setState(() {
                                      _editing = true;
                                    });
                                  },
                                )
                              else ...[
                                AppTextField(
                                  controller: _minDaysCtrl,
                                  label: 'Minimo de dias',
                                  keyboardType: TextInputType.number,
                                ),
                                const SizedBox(height: 8),
                                SwitchListTile(
                                  contentPadding: EdgeInsets.zero,
                                  title: const Text(
                                    'Requerir comprobante para confirmar',
                                  ),
                                  value: _requirePaymentProof,
                                  onChanged: (value) {
                                    setState(() {
                                      _requirePaymentProof = value;
                                    });
                                  },
                                ),
                                if (_error != null) ...[
                                  const SizedBox(height: 8),
                                  AppBadge(
                                    label: _error!,
                                    tone: AppBadgeTone.danger,
                                    uppercase: false,
                                  ),
                                ],
                                const SizedBox(height: 8),
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
                                  onPressed: () {
                                    setState(() {
                                      _editing = false;
                                      _error = null;
                                    });
                                  },
                                ),
                              ],
                            ],
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
