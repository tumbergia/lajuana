import 'package:sqflite/sqflite.dart';
import 'package:sqflite_common_ffi_web/sqflite_ffi_web.dart';

bool _factoryInitialized = false;

Future<void> ensureDatabaseFactoryInitialized() async {
  if (_factoryInitialized) return;
  databaseFactory = databaseFactoryFfiWebNoWebWorker;
  _factoryInitialized = true;
}
