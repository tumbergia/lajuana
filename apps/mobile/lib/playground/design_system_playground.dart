import 'package:flutter/material.dart';
import '../app/widgets/app_badge.dart';
import '../app/widgets/app_breadcrumb.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_entity_row_card.dart';
import '../app/widgets/app_metric_card.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_section_header.dart';
import '../app/widgets/app_segmented_filter.dart';
import '../app/widgets/app_timeline.dart';
import '../app/widgets/app_top_bar.dart';
import '../app/widgets/app_bottom_nav.dart';

class DesignSystemPlayground extends StatefulWidget {
  const DesignSystemPlayground({super.key});

  @override
  State<DesignSystemPlayground> createState() => _DesignSystemPlaygroundState();
}

class _DesignSystemPlaygroundState extends State<DesignSystemPlayground> {
  String reservationFilter = 'pendientes';

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
          const AppSectionHeader(
            eyebrow: 'Inicio',
            title: 'Supervisión Operacional',
          ),
          const SizedBox(height: 24),

          const AppBreadcrumb(items: ['Gestión', 'Experiencias']),
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
            title: 'Badges',
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
          const SizedBox(height: 32),

          const AppSectionHeader(
            eyebrow: 'Resumen',
            title: 'Métricas',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),

          const AppMetricCard(
            title: 'Total SKU de productos',
            value: '124',
            suffix: 'ITEMS',
          ),
          const SizedBox(height: 16),
          const AppMetricCard(
            title: 'Stock crítico',
            value: '08',
            supportingText: 'SE RECOMIENDA COMPRAR',
            tone: AppMetricCardTone.danger,
            icon: Icons.warning_amber_rounded,
          ),
          const SizedBox(height: 16),
          const AppMetricCard(
            title: 'Acciones rápidas',
            value: '02',
            supportingText: 'OPERACIONES DISPONIBLES',
            tone: AppMetricCardTone.inverse,
            icon: Icons.bolt_rounded,
          ),
          const SizedBox(height: 32),

          const AppSectionHeader(
            eyebrow: 'Reservas',
            title: 'Filtros',
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
            eyebrow: 'Clientes',
            title: 'Rows',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),

          const AppEntityRowCard(
            title: 'Elena Rodriguez',
            subtitle: 'EXP: INTERMEDIO • 68KG',
            selected: true,
            badge: AppBadge(label: 'Alto riesgo', tone: AppBadgeTone.danger),
          ),
          const SizedBox(height: 12),
          const AppEntityRowCard(
            title: 'Marcus Thorne',
            subtitle: 'EXP: AVANZADO • 82KG',
            badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
          ),
          const SizedBox(height: 12),
          const AppEntityRowCard(
            title: 'Sarah Jenkins',
            subtitle: 'EXP: PRINCIPIANTE • 55KG',
            badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
          ),
          const SizedBox(height: 32),

          const AppSectionHeader(
            eyebrow: 'Bitácora',
            title: 'Timeline',
            variant: AppSectionHeaderVariant.compact,
          ),
          const SizedBox(height: 16),

          AppTimeline(
            children: const [
              AppTimelineItem(
                state: AppTimelineNodeState.active,
                child: AppTimelineEntryCard(
                  date: 'Oct 24, 2026 • 09:00 AM',
                  title: 'Monta Controlada',
                  badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.ghost),
                  description:
                      'Monta natural realizada con yegua en condiciones controladas. Se verifica comportamiento del burro, respuesta reproductiva y ausencia de incidentes durante el proceso.',
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.completed,
                child: AppTimelineEntryCard(
                  date: 'Sep 15, 2026',
                  title: 'Vacunación anual',
                  badge: AppBadge(
                    label: 'Completado',
                    tone: AppBadgeTone.ghost,
                  ),
                  description:
                      'Aplicación de vacuna contra influenza y tétanos según protocolo veterinario. Animal sin reacciones adversas inmediatas. Se programa refuerzo anual.',
                  footer: Row(
                    children: [
                      Icon(
                        Icons.medical_services_outlined,
                        size: 16,
                        color: Color(0xFFC6C6C6),
                      ),
                      SizedBox(width: 8),
                      Text(
                        'SERVICIOS VETERINARIOS',
                        style: TextStyle(
                          color: Color(0xFFC6C6C6),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.7,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.completed,
                child: AppTimelineEntryCard(
                  date: 'Sep 12, 2026',
                  title: 'Sesión de acondicionamiento',
                  badge: AppBadge(
                    label: 'Completado',
                    tone: AppBadgeTone.ghost,
                  ),
                  highlightedContent: AppTimelineMetrics(
                    items: [
                      AppTimelineMetricItem(value: '4.2', label: 'KM'),
                      AppTimelineMetricItem(value: '118', label: 'PROM BPM'),
                      AppTimelineMetricItem(value: '45m', label: 'Duración'),
                    ],
                  ),
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.cancelled,
                child: AppTimelineEntryCard(
                  date: 'Ago 28, 2026',
                  title: 'Monta Controlada',
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
        ],
      ),
    );
  }
}
