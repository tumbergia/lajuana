import 'package:country_flags/country_flags.dart';
import 'package:flutter/material.dart';

import 'package:mobile_ui/src/input/app_input_formatters.dart';
import 'package:mobile_ui/src/theme/theme_extensions.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile/features/providers/presentation/utils/phone_country.dart';

class ProviderPhoneField extends StatefulWidget {
  const ProviderPhoneField({
    super.key,
    this.initialPhone,
    this.label = 'Telefono / WhatsApp',
    this.onChanged,
  });

  final String? initialPhone;
  final String label;
  final ValueChanged<String?>? onChanged;

  @override
  State<ProviderPhoneField> createState() => ProviderPhoneFieldState();
}

class ProviderPhoneFieldState extends State<ProviderPhoneField> {
  late PhoneCountry _selectedCountry;
  late final TextEditingController _localCtrl;

  @override
  void initState() {
    super.initState();
    final parsed = parsePhoneNumber(widget.initialPhone);
    _selectedCountry = parsed.country;
    _localCtrl = TextEditingController(text: parsed.localNumber);
  }

  @override
  void dispose() {
    _localCtrl.dispose();
    super.dispose();
  }

  String? get e164Phone => buildE164Phone(_selectedCountry, _localCtrl.text);

  void _notifyChanged() {
    widget.onChanged?.call(e164Phone);
  }

  void _applyCountry(PhoneCountry picked) {
    final normalized = parsePhoneNumber(
      buildE164Phone(_selectedCountry, _localCtrl.text) ?? _localCtrl.text,
      defaultCountry: picked,
    );
    setState(() {
      _selectedCountry = picked;
    });
    if (_localCtrl.text != normalized.localNumber) {
      _localCtrl.text = normalized.localNumber;
    }
    _notifyChanged();
  }

  Future<void> _pickCountry() async {
    final picked = await showModalBottomSheet<PhoneCountry>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _CountryPickerSheet(selected: _selectedCountry),
    );
    if (picked == null || !mounted) return;
    _applyCountry(picked);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final tokens = theme.appTokens;

    final outlineBorder = OutlineInputBorder(
      borderRadius: tokens.radiusMd,
      borderSide: BorderSide(color: scheme.outlineVariant),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              widget.label.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                letterSpacing: 1.2,
                color: scheme.onSurfaceVariant,
              ),
            ),
          ),
        TextField(
          controller: _localCtrl,
          keyboardType: TextInputType.phone,
          inputFormatters: AppInputFormatters.phone,
          onChanged: (_) => _notifyChanged(),
          style: theme.textTheme.bodyMedium?.copyWith(color: scheme.onSurface),
          decoration: InputDecoration(
            hintText: '300 123 4567',
            isDense: true,
            filled: true,
            fillColor: scheme.surfaceContainerLow,
            contentPadding: EdgeInsets.symmetric(
              horizontal: tokens.spaceLg,
              vertical: 14,
            ),
            enabledBorder: outlineBorder,
            focusedBorder: outlineBorder.copyWith(
              borderSide: BorderSide(color: scheme.primary, width: 1.2),
            ),
            border: outlineBorder,
            prefixIconConstraints: const BoxConstraints(minWidth: 0, minHeight: 0),
            prefixIcon: _CountryPrefix(
              country: _selectedCountry,
              onTap: _pickCountry,
            ),
          ),
        ),
      ],
    );
  }
}

class _CountryPrefix extends StatelessWidget {
  const _CountryPrefix({
    required this.country,
    required this.onTap,
  });

  final PhoneCountry country;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;

    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.only(left: 12, right: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(3),
              child: CountryFlag.fromCountryCode(
                country.iso,
                width: 22,
                height: 16,
              ),
            ),
            const SizedBox(width: 6),
            Text(
              country.displayCode,
              style: theme.textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            Icon(
              Icons.expand_more_rounded,
              size: 18,
              color: scheme.onSurfaceVariant,
            ),
            Container(
              width: 1,
              height: 24,
              margin: const EdgeInsets.only(left: 8),
              color: scheme.outlineVariant,
            ),
          ],
        ),
      ),
    );
  }
}

class _CountryPickerSheet extends StatefulWidget {
  const _CountryPickerSheet({required this.selected});

  final PhoneCountry selected;

  @override
  State<_CountryPickerSheet> createState() => _CountryPickerSheetState();
}

class _CountryPickerSheetState extends State<_CountryPickerSheet> {
  final TextEditingController _searchCtrl = TextEditingController();
  late List<PhoneCountry> _filtered;

  @override
  void initState() {
    super.initState();
    _filtered = kPhoneCountries;
    _searchCtrl.addListener(_applyFilter);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _applyFilter() {
    final q = _searchCtrl.text.trim().toLowerCase();
    setState(() {
      if (q.isEmpty) {
        _filtered = kPhoneCountries;
        return;
      }
      _filtered = kPhoneCountries
          .where(
            (country) =>
                country.name.toLowerCase().contains(q) ||
                country.iso.toLowerCase().contains(q) ||
                country.dialCode.contains(q.replaceAll('+', '')),
          )
          .toList(growable: false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final maxHeight = MediaQuery.sizeOf(context).height * 0.75;

    return Padding(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SizedBox(
        height: maxHeight,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: scheme.onSurfaceVariant.withValues(alpha: 0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Seleccionar pais',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            AppTextField(
              controller: _searchCtrl,
              hintText: 'Buscar pais o codigo...',
              suffix: const Icon(Icons.search_rounded, size: 20),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.separated(
                itemCount: _filtered.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (context, index) {
                  final country = _filtered[index];
                  final selected = country.iso == widget.selected.iso;
                  return ListTile(
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: CountryFlag.fromCountryCode(
                        country.iso,
                        width: 28,
                        height: 20,
                      ),
                    ),
                    title: Text(country.name),
                    trailing: Text(
                      country.displayCode,
                      style: TextStyle(
                        fontWeight:
                            selected ? FontWeight.w700 : FontWeight.w500,
                        color: selected ? scheme.primary : scheme.onSurface,
                      ),
                    ),
                    selected: selected,
                    onTap: () => Navigator.of(context).pop(country),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
