import 'dart:convert';
import 'dart:io' show Platform;
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import '../models/grocery_item.dart';
import '../models/scan_log.dart';
import '../models/depletion_metric.dart';

/// Result wrapper returned by every ApiService call.
/// [isOnline] is false when the backend could not be reached.
class ApiResult<T> {
  final T data;
  final bool isOnline;

  const ApiResult({required this.data, required this.isOnline});
}

class ApiService {
  // For Android emulator, 10.0.2.2 maps to the host machine's localhost.
  // For a physical device on Wi-Fi, set this to your machine's LAN IP.
  static const String serverIp = "10.65.157.91";

  static String get baseUrl {
    if (!kIsWeb && Platform.isAndroid) {
      return "http://$serverIp:8000";
    }
    return "http://127.0.0.1:8000";
  }

  // ---------------------------------------------------------------------------
  // Inventory
  // ---------------------------------------------------------------------------

  static Future<ApiResult<List<GroceryItem>>> getInventory() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/inventory'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return ApiResult(
          data: data.map((e) => GroceryItem.fromJson(e)).toList(),
          isOnline: true,
        );
      }
    } catch (_) {}
    return const ApiResult(data: [], isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Scan logs
  // ---------------------------------------------------------------------------

  static Future<ApiResult<List<ScanLog>>> getRecentScans() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/scans'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return ApiResult(
          data: data.map((e) => ScanLog.fromJson(e)).toList(),
          isOnline: true,
        );
      }
    } catch (_) {}
    return const ApiResult(data: [], isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Weight update
  // ---------------------------------------------------------------------------

  static Future<ApiResult<Map<String, dynamic>>> updateWeight(
      int quadrant, double weightG) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/update-weight'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'quadrant': quadrant, 'weight_grams': weightG}),
          )
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return ApiResult(data: jsonDecode(response.body), isOnline: true);
      }
    } catch (_) {}
    return const ApiResult(data: {}, isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Simulate scan
  // ---------------------------------------------------------------------------

  static Future<ApiResult<Map<String, dynamic>>> simulateScan(
      String label, double confidence) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/api/v1/simulate-scan'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'label': label, 'confidence': confidence}),
          )
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return ApiResult(data: jsonDecode(response.body), isOnline: true);
      }
    } catch (_) {}
    return const ApiResult(data: {}, isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Depletion analytics
  // ---------------------------------------------------------------------------

  static Future<ApiResult<List<DepletionMetric>>> getDepletionMetrics() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/depletion-analytics'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return ApiResult(
          data: data.map((e) => DepletionMetric.fromJson(e)).toList(),
          isOnline: true,
        );
      }
    } catch (_) {}
    return const ApiResult(data: [], isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Inventory summary
  // ---------------------------------------------------------------------------

  static Future<ApiResult<Map<String, dynamic>>> getInventorySummary() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/api/v1/inventory/summary'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return ApiResult(data: jsonDecode(response.body), isOnline: true);
      }
    } catch (_) {}
    return const ApiResult(data: {}, isOnline: false);
  }

  // ---------------------------------------------------------------------------
  // Camera scan (multipart upload)
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> scanItem(Uint8List imageBytes) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/api/v1/scan-item'),
      );
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          imageBytes,
          filename: 'scan.jpg',
        ),
      );
      final streamedResponse =
          await request.send().timeout(const Duration(seconds: 15));
      final response = await http.Response.fromStream(streamedResponse);
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
    return {'success': false, 'error': 'Server returned an error'};
  }
}
