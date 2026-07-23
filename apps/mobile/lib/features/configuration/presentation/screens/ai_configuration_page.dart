import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';

import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile/features/providers/presentation/utils/phone_country.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_phone_field.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_error.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_date_leading.dart';
import 'package:mobile_domain/src/reservations/reservation_list_item.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_card.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_search_field.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_select_field.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

class AiConfigurationPage extends StatefulWidget {
  const AiConfigurationPage({
    super.key,
    required this.module,
    this.reservationsRepository,
  });

  final LaJuanaConfigurationModule module;
  final ReservationsRepository? reservationsRepository;

  @override
  State<AiConfigurationPage> createState() => _AiConfigurationPageState();
}

class _AiConfigurationPageState extends State<AiConfigurationPage>
    with RefreshableState {
  final _services = List<String?>.filled(3, null);
  final _models = List.generate(3, (_) => TextEditingController());
  final _keys = List.generate(3, (_) => TextEditingController());
  final _configured = List<bool>.filled(3, false);
  final _mutedPhones = <String>[];

  List<ReservationListItem> _disabledReservations = const [];
  List<ReservationListItem> _selectableReservations = const [];
  ReservationListItem? _selectedReservation;

  bool _enabled = false;
  bool _loading = true;
  bool _saving = false;
  bool _editingModels = false;
  bool _busyAssistant = false;
  bool _busyProviderMode = false;
  bool _busyMuteAdd = false;
  String? _busyMuteRemovePhone;
  bool _busyReservationDisable = false;
  String? _busyReservationEnableId;

  /// `env` = recomendado desde servidor; `manual` = modelos digitados.
  String _providerMode = 'env';
  AiEnvProvider _envProvider = const AiEnvProvider(available: false);
  int _version = 1;
  int _phoneFieldResetToken = 0;
  String? _pendingPhoneE164;
  String? _error;
  String? _loadError;
  String? _reservationsError;

  static const _serviceLabels = {
    'gemini': 'Gemini',
    'openai': 'OpenAI',
    'groq': 'Groq',
    'openrouter': 'OpenRouter',
  };

  ReservationsRepository? get _reservationsRepo =>
      widget.reservationsRepository ?? widget.module.reservationsRepository;

  bool get _usesEnv => _providerMode != 'manual';

  @override
  Future<void> onRefresh() => _load();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [..._models, ..._keys]) {
      c.dispose();
    }
    super.dispose();
  }

  String _friendlyError(Object e) => e is ConfigurationApiFailure
      ? e.message
      : 'No se pudo cargar la configuración.';

  Future<void> _load() async {
    setState(() {
      _loadError = null;
      if (!_editingModels) _loading = true;
    });
    try {
      final results = await Future.wait<Object?>([
        widget.module.api.getAi(),
        _fetchReservationLists(),
      ]);
      final value = results[0] as AiConfiguration;
      final reservationResult = results[1] as _ReservationListsResult;
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _disabledReservations = reservationResult.disabled;
        _selectableReservations = reservationResult.selectable;
        _reservationsError = reservationResult.error;
        _selectedReservation = null;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loadError = _friendlyError(e);
        _loading = false;
      });
    }
  }

  Future<_ReservationListsResult> _fetchReservationLists() async {
    final repo = _reservationsRepo;
    if (repo == null) {
      return const _ReservationListsResult(
        error: 'No hay acceso al módulo de reservas en esta sesión.',
      );
    }
    try {
      final all = await repo.listReservations();
      return _ReservationListsResult(
        disabled: all
            .where((item) => !item.isDeleted && item.assistantDisabled)
            .toList(growable: false),
        selectable: all
            .where((item) => !item.isDeleted && !item.assistantDisabled)
            .toList(growable: false),
      );
    } catch (e) {
      return _ReservationListsResult(
        error: e is ReservationsApiFailure
            ? e.message
            : 'No se pudieron cargar las reservas.',
      );
    }
  }

  Future<void> _refreshReservationLists() async {
    final result = await _fetchReservationLists();
    if (!mounted) return;
    setState(() {
      _disabledReservations = result.disabled;
      _selectableReservations = result.selectable;
      _reservationsError = result.error;
    });
  }

  bool get _hasManualModelReady => List.generate(3, (i) => i).any(
    (i) =>
        _services[i] != null &&
        _models[i].text.trim().isNotEmpty &&
        _configured[i],
  );

  bool get _canEnableAssistant {
    if (_usesEnv) return _envProvider.available;
    return _hasManualModelReady;
  }

  Future<void> _setProviderMode(String mode) async {
    if (_busyProviderMode || mode == _providerMode) return;
    final previousMode = _providerMode;
    final previousEnabled = _enabled;
    // Si pasas a personalizado sin modelos listos y el asistente está on,
    // se apaga para dejar configurar; no se bloquea el cambio de modo.
    final nextEnabled = mode == 'manual' && !_hasManualModelReady
        ? false
        : _enabled;
    setState(() {
      _providerMode = mode;
      _enabled = nextEnabled;
      _busyProviderMode = true;
      if (mode == 'env') {
        _editingModels = false;
      } else if (!_hasManualModelReady) {
        _editingModels = true;
      }
    });
    try {
      final value = await _persistAi(
        enabled: nextEnabled,
        mutedPhones: List<String>.from(_mutedPhones),
        providerMode: mode,
      );
      if (!mounted) return;
      final keepEditing = mode == 'manual' && !_hasManualModelReady;
      setState(() {
        _applySnapshot(value);
        _busyProviderMode = false;
        if (keepEditing) _editingModels = true;
      });
      if (mode == 'env') {
        showAppToast(context, message: 'Usando modelos recomendados.');
      } else if (keepEditing) {
        showAppToast(
          context,
          message: previousEnabled && !nextEnabled
              ? 'Asistente en pausa. Configura un modelo y actívalo de nuevo.'
              : 'Listo: completa un modelo y guárdalo.',
        );
      } else {
        showAppToast(context, message: 'Usando modelos personalizados.');
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _providerMode = previousMode;
        _enabled = previousEnabled;
        _busyProviderMode = false;
        _editingModels = false;
      });
      showAppToast(context, message: _friendlyError(e));
      if (e is ConfigurationApiFailure && e.statusCode == 409) {
        await _load();
      }
    }
  }

  void _applySnapshot(AiConfiguration value) {
    _enabled = value.enabled;
    _version = value.version;
    _providerMode = value.providerMode;
    _envProvider = value.envProvider;
    _mutedPhones
      ..clear()
      ..addAll(value.mutedPhones);
    for (var i = 0; i < 3; i++) {
      _services[i] = null;
      _models[i].clear();
      _configured[i] = false;
      _keys[i].clear();
    }
    for (final route in value.routes) {
      final i = route.position - 1;
      if (i < 0 || i >= 3) continue;
      _services[i] = route.service;
      _models[i].text = route.model ?? '';
      _configured[i] = route.credentialConfigured;
      _keys[i].clear();
    }
  }

  List<Map<String, dynamic>> _routesPayload() => List.generate(
    3,
    (i) => {
      'position': i + 1,
      'service': _services[i],
      'model': _models[i].text.trim().isEmpty ? null : _models[i].text.trim(),
      if (_keys[i].text.isNotEmpty) 'api_key': _keys[i].text,
    },
  );

  Future<AiConfiguration> _persistAi({
    required bool enabled,
    required List<String> mutedPhones,
    bool includeRoutes = false,
    String? providerMode,
  }) {
    return widget.module.api.updateAi({
      'enabled': enabled,
      'provider_mode': providerMode ?? _providerMode,
      'muted_phones': mutedPhones,
      'expected_version': _version,
      if (includeRoutes) 'routes': _routesPayload(),
    });
  }

  Future<void> _cancelEditModels() async {
    setState(() {
      _editingModels = false;
      _error = null;
      _loading = true;
    });
    await _load();
  }

  Future<void> _saveModels() async {
    for (var i = 0; i < 3; i++) {
      if (_services[i] != null && _models[i].text.trim().isEmpty) {
        setState(() {
          _error = 'El modelo ${i + 1} necesita un nombre de modelo.';
        });
        return;
      }
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final value = await _persistAi(
        enabled: _enabled,
        mutedPhones: List<String>.from(_mutedPhones),
        includeRoutes: true,
        providerMode: 'manual',
      );
      for (final c in _keys) {
        c.clear();
      }
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _saving = false;
        _editingModels = false;
      });
      showAppToast(context, message: 'Modelos de IA guardados.');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = _friendlyError(e);
        _saving = false;
      });
    }
  }

  Future<void> _setEnabled(bool enabled) async {
    if (_busyAssistant) return;
    if (enabled && !_canEnableAssistant) {
      showAppToast(
        context,
        message: _usesEnv
            ? 'Los modelos recomendados no están disponibles ahora.'
            : 'Configura al menos un modelo con servicio, nombre y clave.',
      );
      return;
    }
    final previous = _enabled;
    setState(() {
      _enabled = enabled;
      _busyAssistant = true;
    });
    try {
      final value = await _persistAi(
        enabled: enabled,
        mutedPhones: List<String>.from(_mutedPhones),
      );
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _busyAssistant = false;
      });
      showAppToast(
        context,
        message: enabled
            ? 'Asistente activado.'
            : 'Asistente desactivado por completo.',
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _enabled = previous;
        _busyAssistant = false;
      });
      showAppToast(context, message: _friendlyError(e));
      if (e is ConfigurationApiFailure && e.statusCode == 409) {
        await _load();
      }
    }
  }

  Future<void> _addMutedPhone() async {
    final e164 = _pendingPhoneE164;
    if (e164 == null || e164.isEmpty || _busyMuteAdd) return;
    final next = List<String>.from(_mutedPhones);
    final digits = e164.replaceAll(RegExp(r'\D'), '');
    if (next.any((p) => p.replaceAll(RegExp(r'\D'), '') == digits)) {
      showAppToast(context, message: 'Ese número ya está silenciado.');
      return;
    }
    next.add(e164);
    setState(() => _busyMuteAdd = true);
    try {
      final value = await _persistAi(enabled: _enabled, mutedPhones: next);
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _pendingPhoneE164 = null;
        _phoneFieldResetToken++;
        _busyMuteAdd = false;
      });
      showAppToast(context, message: 'Número silenciado.');
    } catch (e) {
      if (!mounted) return;
      setState(() => _busyMuteAdd = false);
      showAppToast(context, message: _friendlyError(e));
    }
  }

  Future<void> _removeMutedPhone(String phone) async {
    if (_busyMuteRemovePhone != null) return;
    final next = List<String>.from(_mutedPhones)..remove(phone);
    setState(() => _busyMuteRemovePhone = phone);
    try {
      final value = await _persistAi(enabled: _enabled, mutedPhones: next);
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _busyMuteRemovePhone = null;
      });
      showAppToast(context, message: 'Número reactivado.');
    } catch (e) {
      if (!mounted) return;
      setState(() => _busyMuteRemovePhone = null);
      showAppToast(context, message: _friendlyError(e));
    }
  }

  Future<void> _disableSelectedReservation() async {
    final repo = _reservationsRepo;
    final selected = _selectedReservation;
    if (repo == null || selected == null || _busyReservationDisable) return;
    setState(() => _busyReservationDisable = true);
    try {
      await repo.updateReservation(
        reservationId: selected.id,
        assistantDisabled: true,
      );
      await _refreshReservationLists();
      if (!mounted) return;
      setState(() {
        _selectedReservation = null;
        _busyReservationDisable = false;
      });
      showAppToast(
        context,
        message: 'Asistente desactivado para ${selected.code}.',
      );
    } catch (_) {
      if (!mounted) return;
      setState(() => _busyReservationDisable = false);
      showAppToast(
        context,
        message: 'No se pudo desactivar el asistente para esa reserva.',
      );
    }
  }

  Future<void> _enableReservation(ReservationListItem item) async {
    final repo = _reservationsRepo;
    if (repo == null || _busyReservationEnableId != null) return;
    setState(() => _busyReservationEnableId = item.id);
    try {
      await repo.updateReservation(
        reservationId: item.id,
        assistantDisabled: false,
      );
      await _refreshReservationLists();
      if (!mounted) return;
      setState(() => _busyReservationEnableId = null);
      showAppToast(context, message: 'Asistente reactivado para ${item.code}.');
    } catch (_) {
      if (!mounted) return;
      setState(() => _busyReservationEnableId = null);
      showAppToast(context, message: 'No se pudo reactivar el asistente.');
    }
  }

  String _modelSummary(int i) {
    final service = _services[i];
    if (service == null) return 'Sin configurar';
    final label = _serviceLabels[service] ?? service;
    final model = _models[i].text.trim();
    final keyNote = _configured[i] ? 'clave guardada' : 'sin clave';
    if (model.isEmpty) return '$label · $keyNote';
    return '$label · $model · $keyNote';
  }

  String _reservationCardSubtitle(ReservationListItem item) {
    final name = (item.holderName ?? '').trim();
    final phone = (item.holderPhone ?? '').trim();
    return [
      if (name.isNotEmpty) name else 'Sin nombre',
      if (phone.isNotEmpty) formatPhoneForDisplay(phone) else 'Sin teléfono',
    ].join(' · ');
  }

  Widget _reservationDateLeading(ReservationListItem item) {
    final raw = item.requestedDate;
    if (raw == null || raw.isEmpty) {
      return _leadingIcon(Symbols.event);
    }
    return ReservationDateLeading(requestedDate: raw);
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

  Widget _sectionHint(BuildContext context, String text) {
    return Text(
      text,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }

  Widget _leadingIcon(IconData icon) {
    return Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
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

  Widget _sectionCard(List<Widget> children) {
    return AppCard(
      tone: AppCardTone.surface,
      outlined: true,
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: children,
      ),
    );
  }

  Widget _assistantSection(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return _sectionCard([
      _sectionTitle(context, 'Asistente'),
      const SizedBox(height: 8),
      _sectionHint(
        context,
        'Apaga el asistente por completo. Los mensajes de WhatsApp se seguirán guardando, pero no habrá respuesta automática.',
      ),
      const SizedBox(height: 10),
      AppEntityRowCard(
        title: 'Asistente',
        subtitle: _enabled ? 'Activado' : 'Desactivado',
        leading: _leadingIcon(Symbols.smart_toy),
        selected: _enabled,
        trailing: _busyAssistant
            ? const SizedBox(
                width: 36,
                height: 36,
                child: Padding(
                  padding: EdgeInsets.all(8),
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              )
            : _SquarePowerToggle(
                isOn: _enabled,
                onColor: scheme.primary,
                offColor: scheme.outlineVariant,
                glowColor: scheme.primary,
              ),
        onTap: _busyAssistant || _editingModels
            ? null
            : () => _setEnabled(!_enabled),
      ),
    ]);
  }

  String _envModelSubtitle() {
    if (!_envProvider.available) {
      return 'Modelos recomendados no disponibles ahora';
    }
    final model = (_envProvider.model ?? '').trim();
    final keys = _envProvider.keysConfigured;
    final fallbacks = _envProvider.fallbackModels;
    final parts = <String>[
      if (model.isNotEmpty) model else 'Modelo principal listo',
      if (fallbacks.isNotEmpty)
        '${fallbacks.length} respaldo${fallbacks.length == 1 ? '' : 's'}',
      if (keys > 1) '$keys claves de acceso',
    ];
    return parts.isEmpty ? 'Listo para usar' : parts.join(' · ');
  }

  Widget _modelsSection(BuildContext context) {
    if (_editingModels && !_usesEnv) {
      return _sectionCard([
        _sectionTitle(context, 'Modelos personalizados'),
        const SizedBox(height: 8),
        _sectionHint(
          context,
          'Configura uno o más modelos. El primero se usa primero y los demás son respaldo si falla.',
        ),
        for (int i = 0; i < 3; i++) ...[
          const SizedBox(height: 12),
          _sectionTitle(
            context,
            'Modelo ${i + 1}${i == 0 ? ' · principal' : ' · respaldo'}',
          ),
          const SizedBox(height: 8),
          AppSelectField<String>(
            key: ValueKey('ai-service-$i-${_services[i]}'),
            label: 'Servicio de IA',
            value: _services[i],
            hintText: 'Selecciona un servicio',
            items: _serviceLabels.entries
                .map(
                  (e) => DropdownMenuItem(value: e.key, child: Text(e.value)),
                )
                .toList(),
            onChanged: (v) => setState(() => _services[i] = v),
          ),
          const SizedBox(height: 10),
          AppTextField(controller: _models[i], label: 'Nombre del modelo'),
          const SizedBox(height: 10),
          AppTextField(
            controller: _keys[i],
            label: _configured[i]
                ? 'Clave guardada · escribe para reemplazar'
                : 'Clave de acceso',
            inputKind: AppTextInputKind.password,
            obscureText: true,
          ),
        ],
        if (_error != null) ...[
          const SizedBox(height: 12),
          AppStatusBanner(
            title: 'No se pudo guardar',
            message: _error!,
            tone: AppStatusBannerTone.danger,
            icon: Icons.error_outline_rounded,
          ),
        ],
        const SizedBox(height: 12),
        AppButton(
          label: _saving ? 'Guardando...' : 'Guardar modelos',
          expanded: true,
          onPressed: _saving ? null : _saveModels,
        ),
        const SizedBox(height: 8),
        AppButton(
          label: 'Cancelar',
          expanded: true,
          variant: AppButtonVariant.secondary,
          onPressed: _saving ? null : _cancelEditModels,
        ),
      ]);
    }

    return _sectionCard([
      _sectionTitle(context, 'Modelos'),
      const SizedBox(height: 8),
      _sectionHint(
        context,
        'Un modelo es el “cerebro” que lee el mensaje y escribe la respuesta. '
        'Puedes usar los recomendados (ya preparados para La Juana, con respaldos si uno falla) '
        'o configurar los tuyos.',
      ),
      const SizedBox(height: 10),
      AppEntityRowCard(
        title: 'Recomendados',
        subtitle: _envModelSubtitle(),
        leading: _leadingIcon(Symbols.verified),
        selected: _usesEnv,
        trailing: Icon(
          _usesEnv ? Icons.check_circle_rounded : Icons.circle_outlined,
          size: 22,
          color: _usesEnv
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.outlineVariant,
        ),
        onTap: _busyProviderMode || _editingModels
            ? null
            : () => _setProviderMode('env'),
      ),
      const SizedBox(height: 8),
      AppEntityRowCard(
        title: 'Personalizados',
        subtitle: _usesEnv
            ? 'Elige servicio, nombre de modelo y clave tú mismo'
            : 'Activo · ${_manualModelsSummary()}',
        leading: _leadingIcon(Symbols.tune),
        selected: !_usesEnv,
        trailing: Icon(
          !_usesEnv ? Icons.check_circle_rounded : Icons.circle_outlined,
          size: 22,
          color: !_usesEnv
              ? Theme.of(context).colorScheme.primary
              : Theme.of(context).colorScheme.outlineVariant,
        ),
        onTap: _busyProviderMode || _editingModels
            ? null
            : () => _setProviderMode('manual'),
      ),
      if (!_usesEnv) ...[
        const SizedBox(height: 12),
        for (int i = 0; i < 3; i++) ...[
          AppEntityRowCard(
            title: 'Modelo ${i + 1}${i == 0 ? ' · principal' : ' · respaldo'}',
            subtitle: _modelSummary(i),
            leading: _leadingIcon(
              i == 0 ? Symbols.psychology : Symbols.alt_route,
            ),
          ),
          if (i < 2) const SizedBox(height: 10),
        ],
        const SizedBox(height: 12),
        AppButton(
          label: 'Editar modelos',
          icon: Icons.edit_rounded,
          expanded: true,
          onPressed: () => setState(() => _editingModels = true),
        ),
      ],
    ]);
  }

  String _manualModelsSummary() {
    final count = List.generate(3, (i) => i)
        .where(
          (i) =>
              _services[i] != null &&
              _models[i].text.trim().isNotEmpty &&
              _configured[i],
        )
        .length;
    if (count == 0) return 'Sin modelos configurados';
    return '$count modelo${count == 1 ? '' : 's'} listo${count == 1 ? '' : 's'}';
  }

  Widget _mutedPhonesSection(BuildContext context) {
    return _sectionCard([
      _sectionTitle(context, 'Números silenciados'),
      const SizedBox(height: 8),
      _sectionHint(
        context,
        'El asistente no responderá a estos teléfonos. Los mensajes se guardan igual.',
      ),
      const SizedBox(height: 10),
      if (_mutedPhones.isEmpty)
        AppEntityRowCard(
          title: 'Ningún número silenciado',
          subtitle: 'Agrega un teléfono para silenciar el asistente',
          leading: _leadingIcon(Symbols.phone_disabled),
        )
      else
        for (final phone in _mutedPhones) ...[
          AppEntityRowCard(
            title: formatPhoneForDisplay(phone),
            subtitle: 'Asistente desactivado',
            leading: _leadingIcon(Symbols.phone_disabled),
            trailing: _busyMuteRemovePhone == phone
                ? const SizedBox(
                    width: 32,
                    height: 32,
                    child: Padding(
                      padding: EdgeInsets.all(6),
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20),
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints.tightFor(
                      width: 32,
                      height: 32,
                    ),
                    onPressed: _busyMuteRemovePhone != null
                        ? null
                        : () => _removeMutedPhone(phone),
                  ),
          ),
          const SizedBox(height: 8),
        ],
      const SizedBox(height: 8),
      ProviderPhoneField(
        key: ValueKey('mute-phone-$_phoneFieldResetToken'),
        label: 'Número de teléfono',
        onChanged: (value) => _pendingPhoneE164 = value,
      ),
      const SizedBox(height: 8),
      AppButton(
        label: _busyMuteAdd ? 'Silenciando...' : 'Silenciar número',
        expanded: true,
        onPressed: _busyMuteAdd ? null : _addMutedPhone,
      ),
    ]);
  }

  Future<void> _pickReservation() async {
    if (_busyReservationDisable || _reservationsRepo == null) return;
    if (_selectableReservations.isEmpty) {
      showAppToast(
        context,
        message:
            _reservationsError ?? 'No hay reservas disponibles para silenciar.',
      );
      return;
    }
    final picked = await showModalBottomSheet<ReservationListItem>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _ReservationPickerSheet(
        reservations: _selectableReservations,
        selectedId: _selectedReservation?.id,
        subtitleBuilder: _reservationCardSubtitle,
      ),
    );
    if (picked == null || !mounted) return;
    setState(() => _selectedReservation = picked);
  }

  Widget _reservationsSection(BuildContext context) {
    final selected = _selectedReservation;
    return _sectionCard([
      _sectionTitle(context, 'Reservas sin asistente'),
      const SizedBox(height: 8),
      _sectionHint(
        context,
        'Desactiva el asistente para el teléfono de una reserva. Los mensajes de ese número se guardan sin respuesta automática.',
      ),
      const SizedBox(height: 10),
      if (_reservationsError != null) ...[
        AppStatusBanner(
          title: 'Reservas',
          message: _reservationsError!,
          tone: AppStatusBannerTone.danger,
          icon: Icons.error_outline_rounded,
        ),
        const SizedBox(height: 10),
      ],
      if (_disabledReservations.isEmpty)
        AppEntityRowCard(
          title: 'Ninguna reserva silenciada',
          subtitle: 'Selecciona una reserva para desactivar el asistente',
          leading: _leadingIcon(Symbols.event_busy),
        )
      else
        for (final item in _disabledReservations) ...[
          AppEntityRowCard(
            title: item.code,
            subtitle: _reservationCardSubtitle(item),
            leading: _reservationDateLeading(item),
            trailing: _busyReservationEnableId == item.id
                ? const SizedBox(
                    width: 32,
                    height: 32,
                    child: Padding(
                      padding: EdgeInsets.all(6),
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  )
                : IconButton(
                    icon: const Icon(Icons.close_rounded, size: 20),
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints.tightFor(
                      width: 32,
                      height: 32,
                    ),
                    onPressed: _busyReservationEnableId != null
                        ? null
                        : () => _enableReservation(item),
                  ),
          ),
          const SizedBox(height: 8),
        ],
      const SizedBox(height: 8),
      AppEntityRowCard(
        title: selected?.code ?? 'Elegir reserva',
        subtitle: selected == null
            ? (_selectableReservations.isEmpty
                  ? 'No hay reservas disponibles'
                  : '${_selectableReservations.length} disponibles · toca para elegir')
            : _reservationCardSubtitle(selected),
        leading: selected == null
            ? _leadingIcon(Symbols.search)
            : _reservationDateLeading(selected),
        trailing: const Icon(Icons.expand_more_rounded, size: 20),
        selected: selected != null,
        onTap: _busyReservationDisable ? null : _pickReservation,
      ),
      const SizedBox(height: 8),
      AppButton(
        label: _busyReservationDisable
            ? 'Desactivando...'
            : 'Desactivar asistente',
        expanded: true,
        onPressed:
            _reservationsRepo == null ||
                _busyReservationDisable ||
                selected == null
            ? null
            : _disableSelectedReservation,
      ),
    ]);
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
            title: 'Configuración de IA',
            subtitle:
                'Activa o apaga el asistente, configura sus modelos y siléncialo por teléfono o reserva.',
            trailing: AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.pop(context),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _loading
                ? const RefreshableViewport(child: AppCenteredLoader())
                : ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: [
                      if (_loadError != null) ...[
                        AppStatusBanner(
                          title: 'No se pudo cargar',
                          message: _loadError!,
                          tone: AppStatusBannerTone.danger,
                          icon: Icons.error_outline_rounded,
                        ),
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Reintentar',
                          expanded: true,
                          onPressed: _load,
                        ),
                      ] else ...[
                        _assistantSection(context),
                        const SizedBox(height: 16),
                        _modelsSection(context),
                        if (!_editingModels) ...[
                          const SizedBox(height: 16),
                          _mutedPhonesSection(context),
                          const SizedBox(height: 16),
                          _reservationsSection(context),
                        ],
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }
}

class _SquarePowerToggle extends StatelessWidget {
  const _SquarePowerToggle({
    required this.isOn,
    required this.onColor,
    required this.offColor,
    required this.glowColor,
  });

  final bool isOn;
  final Color onColor;
  final Color offColor;
  final Color glowColor;

  @override
  Widget build(BuildContext context) {
    final fill = isOn ? onColor : offColor.withValues(alpha: 0.35);
    final iconColor = isOn
        ? Theme.of(context).colorScheme.onPrimary
        : Theme.of(context).colorScheme.onSurfaceVariant;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 220),
      curve: Curves.easeOut,
      width: 36,
      height: 36,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: isOn ? onColor : offColor, width: 1.5),
        boxShadow: isOn
            ? [
                BoxShadow(
                  color: glowColor.withValues(alpha: 0.45),
                  blurRadius: 10,
                  spreadRadius: 0.5,
                ),
              ]
            : const [],
      ),
      child: Icon(Icons.power_settings_new_rounded, size: 18, color: iconColor),
    );
  }
}

class _ReservationListsResult {
  const _ReservationListsResult({
    this.disabled = const [],
    this.selectable = const [],
    this.error,
  });

  final List<ReservationListItem> disabled;
  final List<ReservationListItem> selectable;
  final String? error;
}

class _ReservationPickerSheet extends StatefulWidget {
  const _ReservationPickerSheet({
    required this.reservations,
    required this.subtitleBuilder,
    this.selectedId,
  });

  final List<ReservationListItem> reservations;
  final String? selectedId;
  final String Function(ReservationListItem) subtitleBuilder;

  @override
  State<_ReservationPickerSheet> createState() =>
      _ReservationPickerSheetState();
}

class _ReservationPickerSheetState extends State<_ReservationPickerSheet> {
  final _searchCtrl = TextEditingController();
  late List<ReservationListItem> _filtered;

  @override
  void initState() {
    super.initState();
    _filtered = widget.reservations;
    _searchCtrl.addListener(_applyFilter);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _applyFilter() {
    final q = _searchCtrl.text.trim().toLowerCase();
    setState(() {
      if (q.isEmpty) {
        _filtered = widget.reservations;
        return;
      }
      _filtered = widget.reservations
          .where((item) {
            final haystack = [
              item.code,
              item.holderName ?? '',
              item.holderPhone ?? '',
              item.experienceName ?? '',
            ].join(' ').toLowerCase();
            return haystack.contains(q);
          })
          .toList(growable: false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final maxHeight = MediaQuery.sizeOf(context).height * 0.8;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SizedBox(
        height: maxHeight,
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
            Text(
              'Seleccionar reserva',
              style: Theme.of(
                context,
              ).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            AppSearchField(
              controller: _searchCtrl,
              hintText: 'Buscar por codigo, nombre o telefono...',
            ),
            const SizedBox(height: 12),
            Expanded(
              child: _filtered.isEmpty
                  ? Center(
                      child: Text(
                        'No hay coincidencias',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                    )
                  : ListView.separated(
                      itemCount: _filtered.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        final item = _filtered[index];
                        final selected = item.id == widget.selectedId;
                        return AppEntityRowCard(
                          title: item.code,
                          subtitle: widget.subtitleBuilder(item),
                          selected: selected,
                          leading:
                              (item.requestedDate == null ||
                                  item.requestedDate!.isEmpty)
                              ? Container(
                                  width: 48,
                                  height: 48,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: scheme.surfaceContainerHighest,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Icon(
                                    Icons.event_rounded,
                                    size: 22,
                                    color: scheme.onSurfaceVariant,
                                  ),
                                )
                              : ReservationDateLeading(
                                  requestedDate: item.requestedDate,
                                ),
                          onTap: () => Navigator.of(context).pop(item),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
