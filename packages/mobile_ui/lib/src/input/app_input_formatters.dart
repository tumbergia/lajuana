import 'package:flutter/services.dart';

/// Shared input formatters for typed [AppTextField] kinds.
abstract final class AppInputFormatters {
  static final List<TextInputFormatter> integer = [
    FilteringTextInputFormatter.digitsOnly,
  ];

  static final List<TextInputFormatter> decimal = [
    FilteringTextInputFormatter.allow(RegExp(r'^\d*[,.]?\d*')),
  ];

  static final List<TextInputFormatter> phone = [
    FilteringTextInputFormatter.digitsOnly,
  ];
}
