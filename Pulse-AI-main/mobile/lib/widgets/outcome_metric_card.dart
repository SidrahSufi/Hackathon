import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class OutcomeMetricCard extends StatelessWidget {
  final String pillLabel;
  final Color pillBgColor;
  final Color pillTextColor;
  final String primaryNumber;
  final Color primaryNumberColor;
  final String primarySublabel;
  final String secondaryNumber;
  final Color secondaryNumberColor;
  final String secondarySublabel;

  const OutcomeMetricCard({
    super.key,
    required this.pillLabel,
    required this.pillBgColor,
    required this.pillTextColor,
    required this.primaryNumber,
    required this.primaryNumberColor,
    required this.primarySublabel,
    required this.secondaryNumber,
    required this.secondaryNumberColor,
    required this.secondarySublabel,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: pillBgColor,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              pillLabel,
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w500,
                color: pillTextColor,
                fontFamily: 'Poppins',
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            primaryNumber,
            style: TextStyle(
              fontSize: 28,
              fontWeight: FontWeight.w500,
              color: primaryNumberColor,
              fontFamily: 'Poppins',
              height: 1.2,
            ),
          ),
          Text(
            primarySublabel,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w400,
              color: AppColors.textSecondary,
              fontFamily: 'Poppins',
            ),
          ),
          const SizedBox(height: 16),
          Text(
            secondaryNumber,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w400,
              color: secondaryNumberColor,
              fontFamily: 'Poppins',
              height: 1.2,
            ),
          ),
          Text(
            secondarySublabel,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w400,
              color: AppColors.textSecondary,
              fontFamily: 'Poppins',
            ),
          ),
        ],
      ),
    );
  }
}
