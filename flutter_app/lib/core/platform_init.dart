/// Platform-specific database initialization.
/// Uses conditional export so dart:io is never imported on web.
library;
export 'platform_init_stub.dart'
    if (dart.library.io) 'platform_init_native.dart';
