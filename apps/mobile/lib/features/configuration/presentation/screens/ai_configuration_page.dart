import 'package:flutter/material.dart';

import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_select_field.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_switch_row.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

class AiConfigurationPage extends StatefulWidget {
  const AiConfigurationPage({super.key, required this.module});

  final LaJuanaConfigurationModule module;

  @override
  State<AiConfigurationPage> createState() => _AiConfigurationPageState();
}

class _AiConfigurationPageState extends State<AiConfigurationPage>
    with RefreshableState {
  final _services = List<String?>.filled(3, null);
  final _models = List.generate(3, (_) => TextEditingController());
  final _keys = List.generate(3, (_) => TextEditingController());
  final _configured = List<bool>.filled(3, false);
  bool _enabled = false;
  bool _loading = true;
  bool _saving = false;
  bool _editing = false;
  int _version = 1;
  String? _error;
  String? _loadError;

  static const _serviceLabels = {
    'gemini': 'Gemini',
    'openai': 'OpenAI',
    'groq': 'Groq',
    'openrouter': 'OpenRouter',
  };

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

  String _friendlyError(Object e) =>
      e is ConfigurationApiFailure ? e.message : 'No se pudo cargar la configuración.';

  Future<void> _load() async {
    setState(() {
      _loadError = null;
      if (!_editing) _loading = true;
    });
    try {
      final value = await widget.module.api.getAi();
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
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

  void _applySnapshot(AiConfiguration value) {
    _enabled = value.enabled;
    _version = value.version;
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

  Future<void> _cancelEdit() async {
    setState(() {
      _editing = false;
      _error = null;
      _loading = true;
    });
    await _load();
  }

  Future<void> _save() async {
    for (var i = 0; i < 3; i++) {
      if (_services[i] != null && _models[i].text.trim().isEmpty) {
        setState(() {
          _error = 'La ruta ${i + 1} necesita un modelo.';
        });
        return;
      }
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final routes = List.generate(
        3,
        (i) => {
          'position': i + 1,
          'service': _services[i],
          'model': _models[i].text.trim().isEmpty
              ? null
              : _models[i].text.trim(),
          if (_keys[i].text.isNotEmpty) 'api_key': _keys[i].text,
        },
      );
      final value = await widget.module.api.updateAi({
        'enabled': _enabled,
        'routes': routes,
        'expected_version': _version,
      });
      for (final c in _keys) {
        c.clear();
      }
      if (!mounted) return;
      setState(() {
        _applySnapshot(value);
        _saving = false;
        _editing = false;
      });
      showAppToast(context, message: 'Configuración de IA guardada.');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = _friendlyError(e);
        _saving = false;
      });
    }
  }

  String _routeSummary(int i) {
    final service = _services[i];
    if (service == null) return 'Sin configurar';
    final label = _serviceLabels[service] ?? service;
    final model = _models[i].text.trim();
    final keyNote = _configured[i] ? 'clave guardada' : 'sin clave';
    if (model.isEmpty) return '$label · $keyNote';
    return '$label · $model · $keyNote';
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
                'El asistente prueba estas tres rutas en orden. Los modelos no se completan automáticamente.',
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
                      ] else if (!_editing) ...[
                        AppEntityRowCard(
                          title: 'Asistente',
                          subtitle: _enabled ? 'Activado' : 'Desactivado',
                          selected: true,
                        ),
                        const SizedBox(height: 10),
                        for (int i = 0; i < 3; i++) ...[
                          AppEntityRowCard(
                            title:
                                'Ruta ${i + 1}${i == 0 ? ' · principal' : ' · respaldo'}',
                            subtitle: _routeSummary(i),
                          ),
                          if (i < 2) const SizedBox(height: 10),
                        ],
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Editar',
                          icon: Icons.edit_rounded,
                          expanded: true,
                          onPressed: () => setState(() => _editing = true),
                        ),
                      ] else ...[
                        AppSwitchRow(
                          title: 'Activar asistente con estas rutas',
                          value: _enabled,
                          onChanged: (v) => setState(() => _enabled = v),
                        ),
                        for (int i = 0; i < 3; i++) ...[
                          const SizedBox(height: 12),
                          _sectionTitle(
                            context,
                            'Ruta ${i + 1}${i == 0 ? ' · principal' : ' · respaldo'}',
                          ),
                          const SizedBox(height: 8),
                          AppSelectField<String>(
                            key: ValueKey('ai-service-$i-${_services[i]}'),
                            label: 'Servicio de IA',
                            value: _services[i],
                            hintText: 'Selecciona un servicio',
                            items: _serviceLabels.entries
                                .map(
                                  (e) => DropdownMenuItem(
                                    value: e.key,
                                    child: Text(e.value),
                                  ),
                                )
                                .toList(),
                            onChanged: (v) => setState(() => _services[i] = v),
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: _models[i],
                            label: 'Modelo del servicio',
                          ),
                          const SizedBox(height: 10),
                          AppTextField(
                            controller: _keys[i],
                            label: _configured[i]
                                ? 'Clave guardada · escribe para reemplazar'
                                : 'Clave de acceso',
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
                          label: _saving ? 'Guardando...' : 'Guardar',
                          expanded: true,
                          onPressed: _saving ? null : _save,
                        ),
                        const SizedBox(height: 8),
                        AppButton(
                          label: 'Cancelar',
                          expanded: true,
                          variant: AppButtonVariant.secondary,
                          onPressed: _saving ? null : _cancelEdit,
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
