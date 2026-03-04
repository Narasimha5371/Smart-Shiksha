import 'package:smart_shiksha/models/lesson.dart';

/// No-op stub for web – SQLite is not available in browsers.
class DbService {
  Future<void> cacheLesson(Lesson lesson) async {}

  Future<List<Lesson>> getCachedLessons() async => [];

  Future<void> deleteCachedLesson(String id) async {}

  Future<void> clearCache() async {}
}
