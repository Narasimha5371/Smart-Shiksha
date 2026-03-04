import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:smart_shiksha/core/theme.dart';
import 'package:smart_shiksha/services/auth_service.dart';
import 'package:smart_shiksha/services/localization_service.dart';
import 'package:smart_shiksha/services/theme_service.dart';
import 'package:smart_shiksha/screens/login_screen.dart';
import 'package:smart_shiksha/screens/onboarding_screen.dart';
import 'package:smart_shiksha/screens/dashboard_screen.dart';
import 'package:smart_shiksha/l10n/app_localizations.dart';

class SmartShikshaApp extends StatelessWidget {
  const SmartShikshaApp({super.key});

  @override
  Widget build(BuildContext context) {
    final locService = context.watch<LocalizationService>();
    final themeService = context.watch<ThemeService>();
    final authService = context.watch<AuthService>();

    // Determine home screen based on auth state
    Widget home;
    if (!authService.isLoggedIn) {
      home = const LoginScreen();
    } else if (authService.needsOnboarding) {
      home = const OnboardingScreen();
    } else {
      home = const DashboardScreen();
    }

    return MaterialApp(
      title: 'Smart Shiksha',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeService.themeMode,
      locale: locService.locale,
      supportedLocales: const [
        Locale('en'),
        Locale('hi'),
        Locale('kn'),
        Locale('te'),
        Locale('ta'),
      ],
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: home,
    );
  }
}
