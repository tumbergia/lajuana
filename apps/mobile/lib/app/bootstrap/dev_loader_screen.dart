import 'package:flutter/material.dart';

class DevLoaderScreen extends StatelessWidget {
  const DevLoaderScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator(strokeWidth: 2.8)),
    );
  }
}
