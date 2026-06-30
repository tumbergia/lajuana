import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';

String providerTypeLabel(String type) {
  return switch (type) {
    'lodging' => 'Alojamiento',
    'food' => 'Alimentacion',
    'transport_people' => 'Transporte pasajeros',
    'equine_transport' => 'Transporte mulas',
    'experience_ally' => 'Aliado experiencia',
    'guide_ally' => 'Guia aliado',
    'park_or_access' => 'Parque / acceso',
    'insurance' => 'Seguro',
    _ => 'Otro',
  };
}

String reservationProviderStatusLabel(String status) {
  return switch (status) {
    'pending' => 'Pendiente',
    'contacted' => 'Contactado',
    'confirmed' => 'Confirmado',
    'cancelled' => 'Cancelado',
    _ => status,
  };
}

String _formatDate(DateTime? date) {
  if (date == null) return 'Por definir';
  final local = date.toLocal();
  final day = local.day.toString().padLeft(2, '0');
  final month = local.month.toString().padLeft(2, '0');
  return '$day/$month/${local.year}';
}

String buildProviderContactMessage(ReservationProviderItem item) {
  return 'Hola, te escribimos de La Juana para coordinar un servicio asociado a la reserva ${item.reservationCode}.\n\n'
      'Experiencia: ${item.experienceName ?? 'Por definir'}\n'
      'Fecha: ${_formatDate(item.scheduledDate)}\n'
      'Servicio requerido: ${item.serviceLabel ?? 'Por definir'}\n'
      'Participantes: ${item.participantsCount}\n\n'
      'Quedamos atentos para confirmar disponibilidad.';
}

String _whatsappDigits(String? phone) {
  if (phone == null || phone.trim().isEmpty) return '';
  return phone.replaceAll(RegExp(r'\D'), '');
}

/// Barra de acciones del detalle: WhatsApp, correo, editar y quitar en una fila.
class ProviderDetailActionsBar extends StatelessWidget {
  const ProviderDetailActionsBar({
    super.key,
    required this.item,
    required this.isAdmin,
    this.onEdit,
    this.onRemove,
    this.buttonHeight = 52,
  });

  static const Color whatsappGreen = Color(0xFF25D366);
  static const Color gmailRed = Color(0xFFD93025);
  static const String whatsappIconAsset = 'assets/icons/whatsapp.svg';
  static const double _designSlotWidth = 96;
  static const double _minWidthScale = 0.55;

  final ReservationProviderItem item;
  final bool isAdmin;
  final VoidCallback? onEdit;
  final VoidCallback? onRemove;
  final double buttonHeight;

  Future<void> _openWhatsApp() async {
    final digits = _whatsappDigits(item.whatsappPhone);
    if (digits.isEmpty) return;
    final text = Uri.encodeComponent(buildProviderContactMessage(item));
    final uri = Uri.parse('https://wa.me/$digits?text=$text');
    if (!await canLaunchUrl(uri)) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _openEmail() async {
    final email = item.email?.trim();
    if (email == null || email.isEmpty) return;
    final subject = Uri.encodeComponent(
      'Coordinacion reserva ${item.reservationCode}',
    );
    final body = Uri.encodeComponent(buildProviderContactMessage(item));
    final uri = Uri.parse('mailto:$email?subject=$subject&body=$body');
    if (!await canLaunchUrl(uri)) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  @override
  Widget build(BuildContext context) {
    final hasWhatsApp = _whatsappDigits(item.whatsappPhone).isNotEmpty;
    final hasEmail = item.email != null && item.email!.trim().isNotEmpty;
    final buttonCount = (hasEmail ? 1 : 0) +
        (hasWhatsApp ? 1 : 0) +
        (isAdmin ? 2 : 0);

    if (buttonCount == 0) {
      return Text(
        'Sin acciones disponibles',
        textAlign: TextAlign.center,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final widthScale = (constraints.maxWidth /
                (buttonCount * _designSlotWidth + (buttonCount - 1) * 8))
            .clamp(_minWidthScale, 1.0);
        final gap = 8.0 * widthScale;
        final height = buttonHeight * widthScale;
        final brandIconSize = 24.0 * widthScale;
        final cornerRadius = 4.0 * widthScale;
        final scheme = Theme.of(context).colorScheme;

        return Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            if (hasEmail) ...[
              Expanded(
                child: _BrandIconButton(
                  backgroundColor: gmailRed,
                  icon: Icons.mail_rounded,
                  iconSize: brandIconSize,
                  borderRadius: cornerRadius,
                  tooltip: 'Correo',
                  height: height,
                  onPressed: _openEmail,
                ),
              ),
              if (hasWhatsApp || isAdmin) SizedBox(width: gap),
            ],
            if (hasWhatsApp) ...[
              Expanded(
                child: _BrandIconButton(
                  backgroundColor: whatsappGreen,
                  svgAsset: whatsappIconAsset,
                  iconSize: brandIconSize,
                  borderRadius: cornerRadius,
                  tooltip: 'WhatsApp',
                  height: height,
                  onPressed: _openWhatsApp,
                ),
              ),
              if (isAdmin) SizedBox(width: gap),
            ],
            if (isAdmin) ...[
              Expanded(
                child: _BrandIconButton(
                  backgroundColor: scheme.surfaceContainerLow,
                  iconColor: scheme.onSurface,
                  borderSide: BorderSide(
                    color: scheme.outlineVariant.withValues(alpha: 0.5),
                  ),
                  icon: Icons.edit_outlined,
                  iconSize: brandIconSize,
                  borderRadius: cornerRadius,
                  tooltip: 'Editar',
                  height: height,
                  onPressed: onEdit,
                ),
              ),
              SizedBox(width: gap),
              Expanded(
                child: _BrandIconButton(
                  backgroundColor: scheme.surfaceContainerLow,
                  iconColor: scheme.onSurface,
                  borderSide: BorderSide(
                    color: scheme.outlineVariant.withValues(alpha: 0.5),
                  ),
                  icon: Icons.delete_outline_rounded,
                  iconSize: brandIconSize,
                  borderRadius: cornerRadius,
                  tooltip: 'Quitar',
                  height: height,
                  onPressed: onRemove,
                ),
              ),
            ],
          ],
        );
      },
    );
  }
}

class _BrandIconButton extends StatefulWidget {
  const _BrandIconButton({
    required this.backgroundColor,
    required this.tooltip,
    required this.height,
    required this.onPressed,
    this.iconSize = 24,
    this.borderRadius = 4,
    this.iconColor = Colors.white,
    this.borderSide,
    this.svgAsset,
    this.icon,
  }) : assert(svgAsset != null || icon != null);

  final Color backgroundColor;
  final String? svgAsset;
  final IconData? icon;
  final double iconSize;
  final double borderRadius;
  final Color iconColor;
  final BorderSide? borderSide;
  final String tooltip;
  final double height;
  final VoidCallback? onPressed;

  @override
  State<_BrandIconButton> createState() => _BrandIconButtonState();
}

class _BrandIconButtonState extends State<_BrandIconButton> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    final isDisabled = widget.onPressed == null;
    final radius = BorderRadius.circular(widget.borderRadius);
    Widget button = SizedBox(
      height: widget.height,
      width: double.infinity,
      child: Material(
        color: widget.backgroundColor,
        borderRadius: radius,
        child: InkWell(
          borderRadius: radius,
          onTap: widget.onPressed,
          onTapDown: isDisabled ? null : (_) => setState(() => _pressed = true),
          onTapUp: isDisabled ? null : (_) => setState(() => _pressed = false),
          onTapCancel: isDisabled ? null : () => setState(() => _pressed = false),
          splashColor: widget.iconColor.withValues(alpha: 0.12),
          highlightColor: widget.iconColor.withValues(alpha: 0.06),
          child: Center(
            child: widget.icon != null
                ? Icon(
                    widget.icon,
                    color: widget.iconColor.withValues(
                      alpha: isDisabled ? 0.38 : 1,
                    ),
                    size: widget.iconSize,
                  )
                : SvgPicture.asset(
                    widget.svgAsset!,
                    width: widget.iconSize,
                    height: widget.iconSize,
                    colorFilter: isDisabled
                        ? ColorFilter.mode(
                            widget.iconColor.withValues(alpha: 0.38),
                            BlendMode.srcIn,
                          )
                        : null,
                  ),
          ),
        ),
      ),
    );

    if (widget.borderSide != null) {
      button = DecoratedBox(
        decoration: BoxDecoration(
          borderRadius: radius,
          border: Border.fromBorderSide(widget.borderSide!),
        ),
        child: button,
      );
    }

    return Tooltip(
      message: widget.tooltip,
      child: AnimatedScale(
        scale: (_pressed && !isDisabled) ? 0.96 : 1,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,
        child: button,
      ),
    );
  }
}
