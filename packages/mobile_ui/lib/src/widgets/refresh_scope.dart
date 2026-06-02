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
  const RefreshScope({super.key, required this.child});

  final Widget child;

  static RefreshScopeState? of(BuildContext context) {
    return context.findAncestorStateOfType<RefreshScopeState>();
  }

  @override
  State<RefreshScope> createState() => RefreshScopeState();
}

class RefreshScopeState extends State<RefreshScope> {
  /// Mapa state -> callback. El orden de insercion importa:
  /// el ultimo en registrarse es el activo.
  final Map<State, Future<void> Function()> _entries = {};

  /// Transition: empty ↔ non-empty cambia el build output.
  /// No podemos llamar setState durante build (el child se registra
  /// en didChangeDependencies dentro del mismo frame), asi que
  /// diferimos con post-frame callback.
  bool _rebuildScheduled = false;

  void _scheduleRebuild() {
    if (!mounted || _rebuildScheduled) return;
    _rebuildScheduled = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _rebuildScheduled = false;
      if (mounted) setState(() {});
    });
  }

  /// La pantalla [caller] se registra con su callback.
  void register(State caller, Future<void> Function() cb) {
    final wasEmpty = _entries.isEmpty;
    _entries[caller] = cb;
    if (wasEmpty) _scheduleRebuild();
  }

  /// La pantalla [caller] se desregistra (normalmente en dispose).
  void unregister(State caller) {
    final hadOne = _entries.length == 1 && _entries.containsKey(caller);
    _entries.remove(caller);
    if (hadOne) _scheduleRebuild();
  }

  Future<void> Function()? get _activeCallback =>
      _entries.isEmpty ? null : _entries.values.last;

  @override
  Widget build(BuildContext context) {
    final cb = _activeCallback;
    if (cb == null) return widget.child;

    return RefreshIndicator(
      onRefresh: cb,
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

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _register();
  }

  @override
  void dispose() {
    _unregister();
    super.dispose();
  }

  void _register() {
    RefreshScope.of(context)?.register(this, onRefresh);
  }

  void _unregister() {
    // context sigue disponible en dispose para findAncestorStateOfType
    final scope = context.findAncestorStateOfType<RefreshScopeState>();
    scope?.unregister(this);
  }
}
