import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../models/grocery_item.dart';
import '../services/api_service.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  List<GroceryItem> _inventory = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInventory();
  }

  Future<void> _loadInventory() async {
    setState(() => _isLoading = true);
    final items = await ApiService.getInventory();
    if (mounted) {
      setState(() {
        _inventory = items;
        _isLoading = false;
      });
    }
  }

  Future<void> _updateQuadrantWeight(int quadrant, double weightG) async {
    await ApiService.updateWeight(quadrant, weightG);
    _loadInventory();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Shelf Inventory Matrix",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            onPressed: _loadInventory,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppTheme.primary))
          : RefreshIndicator(
              onRefresh: _loadInventory,
              color: AppTheme.primary,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "4-Quadrant Tray Telemetry",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      "Real-time HX711 load cell weight tracking across 4 physical zones",
                      style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Grid of 4 Quadrants
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        childAspectRatio: 0.85,
                        crossAxisSpacing: 14,
                        mainAxisSpacing: 14,
                      ),
                      itemCount: _inventory.length,
                      itemBuilder: (context, index) {
                        return _buildQuadrantCard(_inventory[index]);
                      },
                    ),
                    const SizedBox(height: 24),

                    // Test Hardware Weight Simulator Box
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppTheme.primaryLight.withOpacity(0.4)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.04),
                            blurRadius: 8,
                            offset: const Offset(0, 3),
                          ),
                        ],
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: const [
                              Icon(Icons.tune_rounded, color: AppTheme.primary, size: 22),
                              SizedBox(width: 8),
                              Text(
                                "Load Cell Hardware Simulator",
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            "Simulate weight changes on specific quadrant trays to test live updates:",
                            style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                          ),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.primaryLight.withOpacity(0.2),
                                  foregroundColor: AppTheme.primary,
                                  elevation: 0,
                                ),
                                icon: const Icon(Icons.add, size: 16),
                                label: const Text("Q1 +100g"),
                                onPressed: () {
                                  final q1 = _inventory.firstWhere((e) => e.quadrant == 1, orElse: () => _inventory.first);
                                  _updateQuadrantWeight(1, q1.weightG + 100);
                                },
                              ),
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.accentOrange.withOpacity(0.15),
                                  foregroundColor: AppTheme.accentOrange,
                                  elevation: 0,
                                ),
                                icon: const Icon(Icons.remove, size: 16),
                                label: const Text("Q2 -100g"),
                                onPressed: () {
                                  final q2 = _inventory.firstWhere((e) => e.quadrant == 2, orElse: () => _inventory.first);
                                  _updateQuadrantWeight(2, (q2.weightG - 100).clamp(0, 1000));
                                },
                              ),
                              ElevatedButton.icon(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppTheme.accentRed.withOpacity(0.15),
                                  foregroundColor: AppTheme.accentRed,
                                  elevation: 0,
                                ),
                                icon: const Icon(Icons.clear_all, size: 16),
                                label: const Text("Q4 Empty"),
                                onPressed: () => _updateQuadrantWeight(4, 0),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildQuadrantCard(GroceryItem item) {
    final double fillPercent = (item.weightG / item.maxCapacityG).clamp(0.0, 1.0);
    Color statusColor = AppTheme.primary;
    if (item.status == 'Low Stock') statusColor = AppTheme.accentOrange;
    if (item.status == 'Critical') statusColor = AppTheme.accentRed;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  "QUADRANT ${item.quadrant}",
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primary,
                  ),
                ),
              ),
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: statusColor,
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ),
          const Spacer(),
          Text(
            item.itemName,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            "${item.weightG.toInt()}g / ${item.maxCapacityG.toInt()}g",
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w800,
              color: statusColor,
            ),
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: fillPercent,
              minHeight: 6,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(statusColor),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "${(fillPercent * 100).toInt()}% Capacity",
                style: const TextStyle(fontSize: 10, color: AppTheme.textSecondary),
              ),
              Text(
                item.status,
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: statusColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}