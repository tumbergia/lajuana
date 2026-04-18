import 'package:flutter/material.dart';
import '../app/widgets/app_bottom_nav.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_top_bar.dart';
import '../app/widgets/app_badge.dart';
import '../app/widgets/app_section_header.dart';
import '../app/widgets/app_metric_card.dart';
import '../app/widgets/app_segmented_filter.dart';
import '../app/widgets/app_timeline.dart';
import '../app/widgets/app_entity_row_card.dart';
import '../app/widgets/app_breadcrumb.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String _filterValue = 'pendientes';
  AppNavItem _currentNav = AppNavItem.inicio;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      appBar: const AppTopBar(
        logoAssetPath: 'assets/branding/lajuana.svg',
        title: 'LA JUANA',
      ),
      bottomNavigationBar: AppBottomNav(
        current: _currentNav,
        onTap: (item) {
          setState(() {
            _currentNav = item;
          });
        },
      ),
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Inicio',
            title: 'Supervisión Operacional',
            trailing: AppButton(
              label: 'Crear',
              icon: Icons.add,
              onPressed: () {},
            ),
          ),
          const SizedBox(height: 24),

          AppSegmentedFilter<String>(
            value: _filterValue,
            onChanged: (v) {
              setState(() {
                _filterValue = v;
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
          const SizedBox(height: 32),

          const AppTimeline(
            children: [
              AppTimelineItem(
                state: AppTimelineNodeState.active,
                child: AppTimelineEntryCard(
                  date: 'Oct 24, 2026 • 09:00 AM',
                  title: 'Monta Controlada',
                  badge: AppBadge(
                    label: 'Pendiente',
                    tone: AppBadgeTone.neutral,
                  ),
                  description:
                      'Monta natural realizada en yegua en condiciones controladas.',
                ),
              ),
              AppTimelineItem(
                state: AppTimelineNodeState.cancelled,
                child: AppTimelineEntryCard(
                  date: 'Oct 10, 2026',
                  title: 'Traslado suspendido',
                  badge: AppBadge(label: 'Error', tone: AppBadgeTone.danger),
                  description:
                      'Vehículo averiado, no se pudo realizar el traslado del equino.',
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
                      'Aplicación de vacuna contra influenza y tétanos.',
                  footer: Row(
                    children: [
                      Icon(Icons.medical_services_outlined, size: 16),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'SERVICIOS VETERINARIOS',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          const AppBreadcrumb(items: ['Gestión', 'Experiencias']),
          const SizedBox(height: 12),
          const AppEntityRowCard(
            title: 'Elena Rodriguez',
            subtitle: 'EXP: INTERMEDIO • 68KG',
            selected: true,
            badge: AppBadge(label: 'Alto Riesgo', tone: AppBadgeTone.danger),
          ),
          const SizedBox(height: 12),
          const AppEntityRowCard(
            title: 'Marcus Thorne',
            subtitle: 'EXP: AVANZADO • 82KG',
            badge: AppBadge(label: 'Perfecto', tone: AppBadgeTone.success),
          ),
        ],
      ),
    );
  }
}
