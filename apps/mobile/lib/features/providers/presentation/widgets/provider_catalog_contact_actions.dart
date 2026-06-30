import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';

class ProviderCatalogContactActions extends StatelessWidget {
  const ProviderCatalogContactActions({
    super.key,
    required this.email,
    required this.whatsappPhone,
  });

  final String? email;
  final String? whatsappPhone;

  String _whatsappDigits(String? phone) {
    if (phone == null || phone.trim().isEmpty) return '';
    return phone.replaceAll(RegExp(r'\D'), '');
  }

  Future<void> _openWhatsApp() async {
    final digits = _whatsappDigits(whatsappPhone);
    if (digits.isEmpty) return;
    final uri = Uri.parse('https://wa.me/$digits');
    if (!await canLaunchUrl(uri)) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _openEmail() async {
    final value = email?.trim();
    if (value == null || value.isEmpty) return;
    final uri = Uri.parse('mailto:$value');
    if (!await canLaunchUrl(uri)) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    final hasWhatsApp = _whatsappDigits(whatsappPhone).isNotEmpty;
    final hasEmail = email != null && email!.trim().isNotEmpty;
    if (!hasWhatsApp && !hasEmail) return const SizedBox.shrink();

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        if (hasWhatsApp)
          AppButton(
            label: 'WhatsApp',
            icon: Icons.chat_rounded,
            variant: AppButtonVariant.secondary,
            onPressed: _openWhatsApp,
          ),
        if (hasEmail)
          AppButton(
            label: 'Correo',
            icon: Icons.email_outlined,
            variant: AppButtonVariant.secondary,
            onPressed: _openEmail,
          ),
      ],
    );
  }
}
