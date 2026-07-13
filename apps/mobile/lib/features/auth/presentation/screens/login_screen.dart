import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/auth/domain/auth_enums.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/auth/presentation/auth_routes.dart';
import 'package:mobile/features/auth/presentation/auth_ui_helpers.dart';
import 'package:mobile/shared/input_validation.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _passwordCtrl = TextEditingController();
  static const Key _logoKey = Key('login_logo');
  static const Key _titleKey = Key('login_title');
  static const Key _registerLinkKey = Key('login_register_link');
  bool _obscurePassword = true;
  int _lastErrorEventId = 0;
  int _lastNoticeEventId = 0;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        _showFeedbackToastsIfNeeded();

        if (widget.controller.authState == LocalAuthState.signedInVerified ||
            widget.controller.authState ==
                LocalAuthState.signedInLocalUnverified) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!mounted) return;
            Navigator.of(context).pushReplacementNamed(AuthRoutes.home);
          });
        }

        final canSubmit =
            InputValidation.isValidEmail(_emailCtrl.text) &&
            _passwordCtrl.text.isNotEmpty &&
            !widget.controller.isLoading;
        final showLocalSessionButton = widget.controller.hasLocalSession;

        return AppScaffold(
          scrollable: false,
          resizeToAvoidBottomInset: false,
          padding: const EdgeInsets.fromLTRB(48, 16, 48, 32),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final logoSize = constraints.maxHeight >= 700 ? 116.0 : 96.0;

              final form = ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Center(
                      child: SizedBox(
                        key: _logoKey,
                        width: logoSize,
                        height: logoSize,
                        child: SvgPicture.asset(
                          'assets/branding/lajuana.svg',
                          fit: BoxFit.contain,
                          colorFilter: ColorFilter.mode(
                            Theme.of(context).colorScheme.onSurface,
                            BlendMode.srcIn,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Iniciar sesion',
                      key: _titleKey,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 24),
                    AppTextField(
                      controller: _emailCtrl,
                      label: 'Correo',
                      hintText: 'usuario@lajuana.co',
                      inputKind: AppTextInputKind.email,
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 16),
                    AppTextField(
                      controller: _passwordCtrl,
                      label: 'Contrasena',
                      hintText: '********',
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
                    const SizedBox(height: 24),
                    AppButton(
                      label: widget.controller.isLoading
                          ? 'Ingresando...'
                          : 'Iniciar sesion',
                      onPressed: canSubmit
                          ? () {
                              widget.controller.loginSubmitted(
                                email: _emailCtrl.text.trim(),
                                password: _passwordCtrl.text,
                              );
                            }
                          : null,
                      expanded: true,
                    ),
                    const SizedBox(height: 16),
                    _RegisterInlineLink(
                      key: _registerLinkKey,
                      isEnabled: !widget.controller.isLoading,
                      onTap: () {
                        Navigator.of(context).pushNamed(AuthRoutes.register);
                      },
                    ),
                    if (showLocalSessionButton) ...[
                      const SizedBox(height: 16),
                      AppButton(
                        label: 'Continuar con sesion local',
                        variant: AppButtonVariant.ghost,
                        onPressed: widget.controller.isLoading
                            ? null
                            : widget.controller.enterLocalSessionRequested,
                        expanded: true,
                      ),
                    ],
                  ],
                ),
              );

              return SingleChildScrollView(
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Center(child: form),
                ),
              );
            },
          ),
        );
      },
    );
  }

  void _showFeedbackToastsIfNeeded() {
    final errorEventId = widget.controller.errorEventId;
    if (errorEventId > _lastErrorEventId) {
      _lastErrorEventId = errorEventId;
      final errorMessage =
          widget.controller.errorMessage ??
          widget.controller.messageForCode(widget.controller.errorCode);
      if (errorMessage != null) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (!mounted) return;
          showAuthToast(context, message: errorMessage, isError: true);
        });
      }
    }

    final noticeEventId = widget.controller.noticeEventId;
    if (noticeEventId <= _lastNoticeEventId) return;
    _lastNoticeEventId = noticeEventId;
    final noticeMessage =
        widget.controller.noticeMessage ??
        widget.controller.messageForCode(widget.controller.noticeCode);
    if (noticeMessage == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      showAuthToast(context, message: noticeMessage, isError: false);
      widget.controller.clearNotice();
    });
  }
}

class _RegisterInlineLink extends StatelessWidget {
  const _RegisterInlineLink({
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
            'No tienes cuenta?',
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
              'Registrate',
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
