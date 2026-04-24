import 'package:flutter/material.dart';

class AppCenteredLoader extends StatelessWidget {
  const AppCenteredLoader({super.key, this.strokeWidth = 2.8});

  final double strokeWidth;

  @override
  Widget build(BuildContext context) {
    return Center(child: CircularProgressIndicator(strokeWidth: strokeWidth));
  }
}
