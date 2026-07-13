import 'dart:async';

import 'package:flutter/material.dart';
import 'package:material_symbols_icons/material_symbols_icons.dart';
import 'package:mobile/features/notifications/presentation/notification_visuals.dart';

/// Heads-up toast that slides in from the top like a system notification.
class NotificationHeadsUp extends StatefulWidget {
  const NotificationHeadsUp({
    super.key,
    required this.title,
    required this.onTap,
    required this.onDismiss,
    this.body,
    this.eventType,
    this.count = 1,
    this.displayDuration = const Duration(seconds: 5),
  });

  final String title;
  final String? body;
  final String? eventType;
  final int count;
  final VoidCallback onTap;
  final VoidCallback onDismiss;
  final Duration displayDuration;

  @override
  State<NotificationHeadsUp> createState() => _NotificationHeadsUpState();
}

class _NotificationHeadsUpState extends State<NotificationHeadsUp>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<Offset> _slide;
  late final Animation<double> _fade;
  Timer? _autoDismiss;
  bool _closing = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 320),
      reverseDuration: const Duration(milliseconds: 220),
    );
    _slide = Tween<Offset>(
      begin: const Offset(0, -1.2),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic));
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeOut);
    unawaited(_controller.forward());
    _autoDismiss = Timer(widget.displayDuration, _dismiss);
  }

  @override
  void didUpdateWidget(covariant NotificationHeadsUp oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.title != widget.title ||
        oldWidget.body != widget.body ||
        oldWidget.count != widget.count) {
      _closing = false;
      _autoDismiss?.cancel();
      _autoDismiss = Timer(widget.displayDuration, _dismiss);
      unawaited(_controller.forward(from: 0));
    }
  }

  @override
  void dispose() {
    _autoDismiss?.cancel();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _dismiss() async {
    if (_closing || !mounted) return;
    _closing = true;
    _autoDismiss?.cancel();
    await _controller.reverse();
    if (mounted) widget.onDismiss();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final visuals = notificationVisuals(
      widget.eventType ?? '',
      body: widget.body ?? '',
    );
    final iconColors = notificationIconColors(context, visuals.tone);
    final top = MediaQuery.paddingOf(context).top;

    return Positioned(
      top: top + 8,
      left: 12,
      right: 12,
      child: SlideTransition(
        position: _slide,
        child: FadeTransition(
          opacity: _fade,
          child: Dismissible(
            key: ValueKey('heads-up-${widget.title}-${widget.count}'),
            direction: DismissDirection.up,
            onDismissed: (_) => widget.onDismiss(),
            child: Material(
              color: Colors.transparent,
              child: InkWell(
                onTap: widget.onTap,
                borderRadius: BorderRadius.circular(4),
                child: Ink(
                  decoration: BoxDecoration(
                    color: scheme.surfaceContainerHigh,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: scheme.outlineVariant.withValues(alpha: 0.35),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: scheme.shadow.withValues(alpha: 0.18),
                        blurRadius: 18,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: iconColors.background,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Icon(
                          visuals.icon,
                          size: 24,
                          color: iconColors.foreground,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.count > 1
                                  ? '${widget.count} notificaciones'
                                  : 'La Juana',
                              style: Theme.of(context)
                                  .textTheme
                                  .labelMedium
                                  ?.copyWith(
                                    color: scheme.onSurfaceVariant,
                                    fontWeight: FontWeight.w600,
                                  ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              widget.title,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Icon(
                        Symbols.notifications,
                        size: 18,
                        color: scheme.onSurfaceVariant,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
