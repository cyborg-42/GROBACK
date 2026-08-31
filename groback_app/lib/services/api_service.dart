import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import '../models/grocery_item.dart';
import '../models/scan_log.dart';
import '../models/depletion_metric.dart';

class ApiService {
  // Your PC's active Wi-Fi IP address:
  static const String serverIp = "10.214.49.46";

  static String get baseUrl {
    if (!kIsWeb && Platform.isAndroid) {
      // Use your PC's IP so your physical phone can connect over Wi-Fi
      return "http://$serverIp:8000";
    }
    return "http://127.0.0.1:8000";
  }

  // Mock fallback state for demo/offline mode
  static final List<GroceryItem> _mockInventory = [
    GroceryItem(id: 1, quadrant: 1, itemName: "Apple", weightG: 450.0, maxCapacityG: 1000.0, status: "Available", lastUpdated: "2 mins ago"),
    GroceryItem(id: 2, quadrant: 2, itemName: "Banana", weightG: 180.0, maxCapacityG: 1000.0, status: "Low Stock", lastUpdated: "5 mins ago"),
    GroceryItem(id: 3, quadrant: 3, itemName: "Orange", weightG: 620.0, maxCapacityG: 1000.0, status: "Available", lastUpdated: "Just now"),
    GroceryItem(id: 4, quadrant: 4, itemName: "Carrot", weightG: 80.0, maxCapacityG: 1000.0, status: "Critical", lastUpdated: "10 mins ago"),
  ];

  static final List<ScanLog> _mockScans = [
    ScanLog(id: 1, label: "Apple", confidence: 96.4, timestamp: "10:30 AM"),
    ScanLog(id: 2, label: "Orange", confidence: 92.1, timestamp: "10:15 AM"),
    ScanLog(id: 3, label: "Banana", confidence: 88.7, timestamp: "09:45 AM"),
  ];

  static Future<List<GroceryItem>> getInventory() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/inventory')).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return data.map((e) => GroceryItem.fromJson(e)).toList();
      }
    } catch (_) {}
    return _mockInventory;
  }

  static Future<List<ScanLog>> getRecentScans() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/scans')).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return data.map((e) => ScanLog.fromJson(e)).toList();
      }
    } catch (_) {}
    return _mockScans;
  }

  static Future<Map<String, dynamic>> updateWeight(int quadrant, double weightG) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/update-weight'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'quadrant': quadrant, 'weight_grams': weightG}),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (_) {}
    final index = _mockInventory.indexWhere((item) => item.quadrant == quadrant);
    if (index != -1) {
      final old = _mockInventory[index];
      _mockInventory[index] = GroceryItem(
        id: old.id,
        quadrant: old.quadrant,
        itemName: old.itemName,
        weightG: weightG,
        maxCapacityG: old.maxCapacityG,
        status: weightG < 100 ? "Critical" : (weightG < 250 ? "Low Stock" : "Available"),
        lastUpdated: "Just now",
      );
    }
    return {'status': 'success', 'quadrant': quadrant, 'weight': weightG};
  }

  static Future<Map<String, dynamic>> simulateScan(String label, double confidence) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/v1/simulate-scan'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'label': label, 'confidence': confidence}),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (_) {}
    final newScan = ScanLog(
      id: _mockScans.length + 1,
      label: label,
      confidence: confidence,
      timestamp: "Just now",
    );
    _mockScans.insert(0, newScan);
    return {'status': 'success', 'detected_item': label, 'confidence': confidence};
  }

  static Future<List<DepletionMetric>> getDepletionMetrics() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/depletion-analytics')).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        final List data = jsonDecode(response.body);
        return data.map((e) => DepletionMetric.fromJson(e)).toList();
      }
    } catch (_) {}
    return [
      DepletionMetric(itemName: "Banana", quadrant: 2, currentWeightG: 180, dailyRateG: 150, estimatedDaysRemaining: 1.2, stockStatus: "Low Stock"),
      DepletionMetric(itemName: "Carrot", quadrant: 4, currentWeightG: 80, dailyRateG: 100, estimatedDaysRemaining: 0.8, stockStatus: "Critical"),
      DepletionMetric(itemName: "Apple", quadrant: 1, currentWeightG: 450, dailyRateG: 120, estimatedDaysRemaining: 3.8, stockStatus: "Sufficient"),
      DepletionMetric(itemName: "Orange", quadrant: 3, currentWeightG: 620, dailyRateG: 140, estimatedDaysRemaining: 4.4, stockStatus: "Sufficient"),
    ];
  }

  static Future<Map<String, dynamic>> getInventorySummary() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/v1/inventory/summary')).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (_) {}
    return {'total_items': 4, 'critical': 1, 'low_stock': 1};
  }
}