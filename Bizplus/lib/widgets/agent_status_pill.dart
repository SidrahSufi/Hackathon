import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/app_colors.dart';

/// BizPulse — Agent Status Pill
/// Handles different background and text colors for agents and event kinds.
class AgentStatusPill extends StatelessWidget {
  final String label;
  final Color backgroundColor;
  final Color textColor;
  final double fontSize;

  const AgentStatusPill({
    super.key,
    required this.label,
    required this.backgroundColor,
    required this.textColor,
    this.fontSize = 9,
  });

  factory AgentStatusPill.agent(String agent) {
    Color bg;
    Color text;

    switch (agent) {
      case 'Ingestion':
        bg = const Color(0xFFEEF4FF);
        text = AppColors.primaryBlue;
        break;
      case 'Insight':
        bg = const Color(0xFFE8F8EF);
        text = AppColors.success;
        break;
      case 'ConflictResolver':
        bg = const Color(0xFFFEF6E4);
        text = AppColors.warning;
        break;
      case 'ActionPlanner':
        bg = const Color(0xFFF0EEFF);
        text = const Color(0xFF6C5CE7);
        break;
      case 'Executor':
        bg = const Color(0xFFFEF0EE);
        text = AppColors.error;
        break;
      case 'Monitor':
        bg = const Color(0xFFE8F8EF);
        text = AppColors.success;
        break;
      default:
        bg = AppColors.surface;
        text = AppColors.textSecondary;
    }

    // Special display name for ConflictResolver
    String displayName = agent == 'ConflictResolver' ? 'Conflict' : agent;

    return AgentStatusPill(
      label: displayName,
      backgroundColor: bg,
      textColor: text,
    );
  }

  factory AgentStatusPill.kind(String kind) {
    Color bg;
    Color text;

    switch (kind) {
      case 'completed':
        bg = const Color(0xFFE8F8EF);
        text = AppColors.success;
        break;
      case 'started':
        bg = const Color(0xFFEEF4FF);
        text = AppColors.primaryBlue;
        break;
      case 'failed':
        bg = const Color(0xFFFEF0EE);
        text = AppColors.error;
        break;
      case 'retry':
      case 'fallback':
        bg = const Color(0xFFFEF6E4);
        text = AppColors.warning;
        break;
      default:
        bg = AppColors.surface;
        text = AppColors.textSecondary;
    }

    return AgentStatusPill(
      label: kind.toUpperCase(),
      backgroundColor: bg,
      textColor: text,
      fontSize: 8,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: GoogleFonts.poppins(
          fontSize: fontSize,
          fontWeight: FontWeight.w500,
          color: textColor,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}
