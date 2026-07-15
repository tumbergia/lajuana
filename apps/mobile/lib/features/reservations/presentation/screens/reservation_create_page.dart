import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'package:mobile_domain/src/gen/channel.dart';
import 'package:mobile_domain/src/gen/reservation_create.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/providers/presentation/widgets/provider_phone_field.dart';
import 'package:mobile/features/reservations/infrastructure/remote/reservations_api_error.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/shared/input_validation.dart';

const _channelLabels = <Channel, String>{
  Channel.FACEBOOK: 'Facebook',
  Channel.INSTAGRAM: 'Instagram',
  Channel.WHATSAPP: 'WhatsApp',
  Channel.EMAIL: 'Email',
};

/// Pantalla para crear una reserva manualmente (online-only).
class ReservationCreatePage extends StatefulWidget {
  const ReservationCreatePage({
    super.key,
    required this.reservationsModule,
    required this.catalogsModule,
  });

  final ReservationsModule reservationsModule;
  final CatalogsModule catalogsModule;

  @override
  State<ReservationCreatePage> createState() => _ReservationCreatePageState();
}

class _ReservationCreatePageState extends State<ReservationCreatePage> {
  final _participantsCtrl = TextEditingController(text: '1');
  final _holderNameCtrl = TextEditingController();
  final _holderEmailCtrl = TextEditingController();

  List<CatalogExperience> _experiences = const [];
  bool _loadingExperiences = true;
  String? _experiencesError;

  String? _selectedExperienceId;
  Channel? _channel;
  DateTime? _requestedDate;
  String? _holderPhone;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadExperiences();
  }

  @override
  void dispose() {
    _participantsCtrl.dispose();
    _holderNameCtrl.dispose();
    _holderEmailCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadExperiences() async {
    setState(() {
      _loadingExperiences = true;
      _experiencesError = null;
    });
    try {
      // Misma fuente que la vista Experiencias: bootstrap/pull del stream
      // experiences (el refresh genérico puede dejar el catálogo incompleto).
      try {
        await widget.catalogsModule.repository.refreshExperiencesFromServer();
      } catch (_) {
        // Local cache is enough if offline / sync fails.
      }
      final items = await widget.catalogsModule.experiences.list(
        includeInactive: false,
      );
      if (!mounted) return;
      setState(() {
        _experiences = items;
        _loadingExperiences = false;
        // Drop selection if it disappeared after refresh.
        if (_selectedExperienceId != null &&
            !_experiences.any((e) => e.id == _selectedExperienceId)) {
          _selectedExperienceId = null;
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loadingExperiences = false;
        _experiencesError =
            'No se pudieron cargar las experiencias. Intenta de nuevo.';
      });
    }
  }

  CatalogExperience? get _selectedExperience {
    final id = _selectedExperienceId;
    if (id == null) return null;
    for (final experience in _experiences) {
      if (experience.id == id) return experience;
    }
    return null;
  }

  /// Id remoto para el API; cae al id local si aún no hay remote_id.
  String _experienceApiId(CatalogExperience experience) {
    final remote = experience.remoteId?.trim();
    if (remote != null && remote.isNotEmpty) return remote;
    return experience.id;
  }

  bool get _canSubmit {
    final participants = InputValidation.parseInteger(_participantsCtrl.text);
    return !_saving &&
        !_loadingExperiences &&
        _selectedExperienceId != null &&
        _channel != null &&
        participants != null &&
        participants > 0 &&
        InputValidation.isValidOptionalEmail(_holderEmailCtrl.text);
  }

  String? _nullableText(String value) {
    final trimmed = value.trim();
    return trimmed.isEmpty ? null : trimmed;
  }

  String _formatDate(DateTime date) {
    final y = date.year.toString().padLeft(4, '0');
    final m = date.month.toString().padLeft(2, '0');
    final d = date.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _requestedDate ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 2),
    );
    if (picked == null || !mounted) return;
    setState(() => _requestedDate = picked);
  }

  Future<void> _submit() async {
    if (!_canSubmit) return;

    final participants = InputValidation.parseInteger(_participantsCtrl.text);
    if (participants == null || participants < 1 || _channel == null) return;

    setState(() => _saving = true);
    try {
      final experience = _selectedExperience;
      if (experience == null) {
        setState(() => _saving = false);
        return;
      }

      final detail =
          await widget.reservationsModule.repository.createReservation(
        ReservationCreate(
          experienceId: _experienceApiId(experience),
          participantCount: participants,
          channel: _channel!,
          requestedDate:
              _requestedDate == null ? null : _formatDate(_requestedDate!),
          holderName: _nullableText(_holderNameCtrl.text),
          holderEmail: _nullableText(_holderEmailCtrl.text),
          holderPhone: _holderPhone,
        ),
      );

      if (!mounted) return;
      showAppToast(context, message: 'Reserva creada correctamente');
      Navigator.of(context).pop(detail.id);
    } on ReservationsApiFailure catch (e) {
      if (!mounted) return;
      showAppToast(
        context,
        message: e.message.isNotEmpty
            ? e.message
            : 'No se pudo crear la reserva. Intenta de nuevo.',
        isError: true,
      );
    } catch (_) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo crear la reserva. Intenta de nuevo.',
        isError: true,
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      scrollable: true,
      appBar: AppBar(
        title: Text(
          'Nueva reserva',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: _saving ? null : () => Navigator.of(context).pop(),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const AppSectionHeader(
            eyebrow: 'Gestion',
            title: 'Nueva reserva',
            subtitle:
                'Registra una reserva manual con experiencia, canal de origen y datos del titular.',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 20),
          _FormBlock(
            title: 'Experiencia',
            children: [
              if (_loadingExperiences)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_experiencesError != null) ...[
                Text(
                  _experiencesError!,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.error,
                      ),
                ),
                const SizedBox(height: 8),
                AppButton(
                  label: 'Reintentar',
                  variant: AppButtonVariant.secondary,
                  onPressed: _loadExperiences,
                ),
              ] else if (_experiences.isEmpty)
                Text(
                  'No hay experiencias disponibles.',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                )
              else
                DropdownButtonFormField<String>(
                  value: _selectedExperienceId,
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Experiencia *',
                    border: OutlineInputBorder(),
                  ),
                  items: _experiences
                      .map(
                        (experience) => DropdownMenuItem(
                          value: experience.id,
                          child: Text(
                            experience.name,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: _saving
                      ? null
                      : (value) {
                          setState(() => _selectedExperienceId = value);
                        },
                ),
            ],
          ),
          _FormBlock(
            title: 'Fecha y cupo',
            children: [
              InkWell(
                onTap: _saving ? null : _pickDate,
                borderRadius: BorderRadius.circular(8),
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Fecha solicitada',
                    border: OutlineInputBorder(),
                    suffixIcon: Icon(Icons.calendar_today_rounded, size: 20),
                  ),
                  child: Text(
                    _requestedDate == null
                        ? 'Sin fecha'
                        : _formatDate(_requestedDate!),
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: _requestedDate == null
                              ? Theme.of(context).colorScheme.onSurfaceVariant
                              : null,
                        ),
                  ),
                ),
              ),
              if (_requestedDate != null) ...[
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton(
                    onPressed:
                        _saving ? null : () => setState(() => _requestedDate = null),
                    child: const Text('Quitar fecha'),
                  ),
                ),
              ],
              const SizedBox(height: 12),
              AppTextField(
                controller: _participantsCtrl,
                label: 'Participantes *',
                hintText: 'Ej: 4',
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                onChanged: (_) => setState(() {}),
              ),
            ],
          ),
          _FormBlock(
            title: 'Canal de origen',
            children: [
              DropdownButtonFormField<Channel>(
                value: _channel,
                decoration: const InputDecoration(
                  labelText: 'Canal de origen *',
                  border: OutlineInputBorder(),
                ),
                items: Channel.values
                    .map(
                      (channel) => DropdownMenuItem(
                        value: channel,
                        child: Text(_channelLabels[channel] ?? channel.value),
                      ),
                    )
                    .toList(growable: false),
                onChanged: _saving
                    ? null
                    : (value) {
                        setState(() => _channel = value);
                      },
              ),
            ],
          ),
          _FormBlock(
            title: 'Titular',
            children: [
              AppTextField(
                controller: _holderNameCtrl,
                label: 'Nombre del titular',
                hintText: 'Ej: Ana Perez',
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              AppTextField(
                controller: _holderEmailCtrl,
                label: 'Email',
                hintText: 'Ej: ana@correo.com',
                keyboardType: TextInputType.emailAddress,
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              ProviderPhoneField(
                label: 'Telefono',
                onChanged: (value) {
                  setState(() => _holderPhone = value);
                },
              ),
            ],
          ),
          const SizedBox(height: 8),
          AppButton(
            label: _saving ? 'Creando...' : 'Crear reserva',
            icon: Icons.add,
            expanded: true,
            onPressed: _canSubmit ? _submit : null,
          ),
        ],
      ),
    );
  }
}

class _FormBlock extends StatelessWidget {
  const _FormBlock({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title.toUpperCase(),
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.7,
                ),
          ),
          const SizedBox(height: 10),
          ...children,
        ],
      ),
    );
  }
}
