import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../app/widgets/app_badge.dart';
import '../app/widgets/app_bottom_nav.dart';
import '../app/widgets/app_breadcrumb.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_entity_row_card.dart';
import '../app/widgets/app_metric_card.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_section_header.dart';
import '../app/widgets/app_segmented_filter.dart';
import '../app/widgets/app_text_field.dart';
import '../app/widgets/app_timeline.dart';
import '../app/widgets/app_top_bar.dart';
import '../auth/domain/auth_enums.dart';
import '../auth/infrastructure/remote/auth_api_client.dart';
import '../auth/infrastructure/remote/auth_dtos.dart';
import '../auth/presentation/auth_controller.dart';

enum _MoreDestination { menu, profile, contacts, changePassword }

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.controller,
    this.contactsApiClient,
    this.onCallRequested,
  });

  final AuthController controller;
  final AuthApiClient? contactsApiClient;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const List<String> _monthShortLabels = <String>[
    'ENE',
    'FEB',
    'MAR',
    'ABR',
    'MAY',
    'JUN',
    'JUL',
    'AGO',
    'SEP',
    'OCT',
    'NOV',
    'DIC',
  ];

  String _filterValue = 'pendientes';
  AppNavItem _currentNav = AppNavItem.inicio;
  _MoreDestination _moreDestination = _MoreDestination.menu;
  Future<List<_EmergencyContact>>? _contactsFuture;
  late final AuthApiClient _contactsApiClient;
  late final Future<bool> Function(String phone) _onCallRequested;
  final TextEditingController _currentPasswordCtrl = TextEditingController();
  final TextEditingController _newPasswordCtrl = TextEditingController();
  final TextEditingController _confirmPasswordCtrl = TextEditingController();
  bool _obscureCurrentPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    _contactsApiClient = widget.contactsApiClient ?? AuthApiClient();
    _onCallRequested = widget.onCallRequested ?? _callNativeDialer;
  }

  @override
  void dispose() {
    _currentPasswordCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmPasswordCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        return AppScaffold(
          appBar: const AppTopBar(
            logoAssetPath: 'assets/branding/lajuana.svg',
            title: 'LA JUANA',
          ),
          bottomNavigationBar: AppBottomNav(
            current: _currentNav,
            onTap: _onBottomNavTap,
          ),
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: _buildCurrentView(),
        );
      },
    );
  }

  void _onBottomNavTap(AppNavItem item) {
    setState(() {
      if (_currentNav == AppNavItem.mas && item == AppNavItem.mas) {
        _moreDestination = _MoreDestination.menu;
      } else if (item != AppNavItem.mas) {
        _moreDestination = _MoreDestination.menu;
      }
      _currentNav = item;
    });
  }

  void _openMoreDestination(_MoreDestination destination) {
    setState(() {
      _moreDestination = destination;
      if (destination == _MoreDestination.contacts) {
        _contactsFuture ??= _loadEmergencyContacts();
      }
    });
  }

  Widget _buildCurrentView() {
    if (_currentNav == AppNavItem.mas) {
      return _buildMoreView();
    }
    return _buildInicioView();
  }

  Widget _buildInicioView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Inicio',
          title: 'Supervision Operacional',
          trailing: AppButton(
            label: 'Crear',
            icon: Icons.add,
            onPressed: () {},
          ),
        ),
        const SizedBox(height: 24),
        AppSegmentedFilter<String>(
          value: _filterValue,
          onChanged: (v) {
            setState(() {
              _filterValue = v;
            });
          },
          items: const [
            AppSegmentedFilterItem(label: 'Pendientes', value: 'pendientes'),
            AppSegmentedFilterItem(label: 'Confirmadas', value: 'confirmadas'),
            AppSegmentedFilterItem(label: 'Finalizadas', value: 'finalizadas'),
          ],
        ),
        const SizedBox(height: 16),
        const AppMetricCard(
          title: 'Total SKU de productos',
          value: '124',
          suffix: 'ITEMS',
        ),
        const SizedBox(height: 16),
        const AppMetricCard(
          title: 'Stock critico',
          value: '08',
          supportingText: 'SE RECOMIENDA COMPRAR',
          tone: AppMetricCardTone.danger,
          icon: Icons.warning_amber_rounded,
        ),
        const SizedBox(height: 32),
        const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.active,
              child: AppTimelineEntryCard(
                date: 'Oct 24, 2026 - 09:00 AM',
                title: 'Monta Controlada',
                badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.neutral),
                description:
                    'Monta natural realizada en yegua en condiciones controladas.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.cancelled,
              child: AppTimelineEntryCard(
                date: 'Oct 10, 2026',
                title: 'Traslado suspendido',
                badge: AppBadge(label: 'Error', tone: AppBadgeTone.danger),
                description:
                    'Vehiculo averiado, no se pudo realizar el traslado del equino.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: 'Sep 15, 2026',
                title: 'Vacunacion anual',
                badge: AppBadge(label: 'Completado', tone: AppBadgeTone.ghost),
                description: 'Aplicacion de vacuna contra influenza y tetanos.',
                footer: Row(
                  children: [
                    Icon(Icons.medical_services_outlined, size: 16),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'SERVICIOS VETERINARIOS',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),
        const AppBreadcrumb(items: ['Gestion', 'Experiencias']),
        const SizedBox(height: 12),
        const AppEntityRowCard(
          title: 'Elena Rodriguez',
          subtitle: 'EXP: INTERMEDIO - 68KG',
          selected: true,
          badge: AppBadge(label: 'Alto Riesgo', tone: AppBadgeTone.danger),
        ),
        const SizedBox(height: 12),
        const AppEntityRowCard(
          title: 'Marcus Thorne',
          subtitle: 'EXP: AVANZADO - 82KG',
          badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
        ),
      ],
    );
  }

  Widget _buildMoreView() {
    return switch (_moreDestination) {
      _MoreDestination.menu => _buildMoreMenu(),
      _MoreDestination.profile => _buildProfileView(),
      _MoreDestination.contacts => _buildContactsView(),
      _MoreDestination.changePassword => _buildChangePasswordView(),
    };
  }

  Widget _buildMoreMenu() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments([
          'Mas',
        ], currentLabel: 'Opciones adicionales'),
        const SizedBox(height: 24),
        AppEntityRowCard(
          title: 'Perfil',
          subtitle: 'Datos del usuario y estado de cuenta',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _openMoreDestination(_MoreDestination.profile),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Contactos',
          subtitle: 'Numeros de emergencia',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _openMoreDestination(_MoreDestination.contacts),
        ),
      ],
    );
  }

  Widget _buildProfileView() {
    final user = widget.controller.currentUser;
    final statusBadge = _profileStatusBadge(widget.controller.authState);
    final isUserActive = user?.isActive ?? false;
    final createdAt =
        user?.createdAtRemote ?? user?.updatedAtRemote ?? user?.updatedAtLocal;
    final createdAtLabel = createdAt == null
        ? null
        : _formatMonthAndYear(createdAt);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Perfil',
        ], onBack: () => _openMoreDestination(_MoreDestination.menu)),
        const SizedBox(height: 20),
        if (user == null)
          const AppEntityRowCard(
            title: 'Perfil no disponible',
            subtitle: 'No hay datos de usuario en la sesion actual',
            badge: AppBadge(label: 'Sin datos', tone: AppBadgeTone.danger),
            selected: true,
          )
        else
          AppEntityRowCard(
            title: user.fullName,
            subtitle: createdAtLabel == null
                ? 'Perfil de usuario'
                : 'Creado en $createdAtLabel',
            selected: true,
            badge: statusBadge,
            trailing: const Icon(Icons.person_outline_rounded, size: 18),
          ),
        const SizedBox(height: 12),
        Center(
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              AppBadge(
                label: _roleBadgeLabel(user?.role),
                tone: AppBadgeTone.neutral,
                uppercase: false,
              ),
              AppBadge(
                label: isUserActive ? 'Cuenta activa' : 'Cuenta inactiva',
                tone: isUserActive
                    ? AppBadgeTone.success
                    : AppBadgeTone.warning,
                uppercase: false,
              ),
            ],
          ),
        ),
        if (widget.controller.hasPendingSync ||
            widget.controller.isOfflineRestricted)
          const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          alignment: WrapAlignment.center,
          children: [
            if (widget.controller.hasPendingSync)
              const AppBadge(
                label: 'Sincronizacion pendiente',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
            if (widget.controller.isOfflineRestricted)
              const AppBadge(
                label: 'Modo local',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
          ],
        ),
        const SizedBox(height: 16),
        AppEntityRowCard(
          title: 'Correo principal',
          subtitle: user?.email ?? 'No disponible',
          leading: const Icon(Icons.mail_outline_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Telefono',
          subtitle: user?.phone ?? 'No registrado',
          leading: const Icon(Icons.phone_outlined, size: 18),
        ),
        const SizedBox(height: 16),
        AppButton(
          label: 'Cambiar contrasena',
          icon: Icons.lock_outline_rounded,
          expanded: true,
          onPressed: () =>
              _openMoreDestination(_MoreDestination.changePassword),
        ),
      ],
    );
  }

  Widget _buildChangePasswordView() {
    final isOnline =
        widget.controller.connectivityState != ConnectivityState.offline;
    final passwordsMatch = _newPasswordCtrl.text == _confirmPasswordCtrl.text;
    final canSubmit =
        isOnline &&
        !widget.controller.isLoading &&
        _currentPasswordCtrl.text.isNotEmpty &&
        _newPasswordCtrl.text.length >= 8 &&
        passwordsMatch;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Perfil',
          'Cambiar contrasena',
        ], onBack: () => _openMoreDestination(_MoreDestination.profile)),
        const SizedBox(height: 20),
        if (!isOnline) ...[
          const AppBadge(
            label: 'Requiere internet',
            tone: AppBadgeTone.warning,
            uppercase: false,
          ),
          const SizedBox(height: 12),
        ],
        AppTextField(
          controller: _currentPasswordCtrl,
          label: 'Contrasena actual',
          obscureText: _obscureCurrentPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureCurrentPassword = !_obscureCurrentPassword;
              });
            },
            icon: Icon(
              _obscureCurrentPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 10),
        AppTextField(
          controller: _newPasswordCtrl,
          label: 'Nueva contrasena',
          obscureText: _obscureNewPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureNewPassword = !_obscureNewPassword;
              });
            },
            icon: Icon(
              _obscureNewPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 10),
        AppTextField(
          controller: _confirmPasswordCtrl,
          label: 'Confirmar nueva',
          obscureText: _obscureConfirmPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureConfirmPassword = !_obscureConfirmPassword;
              });
            },
            icon: Icon(
              _obscureConfirmPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        if (!passwordsMatch && _confirmPasswordCtrl.text.isNotEmpty) ...[
          const SizedBox(height: 8),
          const AppBadge(
            label: 'Las contrasenas no coinciden',
            tone: AppBadgeTone.danger,
            uppercase: false,
          ),
        ],
        const SizedBox(height: 16),
        AppButton(
          label: widget.controller.isLoading ? 'Guardando...' : 'Guardar',
          expanded: true,
          onPressed: canSubmit ? _submitPasswordChange : null,
        ),
      ],
    );
  }

  Widget _buildContactsView() {
    _contactsFuture ??= _loadEmergencyContacts();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Contactos',
        ], onBack: () => _openMoreDestination(_MoreDestination.menu)),
        const SizedBox(height: 20),
        FutureBuilder<List<_EmergencyContact>>(
          future: _contactsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const AppEntityRowCard(
                title: 'Cargando contactos',
                subtitle: 'Consultando catalogo de emergencia',
                selected: true,
                trailing: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              );
            }

            if (snapshot.hasError) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const AppEntityRowCard(
                    title: 'No se pudieron cargar los contactos',
                    subtitle: 'Revisa la conexion e intenta de nuevo',
                    badge: AppBadge(
                      label: 'Error de red',
                      tone: AppBadgeTone.danger,
                      uppercase: false,
                    ),
                    selected: true,
                  ),
                  const SizedBox(height: 12),
                  AppButton(
                    label: 'Reintentar',
                    variant: AppButtonVariant.ghost,
                    onPressed: () {
                      setState(() {
                        _contactsFuture = _loadEmergencyContacts();
                      });
                    },
                  ),
                ],
              );
            }

            final contacts = snapshot.data ?? const <_EmergencyContact>[];
            if (contacts.isEmpty) {
              return const AppEntityRowCard(
                title: 'Sin contactos disponibles',
                subtitle: 'No hay registros para mostrar',
                selected: true,
              );
            }

            return Column(
              children: [
                for (int i = 0; i < contacts.length; i++) ...[
                  AppEntityRowCard(
                    title: contacts[i].name,
                    subtitle: contacts[i].detail,
                    badge: AppBadge(
                      label: contacts[i].phone,
                      tone: contacts[i].tone,
                      uppercase: false,
                    ),
                    trailing: const Icon(Icons.call_outlined, size: 18),
                    onTap: () => _handleCallContact(contacts[i]),
                  ),
                  if (i != contacts.length - 1) const SizedBox(height: 10),
                ],
              ],
            );
          },
        ),
      ],
    );
  }

  Future<List<_EmergencyContact>> _loadEmergencyContacts() async {
    final contacts = await _contactsApiClient.getEmergencyContacts();
    return contacts.map(_mapEmergencyContact).toList(growable: false);
  }

  Future<void> _handleCallContact(_EmergencyContact contact) async {
    final launched = await _onCallRequested(contact.phone);
    if (!mounted || launched) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('No se pudo abrir la app de llamadas')),
    );
  }

  Future<void> _submitPasswordChange() async {
    final previousErrorEventId = widget.controller.errorEventId;
    final previousNoticeEventId = widget.controller.noticeEventId;
    await widget.controller.changePasswordSubmitted(
      currentPassword: _currentPasswordCtrl.text,
      newPassword: _newPasswordCtrl.text,
    );
    if (!mounted) return;

    if (widget.controller.errorEventId > previousErrorEventId) {
      final message =
          widget.controller.errorMessage ??
          widget.controller.messageForCode(widget.controller.errorCode) ??
          'No se pudo actualizar la contrasena';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      return;
    }

    if (widget.controller.noticeEventId > previousNoticeEventId) {
      final message =
          widget.controller.noticeMessage ??
          widget.controller.messageForCode(widget.controller.noticeCode) ??
          'Contrasena actualizada.';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      widget.controller.clearNotice();
      _currentPasswordCtrl.clear();
      _newPasswordCtrl.clear();
      _confirmPasswordCtrl.clear();
      setState(() {});
    }
  }

  Future<bool> _callNativeDialer(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (!await canLaunchUrl(uri)) return false;
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  _EmergencyContact _mapEmergencyContact(EmergencyCatalogContactDto contact) {
    return _EmergencyContact(
      code: contact.code,
      name: contact.name,
      phone: contact.phoneNumber,
      detail: contact.description,
      tone: _toneForCategory(contact.category, contact.isPrimary),
    );
  }

  AppBadgeTone _toneForCategory(String category, bool isPrimary) {
    if (!isPrimary) return AppBadgeTone.neutral;
    switch (category) {
      case 'health':
        return AppBadgeTone.success;
      case 'security':
        return AppBadgeTone.danger;
      case 'disaster':
        return AppBadgeTone.warning;
      default:
        return AppBadgeTone.primary;
    }
  }

  String _roleBadgeLabel(String? role) {
    if (role == null || role.trim().isEmpty) return 'Sin rol';
    if (role.toLowerCase() == 'unassigned') return 'Sin rol';
    return role;
  }

  String _formatMonthAndYear(DateTime value) {
    final local = value.toLocal();
    final month = _monthShortLabels[local.month - 1];
    return '$month ${local.year}';
  }

  AppBadge _profileStatusBadge(LocalAuthState authState) {
    switch (authState) {
      case LocalAuthState.signedInVerified:
        return const AppBadge(
          label: 'En linea',
          tone: AppBadgeTone.success,
          uppercase: false,
        );
      case LocalAuthState.signedInLocalUnverified:
        return const AppBadge(
          label: 'Modo local',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case LocalAuthState.refreshRequired:
        return const AppBadge(
          label: 'Requiere internet',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case LocalAuthState.invalid:
        return const AppBadge(
          label: 'Sesion expirada',
          tone: AppBadgeTone.danger,
          uppercase: false,
        );
      case LocalAuthState.signedOut:
        return const AppBadge(
          label: 'Sin sesion',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        );
    }
  }
}

class _RouteHeader extends StatelessWidget {
  const _RouteHeader({
    required this.sectionLabel,
    required this.currentLabel,
    this.onBack,
  });

  factory _RouteHeader.fromSegments(
    List<String> segments, {
    String? currentLabel,
    VoidCallback? onBack,
  }) {
    final sectionLabel = segments.length == 1
        ? segments.first
        : _joinSegments(segments);
    return _RouteHeader(
      sectionLabel: sectionLabel,
      currentLabel: currentLabel ?? segments.last,
      onBack: onBack,
    );
  }

  final String sectionLabel;
  final String currentLabel;
  final VoidCallback? onBack;

  static String _joinSegments(List<String> segments) {
    return segments.sublist(0, segments.length - 1).join(' > ');
  }

  @override
  Widget build(BuildContext context) {
    return AppSectionHeader(
      eyebrow: sectionLabel,
      title: currentLabel,
      trailing: onBack == null
          ? null
          : AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              onPressed: onBack,
              variant: AppButtonVariant.ghost,
            ),
    );
  }
}

class _EmergencyContact {
  const _EmergencyContact({
    required this.code,
    required this.name,
    required this.phone,
    required this.detail,
    required this.tone,
  });

  final String code;
  final String name;
  final String phone;
  final String detail;
  final AppBadgeTone tone;
}
