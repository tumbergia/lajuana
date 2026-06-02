import '../../domain/models/saddle_list_item.dart';
import '../../presentation/models/saddle_view_models.dart';

/// Domain -> ViewModel: SaddleListItem -> SaddleRecord
SaddleRecord listItemToRecord(SaddleListItem item) {
  return SaddleRecord(
    id: item.id,
    code: item.code,
    name: item.name ?? 'Sin nombre',
    isAvailable: item.isAvailable,
    notes: item.notes,
    isDeleted: item.isDeleted,
  );
}
