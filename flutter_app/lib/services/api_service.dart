import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:smart_shiksha/core/api_client.dart';
import 'package:smart_shiksha/models/lesson.dart';
import 'package:smart_shiksha/models/syllabus.dart';
import 'package:smart_shiksha/models/user.dart';

/// HTTP service that talks to the shared FastAPI backend.
class ApiService {
  late final String _base;

  /// Shared JWT token — set once by AuthService, used by every instance.
  static String? _token;

  ApiService() {
    _base = getApiBaseUrl();
  }

  /// Set the JWT auth token for authenticated requests (static — all instances share it).
  static void setToken(String? token) => _token = token;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  /// Safely extract an error message from an HTTP response (handles both JSON and plain text).
  static String _extractError(http.Response resp) {
    try {
      final body = jsonDecode(resp.body);
      return body['detail'] ?? 'Request failed (${resp.statusCode})';
    } catch (_) {
      return resp.body.isNotEmpty
          ? resp.body
          : 'Request failed (${resp.statusCode})';
    }
  }

  // ── Ask / RAG ────────────────────────────
  Future<Lesson> askQuestion(String question, String targetLanguage) async {
    final resp = await http.post(
      Uri.parse('$_base/ask'),
      headers: _headers,
      body: jsonEncode({
        'question': question,
        'target_language': targetLanguage,
      }),
    );
    if (resp.statusCode != 200) {
      throw Exception(_extractError(resp));
    }
    return Lesson.fromAskJson(jsonDecode(resp.body));
  }

  // ── Users ────────────────────────────────
  Future<AppUser> registerUser(String name, String email, String lang) async {
    final resp = await http.post(
      Uri.parse('$_base/users/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'email': email,
        'language_preference': lang,
      }),
    );
    if (resp.statusCode != 201) {
      throw Exception(_extractError(resp));
    }
    return AppUser.fromJson(jsonDecode(resp.body));
  }

  Future<AppUser> updateLanguage(String userId, String lang) async {
    final resp = await http.patch(
      Uri.parse('$_base/users/$userId/language'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'language_preference': lang}),
    );
    if (resp.statusCode != 200) throw Exception('Failed to update language');
    return AppUser.fromJson(jsonDecode(resp.body));
  }

  // ── Saved Lessons ────────────────────────
  Future<Lesson> saveLesson({
    required String userId,
    required String topic,
    required String content,
    required String languageCode,
    List<String> sourceUrls = const [],
  }) async {
    final resp = await http.post(
      Uri.parse('$_base/lessons/save'),
      headers: _headers,
      body: jsonEncode({
        'user_id': userId,
        'topic': topic,
        'content': content,
        'language_code': languageCode,
        'source_urls': sourceUrls,
      }),
    );
    if (resp.statusCode != 201) throw Exception('Failed to save lesson');
    return Lesson.fromSavedJson(jsonDecode(resp.body));
  }

  Future<List<Lesson>> getSavedLessons(String userId) async {
    final resp = await http.get(Uri.parse('$_base/lessons/$userId'));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => Lesson.fromSavedJson(e as Map<String, dynamic>))
        .toList();
  }

  // ── Syllabus ─────────────────────────────
  Future<List<String>> getCurricula() async {
    final resp = await http.get(Uri.parse('$_base/syllabus/curricula'));
    if (resp.statusCode != 200) return [];
    final data = jsonDecode(resp.body);
    return (data['curricula'] as List<dynamic>)
        .map((e) => e.toString())
        .toList();
  }

  Future<List<Subject>> getSubjects({
    required String curriculum,
    required int classGrade,
    String? stream,
  }) async {
    var url =
        '$_base/syllabus/subjects?curriculum=$curriculum&class_grade=$classGrade';
    if (stream != null) url += '&stream=$stream';
    final resp = await http.get(Uri.parse(url));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => Subject.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Chapter>> getChapters(String subjectId) async {
    final resp =
        await http.get(Uri.parse('$_base/syllabus/chapters/$subjectId'));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => Chapter.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<GeneratedLesson>> getGeneratedLessons(String chapterId) async {
    final resp =
        await http.get(Uri.parse('$_base/syllabus/lessons/$chapterId'));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => GeneratedLesson.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<GeneratedLesson> generateLesson(String chapterId) async {
    final resp = await http.post(
      Uri.parse('$_base/syllabus/generate/$chapterId'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception(_extractError(resp));
    }
    return GeneratedLesson.fromJson(jsonDecode(resp.body));
  }

  // ── Quiz / Flashcards ────────────────────
  Future<List<FlashCard>> getFlashcards(String chapterId) async {
    final resp = await http.get(Uri.parse('$_base/quiz/flashcards/$chapterId'));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => FlashCard.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<FlashCard>> generateFlashcards(String chapterId) async {
    final resp = await http.post(
      Uri.parse('$_base/quiz/generate/$chapterId'),
      headers: _headers,
    );
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => FlashCard.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // ── Competitive Exams ────────────────────
  Future<List<CompetitiveExam>> getExams({int? classGrade}) async {
    var url = '$_base/exams/';
    if (classGrade != null) url += '?class_grade=$classGrade';
    final resp = await http.get(Uri.parse(url));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => CompetitiveExam.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<MockTest>> getMockTests(String examId) async {
    final resp = await http.get(Uri.parse('$_base/exams/$examId/mock-tests'));
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list
        .map((e) => MockTest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<MockTest> generateMockTest(String examId) async {
    final resp = await http.post(
      Uri.parse('$_base/exams/mock-tests/$examId/generate'),
      headers: _headers,
    );
    if (resp.statusCode != 200) {
      throw Exception(_extractError(resp));
    }
    return MockTest.fromJson(jsonDecode(resp.body));
  }

  // ── Progress / Stats ─────────────────────
  Future<List<Map<String, dynamic>>> getSubjectStats() async {
    final resp = await http.get(
      Uri.parse('$_base/progress/stats'),
      headers: _headers,
    );
    if (resp.statusCode != 200) return [];
    final List<dynamic> list = jsonDecode(resp.body);
    return list.cast<Map<String, dynamic>>();
  }

  Future<void> updateProgress(
    String chapterId, {
    int? quizScore,
    int? timeSpentSeconds,
    int? flashcardsReviewed,
  }) async {
    final body = <String, dynamic>{};
    if (quizScore != null) body['quiz_score'] = quizScore;
    if (timeSpentSeconds != null) body['time_spent_seconds'] = timeSpentSeconds;
    if (flashcardsReviewed != null) body['flashcards_reviewed'] = flashcardsReviewed;
    await http.patch(
      Uri.parse('$_base/progress/$chapterId'),
      headers: _headers,
      body: jsonEncode(body),
    );
  }
}
