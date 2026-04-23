import 'package:flutter/material.dart';

import '../../../app/widgets/app_badge.dart';
import '../../../app/widgets/app_button.dart';
import '../../../app/widgets/app_card.dart';
import '../../../app/widgets/app_scaffold.dart';
import '../../../app/widgets/app_section_header.dart';
import '../../../app/widgets/app_text_field.dart';
import '../auth_controller.dart';
import '../auth_routes.dart';
import '../auth_ui_helpers.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _fullNameCtrl = TextEditingController();
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _passwordCtrl = TextEditingController();
  final TextEditingController _confirmCtrl = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  int _lastErrorEventId = 0;

  @override
  void dispose() {
    _fullNameCtrl.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        _showErrorToastIfNeeded();

        final passwordsMatch = _passwordCtrl.text == _confirmCtrl.text;
        final validForm =
            _fullNameCtrl.text.trim().isNotEmpty &&
            _emailCtrl.text.trim().isNotEmpty &&
            _passwordCtrl.text.length >= 8 &&
            passwordsMatch &&
            !widget.controller.isLoading;

        if (widget.controller.noticeCode == 'auth.register_success') {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            Navigator.of(context).pushReplacementNamed(AuthRoutes.login);
          });
        }

        return AppScaffold(
          scrollable: true,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const AppSectionHeader(
                      title: 'Registro',
                      subtitle: 'Cuenta de acceso',
                      variant: AppSectionHeaderVariant.compact,
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        connectivityBadge(widget.controller.connectivityState),
                      ],
                    ),
                    const SizedBox(height: 12),
                    AppTextField(
                      controller: _fullNameCtrl,
                      label: 'Nombre',
                      hintText: 'Nombre completo',
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 10),
                    AppTextField(
                      controller: _emailCtrl,
                      label: 'Correo',
                      hintText: 'usuario@lajuana.co',
                      keyboardType: TextInputType.emailAddress,
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 10),
                    AppTextField(
                      controller: _passwordCtrl,
                      label: 'Contrasena',
                      obscureText: _obscurePassword,
                      suffix: IconButton(
                        onPressed: () {
                          setState(() {
                            _obscurePassword = !_obscurePassword;
                          });
                        },
                        icon: Icon(
                          _obscurePassword
                              ? Icons.visibility_outlined
                              : Icons.visibility_off_outlined,
                        ),
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 10),
                    AppTextField(
                      controller: _confirmCtrl,
                      label: 'Confirmar contrasena',
                      obscureText: _obscureConfirm,
                      suffix: IconButton(
                        onPressed: () {
                          setState(() {
                            _obscureConfirm = !_obscureConfirm;
                          });
                        },
                        icon: Icon(
                          _obscureConfirm
                              ? Icons.visibility_outlined
                              : Icons.visibility_off_outlined,
                        ),
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                    if (!passwordsMatch && _confirmCtrl.text.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      const AppBadge(
                        label: 'Las contrasenas no coinciden',
                        tone: AppBadgeTone.danger,
                        uppercase: false,
                      ),
                    ],
                    const SizedBox(height: 16),
                    AppButton(
                      label: widget.controller.isLoading
                          ? 'Creando...'
                          : 'Crear cuenta',
                      expanded: true,
                      onPressed: validForm
                          ? () {
                              widget.controller.registerSubmitted(
                                fullName: _fullNameCtrl.text.trim(),
                                email: _emailCtrl.text.trim(),
                                password: _passwordCtrl.text,
                              );
                            }
                          : null,
                    ),
                    const SizedBox(height: 8),
                    AppButton(
                      label: 'Volver a login',
                      variant: AppButtonVariant.ghost,
                      expanded: true,
                      onPressed: widget.controller.isLoading
                          ? null
                          : () {
                              Navigator.of(
                                context,
                              ).pushReplacementNamed(AuthRoutes.login);
                            },
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  void _showErrorToastIfNeeded() {
    final errorEventId = widget.controller.errorEventId;
    if (errorEventId <= _lastErrorEventId) return;
    _lastErrorEventId = errorEventId;
    final errorMessage =
        widget.controller.errorMessage ??
        widget.controller.messageForCode(widget.controller.errorCode);
    if (errorMessage == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      showAuthToast(context, message: errorMessage, isError: true);
    });
  }
}
