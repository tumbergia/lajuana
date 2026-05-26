import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../../../app/widgets/app_button.dart';
import '../../../../app/widgets/app_centered_loader.dart';
import '../../../../app/widgets/app_section_header.dart';
import '../../../../app/widgets/app_segmented_filter.dart';
import '../../../../app/widgets/app_status_banner.dart';
import '../../../../app/widgets/app_text_field.dart';
import '../../../auth/presentation/auth_controller.dart';
import '../../../catalogs/catalogs_module.dart';
import '../../../catalogs/schedules/presentation/pages/schedules_page.dart';
import '../../domain/models/reservation_detail.dart';
import '../../domain/models/reservation_list_item.dart';
import '../../domain/models/reservation_status.dart';
import '../../domain/repositories/reservations_repository.dart';
import '../../reservations_module.dart';
import '../controllers/reservations_list_controller.dart';
import '../widgets/reservation_row_card.dart';
import 'reservation_detail_shell_screen.dart';

class ReservationsModuleScreen extends StatefulWidget {
  const ReservationsModuleScreen({
    super.key,
    this.catalogsModule,
    this.authController,
    this.reservationsModule,
  });

  final CatalogsModule? catalogsModule;
  final AuthController? authController;
  final ReservationsModule? reservationsModule;

  @override
  State<ReservationsModuleScreen> createState() =>
      _ReservationsModuleScreenState();
}

class _ReservationsModuleScreenState extends State<ReservationsModuleScreen> {
  late final ReservationsListController _listController;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _listController = widget.reservationsModule?.listController ??
        ReservationsListController(
          repository: widget.reservationsModule?.repository ??
              _createFallbackRepository(),
        );
    _listController.addListener(_onListChanged);
    _listController.loadInitial();

    _searchController.addListener(() {
      _listController.setSearchQuery(_searchController.text);
    });
  }

  ReservationsRepository _createFallbackRepository() {
    return _FallbackRepository();
  }

  @override
  void dispose() {
    _listController.removeListener(_onListChanged);
    _listController.dispose();
    _searchController.dispose();
    super.dispose();
  }

  void _onListChanged() {
    if (mounted) setState(() {});
  }

  void _openReservationDetail(String reservationId) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => ReservationDetailShellScreen(
          reservationId: reservationId,
          reservationsModule: widget.reservationsModule,
          authController: widget.authController,
        ),
      ),
    );
  }

  void _openSchedules() {
    if (widget.catalogsModule == null || widget.authController == null) return;
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => SchedulesPage(
          module: widget.catalogsModule!,
          authController: widget.authController!,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            eyebrow: 'Gestion',
            title: 'Reservas',
          ),
          const SizedBox(height: 20),
          Expanded(child: _buildContent()),
        ],
      ),
    );
  }

  Widget _buildContent() {
    final state = _listController.state;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Search + Fechas row
        Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(
              child: AppTextField(
                controller: _searchController,
                hintText: 'Buscar por titular, codigo...',
                variant: AppTextFieldVariant.filled,
                suffix: const Icon(Icons.search_rounded, size: 20),
              ),
            ),
            const SizedBox(width: 8),
            // Calendar icon button — centered, same height as search
            SizedBox(
              height: 44,
              width: 44,
              child: Material(
                color: Theme.of(context).colorScheme.surfaceContainerLow,
                borderRadius: BorderRadius.circular(8),
                child: InkWell(
                  borderRadius: BorderRadius.circular(8),
                  onTap: widget.catalogsModule != null && widget.authController != null
                      ? _openSchedules
                      : null,
                  child: Center(
                    child: Icon(
                      Icons.calendar_today_rounded,
                      size: 20,
                      color: widget.catalogsModule != null && widget.authController != null
                          ? Theme.of(context).colorScheme.onSurface
                          : Theme.of(context).colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Status filter — shorter labels to avoid overflow
        AppSegmentedFilter<String>(
          value: _listController.filterGroup ?? 'pendientes',
          onChanged: (value) => _listController.setFilterGroup(value),
          items: const [
            AppSegmentedFilterItem(label: 'Pendientes', value: 'pendientes'),
            AppSegmentedFilterItem(label: 'Confirmadas', value: 'confirmadas'),
            AppSegmentedFilterItem(label: 'Cerradas', value: 'cerradas'),
          ],
        ),
        const SizedBox(height: 12),

        // Offline banner
        if (state == ReservationsLoadState.offlineFromCache)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: AppStatusBanner(
              title: 'Sin conexion',
              message: 'Mostrando datos almacenados localmente.',
              tone: AppStatusBannerTone.warning,
              icon: Icons.wifi_off_rounded,
              badgeLabel: 'Offline',
            ),
          ),

        // Error banner
        if (state == ReservationsLoadState.error && _listController.items.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: AppStatusBanner(
              title: 'Error de sincronizacion',
              message: _listController.errorMessage ?? 'Error desconocido.',
              tone: AppStatusBannerTone.danger,
              icon: Icons.error_outline_rounded,
              badgeLabel: 'Error',
            ),
          ),

        // List
        Expanded(
          child: _buildListContent(state),
        ),
      ],
    );
  }

  Widget _buildListContent(ReservationsLoadState state) {
    switch (state) {
      case ReservationsLoadState.idle:
      case ReservationsLoadState.loading:
        return const AppCenteredLoader();

      case ReservationsLoadState.refreshing:
        if (_listController.items.isEmpty) return const AppCenteredLoader();
        return _buildList();

      case ReservationsLoadState.success:
      case ReservationsLoadState.offlineFromCache:
        return _buildList();

      case ReservationsLoadState.empty:
        return _buildEmptyState(
          icon: Icons.event_busy_rounded,
          title: 'Sin reservas',
          message: 'No hay reservas para el filtro seleccionado.',
        );

      case ReservationsLoadState.error:
        return Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline_rounded, size: 48),
              const SizedBox(height: 16),
              Text(
                _listController.errorMessage ?? 'Error al cargar reservas.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              AppButton(
                label: 'Reintentar',
                onPressed: () => _listController.loadInitial(),
              ),
            ],
          ),
        );
    }
  }

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

  Widget _buildList() {
    final items = _listController.items;
    if (items.isEmpty) {
      return _buildEmptyState(
        icon: Icons.search_off_rounded,
        title: 'Sin resultados',
        message: 'No hay reservas para el filtro o busqueda actual.',
      );
    }

    return RefreshIndicator(
      onRefresh: () => _listController.refresh(),
      child: ListView.builder(
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: items.length,
        itemBuilder: (context, i) {
          return Padding(
            padding: EdgeInsets.only(
              bottom: i < items.length - 1 ? 10 : 0,
            ),
            child: ReservationRowCard(
              reservation: items[i],
              subtitle: items[i].experienceName ?? items[i].equineName,
              highlightIfPending:
                  items[i].status == 'pendientes',
              openDetailsOnTap: true,
              onOpenDetail: () =>
                  _openReservationDetail(items[i].id ?? items[i].code),
            ),
          );
        },
      ),
    );
  }
}

/// Fallback repository for screens without injected module.
class _FallbackRepository implements ReservationsRepository {
  @override
  Future<List<ReservationListItem>> listReservations({
    ReservationStatus? status,
    String? query,
  }) async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail> getReservationById(String reservationId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<List<ReservationListItem>> getCachedReservations() async {
    return const <ReservationListItem>[];
  }

  @override
  Future<ReservationDetail?> getCachedReservationDetail(
    String reservationId,
  ) async {
    return null;
  }

  @override
  Future<Uint8List> downloadPaymentProofFile(String paymentProofId) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> approvePaymentProof({
    required String paymentProofId,
    String? note,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }

  @override
  Future<ReservationDetail> rejectPaymentProof({
    required String paymentProofId,
    required String reason,
  }) async {
    throw Exception('ReservationsModule no inyectado');
  }
}
