import 'package:flutter/material.dart';

import '../../../app/widgets/app_badge.dart';
import '../../../app/widgets/app_button.dart';
import '../../../app/widgets/app_card.dart';
import '../../../app/widgets/app_scaffold.dart';
import '../../../app/widgets/app_section_header.dart';
import '../../../app/widgets/app_text_field.dart';
import '../../domain/auth_enums.dart';
import '../auth_controller.dart';
import '../auth_feature_flags.dart';
import '../auth_routes.dart';
import '../auth_ui_helpers.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _passwordCtrl = TextEditingController();
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
            _emailCtrl.text.trim().isNotEmpty &&
            _passwordCtrl.text.isNotEmpty &&
            !widget.controller.isLoading;

        return AppScaffold(
          scrollable: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: AppCard(
                tone: AppCardTone.high,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const AppSectionHeader(
                      title: 'Ingresar',
                      subtitle: 'Acceso operativo',
                      variant: AppSectionHeaderVariant.compact,
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        connectivityBadge(widget.controller.connectivityState),
                        if (widget.controller.hasLocalSession)
                          const AppBadge(
                            label: 'Sesion local disponible',
                            tone: AppBadgeTone.warning,
                            uppercase: false,
                          ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    AppTextField(
                      controller: _emailCtrl,
                      label: 'Correo',
                      hintText: 'usuario@lajuana.co',
                      keyboardType: TextInputType.emailAddress,
                      onChanged: (_) => setState(() {}),
                    ),
                    const SizedBox(height: 12),
                    AppTextField(
                      controller: _passwordCtrl,
                      label: 'Contrasena',
                      hintText: '********',
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
                    const SizedBox(height: 16),
                    AppButton(
                      label: widget.controller.isLoading
                          ? 'Ingresando...'
                          : 'Ingresar',
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
                    const SizedBox(height: 8),
                    if (AuthFeatureFlags.enableRegister)
                      AppButton(
                        label: 'Crear cuenta',
                        variant: AppButtonVariant.secondary,
                        onPressed: widget.controller.isLoading
                            ? null
                            : () {
                                Navigator.of(
                                  context,
                                ).pushNamed(AuthRoutes.register);
                              },
                        expanded: true,
                      ),
                    if (widget.controller.hasLocalSession) ...[
                      const SizedBox(height: 8),
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
              ),
            ),
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
