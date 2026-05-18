import 'package:flutter/material.dart';

/// BizPulse Design System — Color Tokens
/// Source of truth for all colors in the app.
/// NEVER hardcode hex values in screen files — always use AppColors.xxx
class AppColors {
  AppColors._(); // prevent instantiation

  static const Color background = Color(0xFFFFFFFF);
  static const Color surface = Color(0xFFF5F7FA);
  static const Color primaryDark = Color(0xFF1A3C6E);
  static const Color primaryBlue = Color(0xFF2E6BE6);
  static const Color success = Color(0xFF27AE60);
  static const Color warning = Color(0xFFF39C12);
  static const Color error = Color(0xFFE74C3C);
  static const Color textPrimary = Color(0xFF1A1A2E);
  static const Color textSecondary = Color(0xFF6B7280);
  static const Color border = Color(0xFFE5E7EB);

  // Derived tints for status pills and highlighted cards
  static const Color successTint = Color(0xFFE8F8EF);
  static const Color warningTint = Color(0xFFFEF6E4);
  static const Color warningBg = Color(0xFFFFFCF5);
  static const Color errorTint = Color(0xFFFDECEC);
  static const Color blueTint = Color(0xFFE8F0FE);

  // DAG node status backgrounds
  static const Color runningBg = Color(0xFFEEF4FF);
  static const Color doneBg = Color(0xFFF0FBF4);
  static const Color failedBg = Color(0xFFFEF0EE);

  // Meta pill accent
  static const Color costPillBg = Color(0xFFEEF3FB);
}
