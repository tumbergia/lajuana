import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';

class AppScaffold extends StatelessWidget {
  final Widget child;
  final PreferredSizeWidget? appBar;
  final Widget? bottomNavigationBar;
  final FloatingActionButton? floatingActionButton;
  final bool scrollable;
  final EdgeInsetsGeometry? padding;
  final Color? backgroundColor;

  /// Evita que el [Scaffold] redimensione el cuerpo al abrir el teclado.
  /// Útil con formularios donde `adjustResize` / insets disparan cierre del IME.
  final bool resizeToAvoidBottomInset;

  const AppScaffold({
    super.key,
    required this.child,
    this.appBar,
    this.bottomNavigationBar,
    this.floatingActionButton,
    this.scrollable = true,
    this.padding,
    this.backgroundColor,
    this.resizeToAvoidBottomInset = true,
  });

  @override
  Widget build(BuildContext context) {
    final tokens = Theme.of(context).appTokens;
    final content = Padding(
      padding: padding ??
          EdgeInsets.fromLTRB(
            tokens.spaceLg,
            tokens.spaceLg,
            tokens.spaceLg,
            tokens.spaceXl + tokens.spaceSm,
          ),
      child: child,
    );

    return Scaffold(
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: backgroundColor ?? Theme.of(context).colorScheme.surface,
      appBar: appBar,
      bottomNavigationBar: bottomNavigationBar,
      floatingActionButton: floatingActionButton,
      body: SafeArea(
        top: false,
        child: scrollable ? SingleChildScrollView(child: content) : content,
      ),
    );
  }
}
