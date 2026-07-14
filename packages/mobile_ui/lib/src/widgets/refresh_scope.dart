import 'dart:async';

import 'package:flutter/material.dart';

/// Colocado en el shell sobre el area de navegacion.
///
/// Provee un [RefreshIndicator] GLOBAL que se activa SOLO si la pantalla
/// actual (la de mas arriba en el stack de navegacion) registro un callback
/// via [RefreshableState].
///
/// Sin registro -> no hay indicador, no hay glow, overhead cero.
/// Con registro -> pull-to-refresh funciona automaticamente sin anidar
/// otro [RefreshIndicator] local.
///
/// Maneja correctamente push/pop de rutas en el mismo Navigator:
/// cuando se pushea un detalle, el callback de la lista queda "debajo"
/// en el stack y al hacer pop el detalle, el callback de la lista
/// vuelve a ser el activo.
class RefreshScope extends StatefulWidget {
  const RefreshScope({super.key, required this.child, this.onAfterRefresh});

  final Widget child;

  /// Se invoca después de cada pull-to-refresh (haya tenido éxito o no), sin
  /// importar qué pantalla lo disparó. Pensado para revalidar conectividad de
  /// inmediato en vez de esperar al próximo ciclo de un timer periódico.
  final Future<void> Function()? onAfterRefresh;

  static RefreshScopeState? of(BuildContext context) {
    return context.findAncestorStateOfType<RefreshScopeState>();
  }

  @override
  State<RefreshScope> createState() => RefreshScopeState();
}

class RefreshScopeState extends State<RefreshScope> {
  /// Mapa state -> callback. El ultimo en registrarse es el activo.
  final Map<State, Future<void> Function()> _entries = {};

  /// La pantalla [caller] se registra con su callback.
  void register(State caller, Future<void> Function() cb) {
    _entries[caller] = cb;
  }

  /// La pantalla [caller] se desregistra (normalmente en dispose).
  void unregister(State caller) {
    _entries.remove(caller);
  }

  Future<void> Function()? get _activeCallback {
    while (_entries.isNotEmpty) {
      final entry = _entries.entries.last;
      if (!entry.key.mounted) {
        _entries.remove(entry.key);
        continue;
      }
      return entry.value;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    // Arbol estable: siempre [RefreshIndicator]. El callback activo se resuelve
    // en tiempo de ejecucion para evitar rebuilds al registrar/desregistrar pantallas.
    return RefreshIndicator(
      onRefresh: () async {
        final cb = _activeCallback;
        try {
          if (cb != null) await cb();
        } finally {
          // Siempre, haya fallado o no: si el refresh no pudo llegar al
          // servidor, esto lo detecta ya mismo en vez de esperar el timer.
          unawaited(widget.onAfterRefresh?.call());
        }
      },
      notificationPredicate: (notification) =>
          _activeCallback != null &&
          defaultScrollNotificationPredicate(notification),
      displacement: 48,
      child: widget.child,
    );
  }
}

/// Mixin para [State] de cualquier pantalla que quiera pull-to-refresh.
///
/// Uso:
/// ```dart
/// class _MyScreenState extends State<MyScreen> with RefreshableState {
///   Future<void> onRefresh() => _controller.loadData();
/// }
/// ```
///
/// Se registra en [RefreshScope] al montar y se desregistra al disposal.
/// Sin el mixin el [RefreshScope] simplemente no muestra el indicador.
///
/// Soporta correctamente push/pop del Navigator: cuando una pantalla B
/// se pushea sobre A, B reemplaza el callback activo. Cuando B se desapila,
/// el callback de A vuelve automaticamente.
mixin RefreshableState<T extends StatefulWidget> on State<T> {
  /// Implementar con la logica de refresco de la pantalla.
  Future<void> onRefresh();

  RefreshScopeState? _refreshScope;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final scope = RefreshScope.of(context);
    if (scope == _refreshScope) {
      _refreshScope?.register(this, _guardedOnRefresh);
      return;
    }
    _refreshScope?.unregister(this);
    _refreshScope = scope;
    _refreshScope?.register(this, _guardedOnRefresh);
  }

  @override
  void dispose() {
    _refreshScope?.unregister(this);
    _refreshScope = null;
    super.dispose();
  }

  Future<void> _guardedOnRefresh() async {
    if (!mounted) return;
    await onRefresh();
  }
}

/// Scroll wrapper que garantiza overscroll para [RefreshIndicator] global.
///
/// Usar en estados loading/error/empty o contenido corto que no llena
/// la pantalla. Combina [AlwaysScrollableScrollPhysics] con altura minima
/// igual al viewport disponible.
class RefreshableViewport extends StatelessWidget {
  const RefreshableViewport({
    super.key,
    required this.child,
    this.padding,
    this.controller,
  });

  final Widget child;
  final EdgeInsetsGeometry? padding;
  final ScrollController? controller;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final minHeight = constraints.hasBoundedHeight
            ? constraints.maxHeight
            : MediaQuery.sizeOf(context).height;

        return SingleChildScrollView(
          controller: controller,
          physics: const AlwaysScrollableScrollPhysics(),
          padding: padding,
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minHeight: minHeight > 0 ? minHeight : 0,
            ),
            child: child,
          ),
        );
      },
    );
  }
}
