import 'dart:async' show unawaited;

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_dtos.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/experiences/presentation/screens/experiences_module_screen.dart';
import 'package:mobile/features/configuration/configuration_module.dart';
import 'package:mobile/features/configuration/presentation/screens/la_juana_configuration_page.dart';
import 'package:mobile/features/providers/presentation/screens/providers_module_screen.dart';
import 'package:mobile/features/saddles/presentation/screens/saddles_module_screen.dart';
import 'package:mobile/features/saddles/saddles_module.dart';
import 'package:mobile/features/providers/providers_module.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/notifications/notifications_module.dart';
import 'package:mobile/features/notifications/presentation/screens/notifications_settings_page.dart';

enum _MoreDestination {
  menu,
  profile,
  contacts,
  changePassword,
  providers,
  sillas,
  experiencias,
}

class MoreFlowScreen extends StatefulWidget {
  const MoreFlowScreen({
    super.key,
    required this.controller,
    required this.contactsApiClient,
    this.catalogsModule,
    this.saddlesModule,
    this.providersModule,
    this.onCallRequested,
    this.configurationModule,
    this.reservationsModule,
    this.notificationsModule,
  });

  final AuthController controller;
  final AuthApiClient contactsApiClient;
  final CatalogsModule? catalogsModule;
  final SaddlesModule? saddlesModule;
  final ProvidersModule? providersModule;
  final Future<bool> Function(String phone)? onCallRequested;
  final LaJuanaConfigurationModule? configurationModule;
  final ReservationsModule? reservationsModule;
  final NotificationsModule? notificationsModule;

  @override
  State<MoreFlowScreen> createState() => _MoreFlowScreenState();
}

class _MoreFlowScreenState extends State<MoreFlowScreen> with RefreshableState {
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

  _MoreDestination _destination = _MoreDestination.menu;
  bool _didProfileRemoteSync = false;
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
    _contactsApiClient = widget.contactsApiClient;
    _onCallRequested = widget.onCallRequested ?? _callNativeDialer;
  }

  @override
  void dispose() {
    _currentPasswordCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmPasswordCtrl.dispose();
    super.dispose();
  }

  void _open(_MoreDestination d) {
    setState(() {
      if (d == _MoreDestination.menu) {
        _didProfileRemoteSync = false;
      }
      _destination = d;
      if (d == _MoreDestination.contacts) {
        _contactsFuture ??= _loadEmergencyContacts();
      }
    });
    if (d == _MoreDestination.profile) {
      unawaited(_maybeSyncProfileFromRemote());
    }
  }

  Future<void> _maybeSyncProfileFromRemote() async {
    if (_didProfileRemoteSync) return;
    if (widget.controller.networkStatus.linkType == LinkType.offline) {
      return;
    }
    if (widget.controller.authState != LocalAuthState.signedInVerified) {
      return;
    }
    _didProfileRemoteSync = true;
    await widget.controller.profileRefreshRequested();
  }

  @override
  Future<void> onRefresh() async {
    switch (_destination) {
      case _MoreDestination.menu:
        await widget.catalogsModule?.repository.autoSync();
      case _MoreDestination.profile:
        _didProfileRemoteSync = false;
        await _maybeSyncProfileFromRemote();
      case _MoreDestination.contacts:
        setState(() {
          _contactsFuture = _loadEmergencyContacts();
        });
        await _contactsFuture;
      case _MoreDestination.changePassword:
        return;
      case _MoreDestination.providers:
      case _MoreDestination.sillas:
      case _MoreDestination.experiencias:
        return;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        return Padding(
          padding: EdgeInsets.all(tokens.spaceLg),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final body = KeyedSubtree(
                key: ValueKey(_destination),
                child: _buildBody(),
              );

              // Sub-vistas con lista propia (Expanded) necesitan altura acotada.
              if (_destination == _MoreDestination.providers ||
                  _destination == _MoreDestination.sillas ||
                  _destination == _MoreDestination.experiencias) {
                final height = constraints.hasBoundedHeight
                    ? constraints.maxHeight
                    : MediaQuery.sizeOf(context).height;
                return SizedBox(
                  height: height > 0 ? height : null,
                  width: double.infinity,
                  child: body,
                );
              }

              return body;
            },
          ),
        );
      },
    );
  }

  Widget _buildBody() {
    switch (_destination) {
      case _MoreDestination.menu:
        return RefreshableViewport(child: _buildMenu());
      case _MoreDestination.profile:
        return RefreshableViewport(child: _buildProfile());
      case _MoreDestination.contacts:
        return RefreshableViewport(child: _buildContacts());
      case _MoreDestination.changePassword:
        return RefreshableViewport(child: _buildChangePassword());
      case _MoreDestination.providers:
        return _buildProvidersEmbedded();
      case _MoreDestination.sillas:
        return _buildSillasEmbedded();
      case _MoreDestination.experiencias:
        return _buildExperienciasEmbedded();
    }
  }

  Widget _menuLeadingIcon(IconData icon) {
    final scheme = Theme.of(context).colorScheme;
    final tokens = Theme.of(context).appTokens;
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: tokens.radiusMd,
      ),
      child: Icon(
        icon,
        size: 22,
        color: scheme.onSurfaceVariant,
      ),
    );
  }

  Widget _buildMenu() {
    final tokens = Theme.of(context).appTokens;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const AppSectionHeader(
          eyebrow: 'Más',
          title: 'Opciones adicionales',
          variant: AppSectionHeaderVariant.compact,
        ),
        SizedBox(height: tokens.spaceLg),
        AppEntityRowCard(
          title: 'Perfil',
          subtitle: 'Datos del usuario y estado de cuenta',
          leading: _menuLeadingIcon(Symbols.person),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.profile),
        ),
        SizedBox(height: tokens.spaceMd),
        if (widget.notificationsModule != null) ...[
          AppEntityRowCard(
            title: 'Notificaciones',
            subtitle: 'Preferencias y alertas en segundo plano',
            leading: _menuLeadingIcon(Symbols.notifications),
            trailing: const Icon(Icons.chevron_right_rounded, size: 18),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => NotificationsSettingsPage(
                    controller: widget.notificationsModule!.controller,
                  ),
                ),
              );
            },
          ),
          SizedBox(height: tokens.spaceMd),
        ],
        AppEntityRowCard(
          title: 'Números',
          subtitle: 'De emergencia',
          leading: _menuLeadingIcon(Symbols.phone),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.contacts),
        ),
        SizedBox(height: tokens.spaceMd),
        AppEntityRowCard(
          title: 'Experiencias',
          subtitle: 'Catálogo de productos',
          leading: _menuLeadingIcon(Symbols.explore),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.experiencias),
        ),
        SizedBox(height: tokens.spaceMd),
        AppEntityRowCard(
          title: 'Proveedores',
          subtitle: 'Catálogo operativo',
          leading: _menuLeadingIcon(Symbols.handshake),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.providers),
        ),
        SizedBox(height: tokens.spaceMd),
        AppEntityRowCard(
          title: 'Sillas',
          subtitle: 'Inventario de montura',
          leading: _menuLeadingIcon(Symbols.airline_seat_legroom_extra),
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.sillas),
        ),
        if (widget.catalogsModule != null &&
            widget.configurationModule != null &&
            widget.controller.currentUser?.role == 'admin') ...[
          SizedBox(height: tokens.spaceMd),
          AppEntityRowCard(
            title: 'Configuración',
            subtitle: 'De la Juana',
            leading: _menuLeadingIcon(Symbols.settings),
            trailing: const Icon(Icons.chevron_right_rounded, size: 18),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => LaJuanaConfigurationPage(
                    module: widget.configurationModule!,
                    catalogsModule: widget.catalogsModule!,
                    authController: widget.controller,
                    reservationsRepository:
                        widget.reservationsModule?.repository,
                  ),
                ),
              );
            },
          ),
        ],
      ],
    );
  }

  Widget _buildProvidersEmbedded() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppSectionHeader(
          eyebrow: 'Más',
          title: 'Proveedores',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 4),
        Expanded(
          child: ProvidersModuleScreen(
            providersModule: widget.providersModule,
            showHeader: false,
          ),
        ),
      ],
    );
  }

  Widget _buildSillasEmbedded() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppSectionHeader(
          eyebrow: 'Gestión',
          title: 'Sillas',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 4),
        Expanded(
          child: SaddlesModuleScreen(
            saddlesModule: widget.saddlesModule,
            showHeader: false,
          ),
        ),
      ],
    );
  }

  Widget _buildExperienciasEmbedded() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppSectionHeader(
          eyebrow: 'Más',
          title: 'Experiencias',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 4),
        Expanded(
          child: ExperiencesModuleScreen(
            catalogsModule: widget.catalogsModule,
            authController: widget.controller,
            showHeader: false,
          ),
        ),
      ],
    );
  }

  Widget _buildProfile() {
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
        AppSectionHeader(
          eyebrow: 'Más',
          title: 'Perfil',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 12),
        if (user == null)
          const AppEntityRowCard(
            title: 'Perfil no disponible',
            subtitle: 'No hay datos de usuario en la sesión actual',
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
                label: displayUserRoleLabel(user?.role),
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
        const SizedBox(height: 16),
        AppEntityRowCard(
          title: 'Correo principal',
          subtitle: user?.email ?? 'No disponible',
          leading: const Icon(Icons.mail_outline_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Teléfono',
          subtitle: user?.phone ?? 'No registrado',
          leading: const Icon(Icons.phone_outlined, size: 18),
        ),
        const SizedBox(height: 16),
        AppButton(
          label: 'Cambiar contraseña',
          icon: Icons.lock_outline_rounded,
          expanded: true,
          onPressed: () => _open(_MoreDestination.changePassword),
        ),
        const SizedBox(height: 8),
        AppButton(
          label: 'Cerrar sesión',
          variant: AppButtonVariant.secondary,
          expanded: true,
          onPressed: _onLogoutPressed,
        ),
      ],
    );
  }

  Future<void> _onLogoutPressed() async {
    await widget.controller.logoutRequested();
    if (!mounted) return;
    await Navigator.of(
      context,
      rootNavigator: true,
    ).pushNamedAndRemoveUntil(AuthRoutes.login, (_) => false);
  }

  Widget _buildChangePassword() {
    final passwordsMatch = _newPasswordCtrl.text == _confirmPasswordCtrl.text;
    final canSubmit =
        !widget.controller.isLoading &&
        _currentPasswordCtrl.text.isNotEmpty &&
        _newPasswordCtrl.text.length >= 8 &&
        passwordsMatch;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Más > Perfil',
          title: 'Cambiar contraseña',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.profile),
          ),
        ),
        const SizedBox(height: 20),
        if (widget.controller.networkStatus.linkType == LinkType.offline) ...[
          const AppBadge(
            label: 'Sin enlace de red',
            tone: AppBadgeTone.warning,
            uppercase: false,
          ),
          const SizedBox(height: 12),
        ] else if (widget.controller.networkStatus.backendReachability ==
            BackendReachability.unreachable) ...[
          const AppBadge(
            label: 'Servidor no alcanzable',
            tone: AppBadgeTone.warning,
            uppercase: false,
          ),
          const SizedBox(height: 12),
        ],
        AppTextField(
          controller: _currentPasswordCtrl,
          label: 'Contraseña actual',
          inputKind: AppTextInputKind.password,
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
          label: 'Nueva contraseña',
          inputKind: AppTextInputKind.password,
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
          inputKind: AppTextInputKind.password,
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
            label: 'Las contraseñas no coinciden',
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

  Widget _buildContacts() {
    _contactsFuture ??= _loadEmergencyContacts();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Más',
          title: 'Números',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 20),
        FutureBuilder<List<_EmergencyContact>>(
          future: _contactsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const AppCenteredLoader(fill: false);
            }

            if (snapshot.hasError) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const AppEntityRowCard(
                    title: 'No se pudieron cargar los contactos',
                    subtitle: 'Revisa la conexión e intenta de nuevo',
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
    showAppToast(
      context,
      message: 'No se pudo abrir la app de llamadas',
      isError: true,
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
          'No se pudo actualizar la contraseña';
      showAppToast(context, message: message, isError: true);
      return;
    }

    if (widget.controller.noticeEventId > previousNoticeEventId) {
      final message =
          widget.controller.noticeMessage ??
          widget.controller.messageForCode(widget.controller.noticeCode) ??
          'Contraseña actualizada.';
      showAppToast(context, message: message);
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

  String _formatMonthAndYear(DateTime value) {
    final local = value.toLocal();
    final month = _monthShortLabels[local.month - 1];
    return '$month ${local.year}';
  }

  AppBadge _profileStatusBadge(LocalAuthState authState) {
    switch (authState) {
      case LocalAuthState.signedInVerified:
        return const AppBadge(
          label: 'En línea',
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
          label: 'Sesión expirada',
          tone: AppBadgeTone.danger,
          uppercase: false,
        );
      case LocalAuthState.signedOut:
        return const AppBadge(
          label: 'Sin sesión',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        );
    }
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
