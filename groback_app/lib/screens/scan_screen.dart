import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/api_service.dart';
import 'package:camera/camera.dart';

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

  // Camera-related variables
  CameraController? _cameraController;
  bool _isCameraInitialized = false;
  String? _cameraError;
  bool _isProcessing = false;

  final List<Map<String, dynamic>> _sampleFruits = [
    {'name': 'Apple', 'icon': '🍎', 'confidence': 96.4},
    {'name': 'Banana', 'icon': '🍌', 'confidence': 91.8},
    {'name': 'Orange', 'icon': '🍊', 'confidence': 94.2},
    {'name': 'Carrot', 'icon': '🥕', 'confidence': 89.5},
  ];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  Future<void> _initializeCamera() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        setState(() {
          _cameraError = 'No cameras found';
        });
        return;
      }
      // Use the first camera (back camera if available, else front)
      final CameraDescription camera = cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => cameras.first,
      );

      _cameraController = CameraController(
        camera,
        ResolutionPreset.medium, // Use medium resolution for balance of quality and performance
        enableAudio: false,
      );

      await _cameraController?.initialize();
      if (!mounted) return;

      setState(() {
        _isCameraInitialized = true;
      });
    } on CameraException catch (e) {
      setState(() {
        _cameraError = 'Camera error: ${e.description}';
      });
    }
  }

  Future<void> _executeScan() async {
    if (!_isCameraInitialized || _cameraController == null || _isProcessing) return;

    setState(() => _isProcessing = true);
    try {
      // Take picture
      final XFile file = await _cameraController!.takePicture();
      final bytes = await file.readAsBytes();

      // Send to backend for processing
      final result = await ApiService.scanItem(bytes);

      if (mounted) {
        setState(() {
          _isProcessing = false;
          _lastScannedResult = "${result['detected_item']} (${result['confidence']}%)";
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("✅ Identified ${result['detected_item']} with ${result['confidence']}% confidence!"),
            backgroundColor: AppTheme.primary,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isProcessing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Error: $e"),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Phone Camera Scanning Station",
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
              "Position produce in front of the camera and tap scan",
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
                    color: Colors.black.withValues(alpha: 0.15),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Stack(
                children: [
                  if (_cameraError != null)
                    Center(
                      child: Text(
                        _cameraError!,
                        style: const TextStyle(color: Colors.red, fontSize: 16),
                        textAlign: TextAlign.center,
                      ),
                    )
                  else if (_isCameraInitialized)
                    CameraPreview(_cameraController!)
                  else
                    const Center(
                      child: CircularProgressIndicator(color: AppTheme.primary),
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
                  if (_isProcessing)
                    const Center(
                      child: CircularProgressIndicator(color: AppTheme.primaryLight, strokeWidth: 4),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Sample Selector Grid
            const Text(
              "Select Item to Scan (Reference)",
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
                onPressed: _isProcessing ? null : _executeScan,
                icon: const Icon(Icons.camera_alt_rounded),
                label: Text(_isProcessing ? "Processing..." : "Scan Item"),
              ),
            ),

            if (_lastScannedResult != null) ...[
              const SizedBox(height: 20),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.primaryLight.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
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