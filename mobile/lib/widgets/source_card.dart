import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class SourceCard extends StatelessWidget {
  final String fileName;
  final String fileType;
  final VoidCallback onRemove;

  const SourceCard({
    super.key,
    required this.fileName,
    required this.fileType,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppColors.border,
          width: 0.5,
        ),
      ),
      child: Row(
        children: [
          _TypePill(fileType: fileType),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              fileName,
              style: const TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                fontSize: 13,
                color: AppColors.textPrimary,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          GestureDetector(
            onTap: onRemove,
            child: const Icon(
              Icons.close,
              size: 18,
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }
}

class _TypePill extends StatelessWidget {
  final String fileType;

  const _TypePill({required this.fileType});

  @override
  Widget build(BuildContext context) {
    final String type = fileType.toUpperCase();
    Color bgColor;
    Color textColor;

    switch (type) {
      case 'PDF':
        bgColor = const Color(0xFFEBF2FE);
        textColor = AppColors.primaryBlue;
        break;
      case 'CSV':
        bgColor = const Color(0xFFE8F5EE);
        textColor = AppColors.success;
        break;
      case 'JSON':
        bgColor = const Color(0xFFFEF3E2);
        textColor = AppColors.warning;
        break;
      case 'TXT':
        bgColor = AppColors.surface;
        textColor = AppColors.textSecondary;
        break;
      case 'URL':
        bgColor = const Color(0xFFF0EEFF);
        textColor = const Color(0xFF6B4EFF);
        break;
      default:
        bgColor = AppColors.surface;
        textColor = AppColors.textSecondary;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        type,
        style: TextStyle(
          fontFamily: 'Poppins',
          fontWeight: FontWeight.w500,
          fontSize: 11,
          color: textColor,
        ),
      ),
    );
  }
}
