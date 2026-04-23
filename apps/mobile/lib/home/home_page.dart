import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../app/widgets/app_badge.dart';
import '../app/widgets/app_bottom_nav.dart';
import '../app/widgets/app_breadcrumb.dart';
import '../app/widgets/app_button.dart';
import '../app/widgets/app_entity_row_card.dart';
import '../app/widgets/app_metric_card.dart';
import '../app/widgets/app_scaffold.dart';
import '../app/widgets/app_section_header.dart';
import '../app/widgets/app_segmented_filter.dart';
import '../app/widgets/app_status_banner.dart';
import '../app/widgets/app_text_field.dart';
import '../app/widgets/app_timeline.dart';
import '../app/widgets/app_top_bar.dart';
import '../auth/domain/auth_enums.dart';
import '../auth/infrastructure/remote/auth_api_client.dart';
import '../auth/infrastructure/remote/auth_dtos.dart';
import '../auth/presentation/auth_controller.dart';
import '../features/dashboard/presentation/controllers/dashboard_controller.dart';
import '../features/equines/presentation/controllers/equines_controller.dart';
import '../features/participants/presentation/controllers/participants_controller.dart';
import '../features/reservations/presentation/controllers/reservations_controller.dart';
import '../features/reservations/presentation/models/reservation_view_models.dart';
import '../features/reservations/presentation/screens/reservation_detail_screen.dart';

enum _MoreDestination { menu, profile, contacts, changePassword }

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.controller,
    this.contactsApiClient,
    this.onCallRequested,
  });

  final AuthController controller;
  final AuthApiClient? contactsApiClient;
  final Future<bool> Function(String phone)? onCallRequested;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const List<String> _monthShortLabels = <String>[
    'ENE',
    'FEB',
    'MAR',
    'ABR',
    'MAY',
    'JUN',
    'JUL',
    'AGO',
    'SEP',
    'OCT',
    'NOV',
    'DIC',
  ];

  static const List<ReservationRecord> _reservations =
      ReservationPresentationFixtures.reservations;
  static const List<ReservationParticipantRecord> _participants =
      ReservationPresentationFixtures.participants;
  static const List<ReservationPaymentProofRecord> _paymentProofs =
      ReservationPresentationFixtures.paymentProofs;
  static const List<ReservationAssignmentRecord> _assignments =
      ReservationPresentationFixtures.assignments;

  static const List<_EquineRecord> _equines = <_EquineRecord>[
    _EquineRecord(
      name: 'Cosaco 24',
      summary: 'Disponible hoy 09:00-13:00',
      statusLabel: 'Disponible',
      statusTone: AppBadgeTone.success,
    ),
    _EquineRecord(
      name: 'Amanecer',
      summary: 'En servicio 11:30',
      statusLabel: 'Asignado',
      statusTone: AppBadgeTone.primary,
    ),
    _EquineRecord(
      name: 'Marte',
      summary: 'Observacion veterinaria activa',
      statusLabel: 'Cuidado',
      statusTone: AppBadgeTone.warning,
    ),
  ];

  AppNavItem _currentNav = AppNavItem.inicio;
  _MoreDestination _moreDestination = _MoreDestination.menu;
  late final DashboardController _dashboardController;
  late final ReservationsController _reservationsController;
  late final EquinesController _equinesController;
  late final ParticipantsController _participantsController;

  Future<List<_EmergencyContact>>? _contactsFuture;
  late final AuthApiClient _contactsApiClient;
  late final Future<bool> Function(String phone) _onCallRequested;
  final TextEditingController _currentPasswordCtrl = TextEditingController();
  final TextEditingController _newPasswordCtrl = TextEditingController();
  final TextEditingController _confirmPasswordCtrl = TextEditingController();
  bool _obscureCurrentPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    _contactsApiClient = widget.contactsApiClient ?? AuthApiClient();
    _onCallRequested = widget.onCallRequested ?? _callNativeDialer;
    _dashboardController = DashboardController();
    _reservationsController = ReservationsController();
    _equinesController = EquinesController();
    _participantsController = ParticipantsController();
  }

  @override
  void dispose() {
    _currentPasswordCtrl.dispose();
    _newPasswordCtrl.dispose();
    _confirmPasswordCtrl.dispose();
    _dashboardController.dispose();
    _reservationsController.dispose();
    _equinesController.dispose();
    _participantsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: Listenable.merge(<Listenable>[
        widget.controller,
        _dashboardController,
        _reservationsController,
        _equinesController,
        _participantsController,
      ]),
      builder: (context, _) {
        return AppScaffold(
          appBar: const AppTopBar(
            logoAssetPath: 'assets/branding/lajuana.svg',
            title: 'LA JUANA',
          ),
          bottomNavigationBar: AppBottomNav(
            current: _currentNav,
            onTap: _onBottomNavTap,
          ),
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: _buildCurrentView(),
        );
      },
    );
  }

  void _onBottomNavTap(AppNavItem item) {
    setState(() {
      if (item != AppNavItem.mas) {
        _moreDestination = _MoreDestination.menu;
      } else if (_currentNav == AppNavItem.mas) {
        _moreDestination = _MoreDestination.menu;
      }
      _currentNav = item;
    });
  }

  void _openMoreDestination(_MoreDestination destination) {
    setState(() {
      _moreDestination = destination;
      if (destination == _MoreDestination.contacts) {
        _contactsFuture ??= _loadEmergencyContacts();
      }
    });
  }

  Widget _buildCurrentView() {
    switch (_currentNav) {
      case AppNavItem.inicio:
        return _buildDashboardView();
      case AppNavItem.reservas:
        return _buildReservationsView();
      case AppNavItem.equinos:
        return _buildEquinesView();
      case AppNavItem.clientes:
        return _buildClientsView();
      case AppNavItem.mas:
        return _buildMoreView();
      case AppNavItem.none:
        return _buildDashboardView();
    }
  }

  Widget _buildDashboardView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildModuleHeader(
          eyebrow: 'Inicio',
          title: 'Tablero operativo',
          subtitle: 'Operacion de reservas y estado del dia',
          subrouteLabels: const ['Resumen', 'Pendientes', 'Salidas', 'Sync'],
          currentSubrouteIndex: _dashboardController.subroute.index,
          onSubrouteTap: _dashboardController.selectSubrouteByIndex,
          trailing: AppButton(
            label: 'Ir a reservas',
            icon: Icons.arrow_forward_rounded,
            variant: AppButtonVariant.secondary,
            onPressed: () => _onBottomNavTap(AppNavItem.reservas),
          ),
        ),
        const SizedBox(height: 20),
        _buildDashboardSubrouteContent(),
      ],
    );
  }

  Widget _buildDashboardSubrouteContent() {
    switch (_dashboardController.subroute) {
      case DashboardSubroute.resumen:
        final pendingCount = _reservations
            .where((item) => item.status == 'pendientes')
            .length;
        final todayCount = _reservations.where((item) {
          return item.slotLabel.startsWith('24 Oct 2026');
        }).length;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppMetricCard(
              title: 'Reservas pendientes',
              value: pendingCount.toString().padLeft(2, '0'),
              suffix: 'CASOS',
              supportingText: 'Requieren accion operativa',
            ),
            const SizedBox(height: 12),
            AppMetricCard(
              title: 'Salidas proximas',
              value: todayCount.toString().padLeft(2, '0'),
              suffix: 'HOY',
              tone: AppMetricCardTone.inverse,
            ),
            const SizedBox(height: 16),
            AppEntityRowCard(
              title: 'Abrir reservas',
              subtitle: 'Gestion de detalle, participantes y pagos',
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () => _onBottomNavTap(AppNavItem.reservas),
            ),
            const SizedBox(height: 10),
            AppEntityRowCard(
              title: 'Abrir equinos',
              subtitle: 'Disponibilidad y asignaciones en campo',
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () => _onBottomNavTap(AppNavItem.equinos),
            ),
            const SizedBox(height: 10),
            AppEntityRowCard(
              title: 'Abrir participantes',
              subtitle: 'Completitud y validaciones por reserva',
              trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              onTap: () => _onBottomNavTap(AppNavItem.clientes),
            ),
          ],
        );
      case DashboardSubroute.pendientes:
        final pending = _reservations
            .where((item) => item.status == 'pendientes')
            .toList(growable: false);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < pending.length; i++) ...[
              _buildReservationRow(
                pending[i],
                subtitle: '${pending[i].equineName} - ${pending[i].slotLabel}',
                highlightIfPending: true,
                openDetailsOnTap: true,
              ),
              if (i != pending.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case DashboardSubroute.salidas:
        final ordered = _reservations
            .where((item) => item.status != 'finalizadas')
            .take(4)
            .toList(growable: false);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < ordered.length; i++) ...[
              AppEntityRowCard(
                title: ordered[i].slotLabel,
                subtitle: '${ordered[i].clientName} - ${ordered[i].equineName}',
                badge: _reservationStatusBadge(ordered[i].status),
                leading: const Icon(Icons.schedule_rounded, size: 18),
              ),
              if (i != ordered.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case DashboardSubroute.sync:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppEntityRowCard(
              title: 'Cambios pendientes',
              subtitle: widget.controller.hasPendingSync
                  ? 'Hay cambios locales por enviar'
                  : 'No hay cambios pendientes',
              badge: AppBadge(
                label: widget.controller.hasPendingSync ? 'Pendiente' : 'OK',
                tone: widget.controller.hasPendingSync
                    ? AppBadgeTone.warning
                    : AppBadgeTone.success,
                uppercase: false,
              ),
            ),
            const SizedBox(height: 10),
            AppEntityRowCard(
              title: 'Conflictos de sincronizacion',
              subtitle: _reservations.any((item) => item.hasSyncError)
                  ? 'Hay reservas con error de sync'
                  : 'Sin conflictos detectados',
              badge: AppBadge(
                label: _reservations.any((item) => item.hasSyncError)
                    ? 'Revisar'
                    : 'Limpio',
                tone: _reservations.any((item) => item.hasSyncError)
                    ? AppBadgeTone.danger
                    : AppBadgeTone.success,
                uppercase: false,
              ),
            ),
          ],
        );
    }
  }

  Widget _buildReservationsView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildModuleHeader(
          eyebrow: 'Reservas',
          title: 'Operacion de reservas',
          subtitle: 'Local primero, sync visible y acciones por estado',
          subrouteLabels: const [
            'Resumen',
            'Participantes',
            'Pagos',
            'Asignaciones',
            'Bitacora',
          ],
          currentSubrouteIndex: _reservationsController.subroute.index,
          onSubrouteTap: _reservationsController.selectSubrouteByIndex,
          trailing: AppButton(
            label: 'Crear',
            icon: Icons.add,
            onPressed: () {},
          ),
        ),
        const SizedBox(height: 20),
        _buildReservationsSubrouteContent(),
      ],
    );
  }

  Widget _buildReservationsSubrouteContent() {
    switch (_reservationsController.subroute) {
      case ReservationsSubroute.resumen:
        final filtered = _filterReservations();
        final visible = filtered
            .take(_reservationsController.visibleReservationCount)
            .toList(growable: false);
        final canLoadMore = visible.length < filtered.length;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppSegmentedFilter<String>(
              value: _reservationsController.filterValue,
              onChanged: _reservationsController.setFilterValue,
              items: const [
                AppSegmentedFilterItem(
                  label: 'Pendientes',
                  value: 'pendientes',
                ),
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
            const SizedBox(height: 14),
            if (visible.isEmpty)
              const AppEntityRowCard(
                title: 'Sin resultados',
                subtitle: 'No hay reservas para el filtro seleccionado',
                selected: true,
              )
            else
              for (int i = 0; i < visible.length; i++) ...[
                _buildReservationRow(
                  visible[i],
                  subtitle:
                      '${visible[i].equineName} - ${visible[i].slotLabel}',
                  highlightIfPending: true,
                  openDetailsOnTap: true,
                ),
                if (i != visible.length - 1) const SizedBox(height: 10),
              ],
            if (canLoadMore) ...[
              const SizedBox(height: 12),
              AppButton(
                label: 'Cargar mas',
                variant: AppButtonVariant.ghost,
                expanded: true,
                onPressed: () {
                  _reservationsController.loadMore();
                },
              ),
            ],
          ],
        );
      case ReservationsSubroute.participantes:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < _participants.length; i++) ...[
              AppEntityRowCard(
                title: _participants[i].fullName,
                subtitle: 'Reserva ${_participants[i].reservationCode}',
                badge: AppBadge(
                  label: _participants[i].completionLabel,
                  tone: _participants[i].isComplete
                      ? AppBadgeTone.success
                      : AppBadgeTone.warning,
                  uppercase: false,
                ),
                leading: const Icon(Icons.person_outline_rounded, size: 18),
              ),
              if (i != _participants.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case ReservationsSubroute.pagos:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < _paymentProofs.length; i++) ...[
              AppEntityRowCard(
                title: _paymentProofs[i].proofCode,
                subtitle: 'Reserva ${_paymentProofs[i].reservationCode}',
                badge: AppBadge(
                  label: _paymentProofs[i].statusLabel,
                  tone: _paymentProofs[i].statusTone,
                  uppercase: false,
                ),
                leading: const Icon(Icons.receipt_long_rounded, size: 18),
              ),
              if (i != _paymentProofs.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case ReservationsSubroute.asignaciones:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < _assignments.length; i++) ...[
              AppEntityRowCard(
                title: _assignments[i].equine,
                subtitle:
                    'Reserva ${_assignments[i].reservationCode} - ${_assignments[i].rider}',
                badge: AppBadge(
                  label: _assignments[i].statusLabel,
                  tone: _assignments[i].statusTone,
                  uppercase: false,
                ),
                leading: const Icon(Icons.shield_moon_outlined, size: 18),
              ),
              if (i != _assignments.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case ReservationsSubroute.bitacora:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.active,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 10:05',
                title: 'Cambio de horario',
                badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.warning),
                description: 'Se ajusto salida por condicion de pista.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 09:15',
                title: 'Participante validado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Documento y consentimiento verificados.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.error,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 08:58',
                title: 'Fallo en carga de comprobante',
                badge: AppBadge(label: 'Error', tone: AppBadgeTone.danger),
                description: 'Se guardo localmente para reintento de sync.',
              ),
            ),
          ],
        );
    }
  }

  Widget _buildEquinesView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildModuleHeader(
          eyebrow: 'Equinos',
          title: 'Gestion de equinos',
          subtitle: 'Disponibilidad, historial y cuidado operativo',
          subrouteLabels: const [
            'Resumen',
            'Historial',
            'Disponibilidad',
            'Cuidado',
          ],
          currentSubrouteIndex: _equinesController.subroute.index,
          onSubrouteTap: _equinesController.selectSubrouteByIndex,
        ),
        const SizedBox(height: 20),
        _buildEquinesSubrouteContent(),
      ],
    );
  }

  Widget _buildEquinesSubrouteContent() {
    switch (_equinesController.subroute) {
      case EquinesSubroute.resumen:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < _equines.length; i++) ...[
              AppEntityRowCard(
                title: _equines[i].name,
                subtitle: _equines[i].summary,
                badge: AppBadge(
                  label: _equines[i].statusLabel,
                  tone: _equines[i].statusTone,
                  uppercase: false,
                ),
                trailing: const Icon(Icons.chevron_right_rounded, size: 18),
              ),
              if (i != _equines.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case EquinesSubroute.historial:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '23 Oct 2026',
                title: 'Cosaco 24 - Servicio finalizado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Actividad completada sin novedades.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.neutral,
              child: AppTimelineEntryCard(
                date: '22 Oct 2026',
                title: 'Marte - Revision veterinaria',
                badge: AppBadge(
                  label: 'Observacion',
                  tone: AppBadgeTone.warning,
                ),
                description: 'Control preventivo por fatiga leve.',
              ),
            ),
          ],
        );
      case EquinesSubroute.disponibilidad:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            AppEntityRowCard(
              title: 'COSACO 24',
              subtitle: 'Disponible: 09:00 - 13:00',
              badge: AppBadge(
                label: 'Disponible',
                tone: AppBadgeTone.success,
                uppercase: false,
              ),
            ),
            SizedBox(height: 10),
            AppEntityRowCard(
              title: 'AMANECER',
              subtitle: 'Asignado: 11:30 - 14:00',
              badge: AppBadge(
                label: 'Asignado',
                tone: AppBadgeTone.primary,
                uppercase: false,
              ),
            ),
          ],
        );
      case EquinesSubroute.cuidado:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            AppEntityRowCard(
              title: 'MARTE',
              subtitle: 'Control veterinario en curso',
              badge: AppBadge(
                label: 'Requiere seguimiento',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
            ),
            SizedBox(height: 10),
            AppEntityRowCard(
              title: 'PRADERA',
              subtitle: 'Sin alertas activas',
              badge: AppBadge(
                label: 'Estable',
                tone: AppBadgeTone.success,
                uppercase: false,
              ),
            ),
          ],
        );
    }
  }

  Widget _buildClientsView() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildModuleHeader(
          eyebrow: 'Participantes',
          title: 'Gestion de participantes',
          subtitle: 'Completitud de datos y validaciones por reserva',
          subrouteLabels: const ['Resumen', 'Participantes', 'Historial'],
          currentSubrouteIndex: _participantsController.subroute.index,
          onSubrouteTap: _participantsController.selectSubrouteByIndex,
        ),
        const SizedBox(height: 20),
        _buildClientsSubrouteContent(),
      ],
    );
  }

  Widget _buildClientsSubrouteContent() {
    switch (_participantsController.subroute) {
      case ParticipantsSubroute.resumen:
        final pending = _participants
            .where((item) => !item.isComplete)
            .length
            .toString()
            .padLeft(2, '0');
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AppMetricCard(
              title: 'Participantes incompletos',
              value: pending,
              suffix: 'CASOS',
              tone: AppMetricCardTone.danger,
              icon: Icons.warning_amber_rounded,
            ),
            const SizedBox(height: 12),
            const AppEntityRowCard(
              title: 'Consentimientos',
              subtitle: 'Verifica antes de confirmar reserva',
              badge: AppBadge(
                label: 'Critico',
                tone: AppBadgeTone.warning,
                uppercase: false,
              ),
            ),
          ],
        );
      case ParticipantsSubroute.participantes:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int i = 0; i < _participants.length; i++) ...[
              AppEntityRowCard(
                title: _participants[i].fullName,
                subtitle:
                    'Reserva ${_participants[i].reservationCode} - Completitud ${_participants[i].completionLabel}',
                badge: AppBadge(
                  label: _participants[i].isComplete
                      ? 'Completo'
                      : 'Incompleto',
                  tone: _participants[i].isComplete
                      ? AppBadgeTone.success
                      : AppBadgeTone.warning,
                  uppercase: false,
                ),
              ),
              if (i != _participants.length - 1) const SizedBox(height: 10),
            ],
          ],
        );
      case ParticipantsSubroute.historial:
        return const AppTimeline(
          children: [
            AppTimelineItem(
              state: AppTimelineNodeState.completed,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 08:45',
                title: 'Consentimiento firmado',
                badge: AppBadge(label: 'OK', tone: AppBadgeTone.success),
                description: 'Reserva RV-1042 consolidada.',
              ),
            ),
            AppTimelineItem(
              state: AppTimelineNodeState.active,
              child: AppTimelineEntryCard(
                date: '24 Oct 2026 - 07:58',
                title: 'Documento pendiente',
                badge: AppBadge(label: 'Pendiente', tone: AppBadgeTone.warning),
                description: 'Falta identificacion de participante.',
              ),
            ),
          ],
        );
    }
  }

  Widget _buildMoreView() {
    switch (_moreDestination) {
      case _MoreDestination.menu:
        return _buildMoreMenu();
      case _MoreDestination.profile:
        return _buildProfileView();
      case _MoreDestination.contacts:
        return _buildContactsView();
      case _MoreDestination.changePassword:
        return _buildChangePasswordView();
    }
  }

  Widget _buildMoreMenu() {
    final statusBanners = _buildGlobalStatusBanners();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments([
          'Mas',
        ], currentLabel: 'Opciones adicionales'),
        const SizedBox(height: 12),
        ...statusBanners,
        if (statusBanners.isNotEmpty) const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Perfil',
          subtitle: 'Datos del usuario y estado de cuenta',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _openMoreDestination(_MoreDestination.profile),
        ),
        const SizedBox(height: 12),
        AppEntityRowCard(
          title: 'Contactos',
          subtitle: 'Numeros de emergencia',
          trailing: const Icon(Icons.chevron_right_rounded, size: 18),
          onTap: () => _openMoreDestination(_MoreDestination.contacts),
        ),
      ],
    );
  }

  Widget _buildProfileView() {
    final statusBanners = _buildGlobalStatusBanners();
    final user = widget.controller.currentUser;
    final statusBadge = _profileStatusBadge(widget.controller.authState);
    final isUserActive = user?.isActive ?? false;
    final createdAt =
        user?.createdAtRemote ?? user?.updatedAtRemote ?? user?.updatedAtLocal;
    final createdAtLabel = createdAt == null
        ? null
        : _formatMonthAndYear(createdAt);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Perfil',
        ], onBack: () => _openMoreDestination(_MoreDestination.menu)),
        const SizedBox(height: 12),
        ...statusBanners,
        if (statusBanners.isNotEmpty) const SizedBox(height: 12),
        if (user == null)
          const AppEntityRowCard(
            title: 'Perfil no disponible',
            subtitle: 'No hay datos de usuario en la sesion actual',
            badge: AppBadge(label: 'Sin datos', tone: AppBadgeTone.danger),
            selected: true,
          )
        else
          AppEntityRowCard(
            title: user.fullName,
            subtitle: createdAtLabel == null
                ? 'Perfil de usuario'
                : 'Creado en $createdAtLabel',
            selected: true,
            badge: statusBadge,
            trailing: const Icon(Icons.person_outline_rounded, size: 18),
          ),
        const SizedBox(height: 12),
        Center(
          child: Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              AppBadge(
                label: _roleBadgeLabel(user?.role),
                tone: AppBadgeTone.neutral,
                uppercase: false,
              ),
              AppBadge(
                label: isUserActive ? 'Cuenta activa' : 'Cuenta inactiva',
                tone: isUserActive
                    ? AppBadgeTone.success
                    : AppBadgeTone.warning,
                uppercase: false,
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        AppEntityRowCard(
          title: 'Correo principal',
          subtitle: user?.email ?? 'No disponible',
          leading: const Icon(Icons.mail_outline_rounded, size: 18),
        ),
        const SizedBox(height: 10),
        AppEntityRowCard(
          title: 'Telefono',
          subtitle: user?.phone ?? 'No registrado',
          leading: const Icon(Icons.phone_outlined, size: 18),
        ),
        const SizedBox(height: 16),
        AppButton(
          label: 'Cambiar contrasena',
          icon: Icons.lock_outline_rounded,
          expanded: true,
          onPressed: () =>
              _openMoreDestination(_MoreDestination.changePassword),
        ),
      ],
    );
  }

  Widget _buildChangePasswordView() {
    final isOnline =
        widget.controller.connectivityState != ConnectivityState.offline;
    final passwordsMatch = _newPasswordCtrl.text == _confirmPasswordCtrl.text;
    final canSubmit =
        isOnline &&
        !widget.controller.isLoading &&
        _currentPasswordCtrl.text.isNotEmpty &&
        _newPasswordCtrl.text.length >= 8 &&
        passwordsMatch;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Perfil',
          'Cambiar contrasena',
        ], onBack: () => _openMoreDestination(_MoreDestination.profile)),
        const SizedBox(height: 20),
        if (!isOnline) ...[
          const AppBadge(
            label: 'Requiere internet',
            tone: AppBadgeTone.warning,
            uppercase: false,
          ),
          const SizedBox(height: 12),
        ],
        AppTextField(
          controller: _currentPasswordCtrl,
          label: 'Contrasena actual',
          obscureText: _obscureCurrentPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureCurrentPassword = !_obscureCurrentPassword;
              });
            },
            icon: Icon(
              _obscureCurrentPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 10),
        AppTextField(
          controller: _newPasswordCtrl,
          label: 'Nueva contrasena',
          obscureText: _obscureNewPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureNewPassword = !_obscureNewPassword;
              });
            },
            icon: Icon(
              _obscureNewPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 10),
        AppTextField(
          controller: _confirmPasswordCtrl,
          label: 'Confirmar nueva',
          obscureText: _obscureConfirmPassword,
          suffix: IconButton(
            onPressed: () {
              setState(() {
                _obscureConfirmPassword = !_obscureConfirmPassword;
              });
            },
            icon: Icon(
              _obscureConfirmPassword
                  ? Icons.visibility_outlined
                  : Icons.visibility_off_outlined,
            ),
          ),
          onChanged: (_) => setState(() {}),
        ),
        if (!passwordsMatch && _confirmPasswordCtrl.text.isNotEmpty) ...[
          const SizedBox(height: 8),
          const AppBadge(
            label: 'Las contrasenas no coinciden',
            tone: AppBadgeTone.danger,
            uppercase: false,
          ),
        ],
        const SizedBox(height: 16),
        AppButton(
          label: widget.controller.isLoading ? 'Guardando...' : 'Guardar',
          expanded: true,
          onPressed: canSubmit ? _submitPasswordChange : null,
        ),
      ],
    );
  }

  Widget _buildContactsView() {
    _contactsFuture ??= _loadEmergencyContacts();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _RouteHeader.fromSegments(const [
          'Mas',
          'Contactos',
        ], onBack: () => _openMoreDestination(_MoreDestination.menu)),
        const SizedBox(height: 20),
        FutureBuilder<List<_EmergencyContact>>(
          future: _contactsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const AppEntityRowCard(
                title: 'Cargando contactos',
                subtitle: 'Consultando catalogo de emergencia',
                selected: true,
                trailing: SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              );
            }

            if (snapshot.hasError) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const AppEntityRowCard(
                    title: 'No se pudieron cargar los contactos',
                    subtitle: 'Revisa la conexion e intenta de nuevo',
                    badge: AppBadge(
                      label: 'Error de red',
                      tone: AppBadgeTone.danger,
                      uppercase: false,
                    ),
                    selected: true,
                  ),
                  const SizedBox(height: 12),
                  AppButton(
                    label: 'Reintentar',
                    variant: AppButtonVariant.ghost,
                    onPressed: () {
                      setState(() {
                        _contactsFuture = _loadEmergencyContacts();
                      });
                    },
                  ),
                ],
              );
            }

            final contacts = snapshot.data ?? const <_EmergencyContact>[];
            if (contacts.isEmpty) {
              return const AppEntityRowCard(
                title: 'Sin contactos disponibles',
                subtitle: 'No hay registros para mostrar',
                selected: true,
              );
            }

            return Column(
              children: [
                for (int i = 0; i < contacts.length; i++) ...[
                  AppEntityRowCard(
                    title: contacts[i].name,
                    subtitle: contacts[i].detail,
                    badge: AppBadge(
                      label: contacts[i].phone,
                      tone: contacts[i].tone,
                      uppercase: false,
                    ),
                    trailing: const Icon(Icons.call_outlined, size: 18),
                    onTap: () => _handleCallContact(contacts[i]),
                  ),
                  if (i != contacts.length - 1) const SizedBox(height: 10),
                ],
              ],
            );
          },
        ),
      ],
    );
  }

  List<Widget> _buildGlobalStatusBanners() {
    final banners = <Widget>[];
    final authState = widget.controller.authState;
    final connectivityState = widget.controller.connectivityState;

    if (connectivityState == ConnectivityState.offline) {
      banners.add(
        const AppStatusBanner(
          title: 'Sin conexion',
          message:
              'Se trabaja en modo local. Se sincronizara cuando regrese red.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.wifi_off_rounded,
          badgeLabel: 'Offline',
        ),
      );
    } else if (connectivityState == ConnectivityState.unstable) {
      banners.add(
        const AppStatusBanner(
          title: 'Conexion inestable',
          message:
              'Puede haber retrasos de sincronizacion en algunas acciones.',
          tone: AppStatusBannerTone.info,
          icon: Icons.network_check_rounded,
          badgeLabel: 'Inestable',
        ),
      );
    }

    if (widget.controller.hasPendingSync) {
      banners.add(
        const AppStatusBanner(
          title: 'Cambios pendientes',
          message: 'Hay actualizaciones locales esperando envio al backend.',
          tone: AppStatusBannerTone.warning,
          icon: Icons.sync_problem_rounded,
          badgeLabel: 'Pendiente',
        ),
      );
    }

    if (widget.controller.isOfflineRestricted) {
      banners.add(
        const AppStatusBanner(
          title: 'Sesion local',
          message:
              'Acciones criticas online-only estan temporalmente bloqueadas.',
          tone: AppStatusBannerTone.info,
          icon: Icons.lock_clock_outlined,
          badgeLabel: 'Modo local',
        ),
      );
    }

    if (authState == LocalAuthState.refreshRequired ||
        authState == LocalAuthState.invalid) {
      banners.add(
        AppStatusBanner(
          title: 'Sesion requiere validacion',
          message:
              'Verifica internet y actualiza sesion para habilitar acciones.',
          tone: AppStatusBannerTone.danger,
          icon: Icons.warning_amber_rounded,
          badgeLabel: 'Atencion',
          onTap: widget.controller.isLoading
              ? null
              : () {
                  widget.controller.refreshRequested();
                },
        ),
      );
    }

    return banners;
  }

  Widget _buildModuleHeader({
    required String eyebrow,
    required String title,
    required List<String> subrouteLabels,
    required int currentSubrouteIndex,
    required ValueChanged<int> onSubrouteTap,
    Widget? trailing,
    String? subtitle,
  }) {
    final banners = _buildGlobalStatusBanners();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AppSectionHeader(
          eyebrow: eyebrow,
          title: title,
          subtitle: subtitle,
          trailing: trailing,
        ),
        const SizedBox(height: 12),
        AppBreadcrumb(
          items: subrouteLabels,
          currentIndex: currentSubrouteIndex,
          onItemTap: onSubrouteTap,
        ),
        if (banners.isNotEmpty) ...[
          const SizedBox(height: 12),
          for (int i = 0; i < banners.length; i++) ...[
            banners[i],
            if (i != banners.length - 1) const SizedBox(height: 10),
          ],
        ],
      ],
    );
  }

  List<ReservationRecord> _filterReservations() {
    return _reservations
        .where((item) => item.status == _reservationsController.filterValue)
        .toList(growable: false);
  }

  Widget _buildReservationRow(
    ReservationRecord reservation, {
    required String subtitle,
    required bool highlightIfPending,
    bool openDetailsOnTap = false,
  }) {
    final syncBadge = reservation.hasSyncError
        ? const AppBadge(
            label: 'Sync error',
            tone: AppBadgeTone.danger,
            uppercase: false,
          )
        : reservation.hasPendingSync
        ? const AppBadge(
            label: 'Pendiente',
            tone: AppBadgeTone.warning,
            uppercase: false,
          )
        : const AppBadge(
            label: 'OK',
            tone: AppBadgeTone.success,
            uppercase: false,
          );

    return AppEntityRowCard(
      title: reservation.clientName,
      subtitle: '$subtitle - ${reservation.code}',
      selected: highlightIfPending && reservation.status == 'pendientes',
      badge: _reservationStatusBadge(reservation.status),
      trailing: syncBadge,
      onTap: openDetailsOnTap
          ? () => _openReservationDetail(reservation)
          : null,
    );
  }

  void _openReservationDetail(ReservationRecord reservation) {
    final participants = _participants
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    final paymentProofs = _paymentProofs
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);
    final assignments = _assignments
        .where((item) => item.reservationCode == reservation.code)
        .toList(growable: false);

    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => ReservationDetailScreen(
          reservation: reservation,
          participants: participants,
          paymentProofs: paymentProofs,
          assignments: assignments,
        ),
      ),
    );
  }

  AppBadge _reservationStatusBadge(String status) {
    switch (status) {
      case 'pendientes':
        return const AppBadge(
          label: 'Pendiente',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case 'confirmadas':
        return const AppBadge(
          label: 'Confirmada',
          tone: AppBadgeTone.primary,
          uppercase: false,
        );
      case 'finalizadas':
        return const AppBadge(
          label: 'Finalizada',
          tone: AppBadgeTone.success,
          uppercase: false,
        );
      default:
        return const AppBadge(
          label: 'Sin estado',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        );
    }
  }

  Future<List<_EmergencyContact>> _loadEmergencyContacts() async {
    final contacts = await _contactsApiClient.getEmergencyContacts();
    return contacts.map(_mapEmergencyContact).toList(growable: false);
  }

  Future<void> _handleCallContact(_EmergencyContact contact) async {
    final launched = await _onCallRequested(contact.phone);
    if (!mounted || launched) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('No se pudo abrir la app de llamadas')),
    );
  }

  Future<void> _submitPasswordChange() async {
    final previousErrorEventId = widget.controller.errorEventId;
    final previousNoticeEventId = widget.controller.noticeEventId;
    await widget.controller.changePasswordSubmitted(
      currentPassword: _currentPasswordCtrl.text,
      newPassword: _newPasswordCtrl.text,
    );
    if (!mounted) return;

    if (widget.controller.errorEventId > previousErrorEventId) {
      final message =
          widget.controller.errorMessage ??
          widget.controller.messageForCode(widget.controller.errorCode) ??
          'No se pudo actualizar la contrasena';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      return;
    }

    if (widget.controller.noticeEventId > previousNoticeEventId) {
      final message =
          widget.controller.noticeMessage ??
          widget.controller.messageForCode(widget.controller.noticeCode) ??
          'Contrasena actualizada.';
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      widget.controller.clearNotice();
      _currentPasswordCtrl.clear();
      _newPasswordCtrl.clear();
      _confirmPasswordCtrl.clear();
      setState(() {});
    }
  }

  Future<bool> _callNativeDialer(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (!await canLaunchUrl(uri)) return false;
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  _EmergencyContact _mapEmergencyContact(EmergencyCatalogContactDto contact) {
    return _EmergencyContact(
      code: contact.code,
      name: contact.name,
      phone: contact.phoneNumber,
      detail: contact.description,
      tone: _toneForCategory(contact.category, contact.isPrimary),
    );
  }

  AppBadgeTone _toneForCategory(String category, bool isPrimary) {
    if (!isPrimary) return AppBadgeTone.neutral;
    switch (category) {
      case 'health':
        return AppBadgeTone.success;
      case 'security':
        return AppBadgeTone.danger;
      case 'disaster':
        return AppBadgeTone.warning;
      default:
        return AppBadgeTone.primary;
    }
  }

  String _roleBadgeLabel(String? role) {
    if (role == null || role.trim().isEmpty) return 'Sin rol';
    if (role.toLowerCase() == 'unassigned') return 'Sin rol';
    return role;
  }

  String _formatMonthAndYear(DateTime value) {
    final local = value.toLocal();
    final month = _monthShortLabels[local.month - 1];
    return '$month ${local.year}';
  }

  AppBadge _profileStatusBadge(LocalAuthState authState) {
    switch (authState) {
      case LocalAuthState.signedInVerified:
        return const AppBadge(
          label: 'En linea',
          tone: AppBadgeTone.success,
          uppercase: false,
        );
      case LocalAuthState.signedInLocalUnverified:
        return const AppBadge(
          label: 'Modo local',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case LocalAuthState.refreshRequired:
        return const AppBadge(
          label: 'Requiere internet',
          tone: AppBadgeTone.warning,
          uppercase: false,
        );
      case LocalAuthState.invalid:
        return const AppBadge(
          label: 'Sesion expirada',
          tone: AppBadgeTone.danger,
          uppercase: false,
        );
      case LocalAuthState.signedOut:
        return const AppBadge(
          label: 'Sin sesion',
          tone: AppBadgeTone.neutral,
          uppercase: false,
        );
    }
  }
}

class _RouteHeader extends StatelessWidget {
  const _RouteHeader({
    required this.sectionLabel,
    required this.currentLabel,
    this.onBack,
  });

  factory _RouteHeader.fromSegments(
    List<String> segments, {
    String? currentLabel,
    VoidCallback? onBack,
  }) {
    final sectionLabel = segments.length == 1
        ? segments.first
        : _joinSegments(segments);
    return _RouteHeader(
      sectionLabel: sectionLabel,
      currentLabel: currentLabel ?? segments.last,
      onBack: onBack,
    );
  }

  final String sectionLabel;
  final String currentLabel;
  final VoidCallback? onBack;

  static String _joinSegments(List<String> segments) {
    return segments.sublist(0, segments.length - 1).join(' > ');
  }

  @override
  Widget build(BuildContext context) {
    return AppSectionHeader(
      eyebrow: sectionLabel,
      title: currentLabel,
      trailing: onBack == null
          ? null
          : AppButton(
              label: 'Volver',
              icon: Icons.arrow_back_rounded,
              onPressed: onBack,
              variant: AppButtonVariant.ghost,
            ),
    );
  }
}

class _EmergencyContact {
  const _EmergencyContact({
    required this.code,
    required this.name,
    required this.phone,
    required this.detail,
    required this.tone,
  });

  final String code;
  final String name;
  final String phone;
  final String detail;
  final AppBadgeTone tone;
}

class _EquineRecord {
  const _EquineRecord({
    required this.name,
    required this.summary,
    required this.statusLabel,
    required this.statusTone,
  });

  final String name;
  final String summary;
  final String statusLabel;
  final AppBadgeTone statusTone;
}
