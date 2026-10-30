part 'phone_countries.dart';

class PhoneCountry {
  const PhoneCountry({
    required this.iso,
    required this.name,
    required this.dialCode,
  });

  final String iso;
  final String name;
  final String dialCode;

  String get flagEmoji {
    final code = iso.toUpperCase();
    if (code.length != 2) return '';
    return String.fromCharCodes(code.runes.map((rune) => rune + 127397));
  }

  String get displayCode => '+$dialCode';
}

class ParsedPhoneNumber {
  const ParsedPhoneNumber({required this.country, required this.localNumber});

  final PhoneCountry country;
  final String localNumber;
}

PhoneCountry get kDefaultPhoneCountry => kPhoneCountries.firstWhere(
  (country) => country.iso == 'CO',
  orElse: () => kPhoneCountries.first,
);

// Sorted once by dial code length (longest first) for prefix matching.
List<PhoneCountry> get kPhoneCountriesByDialCodeLength {
  return [...kPhoneCountries]
    ..sort((a, b) => b.dialCode.length.compareTo(a.dialCode.length));
}

ParsedPhoneNumber parsePhoneNumber(
  String? raw, {
  PhoneCountry? defaultCountry,
}) {
  final fallback = defaultCountry ?? kDefaultPhoneCountry;
  if (raw == null || raw.trim().isEmpty) {
    return ParsedPhoneNumber(country: fallback, localNumber: '');
  }

  final digits = raw.replaceAll(RegExp(r'\D'), '');
  if (digits.isEmpty) {
    return ParsedPhoneNumber(country: fallback, localNumber: '');
  }

  for (final country in kPhoneCountriesByDialCodeLength) {
    if (digits.startsWith(country.dialCode)) {
      return ParsedPhoneNumber(
        country: country,
        localNumber: digits.substring(country.dialCode.length),
      );
    }
  }

  return ParsedPhoneNumber(country: fallback, localNumber: digits);
}

String? buildE164Phone(PhoneCountry country, String localNumber) {
  var localDigits = localNumber.replaceAll(RegExp(r'\D'), '');
  if (localDigits.isEmpty) return null;
  if (localDigits.startsWith(country.dialCode)) {
    localDigits = localDigits.substring(country.dialCode.length);
  }
  if (localDigits.isEmpty) return null;
  return '+${country.dialCode}$localDigits';
}

String formatPhoneForDisplay(String? raw) {
  if (raw == null || raw.trim().isEmpty) return '—';
  final parsed = parsePhoneNumber(raw);
  if (parsed.localNumber.isEmpty) return raw;
  return '${parsed.country.displayCode} ${parsed.localNumber}';
}
