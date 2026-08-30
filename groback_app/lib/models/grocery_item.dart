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
      id: json['id'] as int,
      quadrant: json['quadrant'] as int,
      itemName: json['item_name'] as String,
      weightG: (json['weight_g'] as num).toDouble(),
      maxCapacityG: (json['max_capacity_g'] as num).toDouble(),
      status: json['status'] as String,
      lastUpdated: json['last_updated'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'quadrant': quadrant,
      'item_name': itemName,
      'weight_g': weightG,
      'max_capacity_g': maxCapacityG,
      'status': status,
      'last_updated': lastUpdated,
    };
  }
}