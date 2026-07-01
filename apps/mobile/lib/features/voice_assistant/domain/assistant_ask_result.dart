class AssistantAskResult {
  const AssistantAskResult({
    required this.traceId,
    required this.action,
    required this.response,
    this.toolName,
    this.toolOutput = const {},
    this.plannerOutput = const {},
  });

  final String traceId;
  final String action;
  final String? toolName;
  final String response;
  final Map<String, dynamic> toolOutput;
  final Map<String, dynamic> plannerOutput;

  bool get isToolCall => action == 'tool_call';
  bool get isFinalResponse => action == 'final_response';
  bool get isClarifying => action == 'ask_clarifying_question';
  bool get isHandoff => action == 'human_handoff';

  /// Destructive tool pending explicit sí/no confirmation from orchestrator.
  bool get needsConfirmation => isClarifying && (toolName?.isNotEmpty ?? false);

  factory AssistantAskResult.fromJson(Map<String, dynamic> json) {
    return AssistantAskResult(
      traceId: json['trace_id'] as String? ?? '',
      action: json['action'] as String? ?? 'final_response',
      toolName: json['tool_name'] as String?,
      response: json['response'] as String? ?? '',
      toolOutput: _mapOrEmpty(json['tool_output']),
      plannerOutput: _mapOrEmpty(json['planner_output']),
    );
  }

  static Map<String, dynamic> _mapOrEmpty(Object? value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return const {};
  }
}
