import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/reservations/reservation_participant_detail.dart';

/// Full-screen participant detail view.
///
/// Shows all fields grouped by category: personal info, physical, health,
/// dietary restrictions, emergency contact, and consentements.
class ParticipantDetailView extends StatefulWidget {
  const ParticipantDetailView({super.key, required this.participant});

  final ReservationParticipantDetail participant;

  @override
  State<ParticipantDetailView> createState() => _ParticipantDetailViewState();
}

class _ParticipantDetailViewState extends State<ParticipantDetailView>
    with RefreshableState {
  @override
  Future<void> onRefresh() async {}

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final p = widget.participant;

    return Scaffold(
      appBar: AppBar(
        title: Text(p.fullName),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 12),
              child: AppBadge(
                label: p.isCompleted ? 'Completo' : 'Incompleto',
                tone: p.isCompleted
                    ? AppBadgeTone.success
                    : AppBadgeTone.warning,
                uppercase: false,
              ),
            ),
          ),
        ],
      ),
      body: RefreshableViewport(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _sectionHeader(context, 'INFORMACION PERSONAL'),
            _fieldRow(context, 'Nombre', p.firstName),
            _fieldRow(context, 'Apellido', p.lastName),
            _fieldRow(
              context,
              'Nacimiento',
              p.birthDate != null
                  ? '${p.birthDate}${p.ageYears != null ? ' (${p.ageYears} años)' : ''}'
                  : null,
            ),
            _fieldRow(context, 'Documento', _docLabel(p)),
            _fieldRow(context, 'Teléfono', p.phone),
            _fieldRow(context, 'País', p.country),
            _fieldRow(context, 'Ciudad', p.city),
            const SizedBox(height: 16),
            _sectionHeader(context, 'FISICO'),
            _fieldRow(
              context,
              'Altura',
              p.heightCm != null ? '${p.heightCm} cm' : null,
            ),
            _fieldRow(
              context,
              'Peso',
              p.weightKg != null ? '${p.weightKg} kg' : null,
            ),
            _fieldRow(context, 'Experiencia', _expLabel(p.experienceLevel)),
            const SizedBox(height: 16),
            _sectionHeader(
              context,
              'SALUD',
              alertTone: p.hasMedicalAlert ? AppBadgeTone.danger : null,
            ),
            if (p.hasMedicalAlert)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: AppStatusBanner(
                  title: 'Alerta médica',
                  message:
                      p.healthConditions ?? p.sensoryDisabilities ?? '\u2014',
                  tone: AppStatusBannerTone.danger,
                  icon: Icons.medical_services_outlined,
                ),
              ),
            _fieldRow(context, 'Tipo sangre', p.bloodType),
            _fieldRow(context, 'EPS / Seguro', p.epsOrTravelInsurance),
            _fieldRow(context, 'Condiciones', p.healthConditions),
            _fieldRow(context, 'Discapacidad', p.sensoryDisabilities),
            const SizedBox(height: 16),
            _sectionHeader(context, 'ALIMENTACION'),
            if (p.hasFoodRestriction)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: AppStatusBanner(
                  title: 'Restricción alimentaria',
                  message: p.dietaryRestrictions ?? '\u2014',
                  tone: AppStatusBannerTone.warning,
                  icon: Icons.restaurant_outlined,
                ),
              ),
            _fieldRow(context, 'Restricciones', p.dietaryRestrictions),
            const SizedBox(height: 16),
            _sectionHeader(context, 'CONTACTO DE EMERGENCIA'),
            _fieldRow(context, 'Nombre', p.emergencyContactName),
            _fieldRow(context, 'Teléfono', p.emergencyContactPhone),
            _fieldRow(context, 'Relación', p.emergencyContactRelationship),
            const SizedBox(height: 16),
            _sectionHeader(context, 'CONSENTIMIENTOS'),
            _boolRow(context, 'Tratamiento de datos', p.acceptedDataProcessing),
            _boolRow(context, 'Fotos / Video', p.photoVideoConsent),
            _boolRow(context, 'Liberación de riesgo', p.acceptedRiskRelease),
          ],
        ),
      ),
    );
  }

  Widget _sectionHeader(
    BuildContext context,
    String title, {
    AppBadgeTone? alertTone,
  }) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Text(
            title,
            style: theme.textTheme.labelLarge?.copyWith(
              fontWeight: FontWeight.w800,
              letterSpacing: 0.8,
              color: alertTone != null
                  ? appBadgeToneColors(context, alertTone).foreground
                  : theme.colorScheme.primary,
            ),
          ),
          if (alertTone != null) ...[
            const SizedBox(width: 8),
            Icon(
              Icons.warning_amber_rounded,
              size: 16,
              color: appBadgeToneColors(context, alertTone).foreground,
            ),
          ],
        ],
      ),
    );
  }

  Widget _fieldRow(BuildContext context, String label, String? value) {
    final theme = Theme.of(context);
    final hasValue = value != null && value.isNotEmpty && value != '\u2014';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Expanded(
            child: Text(
              hasValue ? value : '\u2014',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: hasValue
                    ? theme.colorScheme.onSurface
                    : theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _boolRow(BuildContext context, String label, bool? value) {
    final theme = Theme.of(context);
    final ok = value == true;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          SizedBox(
            width: 160,
            child: Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          Icon(
            ok ? Icons.check_circle_rounded : Icons.cancel_outlined,
            size: 20,
            color: ok ? theme.colorScheme.primary : theme.colorScheme.error,
          ),
          const SizedBox(width: 6),
          Text(
            ok ? 'Aceptado' : 'No aceptado',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: ok ? theme.colorScheme.primary : theme.colorScheme.error,
            ),
          ),
        ],
      ),
    );
  }

  String _docLabel(ReservationParticipantDetail p) {
    if (p.documentType == null && p.documentNumber == null) return '\u2014';
    final parts = <String>[];
    if (p.documentType != null) parts.add(p.documentType!.toUpperCase());
    if (p.documentNumber != null) parts.add(p.documentNumber!);
    return parts.join(' · ');
  }

  String _expLabel(String? level) {
    if (level == null) return '\u2014';
    switch (level.toLowerCase()) {
      case 'basic':
        return 'Básico';
      case 'intermediate':
        return 'Intermedio';
      case 'advanced':
        return 'Avanzado';
      default:
        return level;
    }
  }
}
