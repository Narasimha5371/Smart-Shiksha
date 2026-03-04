import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';
import 'package:smart_shiksha/models/lesson.dart';

/// Local SQLite cache for offline lesson reading (native platforms).
class DbService {
  static Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dir = await getApplicationDocumentsDirectory();
    final path = join(dir.path, 'smartsiksha_cache.db');
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE cached_lessons (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            language_code TEXT NOT NULL,
            sources TEXT,
            created_at TEXT
          )
        ''');
      },
    );
  }

  /// Cache a lesson locally for offline access.
  Future<void> cacheLesson(Lesson lesson) async {
    final db = await database;
    await db.insert(
      'cached_lessons',
      lesson.toDbMap(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Retrieve all locally cached lessons.
  Future<List<Lesson>> getCachedLessons() async {
    final db = await database;
    final maps = await db.query('cached_lessons', orderBy: 'created_at DESC');
    return maps.map(Lesson.fromDbMap).toList();
  }

  /// Delete a cached lesson.
  Future<void> deleteCachedLesson(String id) async {
    final db = await database;
    await db.delete('cached_lessons', where: 'id = ?', whereArgs: [id]);
  }

  /// Clear all cached lessons.
  Future<void> clearCache() async {
    final db = await database;
    await db.delete('cached_lessons');
  }
}
