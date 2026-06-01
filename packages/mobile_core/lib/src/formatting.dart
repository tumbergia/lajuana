/// Formats a numeric string in Colombian pesos format:
/// apostrophe for millions, dot for thousands, comma for decimals.
/// Example: 1'234.567,89 | 500.000,00 | 999,00
String formatColombianPrice(String value) {
  final number = double.tryParse(value.replaceAll(',', '.').replaceAll("'", ''));
  if (number == null) return value;
  final formatted = number.toStringAsFixed(2);
  final dotPos = formatted.indexOf('.');
  final intPart = dotPos >= 0 ? formatted.substring(0, dotPos) : formatted;
  final decPart = dotPos >= 0 ? formatted.substring(dotPos + 1) : '00';

  final groups = <String>[];
  int remaining = intPart.length;
  while (remaining > 0) {
    final chunkSize = remaining >= 3 ? 3 : remaining;
    groups.insert(0, intPart.substring(remaining - chunkSize, remaining));
    remaining -= chunkSize;
  }

  final buffer = StringBuffer();
  for (int i = 0; i < groups.length; i++) {
    if (i > 0) {
      if (groups.length - i == 1) {
        buffer.write('.');
      } else {
        buffer.write("'");
      }
    }
    buffer.write(groups[i]);
  }

  return '\$${buffer.toString()},$decPart';
}
