class GroceryItem {
  final int id;
  final int quadrant;
  final String itemName;
  final double weightG;
  final double maxCapacityG;
  final String status;
  final String lastUpdated;

  GroceryItem({
    required this.id,
    required this.quadrant,
    required this.itemName,
    required this.weightG,
    required this.maxCapacityG,
    required this.status,
    required this.lastUpdated,
  });

  factory GroceryItem.fromJson(Map<String, dynamic> json) {
    return GroceryItem(
      id: json['id'] ?? 0,
      quadrant: json['quadrant'] ?? 1,
      itemName: json['item_name'] ?? 'Empty',
      weightG: (json['weight_g'] as num?)?.toDouble() ?? 0.0,
      maxCapacityG: (json['max_capacity_g'] as num?)?.toDouble() ?? 1000.0,
      status: json['status'] ?? 'Available',
      lastUpdated: json['last_updated'] ?? '',
    );
  }
}

class ScanLog {
  final int id;
  final String label;
  final double confidence;
  final String timestamp;

  ScanLog({
    required this.id,
    required this.label,
    required this.confidence,
    required this.timestamp,
  });

  factory ScanLog.fromJson(Map<String, dynamic> json) {
    return ScanLog(
      id: json['id'] ?? 0,
      label: json['label'] ?? 'Unknown',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      timestamp: json['timestamp'] ?? '',
    );
  }
}

class DepletionMetric {
  final String itemName;
  final int quadrant;
  final double currentWeightG;
  final double dailyRateG;
  final double estimatedDaysRemaining;
  final String stockStatus;

  DepletionMetric({
    required this.itemName,
    required this.quadrant,
    required this.currentWeightG,
    required this.dailyRateG,
    required this.estimatedDaysRemaining,
    required this.stockStatus,
  });

  factory DepletionMetric.fromJson(Map<String, dynamic> json) {
    return DepletionMetric(
      itemName: json['item_name'] ?? 'Item',
      quadrant: json['quadrant'] ?? 1,
      currentWeightG: (json['current_weight_g'] as num?)?.toDouble() ?? 0.0,
      dailyRateG: (json['daily_rate_g'] as num?)?.toDouble() ?? 0.0,
      estimatedDaysRemaining: (json['estimated_days_remaining'] as num?)?.toDouble() ?? 0.0,
      stockStatus: json['stock_status'] ?? 'Sufficient',
    );
  }
}
