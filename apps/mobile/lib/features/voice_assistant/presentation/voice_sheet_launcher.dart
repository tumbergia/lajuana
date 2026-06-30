import 'package:flutter/material.dart';

import 'controllers/voice_assistant_controller.dart';
import 'navigation/voice_assistant_navigation.dart';
import 'widgets/admin_voice_sheet.dart';

Future<void> openAdminVoiceSheet(
  BuildContext context, {
  required VoiceAssistantController controller,
  required VoiceAssistantNavigation navigation,
}) {
  final hostContext = context;
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    useRootNavigator: true,
    showDragHandle: true,
    backgroundColor: Theme.of(context).colorScheme.surface,
    builder: (sheetContext) {
      return AdminVoiceSheet(
        controller: controller,
        hostContext: hostContext,
        navigation: navigation,
        onClose: () => Navigator.of(sheetContext).pop(),
      );
    },
  );
}
