import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/theme_extensions.dart';

/// Scaffold base de la app. Absorbe el patrón visual del mockup:
/// fondo dark, app bar minimal con eyebrow + título Manrope,
/// safe area correcta y padding editorial consistente.
class AppScaffold extends StatelessWidget {
  final Widget child;

  /// Supertítulo en mayúsculas (ej: "Operational Module")
  final String? eyebrow;

  /// Título principal en Manrope extrabold (ej: "RESERVATIONS")
  final String? title;

  /// Widget leading en la app bar (ej: back button, logo)
  final Widget? leading;

  /// Acciones en la app bar (ej: avatar, notificaciones)
  final List<Widget>? actions;

  /// Bottom nav bar persistente
  final Widget? bottomNavigationBar;

  /// FAB opcional
  final Widget? floatingActionButton;

  /// Si true, envuelve el child en SingleChildScrollView
  final bool scrollable;

  /// Padding interno del body. Por defecto: 16 laterales, 16 arriba, 48 abajo.
  final EdgeInsetsGeometry? padding;

  const AppScaffold({
    super.key,
    required this.child,
    this.eyebrow,
    this.title,
    this.leading,
    this.actions,
    this.bottomNavigationBar,
    this.floatingActionButton,
    this.scrollable = true,
    this.padding,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tokens = theme.appTokens;
    final scheme = theme.colorScheme;

    final hasAppBar = title != null ||
        eyebrow != null ||
        leading != null ||
        (actions != null && actions!.isNotEmpty);

    final body = Padding(
      padding: padding ??
          EdgeInsets.fromLTRB(
            tokens.spaceLg,
            tokens.spaceLg,
            tokens.spaceLg,
            tokens.spaceXl * 2,
          ),
      child: child,
    );

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: theme.brightness == Brightness.dark
          ? SystemUiOverlayStyle.light
          : SystemUiOverlayStyle.dark,
      child: Scaffold(
        backgroundColor: scheme.surface,
        appBar: hasAppBar
            ? AppBar(
                backgroundColor: scheme.surface,
                elevation: 0,
                scrolledUnderElevation: 0,
                leading: leading,
                automaticallyImplyLeading: leading == null,
                actions: actions,
                toolbarHeight: 64,
                titleSpacing: leading != null ? 0 : tokens.spaceLg,
                title: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    if (eyebrow != null)
                      Text(
                        eyebrow!.toUpperCase(),
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: scheme.onSurfaceVariant,
                          letterSpacing: 1.8,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    if (title != null)
                      Text(
                        title!.toUpperCase(),
                        style: theme.textTheme.headlineLarge?.copyWith(
                          fontFamily: 'Manrope',
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.5,
                          height: 1.1,
                        ),
                      ),
                  ],
                ),
              )
            : null,
        bottomNavigationBar: bottomNavigationBar,
        floatingActionButton: floatingActionButton,
        body: SafeArea(
          top: false,
          child: scrollable
              ? SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  child: body,
                )
              : body,
        ),
      ),
    );
  }
}
