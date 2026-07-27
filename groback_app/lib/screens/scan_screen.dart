import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  String _selectedProduce = 'Apple';
  double _simulatedConfidence = 96.4;
  bool _isScanning = false;
  String? _lastScannedResult;

  final List<Map<String, dynamic>> _sampleFruits = [
    {'name': 'Apple', 'icon': '🍎', 'confidence': 96.4},
    {'name': 'Banana', 'icon': '🍌', 'confidence': 91.8},
    {'name': 'Orange', 'icon': '🍊', 'confidence': 94.2},
    {'name': 'Carrot', 'icon': '🥕', 'confidence': 89.5},
  ];

  Future<void> _executeScan() async {
    setState(() => _isScanning = true);
    await Future.delayed(const Duration(milliseconds: 800)); // Simulate camera processing delay
    final result = await ApiService.simulateScan(_selectedProduce, _simulatedConfidence);
    if (mounted) {
      setState(() {
        _isScanning = false;
        _lastScannedResult = "${result['detected_item']} (${result['confidence']}%)";
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text("✅ Identified $_selectedProduce with $_simulatedConfidence% confidence!"),
          backgroundColor: AppTheme.primary,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "ESP32-CAM Scanning Station",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Visual Produce Scanner",
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              "Position produce at the external scanning camera before placing into tray",
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 20),

            // Camera Viewfinder Box
            Container(
              width: double.infinity,
              height: 240,
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.15),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Stack(
                children: [
                  // Center viewfinder item preview
                  Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          _sampleFruits.firstWhere((e) => e['name'] == _selectedProduce)['icon'],
                          style: const TextStyle(fontSize: 72),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          "Frame Aligned: $_selectedProduce",
                          style: const TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                      ],
                    ),
                  ),
                  // Reticle corners
                  Positioned(
                    top: 20,
                    left: 20,
                    child: _buildCorner(top: true, left: true),
                  ),
                  Positioned(
                    top: 20,
                    right: 20,
                    child: _buildCorner(top: true, left: false),
                  ),
                  Positioned(
                    bottom: 20,
                    left: 20,
                    child: _buildCorner(top: false, left: true),
                  ),
                  Positioned(
                    bottom: 20,
                    right: 20,
                    child: _buildCorner(top: false, left: false),
                  ),
                  if (_isScanning)
                    const Center(
                      child: CircularProgressIndicator(color: AppTheme.primaryLight, strokeWidth: 4),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Sample Selector Grid
            const Text(
              "Select Item to Scan (Simulation Mode)",
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: _sampleFruits.map((item) {
                final isSelected = item['name'] == _selectedProduce;
                return Expanded(
                  child: GestureDetector(
                    onTap: () {
                      setState(() {
                        _selectedProduce = item['name'];
                        _simulatedConfidence = item['confidence'];
                      });
                    },
                    child: Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: isSelected ? AppTheme.primary : Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isSelected ? AppTheme.primary : Colors.grey.shade300,
                        ),
                      ),
                      child: Column(
                        children: [
                          Text(item['icon'], style: const TextStyle(fontSize: 28)),
                          const SizedBox(height: 4),
                          Text(
                            item['name'],
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: isSelected ? Colors.white : AppTheme.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 24),

            // Scan Action Button
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _isScanning ? null : _executeScan,
                icon: const Icon(Icons.camera_alt_rounded),
                label: Text(_isScanning ? "Analyzing Frame with CNN..." : "Trigger ESP32-CAM Scan"),
              ),
            ),

            if (_lastScannedResult != null) ...[
              const SizedBox(height: 20),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_rounded, color: AppTheme.primary, size: 24),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Last Scanned Result",
                          style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
                        ),
                        Text(
                          _lastScannedResult!,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryDark,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCorner({required bool top, required bool left}) {
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        border: Border(
          top: top ? const BorderSide(color: AppTheme.primaryLight, width: 3) : BorderSide.none,
          bottom: !top ? const BorderSide(color: AppTheme.primaryLight, width: 3) : BorderSide.none,
          left: left ? const BorderSide(color: AppTheme.primaryLight, width: 3) : BorderSide.none,
          right: !left ? const BorderSide(color: AppTheme.primaryLight, width: 3) : BorderSide.none,
        ),
      ),
    );
  }
}