import 'package:flutter/material.dart';

import 'package:mobile_ui/src/widgets/app_button.dart';
import 'package:mobile_ui/src/widgets/app_centered_loader.dart';
import 'package:mobile_ui/src/widgets/app_confirm_dialog.dart';
import 'package:mobile_ui/src/widgets/app_text_field.dart';
import 'package:mobile_ui/src/widgets/app_toast.dart';
import 'package:mobile_ui/src/widgets/refresh_scope.dart';
import 'package:mobile_domain/src/reservations/reservation_provider_item.dart';

import 'package:mobile/features/reservations/presentation/controllers/reservation_providers_section_controller.dart';
import 'package:mobile/features/reservations/presentation/widgets/provider_reservation_card.dart';
import 'package:mobile/features/reservations/presentation/widgets/reservation_provider_detail_view.dart';

class ReservationProvidersTab extends StatelessWidget {
  const ReservationProvidersTab({
    super.key,
    required this.controller,
    required this.isAdmin,
    required this.emptyState,
  });

  final ReservationProvidersSectionController controller;
  final bool isAdmin;
  final Widget emptyState;

  void _openProviderDetail(BuildContext context, ReservationProviderItem item) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (detailContext) => ReservationProviderDetailView(
          item: item,
          isAdmin: isAdmin,
          onEdit: () {
            Navigator.of(detailContext).pop();
            _showEditDialog(context, item);
          },
          onRemove: () {
            Navigator.of(detailContext).pop();
            _confirmRemove(context, item);
          },
        ),
      ),
    );
  }

  Future<void> _showAddDialog(BuildContext context) async {
    final serviceController = TextEditingController();
    final notesController = TextEditingController();
    List<ProviderCatalogItem> catalog = const [];
    String? selectedProviderId;
    var loadingCatalog = true;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            if (loadingCatalog) {
              controller.loadCatalog().then((items) {
                setSheetState(() {
                  catalog = items
                      .where((item) => item.status != 'needs_review')
                      .toList(growable: false);
                  loadingCatalog = false;
                });
              });
            }

            return Padding(
              padding: EdgeInsets.only(
                left: 24,
                right: 24,
                top: 24,
                bottom: MediaQuery.viewInsetsOf(context).bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Asociar proveedor',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 16),
                  if (loadingCatalog)
                    const AppCenteredLoader(fill: false)
                  else ...[
                    DropdownButtonFormField<String>(
                      value: selectedProviderId,
                      decoration: const InputDecoration(
                        labelText: 'Proveedor',
                        border: OutlineInputBorder(),
                      ),
                      items: catalog
                          .map(
                            (item) => DropdownMenuItem(
                              value: item.id,
                              child: Text(item.name),
                            ),
                          )
                          .toList(growable: false),
                      onChanged: (value) {
                        setSheetState(() => selectedProviderId = value);
                      },
                    ),
                    const SizedBox(height: 12),
                    AppTextField(
                      controller: serviceController,
                      label: 'Servicio requerido',
                    ),
                    const SizedBox(height: 12),
                    AppTextField(
                      controller: notesController,
                      label: 'Notas',
                      maxLines: 3,
                    ),
                    const SizedBox(height: 20),
                    Center(
                      child: AppButton(
                        label: 'Asociar',
                        icon: Icons.link_rounded,
                        onPressed: selectedProviderId == null
                            ? null
                            : () async {
                                final ok = await controller.addProvider(
                                  providerId: selectedProviderId!,
                                  serviceLabel:
                                      serviceController.text.trim().isEmpty
                                      ? null
                                      : serviceController.text.trim(),
                                  notes: notesController.text.trim().isEmpty
                                      ? null
                                      : notesController.text.trim(),
                                );
                                if (!context.mounted) return;
                                if (ok) {
                                  Navigator.of(sheetContext).pop();
                                } else {
                                  showAppToast(
                                    context,
                                    message:
                                        controller.errorMessage ??
                                        'No se pudo asociar',
                                    isError: true,
                                  );
                                }
                              },
                      ),
                    ),
                  ],
                ],
              ),
            );
          },
        );
      },
    );

    serviceController.dispose();
    notesController.dispose();
  }

  Future<void> _showEditDialog(
    BuildContext context,
    ReservationProviderItem item,
  ) async {
    final serviceController = TextEditingController(
      text: item.serviceLabel ?? '',
    );
    final notesController = TextEditingController(text: item.notes ?? '');
    var status = item.status;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 24,
                right: 24,
                top: 24,
                bottom: MediaQuery.viewInsetsOf(context).bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    item.providerName,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 16),
                  AppTextField(
                    controller: serviceController,
                    label: 'Servicio requerido',
                  ),
                  const SizedBox(height: 12),
                  AppTextField(
                    controller: notesController,
                    label: 'Notas',
                    maxLines: 3,
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: status,
                    decoration: const InputDecoration(
                      labelText: 'Estado',
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'pending',
                        child: Text('Pendiente'),
                      ),
                      DropdownMenuItem(
                        value: 'contacted',
                        child: Text('Contactado'),
                      ),
                      DropdownMenuItem(
                        value: 'confirmed',
                        child: Text('Confirmado'),
                      ),
                      DropdownMenuItem(
                        value: 'cancelled',
                        child: Text('Cancelado'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value != null) setSheetState(() => status = value);
                    },
                  ),
                  const SizedBox(height: 20),
                  Center(
                    child: AppButton(
                      label: 'Guardar',
                      icon: Icons.save_rounded,
                      onPressed: () async {
                        final ok = await controller.updateProvider(
                          reservationProviderId: item.reservationProviderId,
                          serviceLabel: serviceController.text.trim(),
                          notes: notesController.text.trim(),
                          status: status,
                        );
                        if (!context.mounted) return;
                        if (ok) {
                          Navigator.of(sheetContext).pop();
                        } else {
                          showAppToast(
                            context,
                            message:
                                controller.errorMessage ?? 'No se pudo guardar',
                            isError: true,
                          );
                        }
                      },
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );

    serviceController.dispose();
    notesController.dispose();
  }

  Future<void> _confirmRemove(
    BuildContext context,
    ReservationProviderItem item,
  ) async {
    await AppConfirmDialog.show(
      context: context,
      icon: Icons.delete_outline_rounded,
      title: 'Quitar proveedor',
      message: 'Se eliminara la asociacion con ${item.providerName}.',
      confirmLabel: 'Quitar',
      style: DialogStyle.danger,
      onConfirm: () async {
        final ok = await controller.removeProvider(item.reservationProviderId);
        if (!context.mounted) return;
        showAppToast(
          context,
          message: ok
              ? 'Proveedor quitado'
              : (controller.errorMessage ?? 'No se pudo quitar'),
          isError: !ok,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    switch (controller.state) {
      case ReservationProvidersLoadState.initial:
      case ReservationProvidersLoadState.loading:
        return const RefreshableViewport(child: AppCenteredLoader());
      case ReservationProvidersLoadState.error:
        return RefreshableViewport(
          child: Center(
            child: Text(
              controller.errorMessage ?? 'Error al cargar proveedores',
            ),
          ),
        );
      case ReservationProvidersLoadState.loaded:
      case ReservationProvidersLoadState.saving:
        if (controller.items.isEmpty) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (isAdmin)
                AppButton(
                  label: 'Agregar proveedor',
                  icon: Icons.add_rounded,
                  expanded: true,
                  onPressed:
                      controller.state == ReservationProvidersLoadState.saving
                      ? null
                      : () => _showAddDialog(context),
                ),
              if (isAdmin) const SizedBox(height: 16),
              Expanded(child: RefreshableViewport(child: emptyState)),
            ],
          );
        }
        return ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.only(bottom: 24),
          children: [
            if (isAdmin)
              AppButton(
                label: 'Agregar proveedor',
                icon: Icons.add_rounded,
                expanded: true,
                onPressed:
                    controller.state == ReservationProvidersLoadState.saving
                    ? null
                    : () => _showAddDialog(context),
              ),
            if (isAdmin) const SizedBox(height: 16),
            ...controller.items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: ProviderReservationCard(
                  item: item,
                  onTap: () => _openProviderDetail(context, item),
                ),
              ),
            ),
          ],
        );
    }
  }
}
