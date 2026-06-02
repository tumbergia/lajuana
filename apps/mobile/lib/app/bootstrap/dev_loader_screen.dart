import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_badge.dart';
import 'package:mobile_ui/src/widgets/app_bottom_nav.dart';
import 'package:mobile_ui/src/widgets/app_breadcrumb.dart';
import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_card.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_entity_row_card.dart';
import 'package:mobile_ui/src/widgets/app_metric_card.dart';
import 'package:mobile_ui/src/widgets/app_scaffold.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_timeline.dart';
import 'package:mobile_ui/src/widgets/app_top_bar.dart';
import 'package:mobile_ui/src/widgets/app_voice_fab.dart';
import 'package:mobile_ui/src/widgets/cards/app_assignment_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_centered_badge_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_experience_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_image_feature_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_logbook_timeline.dart';
import 'package:mobile_ui/src/widgets/cards/app_pricing_tiers_table.dart';
import 'package:mobile_ui/src/widgets/cards/app_selectable_card.dart';
import 'package:mobile_ui/src/widgets/cards/app_stats_card.dart';

class DevWidgetCatalogScreen extends StatefulWidget {
  const DevWidgetCatalogScreen({super.key});

  @override
  State<DevWidgetCatalogScreen> createState() => _DevWidgetCatalogScreenState();
}

class _DevWidgetCatalogScreenState extends State<DevWidgetCatalogScreen> {
  String reservationFilter = 'pendientes';
  bool useMicOffIcon = false;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      appBar: const AppTopBar(
        logoAssetPath: 'assets/branding/lajuana.svg',
        title: 'LA JUANA',
      ),
      bottomNavigationBar: AppBottomNav(
        current: AppNavItem.inicio,
        onTap: (_) {},
      ),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const AppSectionHeader(eyebrow: 'Dev', title: 'Catalogo de Widgets'),
          const SizedBox(height: 16),
          const AppBreadcrumb(items: ['Diseno', 'Sistema UI', 'Widgets']),
          const SizedBox(height: 24),
          AppSectionHeader(
            eyebrow: 'Acciones',
            title: 'Botones',
            variant: AppSectionHeaderVariant.compact,
            trailing: AppButton(
              label: 'Crear',
              icon: Icons.add,
              onPressed: () {},
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              AppButton(label: 'Primario', onPressed: () {}, icon: Icons.check),
              AppButton(
                label: 'Secundario',
                onPressed: () {},
                icon: Icons.group,
                variant: AppButtonVariant.secondary,
              ),
              AppButton(
                label: 'Ghost',
                onPressed: () {},
                icon: Icons.edit,
                variant: AppButtonVariant.ghost,
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Estados',
            title: 'Badges y Banners',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          const Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              AppBadge(label: 'Pendiente', tone: AppBadgeTone.neutral),
              AppBadge(label: 'Activo', tone: AppBadgeTone.primary),
              AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
              AppBadge(label: 'Alto riesgo', tone: AppBadgeTone.danger),
              AppBadge(label: 'Advertencia', tone: AppBadgeTone.warning),
              AppBadge(label: 'Ghost', tone: AppBadgeTone.ghost),
            ],
          ),
          const SizedBox(height: 12),
          const AppStatusBanner(
            title: 'Sincronizacion en cola',
            message: 'Se enviaran cambios cuando vuelva la conectividad.',
            tone: AppStatusBannerTone.warning,
            badgeLabel: 'Pendiente',
          ),
          const SizedBox(height: 12),
          const AppStatusBanner(
            title: 'Servidor no disponible',
            message: 'No se pudo confirmar token, intenta de nuevo.',
            tone: AppStatusBannerTone.danger,
            icon: Icons.error_outline_rounded,
            badgeLabel: 'Error',
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Resumen',
            title: 'Metricas',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          const AppMetricCard(
            title: 'Reservas activas',
            value: '124',
            suffix: 'ITEMS',
          ),
          const SizedBox(height: 16),
          const AppMetricCard(
            title: 'Stock critico',
            value: '08',
            supportingText: 'SE RECOMIENDA COMPRAR',
            tone: AppMetricCardTone.danger,
            icon: Icons.warning_amber_rounded,
          ),
          const SizedBox(height: 16),
          const AppMetricCard(
            title: 'Acciones rapidas',
            value: '02',
            supportingText: 'OPERACIONES DISPONIBLES',
            tone: AppMetricCardTone.inverse,
            icon: Icons.bolt_rounded,
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Formularios',
            title: 'Campos',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          const AppTextField(
            label: 'Busqueda',
            hintText: 'Buscar reserva',
            suffix: Icon(Icons.search),
          ),
          const SizedBox(height: 12),
          const AppTextField(
            label: 'Notas',
            hintText: 'Escribe observaciones',
            maxLines: 3,
            variant: AppTextFieldVariant.underlined,
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Filtros',
            title: 'Segmented',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppSegmentedFilter<String>(
            value: reservationFilter,
            onChanged: (value) {
              setState(() {
                reservationFilter = value;
              });
            },
            items: const [
              AppSegmentedFilterItem(label: 'Pendientes', value: 'pendientes'),
              AppSegmentedFilterItem(
                label: 'Confirmadas',
                value: 'confirmadas',
              ),
              AppSegmentedFilterItem(
                label: 'Finalizadas',
                value: 'finalizadas',
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Cards',
            title: 'Basicas y Flip',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppCard(
            tone: AppCardTone.high,
            outlined: true,
            accentColor: Theme.of(context).colorScheme.primary,
            child: const Text('AppCard simple con borde y acento.'),
          ),
          const SizedBox(height: 12),
          AppCard(
            tone: AppCardTone.surface,
            accentColor: Theme.of(context).colorScheme.secondary,
            backChild: const Text(
              'Cara trasera de AppCard. Toca para volver al frente.',
            ),
            child: const Text(
              'Cara frontal de AppCard. Toca para ver reverso.',
            ),
            onTap: () {},
          ),
          const SizedBox(height: 16),
          AppSelectableCard(
            selected: true,
            onTap: () {},
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'COSACO 24',
                        style: Theme.of(context).textTheme.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'CRIOLLO - 11 ANOS',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                const AppBadge(
                  label: 'Seleccionado',
                  tone: AppBadgeTone.primary,
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 260,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: const [
                AppImageFeatureCard(
                  title: 'Cosaco 24',
                  subtitle: 'Criollo - 11 anos',
                  selected: true,
                  badge: AppBadge(
                    label: 'Paso fino',
                    tone: AppBadgeTone.primary,
                  ),
                  image: NetworkImage(
                    'https://picsum.photos/seed/equino1/360/220',
                  ),
                ),
                SizedBox(width: 12),
                AppImageFeatureCard(
                  title: 'Juana',
                  subtitle: 'Criolla - 6 anos',
                  image: NetworkImage(
                    'https://picsum.photos/seed/equino2/360/220',
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          AppStatsCard(
            eyebrow: 'Estadisticas vitales',
            title: 'Cosaco 24',
            selected: true,
            topRight: const AppBadge(
              label: 'No disponible',
              tone: AppBadgeTone.warning,
            ),
            children: const [
              Row(
                children: [
                  Expanded(
                    child: _MiniStat(
                      label: 'Edad',
                      value: '11',
                      suffix: 'anos',
                    ),
                  ),
                  SizedBox(width: 12),
                  Expanded(
                    child: _MiniStat(label: 'Peso', value: '300', suffix: 'kg'),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Experiencias',
            title: 'Cards de venta',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppExperienceCard(
            variant: AppExperienceCardVariant.commercial,
            data: const AppExperienceCardData(
              title: 'Ruta al Mirador del Cucharo',
              description:
                  'Recorrido guiado por senderos de montana con parada panoramica y fotografo de apoyo.',
              priceLabel: '\$220.000',
              priceCaption: 'Desde por persona',
              activityDurationLabel: '5h actividad',
              routeDurationLabel: '2h recorrido',
              distanceLabel: '8 km',
              terrainLabel: 'Bosque de pino',
              difficultyLabel: 'Intermedio',
              capacityLabel: '1 a 8 participantes',
              inclusions: [
                'Guia y logistica',
                'Almuerzo tradicional',
                'Poliza de accidentes',
              ],
              image: NetworkImage(
                'https://picsum.photos/seed/experience1/900/520',
              ),
              badges: [
                AppOperationalBadgeData(
                  label: 'Top venta',
                  tone: AppBadgeTone.primary,
                ),
                AppOperationalBadgeData(
                  label: 'Disponible',
                  tone: AppBadgeTone.success,
                ),
              ],
            ),
            selected: true,
            onPrimaryAction: () {},
          ),
          const SizedBox(height: 12),
          AppExperienceCard(
            variant: AppExperienceCardVariant.compact,
            data: const AppExperienceCardData(
              title: 'Cabalgata de atardecer',
              description:
                  'Sesion corta para principiantes con guia y briefing.',
              priceLabel: '\$140.000',
              activityDurationLabel: '1h 20m',
              routeDurationLabel: '55m',
              difficultyLabel: 'Basico',
              badges: [
                AppOperationalBadgeData(
                  label: 'Ultimos cupos',
                  tone: AppBadgeTone.warning,
                ),
              ],
            ),
            onPrimaryAction: () {},
          ),
          const SizedBox(height: 12),
          AppExperienceCard(
            variant: AppExperienceCardVariant.operational,
            data: const AppExperienceCardData(
              title: 'Ruta del Bosque',
              description:
                  'Salida asociada a reserva, lista para confirmacion.',
              activityDurationLabel: '5h actividad',
              routeDurationLabel: '2h recorrido',
              difficultyLabel: 'Intermedio',
              capacityLabel: 'Capacidad: 8',
              scheduleLabel: '26/04/2026 - 08:30 AM',
              availableSlotsLabel: 'Cupos disponibles: 3',
              stateLabel: 'Estado: OPEN',
              badges: [
                AppOperationalBadgeData(
                  label: 'Operativa',
                  tone: AppBadgeTone.primary,
                ),
              ],
            ),
            onPrimaryAction: () {},
          ),
          const SizedBox(height: 12),
          const AppPricingTiersTable(
            currency: 'COP',
            pricesAreNet: true,
            notes: 'Netas en pesos colombianos (COP)',
            tiers: [
              AppPricingTierData(
                minParticipants: 1,
                maxParticipants: 1,
                pricePerPerson: 875000,
              ),
              AppPricingTierData(
                minParticipants: 2,
                maxParticipants: 2,
                pricePerPerson: 530000,
              ),
              AppPricingTierData(
                minParticipants: 3,
                maxParticipants: 3,
                pricePerPerson: 450000,
              ),
              AppPricingTierData(
                minParticipants: 4,
                maxParticipants: 8,
                pricePerPerson: 420000,
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Asignacion',
            title: 'Participante y Equino',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppAssignmentCard(
            startTimeLabel: '09:15 AM',
            reservationLabel: 'RES-2419',
            participant: const AppAssignmentParticipantData(
              name: 'Elena Rodriguez',
              weightLabel: '68 kg',
              experienceLabel: 'Intermedia',
              ageLabel: '29 anos',
            ),
            equine: const AppAssignmentEquineData(
              name: 'Cosaco 24',
              capacityLabel: 'Carga max 90 kg',
              statusLabel: 'Paso fino',
              image: NetworkImage(
                'https://picsum.photos/seed/horse-card-1/120/120',
              ),
            ),
            saddleLabel: 'Silla trail media',
            loadRatio: 0.72,
            state: AppAssignmentCardState.warning,
            validationMessage:
                'La asignacion queda cerca del limite de carga para esta ruta.',
            onChangeEquine: () {},
            onChangeSaddle: () {},
          ),
          const SizedBox(height: 12),
          AppAssignmentCard(
            startTimeLabel: '11:30 AM',
            reservationLabel: 'RES-2427',
            participant: const AppAssignmentParticipantData(
              name: 'Marcus Thorne',
              weightLabel: '82 kg',
              experienceLabel: 'Avanzado',
            ),
            equine: const AppAssignmentEquineData(
              name: 'Juana',
              capacityLabel: 'Carga max 80 kg',
              statusLabel: 'En revision',
            ),
            saddleLabel: 'Silla endurance #3',
            loadRatio: 1.04,
            state: AppAssignmentCardState.error,
            validationMessage:
                'Excede la capacidad recomendada para este equino y configuracion.',
            onChangeEquine: () {},
          ),
          const SizedBox(height: 24),
          const AppSectionHeader(
            eyebrow: 'Listas',
            title: 'Rows',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          const AppEntityRowCard(
            title: 'Elena Rodriguez',
            subtitle: 'EXP: INTERMEDIO - 68KG',
            selected: true,
            badge: AppBadge(label: 'Alto riesgo', tone: AppBadgeTone.danger),
          ),
          const SizedBox(height: 12),
          const AppEntityRowCard(
            title: 'Marcus Thorne',
            subtitle: 'EXP: AVANZADO - 82KG',
            badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Card estandar',
            title: 'Centrada con badges',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppCenteredBadgeCard(
            kicker: 'Reserva principal',
            title: 'Elena + Cosaco',
            subtitle: 'Asignacion preparada para salida de las 09:15 AM',
            tone: AppBadgeTone.primary,
            badges: const [
              AppBadge(label: 'Confirmada', tone: AppBadgeTone.success),
              AppBadge(label: 'Pago parcial', tone: AppBadgeTone.warning),
              AppBadge(label: '2 extras', tone: AppBadgeTone.ghost),
            ],
            onTap: () {},
            onTrailingTap: () {},
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Bitacora',
            title: 'Timeline',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppTimeline(
            children: const [
              AppTimelineItem(
                state: AppTimelineNodeState.active,
                child: AppTimelineEntryCard(
                  date: 'Oct 24, 2026 - 09:00 AM',
                  title: 'Monta controlada',
                  badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.ghost),
                  description:
                      'Monta natural con yegua en condiciones controladas y sin incidentes.',
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.completed,
                child: AppTimelineEntryCard(
                  date: 'Sep 15, 2026',
                  title: 'Vacunacion anual',
                  badge: AppBadge(
                    label: 'Completado',
                    tone: AppBadgeTone.ghost,
                  ),
                  description:
                      'Aplicacion de vacuna contra influenza y tetanos segun protocolo.',
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.cancelled,
                child: AppTimelineEntryCard(
                  date: 'Ago 28, 2026',
                  title: 'Monta controlada',
                  badge: AppBadge(
                    label: 'Cancelado',
                    tone: AppBadgeTone.danger,
                  ),
                  description: 'Reprogramada para octubre 24.',
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Bitacora',
            title: 'Timeline personalizable',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          AppLogbookTimeline(
            entries: [
              AppLogbookTimelineEntry(
                state: AppLogbookEntryState.active,
                title: 'Monta guiada',
                dateLabel: '24 Oct 2026 - 09:00 AM',
                reservationLabel: 'RES-2419',
                guideLabel: 'Juan P.',
                durationLabel: '2h 30m',
                badge: const AppBadge(
                  label: 'En curso',
                  tone: AppBadgeTone.primary,
                ),
                observations:
                    'Terreno seco, respuesta estable del equino y cliente confiado en transiciones.',
                photos: const [
                  NetworkImage('https://picsum.photos/seed/log1/120/120'),
                  NetworkImage('https://picsum.photos/seed/log2/120/120'),
                ],
                highlightedContent: const _TimelineHighlights(
                  items: [
                    _HighlightItem(label: 'Paradas', value: '3'),
                    _HighlightItem(label: 'Km', value: '8.4'),
                    _HighlightItem(label: 'BPM prom', value: '118'),
                  ],
                ),
                onEdit: () {},
                onAddPhoto: () {},
              ),
              AppLogbookTimelineEntry(
                state: AppLogbookEntryState.warning,
                title: 'Ajuste de silla',
                dateLabel: '24 Oct 2026 - 08:40 AM',
                reservationLabel: 'RES-2419',
                guideLabel: 'Laura V.',
                durationLabel: '20m',
                badge: const AppBadge(
                  label: 'Atencion',
                  tone: AppBadgeTone.warning,
                ),
                observations:
                    'Se cambia cincha por ajuste incomodo reportado por cliente.',
              ),
              AppLogbookTimelineEntry(
                state: AppLogbookEntryState.completed,
                title: 'Checklist pre salida',
                dateLabel: '24 Oct 2026 - 08:20 AM',
                reservationLabel: 'RES-2419',
                guideLabel: 'Laura V.',
                durationLabel: '12m',
                badge: const AppBadge(
                  label: 'Completado',
                  tone: AppBadgeTone.ghost,
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
          const AppSectionHeader(
            eyebrow: 'Accesorios',
            title: 'Loader y Voice FAB',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),
          const SizedBox(height: 96, child: AppCenteredLoader()),
          const SizedBox(height: 16),
          Row(
            children: [
              AppVoiceFab(
                icon: useMicOffIcon ? Icons.mic_off_rounded : Icons.mic_rounded,
                onTap: () {
                  setState(() {
                    useMicOffIcon = !useMicOffIcon;
                  });
                },
              ),
              const SizedBox(width: 12),
              const Expanded(
                child: Text(
                  'Toca el boton para alternar icono y validar animacion.',
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({
    required this.label,
    required this.value,
    required this.suffix,
  });

  final String label;
  final String value;
  final String suffix;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: Theme.of(
              context,
            ).textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant),
          ),
          const SizedBox(height: 8),
          RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: value,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    color: scheme.onSurface,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                TextSpan(
                  text: ' $suffix',
                  style: Theme.of(
                    context,
                  ).textTheme.labelLarge?.copyWith(color: scheme.onSurface),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TimelineHighlights extends StatelessWidget {
  const _TimelineHighlights({required this.items});

  final List<_HighlightItem> items;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return Row(
      children: items.map((item) {
        final isLast = item == items.last;
        return Expanded(
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 6),
            decoration: BoxDecoration(
              border: isLast
                  ? null
                  : Border(
                      right: BorderSide(
                        color: scheme.outlineVariant.withValues(alpha: 0.25),
                      ),
                    ),
            ),
            child: Column(
              children: [
                Text(
                  item.value,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  item.label.toUpperCase(),
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    letterSpacing: 0.6,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _HighlightItem {
  const _HighlightItem({required this.label, required this.value});

  final String label;
  final String value;
}
