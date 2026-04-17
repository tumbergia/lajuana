import 'package:flutter/material.dart';

class LaJuanaApp extends StatelessWidget {
  const LaJuanaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'La Juana',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.brown,
        useMaterial3: true,
      ),
      home: const Scaffold(
        body: Center(
          child: Text('La Juana'),
        ),
      ),
    );
  }
}
