import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import 'package:mobile_ui/mobile_ui.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experience_form_controller.dart';

final _integerInputFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.digitsOnly,
];

final _decimalInputFormatters = <TextInputFormatter>[
  FilteringTextInputFormatter.allow(RegExp(r'^\d*[,.]?\d*')),
];

class ExperienceFormPage extends StatefulWidget {
  const ExperienceFormPage({
    super.key,
    required this.module,
    required this.authController,
    this.editing,
  });

  final CatalogsModule module;
  final AuthController authController;
  final CatalogExperience? editing;

  @override
  State<ExperienceFormPage> createState() => _ExperienceFormPageState();
}

class _ExperienceFormPageState extends State<ExperienceFormPage> {
  final ExperienceFormController _controller = ExperienceFormController();

  late final TextEditingController _nombreCtrl;
  late final TextEditingController _descripcionCtrl;

  late final TextEditingController _duracionExperienciaCtrl;
  late final TextEditingController _duracionRecorridoCtrl;
  late final TextEditingController _textoDuracionCtrl;

  late final TextEditingController _distanciaCtrl;
  late final TextEditingController _terrenoCtrl;
  late final TextEditingController _notasTerrenoCtrl;

  late final TextEditingController _monedaCtrl;
  late final TextEditingController _notasTarifaCtrl;
  final TextEditingController _tarifaMinCtrl = TextEditingController();
  final TextEditingController _tarifaMaxCtrl = TextEditingController();
  final TextEditingController _tarifaValorCtrl = TextEditingController();

  final TextEditingController _incluyeInputCtrl = TextEditingController();
  late final TextEditingController _incluyeTextoCtrl;

  bool _guardando = false;

  bool get _esEdicion => widget.editing != null;

  @override
  void initState() {
    super.initState();
    if (_esEdicion) {
      _controller.loadFromExperience(widget.editing!);
    }
    _nombreCtrl = TextEditingController(text: _controller.nombre);
    _descripcionCtrl = TextEditingController(text: _controller.descripcion);

    _duracionExperienciaCtrl = TextEditingController(
      text: _controller.duracionExperienciaMinutos?.toString() ?? '',
    );
    _duracionRecorridoCtrl = TextEditingController(
      text: _controller.duracionRecorridoMinutos?.toString() ?? '',
    );
    _textoDuracionCtrl = TextEditingController(
      text: _controller.textoDuracionVisible ?? '',
    );

    _distanciaCtrl = TextEditingController(
      text: _controller.distanciaKm?.toString() ?? '',
    );
    _terrenoCtrl = TextEditingController(text: _controller.terreno);
    _notasTerrenoCtrl = TextEditingController(
      text: _controller.notasTerreno ?? '',
    );

    _monedaCtrl = TextEditingController(text: _controller.moneda);
    _notasTarifaCtrl = TextEditingController(
      text: _controller.notasTarifa ?? '',
    );
    _incluyeTextoCtrl = TextEditingController(
      text: _controller.textoIncluyeVisible ?? '',
    );
  }

  @override
  void dispose() {
    _nombreCtrl.dispose();
    _descripcionCtrl.dispose();

    _duracionExperienciaCtrl.dispose();
    _duracionRecorridoCtrl.dispose();
    _textoDuracionCtrl.dispose();
    _distanciaCtrl.dispose();
    _terrenoCtrl.dispose();
    _notasTerrenoCtrl.dispose();

    _monedaCtrl.dispose();
    _notasTarifaCtrl.dispose();
    _tarifaMinCtrl.dispose();
    _tarifaMaxCtrl.dispose();
    _tarifaValorCtrl.dispose();
    _incluyeInputCtrl.dispose();
    _incluyeTextoCtrl.dispose();

    _controller.dispose();
    super.dispose();
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final image = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1200,
      maxHeight: 1200,
      imageQuality: 80,
    );
    if (image == null) return;
    final bytes = await image.readAsBytes();
    if (!mounted) return;
    final base64 = base64Encode(bytes);
    _controller.actualizarImageBase64(base64);
  }

  void _agregarTarifa() {
    final min = int.tryParse(_tarifaMinCtrl.text.trim());
    final max = int.tryParse(_tarifaMaxCtrl.text.trim());
    final valor = int.tryParse(_tarifaValorCtrl.text.trim());

    if (min == null || max == null || valor == null) {
      showAppToast(
        context,
        message:
            'Completa personas desde, personas hasta y valor por persona para agregar la tarifa.',
        isError: true,
      );
      return;
    }

    _controller.agregarTarifa(
      ExperiencePricingTierDraft(
        minParticipants: min,
        maxParticipants: max,
        pricePerPerson: valor,
      ),
    );
    _tarifaMinCtrl.clear();
    _tarifaMaxCtrl.clear();
    _tarifaValorCtrl.clear();
  }

  Future<void> _editarTarifa(int index) async {
    final tier = _controller.tarifas[index];

    final result = await showModalBottomSheet<Map<String, int>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _TarifaEditSheet(
        minInicial: tier.minParticipants,
        maxInicial: tier.maxParticipants,
        valorInicial: tier.pricePerPerson,
      ),
    );

    if (result != null && mounted) {
      _controller.actualizarTarifa(
        index,
        ExperiencePricingTierDraft(
          minParticipants: result['min']!,
          maxParticipants: result['max']!,
          pricePerPerson: result['val']!,
        ),
      );
    }
  }

  void _agregarIncluye() {
    _controller.agregarIncluye(_incluyeInputCtrl.text);
    _incluyeInputCtrl.clear();
  }

  Future<void> _guardar() async {
    // Capturar texto pendiente en inputs antes de validar
    if (_incluyeInputCtrl.text.trim().isNotEmpty) {
      _agregarIncluye();
    }

    final validationError = _controller.validar();
    if (validationError != null) {
      showAppToast(context, message: validationError, isError: true);
      return;
    }

    setState(() {
      _guardando = true;
    });
    try {
      if (_esEdicion) {
        await widget.module.experiences.update(
          id: widget.editing!.id,
          name: _controller.nombre.trim(),
          slug: _controller.identificadorUrl.trim(),
          description: _controller.descripcion.trim(),
          level: _controller.nivel,
          imageBase64: _controller.imageBase64,
          difficulty: _controller.dificultad,
          duration: _controller.buildDuration(),
          routeDetails: _controller.buildRouteDetails(),
          pricing: _controller.buildPricing(),
          inclusions: _controller.buildInclusions(),
          isActive: _controller.activa,
        );
      } else {
        await widget.module.experiences.create(
          name: _controller.nombre.trim(),
          slug: _controller.identificadorUrl.trim(),
          description: _controller.descripcion.trim(),
          level: _controller.nivel,
          imageBase64: _controller.imageBase64,
          difficulty: _controller.dificultad,
          duration: _controller.buildDuration(),
          routeDetails: _controller.buildRouteDetails(),
          pricing: _controller.buildPricing(),
          inclusions: _controller.buildInclusions(),
          isActive: _controller.activa,
        );
      }

      if (!mounted) return;
      showAppToast(
        context,
        message: _esEdicion
            ? 'Experiencia actualizada correctamente'
            : 'Experiencia creada correctamente',
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (!mounted) return;
      showAppToast(
        context,
        message: 'No se pudo guardar la experiencia. Intenta de nuevo.',
        isError: true,
      );
    } finally {
      if (mounted) {
        setState(() {
          _guardando = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppSectionHeader(
                eyebrow: 'Experiencias',
                title: _esEdicion ? 'Editar experiencia' : 'Nueva experiencia',
                subtitle:
                    'Completa la ficha comercial y operativa base de la experiencia.',
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView(
                  children: [
                    _FormBlock(
                      title: 'Informacion principal',
                      children: [
                        AppTextField(
                          controller: _nombreCtrl,
                          label: 'Nombre de la experiencia',
                          hintText: 'Ej: Sendero de pino y bosque alto',
                          prefixIcon: const Icon(Icons.label_rounded, size: 20),
                          onChanged: _controller.actualizarNombre,
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _descripcionCtrl,
                          label: 'Descripcion',
                          hintText:
                              'Describe de forma clara que hara el cliente.',
                          maxLines: 3,
                          prefixIcon: const Icon(Icons.description_rounded, size: 20),
                          onChanged: _controller.actualizarDescripcion,
                        ),
                        const SizedBox(height: 10),
                        _buildImagePicker(),
                      ],
                    ),
                    _FormBlock(
                      title: 'Duraciones',
                      children: [
                        _InfoText(
                          text:
                              'Solo necesitas dos tiempos: duracion total de experiencia y duracion del recorrido.',
                        ),
                        const SizedBox(height: 10),
                        LayoutBuilder(
                          builder: (context, constraints) {
                            final isWide = constraints.maxWidth >= 680;
                            if (!isWide) {
                              return Column(
                                children: [
                                  AppTextField(
                                    controller: _duracionExperienciaCtrl,
                                    label: 'Duracion experiencia (minutos)',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.schedule_rounded, size: 20),
                                    onChanged: (value) => _controller
                                        .actualizarDuracionExperiencia(
                                          int.tryParse(value.trim()),
                                        ),
                                  ),
                                  const SizedBox(height: 10),
                                  AppTextField(
                                    controller: _duracionRecorridoCtrl,
                                    label: 'Duracion recorrido (minutos)',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.timer_rounded, size: 20),
                                    onChanged: (value) =>
                                        _controller.actualizarDuracionRecorrido(
                                          int.tryParse(value.trim()),
                                        ),
                                  ),
                                ],
                              );
                            }
                            return Row(
                              children: [
                                Expanded(
                                  child: AppTextField(
                                    controller: _duracionExperienciaCtrl,
                                    label: 'Duracion experiencia (minutos)',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.schedule_rounded, size: 20),
                                    onChanged: (value) => _controller
                                        .actualizarDuracionExperiencia(
                                          int.tryParse(value.trim()),
                                        ),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: AppTextField(
                                    controller: _duracionRecorridoCtrl,
                                    label: 'Duracion recorrido (minutos)',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.timer_rounded, size: 20),
                                    onChanged: (value) =>
                                        _controller.actualizarDuracionRecorrido(
                                          int.tryParse(value.trim()),
                                        ),
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _textoDuracionCtrl,
                          label: 'Texto visible de duracion (opcional)',
                          hintText:
                              'Ej: Actividad 5 horas aprox. Recorrido 2 horas aprox.',
                          maxLines: 2,
                          prefixIcon: const Icon(Icons.text_fields_rounded, size: 20),
                          onChanged: _controller.actualizarTextoDuracionVisible,
                        ),
                      ],
                    ),
                    _FormBlock(
                      title: 'Ruta',
                      children: [
                        AppTextField(
                          controller: _terrenoCtrl,
                          label: 'Terreno',
                          hintText: 'Ej: Camino destapado entre bosque de pino',
                          prefixIcon: const Icon(Icons.terrain_rounded, size: 20),
                          onChanged: _controller.actualizarTerreno,
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _distanciaCtrl,
                          label: 'Distancia en kilometros (opcional)',
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          inputFormatters: _decimalInputFormatters,
                          prefixIcon: const Icon(Icons.straighten_rounded, size: 20),
                          onChanged: (value) =>
                              _controller.actualizarDistanciaKm(
                                double.tryParse(
                                  value.trim().replaceAll(',', '.'),
                                ),
                              ),
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _notasTerrenoCtrl,
                          label: 'Notas de ruta (opcional)',
                          maxLines: 2,
                          prefixIcon: const Icon(Icons.notes_rounded, size: 20),
                          onChanged: _controller.actualizarNotasTerreno,
                        ),
                      ],
                    ),
                    _FormBlock(
                      title: 'Tarifas por numero de personas',
                      children: [
                        _InfoText(
                          text:
                              'Agrega rangos sin cruces. Toca una tarifa para editarla.',
                        ),
                        const SizedBox(height: 10),
                        _HelpLabel(
                          label: 'Moneda y tipo de tarifa',
                          helpTitle: 'Tarifa neta',
                          helpMessage:
                              'Tarifa neta es el valor base por persona definido por operacion, antes de ajustes comerciales manuales.',
                        ),
                        AppTextField(
                          controller: _monedaCtrl,
                          label: null,
                          hintText: 'COP',
                          prefixIcon: const Icon(Icons.attach_money_rounded, size: 20),
                          onChanged: _controller.actualizarMoneda,
                        ),
                        const SizedBox(height: 10),
                        _FormSwitch(
                          label: 'Las tarifas estan en valor neto',
                          value: _controller.tarifasNetas,
                          onChanged: _controller.actualizarTarifasNetas,
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _notasTarifaCtrl,
                          label: 'Notas de tarifa (opcional)',
                          maxLines: 2,
                          prefixIcon: const Icon(Icons.receipt_rounded, size: 20),
                          onChanged: _controller.actualizarNotasTarifa,
                        ),
                        const SizedBox(height: 10),
                        LayoutBuilder(
                          builder: (context, constraints) {
                            final isWide = constraints.maxWidth >= 760;
                            if (!isWide) {
                              return Column(
                                children: [
                                  AppTextField(
                                    controller: _tarifaMinCtrl,
                                    label: 'Personas desde',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.person_rounded, size: 20),
                                  ),
                                  const SizedBox(height: 10),
                                  AppTextField(
                                    controller: _tarifaMaxCtrl,
                                    label: 'Personas hasta',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.group_add_rounded, size: 20),
                                  ),
                                  const SizedBox(height: 10),
                                  AppTextField(
                                    controller: _tarifaValorCtrl,
                                    label: 'Valor por persona',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.payments_rounded, size: 20),
                                  ),
                                ],
                              );
                            }
                            return Row(
                              children: [
                                Expanded(
                                  child: AppTextField(
                                    controller: _tarifaMinCtrl,
                                    label: 'Personas desde',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.person_rounded, size: 20),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: AppTextField(
                                    controller: _tarifaMaxCtrl,
                                    label: 'Personas hasta',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.group_add_rounded, size: 20),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: AppTextField(
                                    controller: _tarifaValorCtrl,
                                    label: 'Valor por persona',
                                    keyboardType: TextInputType.number,
                                    inputFormatters: _integerInputFormatters,
                                    prefixIcon: const Icon(Icons.payments_rounded, size: 20),
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
                        const SizedBox(height: 10),
                        AppButton(
                          label: 'Agregar tarifa',
                          icon: Icons.add_rounded,
                          variant: AppButtonVariant.secondary,
                          expanded: true,
                          onPressed: _agregarTarifa,
                        ),
                        const SizedBox(height: 12),
                        if (_controller.tarifas.isEmpty)
                          const _InfoText(text: 'Aun no has agregado tarifas.'),
                        ..._controller.tarifas.asMap().entries.map((entry) {
                          final index = entry.key;
                          final item = entry.value;
                          final valueLabel =
                              '${_controller.moneda} ${item.pricePerPerson}';
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: _LineItem(
                              text:
                                  '${item.minParticipants}-${item.maxParticipants} personas | $valueLabel por persona',
                              icon: Icons.paid_rounded,
                              onTap: () => _editarTarifa(index),
                              onRemove: () => _controller.eliminarTarifa(index),
                            ),
                          );
                        }),
                      ],
                    ),
                    _FormBlock(
                      title: 'Incluye',
                      children: [
                        _InfoText(
                          text:
                              'Cada item debe representar algo concreto que recibe el cliente.',
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _incluyeInputCtrl,
                          label: 'Nuevo item incluido',
                          hintText: 'Ej: Almuerzo tradicional campesino',
                          prefixIcon: const Icon(Icons.playlist_add_rounded, size: 20),
                        ),
                        const SizedBox(height: 10),
                        AppButton(
                          label: 'Agregar item',
                          icon: Icons.add_rounded,
                          variant: AppButtonVariant.secondary,
                          expanded: true,
                          onPressed: _agregarIncluye,
                        ),
                        const SizedBox(height: 10),
                        if (_controller.incluye.isEmpty)
                          const _InfoText(
                            text: 'Aun no has agregado items en Incluye.',
                          ),
                        ..._controller.incluye.asMap().entries.map((entry) {
                          final index = entry.key;
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: _LineItem(
                              text: entry.value,
                              icon: Icons.check_circle_rounded,
                              onRemove: () =>
                                  _controller.eliminarIncluye(index),
                            ),
                          );
                        }),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: _incluyeTextoCtrl,
                          label: 'Texto visible de incluye (opcional)',
                          maxLines: 2,
                          prefixIcon: const Icon(Icons.text_fields_rounded, size: 20),
                          onChanged: _controller.actualizarTextoIncluyeVisible,
                        ),
                      ],
                    ),
                    _FormBlock(
                      title: 'Estado y nivel',
                      children: [
                        _SelectField(
                          label: 'Nivel recomendado',
                          value: _controller.nivel,
                          onChanged: _controller.actualizarNivel,
                          items: const [
                            DropdownMenuItem(
                              value: 'basic',
                              child: Text('Basico'),
                            ),
                            DropdownMenuItem(
                              value: 'intermediate',
                              child: Text('Intermedio'),
                            ),
                            DropdownMenuItem(
                              value: 'advanced',
                              child: Text('Avanzado'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        _SelectField(
                          label: 'Dificultad del recorrido',
                          value: _controller.dificultad,
                          onChanged: _controller.actualizarDificultad,
                          items: const [
                            DropdownMenuItem(
                              value: 'basic',
                              child: Text('Basica'),
                            ),
                            DropdownMenuItem(
                              value: 'intermediate',
                              child: Text('Intermedia'),
                            ),
                            DropdownMenuItem(
                              value: 'advanced',
                              child: Text('Avanzada'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        _FormSwitch(
                          label: 'Experiencia activa',
                          value: _controller.activa,
                          onChanged: _controller.actualizarActiva,
                        ),
                      ],
                    ),
                    _ActionButtons(
                      guardando: _guardando,
                      onGuardar: _guardando ? null : _guardar,
                      onCancelar: () => Navigator.of(context).pop(),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildImagePicker() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'IMAGEN'.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            fontWeight: FontWeight.w800,
            letterSpacing: 1.8,
          ),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onTap: _pickImage,
          child: Container(
            width: double.infinity,
            height: 160,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerLow,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: Theme.of(context).colorScheme.outlineVariant,
              ),
            ),
            child: _controller.imageBase64 != null &&
                    _controller.imageBase64!.isNotEmpty
                ? ClipRRect(
                    borderRadius: BorderRadius.circular(7),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Image.memory(
                          base64Decode(_controller.imageBase64!),
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => const SizedBox.shrink(),
                        ),
                        Positioned(
                          top: 8,
                          right: 8,
                          child: Material(
                            color: Theme.of(context)
                                .colorScheme
                                .surface
                                .withValues(alpha: 0.85),
                            borderRadius: BorderRadius.circular(20),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(20),
                              onTap: () {
                                _controller.actualizarImageBase64(null);
                              },
                              child: const Padding(
                                padding: EdgeInsets.all(6),
                                child: Icon(
                                  Icons.close_rounded,
                                  size: 18,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.add_photo_alternate_rounded,
                        size: 40,
                        color: Theme.of(context).colorScheme.onSurfaceVariant,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Toca para seleccionar imagen',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
          ),
        ),
      ],
    );
  }
}

/// Bottom sheet content for editing a pricing tier.
/// StatefulWidget ensures TextEditingController lifecycle is managed properly.
class _TarifaEditSheet extends StatefulWidget {
  const _TarifaEditSheet({
    required this.minInicial,
    required this.maxInicial,
    required this.valorInicial,
  });

  final int minInicial;
  final int maxInicial;
  final int valorInicial;

  @override
  State<_TarifaEditSheet> createState() => _TarifaEditSheetState();
}

class _TarifaEditSheetState extends State<_TarifaEditSheet> {
  late final TextEditingController _minCtrl;
  late final TextEditingController _maxCtrl;
  late final TextEditingController _valCtrl;

  @override
  void initState() {
    super.initState();
    _minCtrl = TextEditingController(text: widget.minInicial.toString());
    _maxCtrl = TextEditingController(text: widget.maxInicial.toString());
    _valCtrl = TextEditingController(text: widget.valorInicial.toString());
  }

  @override
  void dispose() {
    _minCtrl.dispose();
    _maxCtrl.dispose();
    _valCtrl.dispose();
    super.dispose();
  }

  void _guardar() {
    final min = int.tryParse(_minCtrl.text.trim());
    final max = int.tryParse(_maxCtrl.text.trim());
    final val = int.tryParse(_valCtrl.text.trim());
    if (min != null && max != null && val != null) {
      Navigator.of(context).pop(<String, int>{'min': min, 'max': max, 'val': val});
      return;
    }
    showAppToast(
      context,
      message: 'Completa todos los campos numericos de la tarifa.',
      isError: true,
    );
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: EdgeInsets.only(
        left: 24, right: 24, top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40, height: 4,
            decoration: BoxDecoration(
              color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          Text('Editar tarifa', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          AppTextField(
            controller: _minCtrl,
            label: 'Personas desde',
            keyboardType: TextInputType.number,
            inputFormatters: _integerInputFormatters,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _maxCtrl,
            label: 'Personas hasta',
            keyboardType: TextInputType.number,
            inputFormatters: _integerInputFormatters,
          ),
          const SizedBox(height: 10),
          AppTextField(
            controller: _valCtrl,
            label: 'Valor por persona',
            keyboardType: TextInputType.number,
            inputFormatters: _integerInputFormatters,
          ),
          const SizedBox(height: 16),
          Row(children: [
            Expanded(child: AppButton(label: 'Cancelar', variant: AppButtonVariant.ghost, onPressed: () => Navigator.of(context).pop())),
            const SizedBox(width: 10),
            Expanded(child: AppButton(label: 'Guardar', onPressed: _guardar)),
          ]),
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

class _HelpLabel extends StatelessWidget {
  const _HelpLabel({
    required this.label,
    required this.helpTitle,
    required this.helpMessage,
  });

  final String label;
  final String helpTitle;
  final String helpMessage;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        children: [
          Flexible(
            child: Text(
              label.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                fontWeight: FontWeight.w800,
                letterSpacing: 1.8,
              ),
            ),
          ),
          const SizedBox(width: 6),
          AppTermHelp(title: helpTitle, message: helpMessage),
        ],
      ),
    );
  }
}

class _InfoText extends StatelessWidget {
  const _InfoText({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
        color: Theme.of(context).colorScheme.onSurfaceVariant,
      ),
    );
  }
}

class _FormSwitch extends StatelessWidget {
  const _FormSwitch({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  final String label;
  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) {
    return SwitchListTile(
      contentPadding: EdgeInsets.zero,
      title: Text(label),
      value: value,
      onChanged: onChanged,
    );
  }
}

class _LineItem extends StatelessWidget {
  const _LineItem({
    required this.text,
    this.onTap,
    required this.onRemove,
    this.icon,
  });

  final String text;
  final VoidCallback? onTap;
  final VoidCallback onRemove;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Row(
        children: [
          if (icon != null) ...[
            Icon(icon, size: 18, color: scheme.primary),
            const SizedBox(width: 10),
          ],
          Expanded(child: Text(text)),
          if (onTap != null) ...[
            IconButton(
              onPressed: onTap,
              icon: Icon(Icons.edit_rounded, size: 16, color: scheme.primary),
              tooltip: 'Editar',
            ),
          ],
          IconButton(
            onPressed: onRemove,
            icon: Icon(Icons.close_rounded, size: 16, color: scheme.error),
            tooltip: 'Eliminar',
          ),
        ],
      ),
    );
  }
}

class _SelectField extends StatelessWidget {
  const _SelectField({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String label;
  final String value;
  final List<DropdownMenuItem<String>> items;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      initialValue: value,
      decoration: InputDecoration(labelText: label),
      items: items,
      onChanged: (next) {
        if (next == null) return;
        onChanged(next);
      },
    );
  }
}

class _ActionButtons extends StatelessWidget {
  const _ActionButtons({
    required this.guardando,
    required this.onGuardar,
    required this.onCancelar,
  });

  final bool guardando;
  final VoidCallback? onGuardar;
  final VoidCallback onCancelar;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 520;
        final saveLabel = guardando ? 'Guardando...' : 'Guardar experiencia';

        if (!isWide) {
          return Column(
            children: [
              AppButton(
                label: saveLabel,
                expanded: true,
                onPressed: onGuardar,
              ),
              const SizedBox(height: 10),
              AppButton(
                label: 'Cancelar',
                expanded: true,
                variant: AppButtonVariant.ghost,
                onPressed: onCancelar,
              ),
            ],
          );
        }
        return Row(
          children: [
            Expanded(
              child: AppButton(
                label: 'Cancelar',
                expanded: true,
                variant: AppButtonVariant.ghost,
                onPressed: onCancelar,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: AppButton(
                label: saveLabel,
                expanded: true,
                onPressed: onGuardar,
              ),
            ),
          ],
        );
      },
    );
  }
}
