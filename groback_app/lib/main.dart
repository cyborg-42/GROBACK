import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'navigation/bottom_navigation.dart';

void main() {
  runApp(const GroBackApp());
}

class GroBackApp extends StatelessWidget {
  const GroBackApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'GroBack - Smart Shelf Monitor',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const BottomNavigation(),
    );
  }
}