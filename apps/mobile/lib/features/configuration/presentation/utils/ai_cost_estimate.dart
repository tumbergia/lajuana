import 'package:mobile/features/configuration/domain/ai_model_catalog.dart';
import 'package:mobile_core/mobile_core.dart';

/// Presets rápidos de carga (aplican valores a [AiLoadConfig]).
enum AiLoadPreset {
  low(label: 'Baja', people: 50, messagesPerPersonPerDay: 10),
  high(label: 'Alta', people: 100, messagesPerPersonPerDay: 10),
  max(label: 'Máxima', people: 150, messagesPerPersonPerDay: 10);

  const AiLoadPreset({
    required this.label,
    required this.people,
    required this.messagesPerPersonPerDay,
  });

  final String label;
  final int people;
  final int messagesPerPersonPerDay;
}

/// Carga configurable para el estimado mensual.
///
/// msgs/mes = personas × msgs/día × días/mes.
class AiLoadConfig {
  const AiLoadConfig({
    required this.people,
    required this.messagesPerPersonPerDay,
    this.daysPerMonth = 30,
  });

  final int people;
  final int messagesPerPersonPerDay;
  final int daysPerMonth;

  factory AiLoadConfig.fromPreset(AiLoadPreset preset) => AiLoadConfig(
    people: preset.people,
    messagesPerPersonPerDay: preset.messagesPerPersonPerDay,
  );

  static const AiLoadConfig defaults = AiLoadConfig(
    people: 150,
    messagesPerPersonPerDay: 10,
  );

  int get messagesPerMonth =>
      people * messagesPerPersonPerDay * daysPerMonth;

  String get summaryLabel =>
      '$people pers · $messagesPerPersonPerDay/día · $messagesPerMonth msgs/mes';

  AiLoadPreset? matchingPreset() {
    for (final preset in AiLoadPreset.values) {
      if (people == preset.people &&
          messagesPerPersonPerDay == preset.messagesPerPersonPerDay &&
          daysPerMonth == 30) {
        return preset;
      }
    }
    return null;
  }

  AiLoadConfig copyWith({
    int? people,
    int? messagesPerPersonPerDay,
    int? daysPerMonth,
  }) => AiLoadConfig(
    people: people ?? this.people,
    messagesPerPersonPerDay:
        messagesPerPersonPerDay ?? this.messagesPerPersonPerDay,
    daysPerMonth: daysPerMonth ?? this.daysPerMonth,
  );
}

/// Constantes configurables para el estimado informativo (no facturación).
abstract final class AiCostEstimate {
  /// Tasa USD → COP aproximada (editable aquí; se puede mover a config servidor).
  static const double usdToCop = 4000;

  /// Tokens estimados por mensaje del chatbot público (~3000 total).
  /// La telemetría real es mayoritariamente prompt; completion es corto.
  static const int inputTokensPerMessage = 2750;
  static const int outputTokensPerMessage = 250;
  static const int tokensPerMessage =
      inputTokensPerMessage + outputTokensPerMessage;

  /// Costo USD de un mensaje dado precios por millón de tokens.
  static double? usdPerMessage(AiModelItem item) {
    final input = double.tryParse(item.inputUsdPerMillion ?? '');
    final output = double.tryParse(item.outputUsdPerMillion ?? '');
    if (input == null && output == null) return null;
    final inCost = ((input ?? 0) / 1e6) * inputTokensPerMessage;
    final outCost = ((output ?? 0) / 1e6) * outputTokensPerMessage;
    return inCost + outCost;
  }

  /// Costo mensual estimado en COP para una carga configurable.
  static double? monthlyCop(AiModelItem item, AiLoadConfig load) {
    final perMsg = usdPerMessage(item);
    if (perMsg == null) return null;
    return perMsg * usdToCop * load.messagesPerMonth;
  }

  /// Formato COP colombiano (\$1.234,56).
  static String formatCop(double value) =>
      formatColombianPrice(value.toStringAsFixed(2));

  /// Formato USD compacto (\$0.12 / \$1.234).
  static String formatUsd(double value) {
    if (value >= 100) return '\$${value.toStringAsFixed(0)}';
    if (value >= 1) return '\$${value.toStringAsFixed(2)}';
    if (value >= 0.01) return '\$${value.toStringAsFixed(3)}';
    return '\$${value.toStringAsFixed(5)}';
  }

  static String formatUsdPerMillion(String? raw) {
    if (raw == null || raw.isEmpty) return '—';
    final value = double.tryParse(raw);
    if (value == null) return '—';
    if (value >= 1) return '\$${value.toStringAsFixed(2)}';
    if (value >= 0.01) return '\$${value.toStringAsFixed(3)}';
    return '\$${value.toStringAsFixed(4)}';
  }
}
