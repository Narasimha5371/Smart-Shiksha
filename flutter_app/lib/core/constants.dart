/// API client constants and configuration.
class AppConstants {
  AppConstants._();

  /// Base URL for the FastAPI backend.
  /// Change this when deploying to production.
  static const String apiBaseUrl =
      'http://10.0.2.2:8001/api'; // Android emulator → host
  static const String apiBaseUrlDesktop = 'http://localhost:8001/api';

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
