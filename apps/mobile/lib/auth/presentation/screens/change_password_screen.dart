import 'package:flutter/material.dart';

import '../../../app/widgets/app_badge.dart';
import '../../../app/widgets/app_button.dart';
import '../../../app/widgets/app_card.dart';
import '../../../app/widgets/app_scaffold.dart';
import '../../../app/widgets/app_section_header.dart';
import '../../../app/widgets/app_text_field.dart';
import '../../../app/widgets/app_top_bar.dart';
import '../../domain/auth_enums.dart';
import '../auth_controller.dart';
import '../auth_ui_helpers.dart';

class ChangePasswordScreen extends StatefulWidget {
  const ChangePasswordScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  State<ChangePasswordScreen> createState() => _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends State<ChangePasswordScreen> {
  final TextEditingController _currentCtrl = TextEditingController();
  final TextEditingController _newCtrl = TextEditingController();
  final TextEditingController _confirmCtrl = TextEditingController();

  bool _obscureCurrent = true;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  int _lastErrorEventId = 0;
  int _lastNoticeEventId = 0;

  @override
  void dispose() {
    _currentCtrl.dispose();
    _newCtrl.dispose();
    _confirmCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        _showFeedbackToastsIfNeeded();

        final isOnline =
            widget.controller.connectivityState != ConnectivityState.offline;
        final passwordsMatch = _newCtrl.text == _confirmCtrl.text;
        final canSubmit =
            isOnline &&
            !widget.controller.isLoading &&
            _currentCtrl.text.isNotEmpty &&
            _newCtrl.text.length >= 8 &&
            passwordsMatch;

        return AppScaffold(
          appBar: const AppTopBar(
            logoAssetPath: 'assets/branding/lajuana.svg',
            title: 'Seguridad',
          ),
          child: AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const AppSectionHeader(
                  title: 'Cambio de contrasena',
                  variant: AppSectionHeaderVariant.compact,
                ),
                const SizedBox(height: 12),
                if (!isOnline)
                  const AppBadge(
                    label: 'Requiere internet',
                    tone: AppBadgeTone.warning,
                    uppercase: false,
                  ),
                const SizedBox(height: 12),
                AppTextField(
                  controller: _currentCtrl,
                  label: 'Contrasena actual',
                  obscureText: _obscureCurrent,
                  suffix: IconButton(
                    onPressed: () {
                      setState(() {
                        _obscureCurrent = !_obscureCurrent;
                      });
                    },
                    icon: Icon(
                      _obscureCurrent
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 10),
                AppTextField(
                  controller: _newCtrl,
                  label: 'Nueva contrasena',
                  obscureText: _obscureNew,
                  suffix: IconButton(
                    onPressed: () {
                      setState(() {
                        _obscureNew = !_obscureNew;
                      });
                    },
                    icon: Icon(
                      _obscureNew
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 10),
                AppTextField(
                  controller: _confirmCtrl,
                  label: 'Confirmar nueva',
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
                      ? 'Guardando...'
                      : 'Guardar',
                  expanded: true,
                  onPressed: canSubmit
                      ? () {
                          widget.controller.changePasswordSubmitted(
                            currentPassword: _currentCtrl.text,
                            newPassword: _newCtrl.text,
                          );
                        }
                      : null,
                ),
              ],
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
