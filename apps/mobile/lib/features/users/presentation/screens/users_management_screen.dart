import 'package:flutter/material.dart';

import 'package:mobile/features/auth/presentation/user_role_display.dart';
import 'package:mobile/features/users/domain/user_models.dart';
import 'package:mobile/features/users/infrastructure/remote/users_api_error.dart';
import 'package:mobile/features/users/presentation/controllers/users_list_controller.dart';
import 'package:mobile/features/users/users_module.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_empty_state.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_search_field.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';

const _roleOptions = <String, String>{
  'guide': 'Guía',
  'admin': 'Administrador',
};

class UsersManagementScreen extends StatefulWidget {
  const UsersManagementScreen({super.key, required this.module});

  final UsersModule module;

  @override
  State<UsersManagementScreen> createState() => _UsersManagementScreenState();
}

class _UsersManagementScreenState extends State<UsersManagementScreen>
    with RefreshableState {
  late final UsersListController _controller;
  final TextEditingController _searchController = TextEditingController();

  @override
  Future<void> onRefresh() => _controller.refresh();

  @override
  void initState() {
    super.initState();
    _controller = widget.module.usersController;
    _controller.addListener(_onChanged);
    _searchController.addListener(() {
      _controller.setSearchQuery(_searchController.text);
    });
    if (_controller.state == UsersLoadState.idle) {
      _controller.loadInitial();
    }
  }

  @override
  void dispose() {
    _controller.removeListener(_onChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _onChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _openCreateSheet() async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => const _UserFormSheet(),
    );
    if (result == null || !mounted) return;
    try {
      await _controller.createUser(
        email: result['email'] as String,
        fullName: result['full_name'] as String,
        password: result['password'] as String,
        role: result['role'] as String,
      );
      if (mounted) {
        showAppToast(context, message: 'Usuario creado correctamente');
      }
    } on UsersApiFailure catch (e) {
      if (mounted) {
        showAppToast(context, message: e.message, isError: true);
      }
    } catch (_) {
      if (mounted) {
        showAppToast(
          context,
          message: 'Error al crear el usuario',
          isError: true,
        );
      }
    }
  }

  Future<void> _openEditSheet(UserRecord user) async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _UserFormSheet(existing: user),
    );
    if (result == null || !mounted) return;
    try {
      await _controller.updateUser(
        user.id,
        fullName: result['full_name'] as String,
        role: result['role'] as String,
        isActive: result['is_active'] as bool?,
      );
      if (mounted) {
        showAppToast(context, message: 'Usuario actualizado correctamente');
      }
    } on UsersApiFailure catch (e) {
      if (mounted) {
        showAppToast(context, message: e.message, isError: true);
      }
    } catch (_) {
      if (mounted) {
        showAppToast(
          context,
          message: 'Error al actualizar el usuario',
          isError: true,
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(tokens.spaceXl),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppSectionHeader(
                title: 'Usuarios',
                subtitle: 'Crea cuentas y asigna roles',
                trailing: AppButton(
                  label: 'Volver',
                  icon: Icons.arrow_back_rounded,
                  variant: AppButtonVariant.ghost,
                  onPressed: () => Navigator.pop(context),
                ),
              ),
              SizedBox(height: tokens.spaceMd),
              AppSearchField(
                controller: _searchController,
                hintText: 'Buscar por nombre, correo o rol',
              ),
              const SizedBox(height: 12),
              AppButton(
                label: 'Crear usuario',
                icon: Icons.add,
                expanded: true,
                onPressed: _openCreateSheet,
              ),
              const SizedBox(height: 16),
              Expanded(child: _buildBody()),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    switch (_controller.state) {
      case UsersLoadState.idle:
      case UsersLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());
      case UsersLoadState.error:
        return RefreshableViewport(
          child: AppEntityRowCard(
            title: 'No se pudieron cargar los usuarios',
            subtitle: _controller.errorMessage ?? 'Revisa la conexión',
            badge: const AppBadge(label: 'Error', tone: AppBadgeTone.danger),
            onTap: _controller.loadInitial,
          ),
        );
      case UsersLoadState.empty:
        return const RefreshableViewport(
          child: AppEmptyState(
            icon: Icons.group_outlined,
            title: 'Sin usuarios',
            message: 'Crea el primero con el botón Crear usuario.',
          ),
        );
      case UsersLoadState.refreshing:
      case UsersLoadState.success:
        if (_controller.items.isEmpty) {
          return const RefreshableViewport(
            child: AppEmptyState(
              icon: Icons.search_off_rounded,
              title: 'Sin coincidencias',
              message: 'Prueba con otro término de búsqueda.',
            ),
          );
        }
        return ListView.separated(
          physics: const AlwaysScrollableScrollPhysics(),
          itemCount: _controller.items.length,
          separatorBuilder: (_, _) => const SizedBox(height: 10),
          itemBuilder: (context, index) {
            final user = _controller.items[index];
            return AppEntityRowCard(
              title: user.fullName,
              subtitle: user.email,
              badge: AppBadge(
                label: displayUserRoleLabel(user.role),
                tone: user.isActive
                    ? AppBadgeTone.primary
                    : AppBadgeTone.neutral,
                uppercase: false,
              ),
              trailing: Icon(
                user.isActive
                    ? Icons.chevron_right_rounded
                    : Icons.person_off_outlined,
                size: 18,
              ),
              onTap: () => _openEditSheet(user),
            );
          },
        );
    }
  }
}

class _UserFormSheet extends StatefulWidget {
  const _UserFormSheet({this.existing});

  final UserRecord? existing;

  bool get isEditing => existing != null;

  @override
  State<_UserFormSheet> createState() => _UserFormSheetState();
}

class _UserFormSheetState extends State<_UserFormSheet> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _emailCtrl;
  late final TextEditingController _passwordCtrl;
  late String _role;
  late bool _isActive;
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    final existing = widget.existing;
    _nameCtrl = TextEditingController(text: existing?.fullName ?? '');
    _emailCtrl = TextEditingController(text: existing?.email ?? '');
    _passwordCtrl = TextEditingController();
    final role = existing?.role;
    _role = (role == 'admin' || role == 'guide') ? role! : 'guide';
    _isActive = existing?.isActive ?? true;
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  bool get _canSubmit {
    if (_nameCtrl.text.trim().length < 3) return false;
    if (widget.isEditing) return true;
    final email = _emailCtrl.text.trim();
    if (email.isEmpty || !email.contains('@')) return false;
    if (_passwordCtrl.text.length < 8) return false;
    return true;
  }

  void _submit() {
    if (!_canSubmit) return;
    Navigator.of(context).pop({
      'full_name': _nameCtrl.text.trim(),
      'email': _emailCtrl.text.trim(),
      'password': _passwordCtrl.text,
      'role': _role,
      if (widget.isEditing) 'is_active': _isActive,
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
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
            AppSectionHeader(
              eyebrow: widget.isEditing ? 'Editar usuario' : 'Nuevo usuario',
              title: widget.isEditing ? 'Actualizar datos' : 'Crear usuario',
              variant: AppSectionHeaderVariant.compact,
            ),
            const SizedBox(height: 20),
            AppTextField(
              controller: _nameCtrl,
              label: 'Nombre completo *',
              hintText: 'Ej: Ana Pérez',
              onChanged: (_) => setState(() {}),
            ),
            if (!widget.isEditing) ...[
              const SizedBox(height: 12),
              AppTextField(
                controller: _emailCtrl,
                label: 'Correo *',
                hintText: 'usuario@ejemplo.com',
                inputKind: AppTextInputKind.email,
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 12),
              AppTextField(
                controller: _passwordCtrl,
                label: 'Contraseña *',
                hintText: 'Mínimo 8 caracteres',
                inputKind: AppTextInputKind.password,
                obscureText: _obscurePassword,
                onChanged: (_) => setState(() {}),
                suffix: IconButton(
                  onPressed: () {
                    setState(() => _obscurePassword = !_obscurePassword);
                  },
                  icon: Icon(
                    _obscurePassword
                        ? Icons.visibility_outlined
                        : Icons.visibility_off_outlined,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: _role,
              decoration: const InputDecoration(
                labelText: 'Rol',
                border: OutlineInputBorder(),
              ),
              items: _roleOptions.entries
                  .map(
                    (entry) => DropdownMenuItem(
                      value: entry.key,
                      child: Text(entry.value),
                    ),
                  )
                  .toList(growable: false),
              onChanged: (value) {
                if (value == null) return;
                setState(() => _role = value);
              },
            ),
            if (widget.isEditing) ...[
              const SizedBox(height: 12),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Cuenta activa'),
                value: _isActive,
                onChanged: (value) => setState(() => _isActive = value),
              ),
            ],
            const SizedBox(height: 20),
            AppButton(
              label: widget.isEditing ? 'Guardar cambios' : 'Crear usuario',
              icon: widget.isEditing ? Icons.save_rounded : Icons.add,
              expanded: true,
              onPressed: _canSubmit ? _submit : null,
            ),
            const SizedBox(height: 10),
            AppButton(
              label: 'Cancelar',
              icon: Icons.close_rounded,
              variant: AppButtonVariant.secondary,
              expanded: true,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ],
        ),
      ),
    );
  }
}
