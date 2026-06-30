// ignore_for_file: public_member_api_docs, constant_identifier_names
// GENERATED CODE -- DO NOT EDIT MANUALLY
// Generated from OpenAPI spec

import 'package:json_annotation/json_annotation.dart';

/// AUTO-GENERATED from OpenAPI schema `AssistantAction`.

enum AssistantAction {
  @JsonValue('final_response')
  FINAL_RESPONSE("final_response"),
  @JsonValue('tool_call')
  TOOL_CALL("tool_call"),
  @JsonValue('ask_clarifying_question')
  ASK_CLARIFYING_QUESTION("ask_clarifying_question"),
  @JsonValue('human_handoff')
  HUMAN_HANDOFF("human_handoff"),
;

  final String value;
  const AssistantAction(this.value);
}

extension AssistantActionX on AssistantAction {
  String toJson() => value;
}

extension AssistantActionParse on String {
  AssistantAction toAssistantAction() => AssistantAction.values.firstWhere(
    (e) => e.value == this,
    orElse: () => throw ArgumentError('Unknown AssistantAction: ${this}'),
  );
}

