import 'package:flutter/material.dart';

import '../../../home/home_page.dart';
import '../auth_controller.dart';
import '../auth_routes.dart';

class AuthenticatedHomeScreen extends StatelessWidget {
  const AuthenticatedHomeScreen({super.key, required this.controller});

  final AuthController controller;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        const HomePage(),
        Positioned(
          right: 16,
          bottom: 24,
          child: FloatingActionButton.small(
            onPressed: () {
              Navigator.of(context).pushNamed(AuthRoutes.sessionView);
            },
            child: const Icon(Icons.verified_user_outlined),
          ),
        ),
      ],
    );
  }
}
