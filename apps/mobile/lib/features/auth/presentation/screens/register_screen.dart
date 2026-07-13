import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/auth_ui_helpers.dart';
import 'package:mobile/shared/input_validation.dart';

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
  static const Key _logoKey = Key('register_logo');
  static const Key _titleKey = Key('register_title');
  static const Key _loginLinkKey = Key('register_login_link');
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
        final showPasswordMismatch =
            !passwordsMatch && _confirmCtrl.text.isNotEmpty;
        final validForm =
            _fullNameCtrl.text.trim().isNotEmpty &&
            InputValidation.isValidEmail(_emailCtrl.text) &&
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
          scrollable: false,
          resizeToAvoidBottomInset: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final slots = _RegisterLayoutSlots.forHeight(
                constraints.maxHeight,
              );
              final contentHeight = slots.contentHeight(
                showPasswordMismatch: showPasswordMismatch,
              );
              final needsScroll = constraints.maxHeight < contentHeight;

              final content = SizedBox(
                height: needsScroll ? contentHeight : constraints.maxHeight,
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Stack(
                      children: [
                        Positioned(
                          top: slots.logoY,
                          left: 0,
                          right: 0,
                          child: Center(
                            child: SizedBox(
                              key: _logoKey,
                              width: slots.logoWidth,
                              height: slots.logoHeight,
                              child: SvgPicture.asset(
                                'assets/branding/lajuana-banner.svg',
                                fit: BoxFit.contain,
                                colorFilter: ColorFilter.mode(
                                  Theme.of(context).colorScheme.onSurface,
                                  BlendMode.srcIn,
                                ),
                              ),
                            ),
                          ),
                        ),
                        Positioned(
                          top: slots.titleY,
                          left: 0,
                          right: 0,
                          child: Text(
                            'Registro',
                            key: _titleKey,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w800),
                          ),
                        ),
                        Positioned(
                          top: slots.fullNameY,
                          left: 0,
                          right: 0,
                          child: AppTextField(
                            controller: _fullNameCtrl,
                            label: 'Nombre',
                            hintText: 'Nombre completo',
                            onChanged: (_) => setState(() {}),
                          ),
                        ),
                        Positioned(
                          top: slots.emailY,
                          left: 0,
                          right: 0,
                          child: AppTextField(
                            controller: _emailCtrl,
                            label: 'Correo',
                            hintText: 'usuario@lajuana.co',
                            inputKind: AppTextInputKind.email,
                            onChanged: (_) => setState(() {}),
                          ),
                        ),
                        Positioned(
                          top: slots.passwordY,
                          left: 0,
                          right: 0,
                          child: AppTextField(
                            controller: _passwordCtrl,
                            label: 'Contrasena',
                            inputKind: AppTextInputKind.password,
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
                        ),
                        Positioned(
                          top: slots.confirmY,
                          left: 0,
                          right: 0,
                          child: AppTextField(
                            controller: _confirmCtrl,
                            label: 'Confirmar contrasena',
                            inputKind: AppTextInputKind.password,
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
                        ),
                        if (showPasswordMismatch)
                          Positioned(
                            top: slots.passwordMismatchY,
                            left: 0,
                            right: 0,
                            child: Text(
                              'Las contrasenas no coinciden',
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: Theme.of(context).colorScheme.error,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                          ),
                        Positioned(
                          top: slots.submitY,
                          left: 0,
                          right: 0,
                          child: AppButton(
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
                        ),
                        Positioned(
                          top: slots.loginLinkY,
                          left: 0,
                          right: 0,
                          child: _LoginInlineLink(
                            key: _loginLinkKey,
                            isEnabled: !widget.controller.isLoading,
                            onTap: () {
                              Navigator.of(
                                context,
                              ).pushReplacementNamed(AuthRoutes.login);
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );

              if (!needsScroll) return content;
              return SingleChildScrollView(child: content);
            },
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

class _RegisterLayoutSlots {
  static const double _linkHeight = 24;
  static const double _passwordMismatchHeight = 20;

  static const _bannerAspectRatio = 1600 / 567;

  final double logoY;
  final double titleY;
  final double fullNameY;
  final double emailY;
  final double passwordY;
  final double confirmY;
  final double passwordMismatchY;
  final double submitY;
  final double loginLinkY;
  final double logoWidth;
  final double bottomPadding;

  const _RegisterLayoutSlots({
    required this.logoY,
    required this.titleY,
    required this.fullNameY,
    required this.emailY,
    required this.passwordY,
    required this.confirmY,
    required this.passwordMismatchY,
    required this.submitY,
    required this.loginLinkY,
    required this.logoWidth,
    required this.bottomPadding,
  });

  double get logoHeight => logoWidth / _bannerAspectRatio;

  factory _RegisterLayoutSlots.forHeight(double height) {
    if (height >= 780) {
      return const _RegisterLayoutSlots(
        logoY: 16,
        titleY: 132,
        fullNameY: 218,
        emailY: 306,
        passwordY: 394,
        confirmY: 482,
        passwordMismatchY: 568,
        submitY: 600,
        loginLinkY: 668,
        logoWidth: 260,
        bottomPadding: 28,
      );
    }

    return const _RegisterLayoutSlots(
      logoY: 4,
      titleY: 100,
      fullNameY: 170,
      emailY: 258,
      passwordY: 346,
      confirmY: 434,
      passwordMismatchY: 520,
      submitY: 548,
      loginLinkY: 616,
      logoWidth: 220,
      bottomPadding: 24,
    );
  }

  double contentHeight({required bool showPasswordMismatch}) {
    final mismatchBottom = showPasswordMismatch
        ? passwordMismatchY + _passwordMismatchHeight
        : submitY;
    final mainBottom = loginLinkY + _linkHeight;
    final bottom = mainBottom > mismatchBottom ? mainBottom : mismatchBottom;
    return bottom + bottomPadding;
  }
}

class _LoginInlineLink extends StatelessWidget {
  const _LoginInlineLink({
    super.key,
    required this.isEnabled,
    required this.onTap,
  });

  final bool isEnabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return Center(
      child: Wrap(
        spacing: 4,
        crossAxisAlignment: WrapCrossAlignment.center,
        alignment: WrapAlignment.center,
        children: [
          Text(
            'Ya tienes cuenta?',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
          ),
          TextButton(
            onPressed: isEnabled ? onTap : null,
            style: TextButton.styleFrom(
              padding: EdgeInsets.zero,
              minimumSize: const Size(0, 0),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              visualDensity: VisualDensity.compact,
            ),
            child: Text(
              'Inicia sesion',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: scheme.primary,
                fontWeight: FontWeight.w700,
                decoration: TextDecoration.underline,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
