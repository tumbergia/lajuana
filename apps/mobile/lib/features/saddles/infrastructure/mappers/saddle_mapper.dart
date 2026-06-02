import '../../domain/models/saddle_list_item.dart';
import '../../presentation/models/saddle_view_models.dart';
import '../remote/saddle_dtos.dart';

/// DTO -> Domain: SaddleDto -> SaddleListItem
SaddleListItem dtoToListItem(SaddleDto dto) {
  return SaddleListItem(
    id: dto.id,
    code: dto.code,
    name: dto.name,
    isAvailable: dto.isAvailable,
    notes: dto.notes,
    isDeleted: dto.deletedAt != null,
  );
}

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

/// Maps DTO directly to a ViewModel for convenience (e.g., after create/update).
SaddleRecord dtoToRecord(SaddleDto dto) {
  return SaddleRecord(
    id: dto.id,
    code: dto.code,
    name: dto.name ?? 'Sin nombre',
    isAvailable: dto.isAvailable,
    notes: dto.notes,
    isDeleted: dto.deletedAt != null,
  );
}
