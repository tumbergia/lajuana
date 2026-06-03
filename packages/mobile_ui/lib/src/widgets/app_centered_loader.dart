import 'package:flutter/material.dart';

/// Loader con [CircularProgressIndicator] centrado horizontal y verticalmente.
///
/// Centra usando [Center], que funciona correctamente en contextos con
/// altura acotada ([Expanded], [SliverFillRemaining], scaffold body).
///
/// Para contextos scrollables ([SingleChildScrollView]) donde [Center] no
/// puede expandirse, ajustar `scrollable` del contenedor padre a `false`
/// cuando el loader es el contenido principal.
///
/// El parámetro [fill] se conserva para compatibilidad de API; el widget
/// siempre usa [Center] internamente.
class AppCenteredLoader extends StatelessWidget {
  const AppCenteredLoader({
    super.key,
    this.strokeWidth = 2.8,
    // ignore: unused_element_parameter
    this.fill = true,
  });

  final double strokeWidth;
  final bool fill;

  @override
  Widget build(BuildContext context) {
    return Center(child: CircularProgressIndicator(strokeWidth: strokeWidth));
  }
}
