import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

import '../../../app/widgets/app_button.dart';
import '../../../app/widgets/app_scaffold.dart';
import '../../../app/widgets/app_text_field.dart';
import '../../domain/auth_enums.dart';
import '../auth_controller.dart';
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
            _emailCtrl.text.trim().isNotEmpty &&
            _passwordCtrl.text.isNotEmpty &&
            !widget.controller.isLoading;
        final showLocalSessionButton = widget.controller.hasLocalSession;

        return AppScaffold(
          scrollable: false,
          child: LayoutBuilder(
            builder: (context, constraints) {
              final slots = _LoginLayoutSlots.forHeight(constraints.maxHeight);
              final contentHeight = slots.contentHeight(
                includeLocalSessionButton: showLocalSessionButton,
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
                              width: slots.logoSize,
                              height: slots.logoSize,
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
                        ),
                        Positioned(
                          top: slots.titleY,
                          left: 0,
                          right: 0,
                          child: Text(
                            'Iniciar sesion',
                            key: _titleKey,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w800),
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
                            keyboardType: TextInputType.emailAddress,
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
                        ),
                        Positioned(
                          top: slots.submitY,
                          left: 0,
                          right: 0,
                          child: AppButton(
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
                        ),
                        Positioned(
                          top: slots.registerLinkY,
                          left: 0,
                          right: 0,
                          child: _RegisterInlineLink(
                            key: _registerLinkKey,
                            isEnabled: !widget.controller.isLoading,
                            onTap: () {
                              Navigator.of(
                                context,
                              ).pushNamed(AuthRoutes.register);
                            },
                          ),
                        ),
                        if (showLocalSessionButton)
                          Positioned(
                            top: slots.localSessionY,
                            left: 0,
                            right: 0,
                            child: AppButton(
                              label: 'Continuar con sesion local',
                              variant: AppButtonVariant.ghost,
                              onPressed: widget.controller.isLoading
                                  ? null
                                  : widget
                                        .controller
                                        .enterLocalSessionRequested,
                              expanded: true,
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

class _LoginLayoutSlots {
  static const double _buttonHeight = 52;
  static const double _registerLinkHeight = 24;

  final double logoY;
  final double titleY;
  final double emailY;
  final double passwordY;
  final double submitY;
  final double registerLinkY;
  final double localSessionY;
  final double logoSize;
  final double bottomPadding;

  const _LoginLayoutSlots({
    required this.logoY,
    required this.titleY,
    required this.emailY,
    required this.passwordY,
    required this.submitY,
    required this.registerLinkY,
    required this.localSessionY,
    required this.logoSize,
    required this.bottomPadding,
  });

  factory _LoginLayoutSlots.forHeight(double height) {
    if (height >= 700) {
      return const _LoginLayoutSlots(
        logoY: 24,
        titleY: 154,
        emailY: 228,
        passwordY: 322,
        submitY: 420,
        registerLinkY: 486,
        localSessionY: 532,
        logoSize: 116,
        bottomPadding: 32,
      );
    }

    return const _LoginLayoutSlots(
      logoY: 8,
      titleY: 118,
      emailY: 186,
      passwordY: 278,
      submitY: 372,
      registerLinkY: 436,
      localSessionY: 478,
      logoSize: 96,
      bottomPadding: 24,
    );
  }

  double contentHeight({required bool includeLocalSessionButton}) {
    double bottom = registerLinkY + _registerLinkHeight;
    if (includeLocalSessionButton) {
      bottom = localSessionY + _buttonHeight;
    }
    return bottom + bottomPadding;
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
