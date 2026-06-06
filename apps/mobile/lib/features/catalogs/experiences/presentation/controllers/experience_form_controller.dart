import 'package:flutter/foundation.dart';

import 'package:mobile/features/catalogs/experiences/domain/experience.dart';

class ExperiencePricingTierDraft {
  ExperiencePricingTierDraft({
    required this.minParticipants,
    required this.maxParticipants,
    required this.pricePerPerson,
  });

  int minParticipants;
  int maxParticipants;
  int pricePerPerson;
}

class ExperienceFormController extends ChangeNotifier {
  String nombre = '';
  String identificadorUrl = '';
  String descripcion = '';
  String? imageBase64;

  String nivel = 'basic';
  String dificultad = 'basic';
  bool activa = true;

  int? duracionExperienciaMinutos;
  int? duracionRecorridoMinutos;
  String? textoDuracionVisible;

  double? distanciaKm;
  String terreno = '';
  String? notasTerreno;

  String moneda = 'COP';
  bool tarifasNetas = true;
  String? notasTarifa;
  final List<ExperiencePricingTierDraft> tarifas =
      <ExperiencePricingTierDraft>[];

  final List<String> incluye = <String>[];
  String? textoIncluyeVisible;

  void loadFromExperience(CatalogExperience value) {
    nombre = value.name;
    identificadorUrl = value.slug;
    descripcion = value.description;
    imageBase64 = value.imageBase64;
    nivel = value.level;
    dificultad = value.difficulty ?? value.level;
    activa = value.isActive;

    duracionExperienciaMinutos = value.duration?.activityMinutes;
    duracionRecorridoMinutos = value.duration?.routeMinutes;
    textoDuracionVisible = value.duration?.displayText;

    distanciaKm = value.routeDetails?.distanceKm;
    terreno = value.routeDetails?.terrain ?? '';
    notasTerreno = value.routeDetails?.terrainNotes;

    moneda = value.pricing?.currency ?? 'COP';
    tarifasNetas = value.pricing?.pricesAreNet ?? true;
    notasTarifa = value.pricing?.pricingNotes;
    tarifas
      ..clear()
      ..addAll(
        (value.pricing?.tiers ?? const <CatalogExperiencePricingTier>[]).map(
          (tier) => ExperiencePricingTierDraft(
            minParticipants: tier.minParticipants,
            maxParticipants: tier.maxParticipants,
            pricePerPerson: tier.pricePerPerson,
          ),
        ),
      );

    incluye
      ..clear()
      ..addAll(value.inclusions?.items ?? const <String>[]);
    textoIncluyeVisible = value.inclusions?.displayText;
  }

  String? validar() {
    if (nombre.trim().isEmpty) return 'Escribe el nombre de la experiencia.';
    if (descripcion.trim().isEmpty) return 'Escribe una descripcion.';
    if ((duracionExperienciaMinutos ?? 0) <= 0) {
      return 'Ingresa la duracion de la experiencia en minutos.';
    }
    if ((duracionRecorridoMinutos ?? 0) <= 0) {
      return 'Ingresa la duracion del recorrido en minutos.';
    }
    if (duracionRecorridoMinutos! > duracionExperienciaMinutos!) {
      return 'La duracion del recorrido no puede ser mayor a la experiencia.';
    }
    if (tarifas.isEmpty) {
      return 'Agrega al menos una tarifa por cantidad de personas.';
    }
    final ordenadas = List<ExperiencePricingTierDraft>.from(tarifas)
      ..sort((a, b) => a.minParticipants.compareTo(b.minParticipants));
    ExperiencePricingTierDraft? previa;
    for (final tarifa in ordenadas) {
      if (tarifa.minParticipants > tarifa.maxParticipants) {
        return 'Hay una tarifa con rango invalido.';
      }
      if (previa != null && tarifa.minParticipants <= previa.maxParticipants) {
        return 'Los rangos de tarifas no pueden superponerse.';
      }
      previa = tarifa;
    }
    return null;
  }

  void actualizarNombre(String value) {
    nombre = value;
    if (identificadorUrl.trim().isEmpty) {
      identificadorUrl = _slugify(value);
    }
    notifyListeners();
  }

  void actualizarDescripcion(String value) {
    descripcion = value;
    notifyListeners();
  }

  void actualizarImageBase64(String? value) {
    imageBase64 = value;
    notifyListeners();
  }

  void actualizarNivel(String value) {
    nivel = value;
    notifyListeners();
  }

  void actualizarDificultad(String value) {
    dificultad = value;
    notifyListeners();
  }

  void actualizarActiva(bool value) {
    activa = value;
    notifyListeners();
  }

  void actualizarDuracionExperiencia(int? value) {
    duracionExperienciaMinutos = value;
    notifyListeners();
  }

  void actualizarDuracionRecorrido(int? value) {
    duracionRecorridoMinutos = value;
    notifyListeners();
  }

  void actualizarTextoDuracionVisible(String value) {
    textoDuracionVisible = _nullable(value);
    notifyListeners();
  }

  void actualizarDistanciaKm(double? value) {
    distanciaKm = value;
    notifyListeners();
  }

  void actualizarTerreno(String value) {
    terreno = value;
    notifyListeners();
  }

  void actualizarNotasTerreno(String value) {
    notasTerreno = _nullable(value);
    notifyListeners();
  }

  void actualizarMoneda(String value) {
    moneda = value.trim().toUpperCase();
    notifyListeners();
  }

  void actualizarTarifasNetas(bool value) {
    tarifasNetas = value;
    notifyListeners();
  }

  void actualizarNotasTarifa(String value) {
    notasTarifa = _nullable(value);
    notifyListeners();
  }

  void actualizarTextoIncluyeVisible(String value) {
    textoIncluyeVisible = _nullable(value);
    notifyListeners();
  }

  void agregarTarifa(ExperiencePricingTierDraft value) {
    tarifas.add(value);
    notifyListeners();
  }

  void actualizarTarifa(int index, ExperiencePricingTierDraft value) {
    if (index < 0 || index >= tarifas.length) return;
    tarifas[index] = value;
    notifyListeners();
  }

  void eliminarTarifa(int index) {
    if (index < 0 || index >= tarifas.length) return;
    tarifas.removeAt(index);
    notifyListeners();
  }

  void agregarIncluye(String value) {
    final cleaned = value.trim();
    if (cleaned.isEmpty) return;
    incluye.add(cleaned);
    notifyListeners();
  }

  void eliminarIncluye(int index) {
    if (index < 0 || index >= incluye.length) return;
    incluye.removeAt(index);
    notifyListeners();
  }

  CatalogExperienceDuration buildDuration() {
    return CatalogExperienceDuration(
      activityMinutes: duracionExperienciaMinutos!,
      routeMinutes: duracionRecorridoMinutos!,
      displayText: textoDuracionVisible,
    );
  }

  CatalogExperienceRouteDetails? buildRouteDetails() {
    if (terreno.trim().isEmpty && distanciaKm == null && notasTerreno == null) {
      return null;
    }
    return CatalogExperienceRouteDetails(
      distanceKm: distanciaKm,
      terrain: terreno.trim().isEmpty ? 'No especificado' : terreno.trim(),
      terrainNotes: notasTerreno,
    );
  }

  CatalogExperiencePricing buildPricing() {
    return CatalogExperiencePricing(
      currency: moneda.trim().isEmpty ? 'COP' : moneda,
      pricesAreNet: tarifasNetas,
      pricingNotes: notasTarifa,
      tiers: tarifas
          .map(
            (tier) => CatalogExperiencePricingTier(
              minParticipants: tier.minParticipants,
              maxParticipants: tier.maxParticipants,
              pricePerPerson: tier.pricePerPerson,
            ),
          )
          .toList(growable: false),
    );
  }

  CatalogExperienceInclusions? buildInclusions() {
    final hasItems = incluye.isNotEmpty;
    final hasDisplayText = textoIncluyeVisible != null && textoIncluyeVisible!.isNotEmpty;
    if (!hasItems && !hasDisplayText) return null;
    return CatalogExperienceInclusions(
      items: hasItems ? List<String>.from(incluye) : <String>[],
      displayText: textoIncluyeVisible,
    );
  }

  String _slugify(String value) {
    final lowered = value.toLowerCase().trim();
    return lowered
        .replaceAll(RegExp(r'[^a-z0-9\s-]'), '')
        .replaceAll(RegExp(r'\s+'), '-')
        .replaceAll(RegExp(r'-+'), '-');
  }

  String? _nullable(String value) {
    final trimmed = value.trim();
    return trimmed.isEmpty ? null : trimmed;
  }
}
