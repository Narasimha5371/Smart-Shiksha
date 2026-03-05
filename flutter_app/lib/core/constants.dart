/// API client constants and configuration.
class AppConstants {
  AppConstants._();

  /// Base URL for the FastAPI backend.
  /// Release builds point to production; debug builds use local emulator/desktop.
  static const String apiBaseUrl = bool.fromEnvironment('dart.vm.product')
      ? 'https://smartsiksha.onrender.com/api' // production (release build)
      : 'http://10.0.2.2:8001/api'; // debug (Android emulator → host)
  static const String apiBaseUrlDesktop =
      bool.fromEnvironment('dart.vm.product')
          ? 'https://smartsiksha.onrender.com/api' // production (release build)
          : 'http://localhost:8001/api'; // debug (local desktop)

  /// Supported language codes mapped to display names.
  static const Map<String, String> supportedLanguages = {
    'en': 'English',
    'hi': 'हिन्दी',
    'kn': 'ಕನ್ನಡ',
    'te': 'తెలుగు',
    'ta': 'தமிழ்',
  };

  /// Default language.
  static const String defaultLanguage = 'en';
}
