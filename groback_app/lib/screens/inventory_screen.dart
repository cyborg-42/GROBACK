import 'package:flutter/material.dart';
import 'package:groback_app/services/api_service.dart';
import 'package:groback_app/models/grocery_item.dart';
import '../widgets/weight_card.dart';
import '../widgets/detection_card.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  late Future<List<GroceryItem>> _inventoryFuture;

  @override
  void initState() {
    super.initState();
    _refreshData();
  }

  void _refreshData() {
    setState(() {
      _inventoryFuture = ApiService.getInventory();
    });
  }

  Future<void> _updateWeight(int quadrant, double change) async {
    // Get current inventory to compute new weight
    final inventory = await ApiService.getInventory();
    final item = inventory.firstWhere((i) => i.quadrant == quadrant);
    double newWeight = item.weightG + change;
    // Clamp between 0 and max capacity
    newWeight = newWeight.clamp(0.0, item.maxCapacityG);
    await ApiService.updateWeight(quadrant, newWeight);
    _refreshData();
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refreshData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Smart Shelf Inventory',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 16),
            Text(
              'Monitor your 4-quadrant tray scale matrix',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),

            // 4-Quadrant Tray Matrix
            GridView.count(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisCount: 2,
              crossAxisSpacing: 16,
              mainAxisSpacing: 16,
              children: List.generate(4, (index) {
                final quadrant = index + 1;
                return FutureBuilder<GroceryItem>(
                  future: ApiService.getInventory().then((list) => list.firstWhere((i) => i.quadrant == quadrant)),
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Card(child: Center(child: CircularProgressIndicator()));
                    }
                    if (snapshot.hasError) {
                      return Card(child: Center(child: Text('Error: ${snapshot.error}')));
                    }
                    final item = snapshot.data!;
                    return Card(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Quadrant Header
                          Padding(
                            padding: const EdgeInsets.all(12),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Quadrant $quadrant',
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                                // Status Badge
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: _getStatusColor(item.status).withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    item.status,
                                    style: TextStyle(
                                      color: _getStatusColor(item.status),
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Divider(height: 1),
                          // Item Name and Weight
                          Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  item.itemName,
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Weight: ${item.weightG.toStringAsFixed(1)} g / ${item.maxCapacityG.toStringAsFixed(0)} g',
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                                const SizedBox(height: 8),
                                // Progress Bar for Capacity
                                SizedBox(
                                  height: 8,
                                  child: LinearProgressIndicator(
                                    value: item.weightG / item.maxCapacityG,
                                    backgroundColor: Colors.grey[300],
                                    valueColor: AlwaysStoppedAnimation<Color>(_getStatusColor(item.status)),
                                  ),
                                ),
                                const SizedBox(height: 12),
                                // Hardware Load Cell Simulator
                                Wrap(
                                  spacing: 8,
                                  children: [
                                    ElevatedButton(
                                      onPressed: () => _updateWeight(quadrant, 100),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: AppTheme.mintLeaf,
                                      ),
                                      child: const Text('Q+100g'),
                                    ),
                                    ElevatedButton(
                                      onPressed: () => _updateWeight(quadrant, -100),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: AppTheme.lowStockAlert,
                                      ),
                                      child: const Text('Q-100g'),
                                    ),
                                    if (quadrant == 4) // Only show 'Empty' for Q4 as example
                                      ElevatedButton(
                                        onPressed: () => _updateWeight(quadrant, 0),
                                        style: ElevatedButton.styleFrom(
                                          backgroundColor: AppTheme.criticalAlert,
                                        ),
                                        child: const Text('Q4 Empty'),
                                      ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                );
              }),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Critical':
        return AppTheme.criticalAlert;
      case 'Low Stock':
        return AppTheme.lowStockAlert;
      default:
        return AppTheme.mintLeaf;
    }
  }
}