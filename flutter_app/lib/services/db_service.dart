// Conditional export: real SQLite on native, no-op on web.
export 'db_service_stub.dart'
    if (dart.library.io) 'db_service_native.dart';
