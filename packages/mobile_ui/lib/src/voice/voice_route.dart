import 'package:flutter/material.dart';
import 'voice_context.dart';
import 'voice_screen.dart';

const String voiceRouteName = '/voice';

void closeAllVoiceScreens(BuildContext context) {
  Navigator.of(
    context,
  ).popUntil((route) => route.settings.name != voiceRouteName);
}

MaterialPageRoute<void> _buildVoiceRoute(VoiceContext voiceContext) {
  return MaterialPageRoute<void>(
    settings: const RouteSettings(name: voiceRouteName),
    builder: (_) => VoiceScreen(voiceContext: voiceContext),
  );
}

Future<void> openVoiceScreen(
  BuildContext context, {
  required VoiceContext voiceContext,
}) {
  final currentRouteName = ModalRoute.of(context)?.settings.name;
  if (currentRouteName == voiceRouteName) {
    return Navigator.of(
      context,
    ).pushReplacement(_buildVoiceRoute(voiceContext));
  }

  return Navigator.of(context).push(_buildVoiceRoute(voiceContext));
}
