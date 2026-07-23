import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:latlong2/latlong.dart' hide Path;
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile/app/errors/user_facing_error.dart';
import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/domain/la_juana_configuration.dart';
import 'package:mobile/features/configuration/infrastructure/configuration_api_client.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

/// Rojo de marca (mismo tono del botón de correo en proveedores).
const Color _mapsActionRed = Color(0xFFD93025);

/// Rojo del pin: intenso en dark mode para contrastar con el basemap.
const Color _mapPinRedLight = Color(0xFFD93025);
const Color _mapPinRedDark = Color(0xFFFF2D20);

/// Invierte tiles claras → dark map con carreteras y líneas bien visibles.
/// Misma matriz que [darkModeTilesContainerBuilder] de flutter_map.
const ColorFilter _darkMapFromLightTilesFilter = ColorFilter.matrix(<double>[
  0.574, -1.43, -0.144, 0, 255,
  -0.426, -0.43, -0.144, 0, 255,
  -0.426, -1.43, 0.856, 0, 255,
  0, 0, 0, 1, 0,
]);

class BusinessLocationPage extends StatefulWidget {
  const BusinessLocationPage({super.key, required this.module});

  final LaJuanaConfigurationModule module;

  @override
  State<BusinessLocationPage> createState() => _BusinessLocationPageState();
}

class _BusinessLocationPageState extends State<BusinessLocationPage>
    with RefreshableState {
  final name = TextEditingController();
  final address = TextEditingController();
  final municipality = TextEditingController();
  final directions = TextEditingController();
  final mapController = MapController();

  LatLng point = const LatLng(5.152583, -75.501472);
  LatLng savedPoint = const LatLng(5.152583, -75.501472);
  bool loading = true;
  bool saving = false;
  bool editing = false;
  bool adjustingMap = false;
  String? error;
  String? loadError;
  String mapsUrl = '';

  static const _defaultLightTiles =
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  @override
  Future<void> onRefresh() => _load();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in [name, address, municipality, directions]) {
      c.dispose();
    }
    super.dispose();
  }

  String _friendlyError(Object e) => userFacingError(
        e,
        fallback: 'No se pudo cargar la ubicación.',
      );

  void _apply(BusinessLocationConfiguration v) {
    name.text = v.name;
    address.text = v.address;
    municipality.text = v.municipality;
    directions.text = v.directions;
    point = LatLng(v.latitude, v.longitude);
    savedPoint = point;
    mapsUrl = v.googleMapsUrl;
  }

  void _centerMapOn(LatLng target, {double zoom = 15}) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      try {
        mapController.move(target, zoom);
      } catch (_) {
        // MapController aún no está ligado al mapa.
      }
    });
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

  Widget _leadingAppIcon() {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: 40,
      height: 40,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(4),
      ),
      alignment: Alignment.center,
      child: SvgPicture.asset(
        'assets/branding/app_icon.svg',
        width: 22,
        height: 22,
        fit: BoxFit.contain,
        colorFilter: ColorFilter.mode(
          scheme.onSurfaceVariant,
          BlendMode.srcIn,
        ),
      ),
    );
  }

  Widget _buildMap(ThemeData theme, AppThemeTokens tokens) {
    return SizedBox(
      height: 280,
      child: ClipRRect(
        borderRadius: tokens.radiusMd,
        child: Stack(
          alignment: Alignment.center,
          children: [
            FlutterMap(
              // Recrea el mapa al entrar en edición / cambiar modo
              // para que initialCenter coincida con el punto guardado.
              key: ValueKey(
                'biz-map-${editing ? (adjustingMap ? 'adj' : 'edit') : 'view'}-'
                '${savedPoint.latitude.toStringAsFixed(5)}-'
                '${savedPoint.longitude.toStringAsFixed(5)}',
              ),
              mapController: mapController,
              options: MapOptions(
                initialCenter: point,
                initialZoom: 15,
                interactionOptions: InteractionOptions(
                  flags: !editing
                      ? InteractiveFlag.pinchZoom |
                            InteractiveFlag.drag |
                            InteractiveFlag.doubleTapZoom
                      : adjustingMap
                      ? InteractiveFlag.all
                      : InteractiveFlag.pinchZoom |
                            InteractiveFlag.drag |
                            InteractiveFlag.doubleTapZoom,
                ),
              ),
              children: [
                _buildTileLayer(theme.brightness),
                if (!adjustingMap)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: point,
                        width: _MapPin.size,
                        height: _MapPin.size,
                        // topCenter: el widget queda encima del
                        // punto; la punta (abajo del pin) cae
                        // exactamente sobre la coordenada.
                        alignment: Alignment.topCenter,
                        child: _MapPin(
                          color: theme.brightness == Brightness.dark
                              ? _mapPinRedDark
                              : _mapPinRedLight,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
            if (adjustingMap)
              // Misma geometría: punta en el centro del mapa
              // (= coordenada que se guardará).
              IgnorePointer(
                child: Transform.translate(
                  offset: const Offset(0, -_MapPin.size / 2),
                  child: _MapPin(
                    color: theme.brightness == Brightness.dark
                        ? _mapPinRedDark
                        : _mapPinRedLight,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _load() async {
    setState(() {
      loadError = null;
      if (!editing) loading = true;
    });
    try {
      final v = await widget.module.api.getLocation();
      if (!mounted) return;
      setState(() {
        _apply(v);
        loading = false;
        error = null;
      });
      _centerMapOn(point);
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
      adjustingMap = false;
      point = savedPoint;
      error = null;
      loading = true;
    });
    await _load();
  }

  void _enterEdit() {
    setState(() {
      editing = true;
      adjustingMap = false;
      point = savedPoint;
    });
    _centerMapOn(savedPoint);
  }

  void _startAdjustingMap() {
    setState(() => adjustingMap = true);
    _centerMapOn(point);
  }

  void _finishAdjustingMap() {
    setState(() {
      point = mapController.camera.center;
      adjustingMap = false;
    });
    _centerMapOn(point);
  }

  void _cancelAdjustingMap() {
    setState(() {
      adjustingMap = false;
      point = savedPoint;
    });
    _centerMapOn(savedPoint);
  }

  Future<void> _openMaps() async {
    if (mapsUrl.isEmpty) return;
    await launchUrl(
      Uri.parse(mapsUrl),
      mode: LaunchMode.externalApplication,
    );
  }

  Future<void> _save() async {
    if (name.text.trim().isEmpty || address.text.trim().isEmpty) {
      setState(() {
        error = 'Nombre y dirección son obligatorios.';
      });
      return;
    }
    if (adjustingMap) {
      point = mapController.camera.center;
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      final v = await widget.module.api.updateLocation({
        'name': name.text.trim(),
        'address': address.text.trim(),
        'municipality': municipality.text.trim(),
        'directions': directions.text.trim(),
        'latitude': point.latitude,
        'longitude': point.longitude,
      });
      if (!mounted) return;
      setState(() {
        _apply(v);
        savedPoint = point;
        saving = false;
        editing = false;
        adjustingMap = false;
      });
      showAppToast(context, message: 'Ubicación actualizada.');
    } catch (e) {
      if (!mounted) return;
      setState(() {
        error = _friendlyError(e);
        saving = false;
      });
    }
  }

  String _tileUrl() {
    const configured = String.fromEnvironment('MAP_TILE_URL');
    if (configured.isNotEmpty) return configured;
    // En dark mode también usamos tiles claras: el ColorFilter las invierte
    // y deja carreteras/líneas mucho más legibles que Carto Dark Matter.
    return _defaultLightTiles;
  }

  Widget _buildTileLayer(Brightness brightness) {
    final tiles = TileLayer(
      urlTemplate: _tileUrl(),
      userAgentPackageName: 'com.lajuana.mobile',
    );
    if (brightness != Brightness.dark) return tiles;
    return ColorFiltered(
      colorFilter: _darkMapFromLightTilesFilter,
      child: tiles,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tokens = theme.appTokens;

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Configuración de La Juana',
            title: 'Ubicación del negocio',
            subtitle: adjustingMap
                ? 'Mueve el mapa hasta dejar el punto exacto bajo el marcador.'
                : editing
                ? 'Edita los datos del lugar. El punto del mapa se ajusta aparte.'
                : 'Dirección, indicaciones y punto en el mapa.',
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
                          title: name.text.trim().isEmpty
                              ? 'Sin nombre'
                              : name.text.trim(),
                          subtitle: [
                            if (address.text.trim().isNotEmpty)
                              address.text.trim(),
                            if (municipality.text.trim().isNotEmpty)
                              municipality.text.trim(),
                          ].join(' · '),
                          leading: _leadingAppIcon(),
                        ),
                        if (directions.text.trim().isNotEmpty) ...[
                          const SizedBox(height: 10),
                          AppEntityRowCard(
                            title: 'Indicaciones',
                            subtitle: directions.text.trim(),
                            leading: _leadingIcon(Symbols.directions),
                          ),
                        ],
                        const SizedBox(height: 12),
                        _buildMap(theme, tokens),
                        const SizedBox(height: 12),
                        _MapsRedButton(
                          label: 'Abrir en Google Maps',
                          icon: Icons.map_rounded,
                          expanded: true,
                          onPressed: mapsUrl.isEmpty ? null : _openMaps,
                        ),
                        const SizedBox(height: 12),
                        AppButton(
                          label: 'Editar',
                          icon: Icons.edit_rounded,
                          expanded: true,
                          onPressed: _enterEdit,
                        ),
                      ] else ...[
                        AppTextField(
                          controller: name,
                          label: 'Nombre del lugar',
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: address,
                          label: 'Dirección',
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: municipality,
                          label: 'Ciudad o municipio',
                        ),
                        const SizedBox(height: 10),
                        AppTextField(
                          controller: directions,
                          label: 'Indicaciones para llegar',
                          maxLines: 3,
                        ),
                        const SizedBox(height: 12),
                        _buildMap(theme, tokens),
                        const SizedBox(height: 12),
                        if (!adjustingMap) ...[
                          AppButton(
                            label: 'Ajustar punto en el mapa',
                            icon: Icons.edit_location_alt_rounded,
                            expanded: true,
                            variant: AppButtonVariant.secondary,
                            onPressed: _startAdjustingMap,
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: _MapsRedButton(
                                  label: 'Centrar',
                                  icon: Icons.my_location_rounded,
                                  onPressed: () {
                                    setState(() => point = savedPoint);
                                    _centerMapOn(savedPoint);
                                  },
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: _MapsRedButton(
                                  label: 'Abrir Maps',
                                  icon: Icons.map_rounded,
                                  onPressed:
                                      mapsUrl.isEmpty ? null : _openMaps,
                                ),
                              ),
                            ],
                          ),
                        ] else ...[
                          AppButton(
                            label: 'Listo con este punto',
                            icon: Icons.check_rounded,
                            expanded: true,
                            onPressed: _finishAdjustingMap,
                          ),
                          const SizedBox(height: 8),
                          AppButton(
                            label: 'Descartar ajuste',
                            icon: Icons.close_rounded,
                            expanded: true,
                            variant: AppButtonVariant.secondary,
                            onPressed: _cancelAdjustingMap,
                          ),
                          const SizedBox(height: 10),
                          Row(
                            children: [
                              Expanded(
                                child: _MapsRedButton(
                                  label: 'Centrar',
                                  icon: Icons.my_location_rounded,
                                  onPressed: () => _centerMapOn(savedPoint),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: _MapsRedButton(
                                  label: 'Abrir Maps',
                                  icon: Icons.map_rounded,
                                  onPressed:
                                      mapsUrl.isEmpty ? null : _openMaps,
                                ),
                              ),
                            ],
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
                          onPressed: saving || adjustingMap ? null : _save,
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

/// Pin con [Symbols.chess_knight] (mismo de la pestaña Equinos).
/// La punta inferior cae exactamente sobre la coordenada del mapa.
class _MapPin extends StatelessWidget {
  const _MapPin({required this.color});

  static const double size = 44;
  static const double _head = 32;

  final Color color;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.topCenter,
        children: [
          Positioned.fill(
            child: CustomPaint(painter: _MapPinStemPainter(color)),
          ),
          SizedBox(
            width: _head,
            height: _head,
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: color,
                shape: BoxShape.circle,
              ),
              child: Icon(
                Symbols.chess_knight,
                size: 20,
                color: Colors.white,
                fill: 1,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MapPinStemPainter extends CustomPainter {
  _MapPinStemPainter(this.color);

  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..style = PaintingStyle.fill
      ..isAntiAlias = true;

    final w = size.width;
    final h = size.height;
    final tip = Offset(w / 2, h);
    final headCenter = Offset(w / 2, _MapPin._head / 2);
    final headRadius = _MapPin._head / 2;

    final stem = Path()
      ..moveTo(tip.dx, tip.dy)
      ..lineTo(
        headCenter.dx - headRadius * 0.72,
        headCenter.dy + headRadius * 0.55,
      )
      ..lineTo(
        headCenter.dx + headRadius * 0.72,
        headCenter.dy + headRadius * 0.55,
      )
      ..close();

    canvas.drawPath(stem, paint);
  }

  @override
  bool shouldRepaint(covariant _MapPinStemPainter oldDelegate) =>
      oldDelegate.color != color;
}

/// Botón rojo estilo correo/Gmail para acciones de Maps.
class _MapsRedButton extends StatefulWidget {
  const _MapsRedButton({
    required this.label,
    required this.icon,
    required this.onPressed,
    this.expanded = false,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool expanded;

  @override
  State<_MapsRedButton> createState() => _MapsRedButtonState();
}

class _MapsRedButtonState extends State<_MapsRedButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tokens = theme.appTokens;
    final isDisabled = widget.onPressed == null;
    final radius = tokens.radiusMd;

    final button = SizedBox(
      height: 52,
      width: widget.expanded ? double.infinity : null,
      child: Material(
        color: isDisabled
            ? theme.colorScheme.onSurface.withValues(alpha: 0.12)
            : _mapsActionRed,
        borderRadius: radius,
        child: InkWell(
          borderRadius: radius,
          onTap: widget.onPressed,
          onTapDown:
              isDisabled ? null : (_) => setState(() => _pressed = true),
          onTapUp:
              isDisabled ? null : (_) => setState(() => _pressed = false),
          onTapCancel:
              isDisabled ? null : () => setState(() => _pressed = false),
          splashColor: Colors.white.withValues(alpha: 0.12),
          highlightColor: Colors.white.withValues(alpha: 0.06),
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: tokens.spaceLg),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize:
                  widget.expanded ? MainAxisSize.max : MainAxisSize.min,
              children: [
                Icon(
                  widget.icon,
                  size: 18,
                  color: Colors.white.withValues(alpha: isDisabled ? 0.38 : 1),
                ),
                SizedBox(width: tokens.spaceSm),
                Flexible(
                  child: Text(
                    widget.label.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: Colors.white.withValues(
                        alpha: isDisabled ? 0.38 : 1,
                      ),
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.2,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    return AnimatedScale(
      scale: (_pressed && !isDisabled) ? 0.96 : 1,
      duration: const Duration(milliseconds: 120),
      curve: Curves.easeOut,
      child: button,
    );
  }
}
