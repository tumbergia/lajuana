enum CatalogScheduleStatus { open, closed, full }

CatalogScheduleStatus parseCatalogScheduleStatus(String raw) {
  switch (raw) {
    case 'open':
      return CatalogScheduleStatus.open;
    case 'closed':
      return CatalogScheduleStatus.closed;
    case 'full':
      return CatalogScheduleStatus.full;
    default:
      return CatalogScheduleStatus.open;
  }
}

String catalogScheduleStatusToApi(CatalogScheduleStatus value) =>
    switch (value) {
      CatalogScheduleStatus.open => 'open',
      CatalogScheduleStatus.closed => 'closed',
      CatalogScheduleStatus.full => 'full',
    };
