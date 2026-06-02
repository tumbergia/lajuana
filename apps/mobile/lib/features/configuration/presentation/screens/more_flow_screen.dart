import 'dart:async' show unawaited;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/infrastructure/connectivity/network_models.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_api_client.dart';
import 'package:mobile/features/auth/infrastructure/remote/auth_dtos.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/catalogs/presentation/pages/catalogs_home_page.dart';
import 'package:mobile/features/providers/presentation/screens/providers_module_screen.dart';
import 'package:mobile/features/saddles/presentation/screens/saddles_module_screen.dart';
import 'package:mobile/features/saddles/saddles_module.dart';

enum _MoreDestination { menu, profile, contacts, changePassword, providers, sillas }

class MoreFlowScreen extends StatefulWidget {
  const MoreFlowScreen({
    super.key,
    required this.controller,
    required this.contactsApiClient,
    this.catalogsModule,
    this.saddlesModule,
    this.onCallRequested,
  });

  final AuthController controller;
  final AuthApiClient contactsApiClient;
  final CatalogsModule? catalogsModule;
  final SaddlesModule? saddlesModule;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  State<MoreFlowScreen> createState() => _MoreFlowScreenState();
}

class _MoreFlowScreenState extends State<MoreFlowScreen> {
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
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: _buildBody(),
        );
      },
    );
  }

  Widget _buildBody() {
    switch (_destination) {
      case _MoreDestination.menu:
        return _buildMenu();
      case _MoreDestination.profile:
        return _buildProfile();
      case _MoreDestination.contacts:
        return _buildContacts();
      case _MoreDestination.changePassword:
        return _buildChangePassword();
      case _MoreDestination.providers:
        return _buildProvidersEmbedded();
      case _MoreDestination.sillas:
        return _buildSillasEmbedded();
    }
  }

  Widget _buildMenu() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const AppSectionHeader(eyebrow: 'Mas', title: 'Opciones adicionales'),
        const SizedBox(height: 20),
        AppEntityRowCard(
          title: 'Perfil',
          subtitle: 'Datos del usuario y estado de cuenta',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.profile),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Contactos',
          subtitle: 'Numeros de emergencia',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.contacts),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Proveedores',
          subtitle: 'Catalogo operativo',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.providers),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Sillas',
          subtitle: 'Inventario de montura',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _open(_MoreDestination.sillas),
        ),
        if (widget.catalogsModule != null) ...[
          const SizedBox(height: 12),
          AppEntityRowCard(
            title: 'Catalogos',
            subtitle: 'Experiencias, fechas, reglas y emergencias',
            trailing: const Icon(Icons.chevron_right_rounded, size: 18),
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => CatalogsHomePage(
                    module: widget.catalogsModule!,
                    authController: widget.controller,
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
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Mas',
          title: 'Proveedores',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const ProvidersModuleScreen(showHeader: false),
      ],
    );
  }

  Widget _buildSillasEmbedded() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Gestion',
          title: 'Sillas',
          trailing: AppButton(
            label: 'Volver',
            icon: Icons.arrow_back_rounded,
            variant: AppButtonVariant.ghost,
            onPressed: () => _open(_MoreDestination.menu),
          ),
        ),
        const SizedBox(height: 4),
        SaddlesModuleScreen(
          saddlesModule: widget.saddlesModule,
          showHeader: false,
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
          eyebrow: 'Mas',
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
          title: 'Telefono',
          subtitle: user?.phone ?? 'No registrado',
          leading: const Icon(Icons.phone_outlined, size: 18),
        ),
        const SizedBox(height: 16),
        AppButton(
          label: 'Cambiar contrasena',
          icon: Icons.lock_outline_rounded,
          expanded: true,
          onPressed: () => _open(_MoreDestination.changePassword),
        ),
        const SizedBox(height: 8),
        AppButton(
          label: 'Cerrar sesion',
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
          eyebrow: 'Mas > Perfil',
          title: 'Cambiar contrasena',
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

  Widget _buildContacts() {
    _contactsFuture ??= _loadEmergencyContacts();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: 'Mas',
          title: 'Contactos',
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
              return const AppCenteredLoader();
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
