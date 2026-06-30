import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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

  Future<void> _pickCountry() async {
    final picked = await showModalBottomSheet<PhoneCountry>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      builder: (_) => _CountryPickerSheet(selected: _selectedCountry),
    );
    if (picked == null || !mounted) return;
    setState(() {
      _selectedCountry = picked;
    });
    _notifyChanged();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (widget.label.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(
              widget.label.toUpperCase(),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    letterSpacing: 1.2,
                    color: scheme.onSurfaceVariant,
                  ),
            ),
          ),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            InkWell(
              onTap: _pickCountry,
              borderRadius: BorderRadius.circular(4),
              child: Container(
                height: 56,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: scheme.outlineVariant),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      _selectedCountry.flagEmoji,
                      style: const TextStyle(fontSize: 20),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _selectedCountry.displayCode,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                    ),
                    const SizedBox(width: 4),
                    Icon(
                      Icons.expand_more_rounded,
                      size: 18,
                      color: scheme.onSurfaceVariant,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: AppTextField(
                controller: _localCtrl,
                hintText: '300 123 4567',
                keyboardType: TextInputType.phone,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                onChanged: (_) => _notifyChanged(),
              ),
            ),
          ],
        ),
      ],
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
                    leading: Text(
                      country.flagEmoji,
                      style: const TextStyle(fontSize: 24),
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
