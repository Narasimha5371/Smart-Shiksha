import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_shiksha/core/constants.dart';

/// Manages the current locale and persists preference to SharedPreferences.
class LocalizationService extends ChangeNotifier {
  static const _prefKey = 'ss_lang';
  Locale _locale = const Locale('en');

  Locale get locale => _locale;
  String get languageCode => _locale.languageCode;

  /// Load saved preference on startup.
  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final code = prefs.getString(_prefKey) ?? AppConstants.defaultLanguage;
    _locale = Locale(code);
    notifyListeners();
  }

  /// Change language and persist.
  Future<void> setLanguage(String code) async {
    if (!AppConstants.supportedLanguages.containsKey(code)) return;
    _locale = Locale(code);
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefKey, code);
  }
}
