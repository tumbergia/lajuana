import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:mobile_ui/src/voice/voice_visualizer.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_voice_fab.dart';

import '../../domain/voice_platform_support.dart';
import '../../domain/voice_chart_spec.dart';
import '../controllers/voice_assistant_controller.dart';
import '../navigation/voice_assistant_navigation.dart';
import 'voice_chart_card.dart';
import 'voice_result_presenter.dart';

class AdminVoiceSheet extends StatefulWidget {
  const AdminVoiceSheet({
    super.key,
    required this.controller,
    required this.onClose,
    required this.hostContext,
    this.navigation,
  });

  final VoiceAssistantController controller;
  final VoidCallback onClose;
  final BuildContext hostContext;
  final VoiceAssistantNavigation? navigation;

  @override
  State<AdminVoiceSheet> createState() => _AdminVoiceSheetState();
}

class _AdminVoiceSheetState extends State<AdminVoiceSheet> {
  late final TextEditingController _textController;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.controller.transcript);
    _textController.addListener(() {
      widget.controller.updateTranscript(_textController.text);
    });
    widget.controller.addListener(_onControllerChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      widget.controller.beginSession();
    });
  }

  void _onControllerChanged() {
    _syncTranscriptFromSpeech();
    _scrollToBottomIfNeeded();
  }

  void _syncTranscriptFromSpeech() {
    final transcript = widget.controller.transcript;
    if (_textController.text == transcript) return;
    _textController.value = _textController.value.copyWith(
      text: transcript,
      selection: TextSelection.collapsed(offset: transcript.length),
    );
  }

  void _scrollToBottomIfNeeded() {
    if (!mounted || !_scrollController.hasClients) return;
    final phase = widget.controller.phase;
    if (phase != VoicePhase.answered &&
        phase != VoicePhase.awaitingConfirmation &&
        phase != VoicePhase.needsInput &&
        phase != VoicePhase.handoff) {
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOut,
      );
    });
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onControllerChanged);
    _textController.dispose();
    _scrollController.dispose();
    unawaited(widget.controller.cleanup());
    super.dispose();
  }

  Future<void> _handleClose() async {
    await widget.controller.endSession();
    widget.onClose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final controller = widget.controller;
        final theme = Theme.of(context);
        final scheme = theme.colorScheme;
        final isDark = theme.brightness == Brightness.dark;
        final visualizerColor = isDark ? Colors.white : scheme.primary;
        final isAnsweredPhase = controller.phase == VoicePhase.answered ||
            controller.phase == VoicePhase.handoff;
        final structuredResult = _structuredResult(controller);
        final chartSpec = _chartSpec(controller);
        final showManualInput = !isAnsweredPhase &&
            (controller.allowsManualInput ||
                !controller.speechSupported ||
                controller.phase == VoicePhase.error ||
                controller.phase == VoicePhase.needsInput);
        final showVisualizer = controller.speechSupported &&
            !isAnsweredPhase &&
            (controller.phase == VoicePhase.listening ||
                controller.phase == VoicePhase.processing ||
                controller.phase == VoicePhase.idle);
        final fallbackMaxHeight = MediaQuery.sizeOf(context).height * 0.92;

        return Padding(
          padding: EdgeInsets.only(
            left: 24,
            right: 24,
            top: 8,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: LayoutBuilder(
            builder: (context, constraints) {
              final maxHeight = constraints.maxHeight.isFinite
                  ? constraints.maxHeight
                  : fallbackMaxHeight;
              final chromeHeight = _chromeHeight(controller.phase);
              final bodyMaxHeight =
                  (maxHeight - chromeHeight).clamp(120.0, maxHeight);

              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const AppSectionHeader(
                    eyebrow: 'Asistente',
                    title: 'Comando de voz',
                    subtitle:
                        'Di una instrucción de gestión y el asistente ejecutará la acción.',
                    variant: AppSectionHeaderVariant.compact,
                  ),
                  const SizedBox(height: 20),
                  ConstrainedBox(
                    constraints: BoxConstraints(maxHeight: bodyMaxHeight),
                    child: SingleChildScrollView(
                      controller: _scrollController,
                      child: _VoiceCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            AnimatedSwitcher(
                              duration: const Duration(milliseconds: 250),
                              switchInCurve: Curves.easeOut,
                              switchOutCurve: Curves.easeIn,
                              child: Text(
                                _statusLabel(controller),
                                key: ValueKey(_statusLabel(controller)),
                                style: theme.textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            AnimatedSwitcher(
                              duration: const Duration(milliseconds: 250),
                              child: Text(
                                _bodyText(controller, structuredResult),
                                key: ValueKey(
                                  _bodyKey(controller, structuredResult),
                                ),
                                style: theme.textTheme.bodyMedium?.copyWith(
                                  color: scheme.onSurfaceVariant,
                                  height: 1.45,
                                ),
                              ),
                            ),
                            if (structuredResult != null) ...[
                              const SizedBox(height: 12),
                              VoiceStructuredResultList(
                                items: structuredResult.items,
                              ),
                            ],
                            if (chartSpec != null) ...[
                              const SizedBox(height: 12),
                              VoiceChartCard(spec: chartSpec),
                            ],
                            if (showManualInput) ...[
                              const SizedBox(height: 16),
                              AppTextField(
                                controller: _textController,
                                hintText: 'Escribe tu comando de gestión…',
                                variant: AppTextFieldVariant.filled,
                                maxLines: 3,
                              ),
                              if (!controller.speechSupported)
                                Padding(
                                  padding: const EdgeInsets.only(top: 8),
                                  child: Text(
                                    VoicePlatformSupport.unsupportedSpeechHint,
                                    style:
                                        theme.textTheme.labelSmall?.copyWith(
                                      color: scheme.onSurfaceVariant,
                                    ),
                                  ),
                                ),
                            ],
                            if (showVisualizer) ...[
                              const SizedBox(height: 24),
                              Center(
                                child: AnimatedScale(
                                  scale: controller.phase ==
                                              VoicePhase.listening ||
                                          controller.phase ==
                                              VoicePhase.processing
                                      ? 1
                                      : 0.96,
                                  duration: const Duration(milliseconds: 250),
                                  child: VoiceVisualizer(
                                    isActive: controller.phase ==
                                            VoicePhase.listening ||
                                        controller.phase ==
                                            VoicePhase.processing,
                                    color: visualizerColor,
                                  ),
                                ),
                              ),
                            ],
                            if (kDebugMode &&
                                controller.result?.toolName != null) ...[
                              const SizedBox(height: 20),
                              _ToolChip(
                                action: controller.result!.action,
                                toolName: controller.result!.toolName!,
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  _buildActions(context, controller),
                ],
              );
            },
          ),
        );
      },
    );
  }

  double _chromeHeight(VoicePhase phase) {
    const headerAndGaps = 130.0;
    final actionsHeight = switch (phase) {
      VoicePhase.awaitingConfirmation => 188.0,
      // Chart + actions: leave more room for the scrollable body.
      VoicePhase.answered || VoicePhase.handoff => 120.0,
      VoicePhase.needsInput || VoicePhase.error => 132.0,
      _ => 88.0,
    };
    return headerAndGaps + actionsHeight;
  }

  Widget _buildActions(BuildContext context, VoiceAssistantController controller) {
    switch (controller.phase) {
      case VoicePhase.answered:
      case VoicePhase.handoff:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppButton(
              label: 'Hablar de nuevo',
              icon: Icons.mic_rounded,
              onPressed: controller.speakAgain,
              expanded: true,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Cerrar',
              variant: AppButtonVariant.secondary,
              onPressed: _handleClose,
              expanded: true,
            ),
          ],
        );
      case VoicePhase.awaitingConfirmation:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppButton(
              label: 'Confirmar',
              icon: Icons.check_rounded,
              onPressed: controller.isProcessing ? null : controller.confirmPendingAction,
              expanded: true,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Cancelar acción',
              variant: AppButtonVariant.secondary,
              icon: Icons.close_rounded,
              onPressed: controller.isProcessing ? null : controller.cancelPendingAction,
              expanded: true,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Cerrar',
              variant: AppButtonVariant.ghost,
              onPressed: _handleClose,
              expanded: true,
            ),
          ],
        );
      case VoicePhase.needsInput:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppButton(
              label: 'Responder',
              icon: Icons.send_rounded,
              onPressed: !controller.canSend ? null : controller.sendTranscript,
              expanded: true,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Cerrar',
              variant: AppButtonVariant.secondary,
              onPressed: _handleClose,
              expanded: true,
            ),
          ],
        );
      case VoicePhase.error:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppButton(
              label: 'Reintentar',
              icon: Icons.refresh_rounded,
              onPressed: controller.beginSession,
              expanded: true,
            ),
            const SizedBox(height: 12),
            AppButton(
              label: 'Cerrar',
              variant: AppButtonVariant.secondary,
              onPressed: _handleClose,
              expanded: true,
            ),
          ],
        );
      default:
        return Row(
          children: [
            Expanded(
              child: AppButton(
                label: 'Cancelar',
                variant: AppButtonVariant.ghost,
                onPressed: controller.isProcessing ? null : _handleClose,
                expanded: true,
              ),
            ),
            if (controller.speechSupported) ...[
              const SizedBox(width: 12),
              AppVoiceFab(
                size: 56,
                elevated: false,
                icon: controller.isListening
                    ? Icons.pause_rounded
                    : Icons.mic_rounded,
                onTap: controller.isProcessing
                    ? null
                    : (controller.isListening
                        ? controller.stopListening
                        : controller.startListening),
              ),
            ],
            const SizedBox(width: 12),
            Expanded(
              child: AppButton(
                label: controller.isProcessing ? 'Procesando' : 'Enviar',
                icon: Icons.send_rounded,
                onPressed:
                    controller.isProcessing || !controller.canSend
                        ? null
                        : controller.sendTranscript,
                expanded: true,
              ),
            ),
          ],
        );
    }
  }

  String _statusLabel(VoiceAssistantController controller) {
    return switch (controller.phase) {
      VoicePhase.idle => 'Listo para escuchar',
      VoicePhase.listening => 'Escuchando…',
      VoicePhase.processing => controller.processingStatusLabel,
      VoicePhase.answered => 'Respuesta del asistente',
      VoicePhase.awaitingConfirmation => 'Confirmación requerida',
      VoicePhase.needsInput => 'Necesita más información',
      VoicePhase.handoff => 'Revisión humana',
      VoicePhase.error => 'No se pudo completar',
    };
  }

  VoiceStructuredResult? _structuredResult(VoiceAssistantController controller) {
    final result = controller.result;
    final navigation = widget.navigation;
    if (result == null || navigation == null) return null;
    if (controller.phase != VoicePhase.answered &&
        controller.phase != VoicePhase.handoff &&
        controller.phase != VoicePhase.awaitingConfirmation &&
        controller.phase != VoicePhase.needsInput) {
      return null;
    }
    return VoiceResultPresenter.present(
      toolName: result.toolName,
      toolOutput: result.toolOutput,
      navigation: navigation,
      hostContext: widget.hostContext,
      closeSheet: widget.onClose,
    );
  }

  VoiceChartSpec? _chartSpec(VoiceAssistantController controller) {
    final result = controller.result;
    if (result == null) return null;
    if (controller.phase != VoicePhase.answered &&
        controller.phase != VoicePhase.handoff &&
        controller.phase != VoicePhase.awaitingConfirmation &&
        controller.phase != VoicePhase.needsInput) {
      return null;
    }
    return VoiceChartSpec.tryParse(result.toolOutput['chart']);
  }

  String _bodyKey(
    VoiceAssistantController controller,
    VoiceStructuredResult? structuredResult,
  ) {
    if (controller.errorMessage != null) return 'error:${controller.errorMessage}';
    if (controller.phase == VoicePhase.processing) {
      return 'processing:${controller.processingStage.name}';
    }
    final chart = _chartSpec(controller);
    if (structuredResult != null || chart != null) {
      return 'structured:${controller.result!.traceId}:'
          '${structuredResult?.summary ?? ''}:${chart?.title ?? ''}';
    }
    if (controller.result != null &&
        (controller.phase == VoicePhase.answered ||
            controller.phase == VoicePhase.awaitingConfirmation ||
            controller.phase == VoicePhase.needsInput ||
            controller.phase == VoicePhase.handoff)) {
      return 'result:${controller.result!.traceId}:${controller.result!.response}';
    }
    return 'transcript:${controller.transcript}';
  }

  String _bodyText(
    VoiceAssistantController controller,
    VoiceStructuredResult? structuredResult,
  ) {
    if (controller.errorMessage != null) {
      return controller.errorMessage!;
    }
    if (controller.phase == VoicePhase.processing) {
      return 'El asistente está interpretando tu instrucción y preparando la acción.';
    }
    if (structuredResult != null) {
      return structuredResult.summary;
    }
    final chart = _chartSpec(controller);
    if (chart != null &&
        controller.result != null &&
        controller.result!.response.trim().isNotEmpty) {
      return controller.result!.response;
    }
    if (chart != null) {
      return chart.subtitle == null
          ? chart.title
          : '${chart.title}. ${chart.subtitle}';
    }
    if (controller.result != null &&
        (controller.phase == VoicePhase.answered ||
            controller.phase == VoicePhase.awaitingConfirmation ||
            controller.phase == VoicePhase.needsInput ||
            controller.phase == VoicePhase.handoff)) {
      return controller.result!.response;
    }
    if (controller.transcript.trim().isNotEmpty) {
      return controller.transcript;
    }
    return 'Ej: listar reservas pendientes o confirmar la reserva de mañana';
  }
}

class _VoiceCard extends StatelessWidget {
  const _VoiceCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHigh,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: scheme.outlineVariant),
      ),
      child: child,
    );
  }
}

class _ToolChip extends StatelessWidget {
  const _ToolChip({
    required this.action,
    required this.toolName,
  });

  final String action;
  final String toolName;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: scheme.surfaceContainer,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(color: scheme.outlineVariant),
        ),
        child: Text(
          '$action · $toolName',
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: scheme.onSurfaceVariant,
                letterSpacing: 0.4,
              ),
        ),
      ),
    );
  }
}
