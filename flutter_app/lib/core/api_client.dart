import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:smart_shiksha/core/constants.dart';
import 'package:smart_shiksha/core/platform_check.dart';

/// Returns the correct API base URL for the current platform.
String getApiBaseUrl() {
  if (kIsWeb) return 'http://localhost:8001/api';
  if (isAndroidPlatform()) return AppConstants.apiBaseUrl; // 10.0.2.2
  return AppConstants.apiBaseUrlDesktop; // iOS simulator / desktop
}
