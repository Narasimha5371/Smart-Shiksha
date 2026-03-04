import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/app.dart';
import 'package:smart_shiksha/services/auth_service.dart';
import 'package:smart_shiksha/services/localization_service.dart';
import 'package:smart_shiksha/services/theme_service.dart';
import 'package:smart_shiksha/core/platform_init.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize sqflite FFI for desktop platforms (Windows, Linux, macOS).
  if (!kIsWeb) {
    initDesktopDatabase();
  }

  // Load saved preferences before building the widget tree.
  final locService = LocalizationService();
  await locService.load();

  final themeService = ThemeService();
  await themeService.load();

  final authService = AuthService();
  await authService.load();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: locService),
        ChangeNotifierProvider.value(value: themeService),
        ChangeNotifierProvider.value(value: authService),
      ],
      child: const SmartShikshaApp(),
    ),
  );
}
