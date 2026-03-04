import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:smart_shiksha/core/api_client.dart';
import 'package:smart_shiksha/models/user.dart';
import 'package:smart_shiksha/services/api_service.dart';

/// Authentication service using JWT tokens.
/// Handles Auth0 sign-in flow via backend, token persistence, and user state.
class AuthService extends ChangeNotifier {
  static const _tokenKey = 'ss_jwt_token';
  static const _userKey = 'ss_user_json';

  final String _base = getApiBaseUrl();

  String? _token;
  AppUser? _user;
  bool _loading = false;

  String? get token => _token;
  AppUser? get user => _user;
  bool get isLoggedIn => _token != null && _user != null;
  bool get isLoading => _loading;
  bool get needsOnboarding => _user != null && !_user!.onboardingComplete;

  Map<String, String> get _authHeaders => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  /// Load persisted session on app startup.
  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(_tokenKey);
    final userJson = prefs.getString(_userKey);
    if (userJson != null) {
      try {
        _user = AppUser.fromJson(jsonDecode(userJson));
      } catch (_) {
        _user = null;
      }
    }
    // Sync token to ApiService so all HTTP calls include it.
    ApiService.setToken(_token);
    // If we have a token, verify it's still valid.
    if (_token != null) {
      try {
        await fetchMe();
      } catch (_) {
        // Token expired — clear session
        await logout();
      }
    }
    notifyListeners();
  }

  /// Authenticate with an Auth0 ID token.
  Future<void> signInWithAuth0Token(String idToken) async {
    _loading = true;
    notifyListeners();
    try {
      final resp = await http.post(
        Uri.parse('$_base/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'id_token': idToken}),
      );
      if (resp.statusCode != 200) {
        final body = jsonDecode(resp.body);
        throw Exception(body['detail'] ?? 'Sign-in failed');
      }
      final data = jsonDecode(resp.body);
      _token = data['access_token'] as String;
      _user = AppUser.fromJson(data['user']);
      ApiService.setToken(_token);
      await _persist();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// For desktop/dev without Auth0 — sign in with email directly.
  /// Creates or retrieves user from the backend via the login endpoint.
  Future<void> signInWithEmail(String email, String name) async {
    _loading = true;
    notifyListeners();
    try {
      // Use a fake token for dev mode (backend DEBUG=True decodes base64)
      final fakeToken = base64Encode(
        utf8.encode(
            '{"sub":"dev_${email.hashCode}","email":"$email","name":"$name"}'),
      );
      final resp = await http.post(
        Uri.parse('$_base/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'id_token': fakeToken}),
      );
      if (resp.statusCode != 200) {
        final body = jsonDecode(resp.body);
        throw Exception(body['detail'] ?? 'Sign-in failed');
      }
      final data = jsonDecode(resp.body);
      _token = data['access_token'] as String;
      _user = AppUser.fromJson(data['user']);
      ApiService.setToken(_token);
      await _persist();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Complete onboarding.
  Future<void> completeOnboarding({
    required String curriculum,
    required int classGrade,
    String? stream,
    String languagePreference = 'en',
  }) async {
    _loading = true;
    notifyListeners();
    try {
      final resp = await http.post(
        Uri.parse('$_base/auth/onboarding'),
        headers: _authHeaders,
        body: jsonEncode({
          'curriculum': curriculum,
          'class_grade': classGrade,
          'stream': stream,
          'language_preference': languagePreference,
        }),
      );
      if (resp.statusCode != 200) {
        final body = jsonDecode(resp.body);
        throw Exception(body['detail'] ?? 'Onboarding failed');
      }
      _user = AppUser.fromJson(jsonDecode(resp.body));
      await _persist();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Fetch current user profile from backend.
  Future<void> fetchMe() async {
    final resp = await http.get(
      Uri.parse('$_base/auth/me'),
      headers: _authHeaders,
    );
    if (resp.statusCode == 200) {
      _user = AppUser.fromJson(jsonDecode(resp.body));
      await _persist();
      notifyListeners();
    } else {
      throw Exception('Session expired');
    }
  }

  /// Update profile fields (class, curriculum, stream, language).
  Future<void> updateProfile({
    String? curriculum,
    int? classGrade,
    String? stream,
    String? languagePreference,
  }) async {
    _loading = true;
    notifyListeners();
    try {
      final body = <String, dynamic>{};
      if (curriculum != null) body['curriculum'] = curriculum;
      if (classGrade != null) body['class_grade'] = classGrade;
      if (stream != null) body['stream'] = stream;
      if (languagePreference != null)
        body['language_preference'] = languagePreference;

      final resp = await http.patch(
        Uri.parse('$_base/auth/profile'),
        headers: _authHeaders,
        body: jsonEncode(body),
      );
      if (resp.statusCode != 200) {
        final data = jsonDecode(resp.body);
        throw Exception(data['detail'] ?? 'Profile update failed');
      }
      _user = AppUser.fromJson(jsonDecode(resp.body));
      await _persist();
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Clear session.
  Future<void> logout() async {
    _token = null;
    _user = null;
    ApiService.setToken(null);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userKey);
    notifyListeners();
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    if (_token != null) {
      await prefs.setString(_tokenKey, _token!);
    }
    if (_user != null) {
      await prefs.setString(
          _userKey,
          jsonEncode({
            'id': _user!.id,
            'name': _user!.name,
            'email': _user!.email,
            'profile_picture_url': _user!.profilePictureUrl,
            'language_preference': _user!.languagePreference,
            'curriculum': _user!.curriculum,
            'class_grade': _user!.classGrade,
            'stream': _user!.stream,
            'onboarding_complete': _user!.onboardingComplete,
          }));
    }
  }
}
