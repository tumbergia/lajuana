import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/catalogs/experiences/domain/experience.dart';
import 'package:mobile/features/catalogs/experiences/presentation/controllers/experience_form_controller.dart';

import 'data/catalog_sync_status_helpers.dart';

void main() {
  late ExperienceFormController controller;

  setUp(() {
    controller = ExperienceFormController();
  });

  tearDown(() {
    controller.dispose();
  });

  group('initial state', () {
    test('starts with default values', () {
      expect(controller.nombre, '');
      expect(controller.identificadorUrl, '');
      expect(controller.descripcion, '');
      expect(controller.imageBase64, isNull);
      expect(controller.activa, true);
      expect(controller.nivel, 'basic');
      expect(controller.dificultad, 'basic');
      expect(controller.moneda, 'COP');
      expect(controller.tarifasNetas, true);
      expect(controller.tarifas, isEmpty);
      expect(controller.incluye, isEmpty);
    });
  });

  group('validar', () {
    test('fails when name is empty', () {
      controller.nombre = '';
      final error = controller.validar();
      expect(error, contains('nombre'));
    });

    test('does not require URL slug when other fields are valid', () {
      controller.nombre = 'Test Experience';
      controller.identificadorUrl = '';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = 60;
      controller.duracionRecorridoMinutos = 30;
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 5,
        pricePerPerson: 50000,
      ));
      final error = controller.validar();
      expect(error, isNull);
    });

    test('fails when description is empty', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = '';
      final error = controller.validar();
      expect(error, contains('descripcion'));
    });

    test('fails when duration is not set', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = null;
      final error = controller.validar();
      expect(error, contains('duracion'));
    });

    test('fails when route duration exceeds experience duration', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = 60;
      controller.duracionRecorridoMinutos = 90;
      final error = controller.validar();
      expect(error, contains('recorrido'));
    });

    test('fails when no pricing tiers are added', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = 60;
      controller.duracionRecorridoMinutos = 30;
      final error = controller.validar();
      expect(error, contains('tarifa'));
    });

    test('fails when pricing tiers have overlapping ranges', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = 60;
      controller.duracionRecorridoMinutos = 30;
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 5,
        pricePerPerson: 50000,
      ));
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 3,
        maxParticipants: 10,
        pricePerPerson: 40000,
      ));
      final error = controller.validar();
      expect(error, contains('superponerse'));
    });

    test('passes without inclusion items', () {
      controller.nombre = 'Test';
      controller.identificadorUrl = 'test';
      controller.descripcion = 'A test';
      controller.duracionExperienciaMinutos = 60;
      controller.duracionRecorridoMinutos = 30;
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 5,
        pricePerPerson: 50000,
      ));
      final error = controller.validar();
      expect(error, isNull);
    });

    test('passes with all valid fields', () {
      controller.nombre = 'Cabalgata Aventura';
      controller.identificadorUrl = 'cabalgata-aventura';
      controller.descripcion = 'Una experiencia increíble';
      controller.duracionExperienciaMinutos = 120;
      controller.duracionRecorridoMinutos = 60;
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 5,
        pricePerPerson: 80000,
      ));
      controller.agregarIncluye('Guía certificado');
      controller.agregarIncluye('Equipo de seguridad');

      final error = controller.validar();
      expect(error, isNull);
    });
  });

  group('mutators', () {
    test('actualizarNombre sets nombre and auto-generates slug', () {
      controller.actualizarNombre('Cabalgata Aventura');
      expect(controller.nombre, 'Cabalgata Aventura');
      expect(controller.identificadorUrl, 'cabalgata-aventura');
    });

    test('actualizarNombre does not override existing slug', () {
      controller.identificadorUrl = 'custom-slug';
      controller.actualizarNombre('New Name');
      expect(controller.identificadorUrl, 'custom-slug');
    });

    test('actualizarNivel changes nivel', () {
      controller.actualizarNivel('advanced');
      expect(controller.nivel, 'advanced');
    });

    test('actualizarActiva toggles active state', () {
      controller.actualizarActiva(false);
      expect(controller.activa, false);

      controller.actualizarActiva(true);
      expect(controller.activa, true);
    });

    test('agregarTarifa adds pricing tier', () {
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 10,
        pricePerPerson: 50000,
      ));
      expect(controller.tarifas.length, 1);
      expect(controller.tarifas.first.pricePerPerson, 50000);
    });

    test('eliminarTarifa removes pricing tier by index', () {
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 5,
        pricePerPerson: 50000,
      ));
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 6,
        maxParticipants: 10,
        pricePerPerson: 40000,
      ));
      expect(controller.tarifas.length, 2);

      controller.eliminarTarifa(0);
      expect(controller.tarifas.length, 1);
      expect(controller.tarifas.first.minParticipants, 6);
    });

    test('eliminarTarifa with invalid index does nothing', () {
      controller.eliminarTarifa(-1);
      controller.eliminarTarifa(99);
      expect(controller.tarifas, isEmpty);
    });

    test('agregarIncluye adds inclusion item', () {
      controller.agregarIncluye('Guía');
      expect(controller.incluye, ['Guía']);
    });

    test('agregarIncluye ignores empty string', () {
      controller.agregarIncluye('  ');
      expect(controller.incluye, isEmpty);
    });

    test('eliminarIncluye removes item by index', () {
      controller.agregarIncluye('A');
      controller.agregarIncluye('B');
      controller.eliminarIncluye(0);
      expect(controller.incluye, ['B']);
    });
  });

  group('loadFromExperience', () {
    test('loads all fields from a CatalogExperience', () {
      final experience = CatalogExperience(
        id: 'exp-1',
        name: 'Cabalgata Aventura',
        slug: 'cabalgata-aventura',
        description: 'Una aventura ecuestre',
        level: 'advanced',
        difficulty: 'intermediate',
        isActive: true,
        syncStatus: catalogSyncStatusSynced,
        subtitle: 'Para expertos',
        imageUrl: 'https://example.com/img.jpg',
        duration: const CatalogExperienceDuration(
          activityMinutes: 120,
          routeMinutes: 60,
          displayText: '2 horas',
        ),
        routeDetails: const CatalogExperienceRouteDetails(
          distanceKm: 10.0,
          terrain: 'Montaña',
          terrainNotes: 'Terreno irregular',
        ),
        pricing: CatalogExperiencePricing(
          currency: 'USD',
          pricesAreNet: false,
          pricingNotes: 'Incluye equipo',
          tiers: [
            const CatalogExperiencePricingTier(
              minParticipants: 1,
              maxParticipants: 5,
              pricePerPerson: 100,
            ),
          ],
        ),
        inclusions: const CatalogExperienceInclusions(
          items: ['Guía', 'Casco'],
          displayText: 'Incluye:',
        ),
        tags: const ['aventura', 'caballo'],
      );

      controller.loadFromExperience(experience);

      expect(controller.nombre, 'Cabalgata Aventura');
      expect(controller.identificadorUrl, 'cabalgata-aventura');
      expect(controller.nivel, 'advanced');
      expect(controller.dificultad, 'intermediate');
      expect(controller.duracionExperienciaMinutos, 120);
      expect(controller.duracionRecorridoMinutos, 60);
      expect(controller.moneda, 'USD');
      expect(controller.tarifasNetas, false);
      expect(controller.tarifas.length, 1);
      expect(controller.incluye, ['Guía', 'Casco']);
    });
  });

  group('builders', () {
    test('buildDuration returns correct duration', () {
      controller.duracionExperienciaMinutos = 120;
      controller.duracionRecorridoMinutos = 60;
      controller.textoDuracionVisible = '2 horas';

      final duration = controller.buildDuration();
      expect(duration.activityMinutes, 120);
      expect(duration.routeMinutes, 60);
      expect(duration.displayText, '2 horas');
    });

    test('buildPricing returns correct pricing', () {
      controller.moneda = 'COP';
      controller.tarifasNetas = true;
      controller.notasTarifa = 'Nota test';
      controller.agregarTarifa(ExperiencePricingTierDraft(
        minParticipants: 1,
        maxParticipants: 10,
        pricePerPerson: 50000,
      ));

      final pricing = controller.buildPricing();
      expect(pricing.currency, 'COP');
      expect(pricing.pricesAreNet, true);
      expect(pricing.pricingNotes, 'Nota test');
      expect(pricing.tiers.length, 1);
    });

    test('buildRouteDetails returns null when all fields empty', () {
      controller.terreno = '';
      controller.distanciaKm = null;
      controller.notasTerreno = null;

      final details = controller.buildRouteDetails();
      expect(details, isNull);
    });

    test('buildRouteDetails returns details with defaults', () {
      controller.terreno = 'Plano';
      final details = controller.buildRouteDetails();
      expect(details, isNotNull);
      expect(details!.terrain, 'Plano');
    });
  });

  group('slugify', () {
    test('converts name to URL-friendly slug', () {
      controller.actualizarNombre('Cabalgata Aventura Extrema!');
      // slug is auto-generated
      expect(controller.identificadorUrl, 'cabalgata-aventura-extrema');
    });
  });
}
