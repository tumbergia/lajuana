import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_section_header.dart';
import 'package:mobile_ui/src/widgets/app_search_field.dart';
import 'package:mobile_ui/src/widgets/app_segmented_filter.dart';
import 'package:mobile_ui/src/widgets/app_status_banner.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile/features/assignments/assignments_module.dart';
import 'package:mobile/features/auth/presentation/auth_controller.dart';
import 'package:mobile/features/catalogs/catalogs_module.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_calendar.dart';
import 'package:mobile_domain/src/reservations/reservations_repository.dart';
import 'package:mobile/features/reservations/infrastructure/repositories/fallback_repository.dart';
import 'package:mobile/features/reservations/reservations_module.dart';
import 'package:mobile/features/reservations/presentation/controllers/reservations_list_controller.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_row_card.dart';
import 'reservation_create_page.dart';
import 'reservation_detail_shell_screen.dart';

class ReservationsModuleScreen extends StatefulWidget {
  const ReservationsModuleScreen({
    super.key,
    this.catalogsModule,
    this.authController,
    this.reservationsModule,
    this.assignmentsModule,
  });

  final CatalogsModule? catalogsModule;
  final AuthController? authController;
  final ReservationsModule? reservationsModule;
  final AssignmentsModule? assignmentsModule;

  @override
  State<ReservationsModuleScreen> createState() =>
      _ReservationsModuleScreenState();
}

class _ReservationsModuleScreenState extends State<ReservationsModuleScreen>
    with RefreshableState {
  late final ReservationsListController _listController;
  late final bool _ownsListController;

  @override
  Future<void> onRefresh() => _listController.refresh();
  final TextEditingController _searchController = TextEditingController();

  bool get _canCreateReservation {
    final role = widget.authController?.currentUser?.role;
    return role == 'admin' &&
        widget.reservationsModule != null &&
        widget.catalogsModule != null;
  }

  bool get _isGuide {
    final role =
        widget.authController?.currentUser?.role.trim().toLowerCase();
    return role == 'guide';
  }

  List<AppSegmentedFilterItem<String?>> get _statusFilterItems {
    if (_isGuide) {
      return const [
        AppSegmentedFilterItem(label: 'Confirmadas', value: 'confirmadas'),
      ];
    }
    return const [
      AppSegmentedFilterItem(label: 'Pendientes', value: 'pendientes'),
      AppSegmentedFilterItem(label: 'Confirmadas', value: 'confirmadas'),
      AppSegmentedFilterItem(label: 'Cerradas', value: 'cerradas'),
      AppSegmentedFilterItem(label: 'Eliminadas', value: 'eliminadas'),
    ];
  }

  @override
  void initState() {
    super.initState();
    if (widget.reservationsModule != null) {
      _listController = widget.reservationsModule!.listController;
      _ownsListController = false;
    } else {
      _listController = ReservationsListController(
        repository: _createFallbackRepository(),
      );
      _ownsListController = true;
    }
    _listController.addListener(_onListChanged);
    if (_isGuide && _listController.filterGroup != 'confirmadas') {
      _listController.setFilterGroup('confirmadas');
    }
    if (_listController.state == ReservationsLoadState.idle) {
      _listController.loadInitial();
    }

    _searchController.addListener(() {
      _listController.setSearchQuery(_searchController.text);
    });
  }

  ReservationsRepository _createFallbackRepository() {
    return FallbackRepository();
  }

  @override
  void dispose() {
    _listController.removeListener(_onListChanged);
    if (_ownsListController) {
      _listController.dispose();
    }
    _searchController.dispose();
    super.dispose();
  }

  void _onListChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _openCreateReservation() async {
    final reservationsModule = widget.reservationsModule;
    final catalogsModule = widget.catalogsModule;
    if (reservationsModule == null || catalogsModule == null) return;

    final createdId = await Navigator.of(context).push<String>(
      MaterialPageRoute(
        builder: (_) => ReservationCreatePage(
          reservationsModule: reservationsModule,
          catalogsModule: catalogsModule,
        ),
      ),
    );

    if (!mounted) return;
    await _listController.refresh();
    if (createdId != null && createdId.isNotEmpty && mounted) {
      _openReservationDetail(createdId);
    }
  }

  void _openReservationDetail(String reservationId) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => ReservationDetailShellScreen(
          reservationId: reservationId,
          reservationsModule: widget.reservationsModule,
          authController: widget.authController,
          assignmentsModule: widget.assignmentsModule,
        ),
      ),
    );
  }

  void _openReservationCalendar() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => ReservationCalendarSheet(
          controller: _listController,
          onOpenDetail: (id) {
            Navigator.of(context).pop();
            _openReservationDetail(id);
          },
        ),
      ),
    );
  }

  // ── BUILD ──────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final state = _listController.state;

    return CustomScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      slivers: [
        // ── Fixed header (section, search, filter, banners) ──
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(24, 24, 24, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppSectionHeader(
                  eyebrow: 'Gestion',
                  title: 'Reservas',
                ),
                const SizedBox(height: 20),

                // Search + calendar row
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    Expanded(
                      child: AppSearchField(
                        controller: _searchController,
                        hintText: 'Buscar por titular, codigo...',
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      height: 44,
                      width: 44,
                      child: Material(
                        color: Theme.of(context)
                            .colorScheme
                            .surfaceContainerLow,
                        borderRadius: BorderRadius.circular(2),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(2),
                          onTap: _openReservationCalendar,
                          child: Center(
                            child: Icon(
                              Icons.calendar_today_rounded,
                              size: 20,
                              color: Theme.of(context).colorScheme.onSurface,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Status filter
                AppSegmentedFilter<String?>(
                  value: _listController.filterGroup,
                  onChanged: _listController.setFilterGroup,
                  allowDeselect: !_isGuide,
                  items: _statusFilterItems,
                ),

                if (_canCreateReservation) ...[
                  const SizedBox(height: 12),
                  AppButton(
                    label: 'Crear reserva',
                    icon: Icons.add,
                    expanded: true,
                    onPressed: _openCreateReservation,
                  ),
                ],

                // Offline banner
                if (state ==
                    ReservationsLoadState.offlineFromCache) ...[
                  const SizedBox(height: 12),
                  AppStatusBanner(
                    title: 'Sin conexion',
                    message: 'Mostrando datos almacenados localmente.',
                    tone: AppStatusBannerTone.warning,
                    icon: Icons.wifi_off_rounded,
                    badgeLabel: 'Offline',
                  ),
                ],

                // Error banner (only when items exist)
                if (state == ReservationsLoadState.error &&
                    _listController.items.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  AppStatusBanner(
                    title: 'Error de sincronizacion',
                    message:
                        _listController.errorMessage ?? 'Error desconocido.',
                    tone: AppStatusBannerTone.danger,
                    icon: Icons.error_outline_rounded,
                    badgeLabel: 'Error',
                  ),
                ],
              ],
            ),
          ),
        ),

        // ── Dynamic content (list / empty / loading / error) ──
        _buildContentSliver(state),
      ],
    );
  }

  // ── CONTENT SLIVER ─────────────────────────────────────────────────

  Widget _buildContentSliver(ReservationsLoadState state) {
    switch (state) {
      case ReservationsLoadState.idle:
      case ReservationsLoadState.loading:
        return SliverFillRemaining(
          hasScrollBody: false,
          child: const AppCenteredLoader(),
        );

      case ReservationsLoadState.refreshing:
        if (_listController.items.isEmpty) {
          return SliverFillRemaining(
            hasScrollBody: false,
            child: const AppCenteredLoader(),
          );
        }
        return _buildListSliver();

      case ReservationsLoadState.success:
      case ReservationsLoadState.offlineFromCache:
        return _buildListSliver();

      case ReservationsLoadState.empty:
        return SliverFillRemaining(
          hasScrollBody: false,
          child: _buildEmptyState(
            icon: Icons.event_busy_rounded,
            title: 'Sin reservas',
            message: 'No hay reservas para el filtro seleccionado.',
          ),
        );

      case ReservationsLoadState.error:
        return SliverFillRemaining(
          hasScrollBody: false,
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline_rounded, size: 48),
                const SizedBox(height: 16),
                Text(
                  _listController.errorMessage ??
                      'Error al cargar reservas.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: 'Reintentar',
                  onPressed: () => _listController.loadInitial(),
                ),
              ],
            ),
          ),
        );
    }
  }

  // ── LIST SLIVER ────────────────────────────────────────────────────

  Widget _buildListSliver() {
    final items = _listController.items;
    if (items.isEmpty) {
      return SliverFillRemaining(
        hasScrollBody: false,
        child: _buildEmptyState(
          icon: Icons.search_off_rounded,
          title: 'Sin resultados',
          message: 'No hay reservas para el filtro o busqueda actual.',
        ),
      );
    }

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, i) {
          return Padding(
            padding: EdgeInsets.fromLTRB(
              24,
              0,
              24,
              i < items.length - 1 ? 10 : 24,
            ),
            child: ReservationRowCard(
              reservation: items[i],
              subtitle:
                  items[i].experienceName ?? items[i].equineName,
              highlightIfPending: items[i].status == 'pendientes',
              openDetailsOnTap: true,
              showRequestedDate: true,
              onOpenDetail: () =>
                  _openReservationDetail(items[i].id ?? items[i].code),
            ),
          );
        },
        childCount: items.length,
      ),
    );
  }

  // ── EMPTY STATE ────────────────────────────────────────────────────

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String message,
  }) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 48,
              color: Theme.of(context).colorScheme.onSurfaceVariant),
          const SizedBox(height: 16),
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}
