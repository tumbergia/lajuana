import 'package:flutter/material.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';

/// Select field aligned with [AppTextField]: external uppercase label and
/// token-based filled/underlined borders (no floating Material label).
class AppSelectField<T> extends StatelessWidget {
  const AppSelectField({
    super.key,
    required this.items,
    this.value,
    this.label,
    this.hintText,
    this.onChanged,
    this.variant = AppTextFieldVariant.filled,
  });

  final T? value;
  final String? label;
  final String? hintText;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?>? onChanged;
  final AppTextFieldVariant variant;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    InputBorder underline(Color color, [double width = 1.0]) =>
        UnderlineInputBorder(
          borderSide: BorderSide(color: color, width: width),
        );

    InputBorder outline(Color color, [double width = 1.0]) =>
        OutlineInputBorder(
          borderRadius: tokens.radiusMd,
          borderSide: BorderSide(color: color, width: width),
        );

    final (enabledBorder, focusedBorder, baseBorder) = switch (variant) {
      AppTextFieldVariant.underlined => (
        underline(scheme.outlineVariant),
        underline(scheme.primary, 1.4),
        underline(scheme.outlineVariant),
      ),
      AppTextFieldVariant.filled => (
        outline(scheme.outlineVariant),
        outline(scheme.primary, 1.2),
        outline(scheme.outlineVariant),
      ),
    };

    final contentPadding = switch (variant) {
      AppTextFieldVariant.underlined => const EdgeInsets.symmetric(
        vertical: 12,
      ),
      AppTextFieldVariant.filled => EdgeInsets.symmetric(
        horizontal: tokens.spaceLg,
        vertical: 4,
      ),
    };

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        if (label != null) ...[
          Text(
            label!.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: scheme.onSurfaceVariant,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.8,
            ),
          ),
          SizedBox(height: tokens.spaceSm),
        ],
        DropdownButtonFormField<T>(
          initialValue: value,
          items: items,
          onChanged: onChanged,
          isExpanded: true,
          icon: Icon(
            Icons.keyboard_arrow_down_rounded,
            color: scheme.onSurfaceVariant,
          ),
          style: theme.textTheme.bodyMedium?.copyWith(color: scheme.onSurface),
          dropdownColor: scheme.surfaceContainerHigh,
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: theme.textTheme.bodyMedium?.copyWith(
              color: scheme.onSurfaceVariant,
            ),
            isDense: true,
            filled: variant == AppTextFieldVariant.filled,
            fillColor: variant == AppTextFieldVariant.filled
                ? scheme.surfaceContainerLow
                : null,
            contentPadding: contentPadding,
            enabledBorder: enabledBorder,
            focusedBorder: focusedBorder,
            border: baseBorder,
            labelText: null,
          ),
        ),
      ],
    );
  }
}
