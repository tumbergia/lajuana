import 'package:flutter/services.dart';
import 'package:mobile_ui/src/input/app_input_formatters.dart';

/// Semantic input kinds that map to keyboard + formatters without styling changes.
enum AppTextInputKind {
  text,
  email,
  password,
  phone,
  url,
  integer,
  decimal,
  search,
}

extension AppTextInputKindResolution on AppTextInputKind {
  TextInputType? get keyboardType => switch (this) {
    AppTextInputKind.text => TextInputType.text,
    AppTextInputKind.email => TextInputType.emailAddress,
    AppTextInputKind.password => TextInputType.visiblePassword,
    AppTextInputKind.phone => TextInputType.phone,
    AppTextInputKind.url => TextInputType.url,
    AppTextInputKind.integer => TextInputType.number,
    AppTextInputKind.decimal =>
      const TextInputType.numberWithOptions(decimal: true),
    AppTextInputKind.search => TextInputType.text,
  };

  List<TextInputFormatter>? get inputFormatters => switch (this) {
    AppTextInputKind.integer => AppInputFormatters.integer,
    AppTextInputKind.decimal => AppInputFormatters.decimal,
    AppTextInputKind.phone => AppInputFormatters.phone,
    AppTextInputKind.text ||
    AppTextInputKind.email ||
    AppTextInputKind.password ||
    AppTextInputKind.url ||
    AppTextInputKind.search => null,
  };
}
