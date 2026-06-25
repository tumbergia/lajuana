import 'dart:io' show Platform;

import 'package:sqflite_common_ffi/sqflite_ffi.dart';

bool _factoryInitialized = false;

Future<void> ensureDatabaseFactoryInitialized() async {
  if (_factoryInitialized) return;
  if (Platform.isLinux || Platform.isWindows || Platform.isMacOS) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  }
  _factoryInitialized = true;
}
