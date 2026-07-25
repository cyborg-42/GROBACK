import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const GroBackApp());
}

class GroBackApp extends StatelessWidget {
  const GroBackApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'GroBack',
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
    );
  }
}