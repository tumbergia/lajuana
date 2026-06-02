import 'package:flutter/material.dart';
import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_top_bar.dart';
import 'package:mobile_ui/src/widgets/app_voice_fab.dart';
import 'voice_context.dart';
import 'voice_route.dart';
import 'voice_visualizer.dart';

enum VoiceRecordState { listening, paused, ready }

class VoiceScreen extends StatefulWidget {
  final VoiceContext voiceContext;

  const VoiceScreen({super.key, required this.voiceContext});

  @override
  State<VoiceScreen> createState() => _VoiceScreenState();
}

class _VoiceScreenState extends State<VoiceScreen> {
  VoiceRecordState _state = VoiceRecordState.listening;

  void _onTogglePause() {
    setState(() {
      if (_state == VoiceRecordState.listening) {
        _state = VoiceRecordState.paused;
      } else if (_state == VoiceRecordState.paused) {
        _state = VoiceRecordState.listening;
      }
    });
  }

  void _onReset() {
    closeAllVoiceScreens(context);
  }

  void _onSend() {
    setState(() {
      _state = VoiceRecordState.ready;
    });
    // Simulate sending action and popping
    Future.delayed(const Duration(milliseconds: 600), () {
      if (mounted) Navigator.of(context).pop();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final backgroundColor = theme.colorScheme.surface;

    final String statusText = switch (_state) {
      VoiceRecordState.listening => 'Escuchando...',
      VoiceRecordState.paused => 'Pausado',
      VoiceRecordState.ready => 'Procesando...',
    };

    return AppScaffold(
      appBar: const AppTopBar(
        logoAssetPath: 'assets/branding/lajuana.svg',
        title: 'LA JUANA',
      ),
      bottomNavigationBar: const AppBottomNav(current: AppNavItem.none),
      padding: EdgeInsets.zero,
      scrollable: false,
      backgroundColor: backgroundColor,
      child: Stack(
        children: [
          Positioned.fill(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 32, 24, 180),
              child: Column(
                children: [
                  const SizedBox(height: 24),
                  Text(
                    widget.voiceContext.guidanceText,
                    textAlign: TextAlign.center,
                    style: theme.textTheme.displaySmall?.copyWith(
                      color: isDark
                          ? const Color(0xFFE2E2E2)
                          : theme.colorScheme.onSurface,
                      fontWeight: FontWeight.w700,
                      fontSize: 40,
                      height: 1.25,
                    ),
                  ),
                  const SizedBox(height: 78),
                  Expanded(
                    child: Container(
                      width: double.infinity,
                      constraints: const BoxConstraints(maxWidth: 448),
                      padding: const EdgeInsets.all(32),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHigh,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            statusText,
                            style: theme.textTheme.headlineSmall?.copyWith(
                              color: isDark
                                  ? const Color(0xFFE2E2E2)
                                  : theme.colorScheme.onSurface,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            widget.voiceContext.transcriptHint,
                            textAlign: TextAlign.center,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: isDark
                                  ? const Color(0xFFC6C6C6)
                                  : theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                          const SizedBox(height: 32),
                          AnimatedOpacity(
                            opacity: _state == VoiceRecordState.listening
                                ? 1.0
                                : 0.35,
                            duration: const Duration(milliseconds: 300),
                            child: VoiceVisualizer(
                              isActive: _state == VoiceRecordState.listening,
                              color: isDark
                                  ? Colors.white
                                  : theme.colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          Positioned(
            left: 0,
            right: 0,
            bottom: 68,
            child: Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Cancel / Reset button — fixed width prevents label shifts
                  SizedBox(
                    width: 80,
                    child: _ControlButton(
                      icon: Icons.close_rounded,
                      onTap: _onReset,
                      label: 'Cancelar',
                      color: theme.colorScheme.error,
                    ),
                  ),
                  const SizedBox(width: 16),
                  // FAB — wrapped in Column with invisible label spacer
                  // so it stays vertically aligned with control buttons
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AppVoiceFab(
                        onTap: _onTogglePause,
                        icon: _state == VoiceRecordState.listening
                            ? Icons.pause_rounded
                            : Icons.mic_rounded,
                      ),
                      // Invisible spacer matching label + SizedBox(8) height
                      const SizedBox(height: 8 + 20),
                    ],
                  ),
                  const SizedBox(width: 16),
                  // Send button — fixed width mirrors left side
                  SizedBox(
                    width: 80,
                    child: _ControlButton(
                      icon: Icons.send_rounded,
                      onTap:
                          _state == VoiceRecordState.listening ||
                              _state == VoiceRecordState.paused
                          ? _onSend
                          : null,
                      label: 'Enviar',
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ControlButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback? onTap;
  final String label;
  final Color color;

  const _ControlButton({
    required this.icon,
    required this.onTap,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final disabled = onTap == null;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Material(
          color: disabled
              ? theme.colorScheme.surfaceContainerHigh
              : color.withValues(alpha: 0.1),
          shape: const CircleBorder(),
          child: InkWell(
            onTap: onTap,
            customBorder: const CircleBorder(),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Icon(
                icon,
                color: disabled
                    ? theme.colorScheme.onSurface.withValues(alpha: 0.3)
                    : color,
                size: 28,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          textAlign: TextAlign.center,
          style: theme.textTheme.labelMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: disabled
                ? theme.colorScheme.onSurface.withValues(alpha: 0.3)
                : color,
          ),
        ),
      ],
    );
  }
}
