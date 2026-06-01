/// Nivel de experiencia recomendado para el equino.
enum EquineExperienceFit {
  beginner,
  intermediate,
  advanced,
  all,
  staffOnly,
  notAssignable;

  static EquineExperienceFit fromApi(String value) {
    switch (value) {
      case 'beginner':
        return EquineExperienceFit.beginner;
      case 'intermediate':
        return EquineExperienceFit.intermediate;
      case 'advanced':
        return EquineExperienceFit.advanced;
      case 'all':
        return EquineExperienceFit.all;
      case 'staff_only':
        return EquineExperienceFit.staffOnly;
      case 'not_assignable':
        return EquineExperienceFit.notAssignable;
      default:
        return EquineExperienceFit.all;
    }
  }
}
