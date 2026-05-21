import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class InsightCard extends StatefulWidget {
  final String id;
  final String title;
  final String detail;
  final String severity;
  final double confidence;
  final List<String> evidenceRefs;

  const InsightCard({
    super.key,
    required this.id,
    required this.title,
    required this.detail,
    required this.severity,
    required this.confidence,
    required this.evidenceRefs,
  });

  @override
  State<InsightCard> createState() => _InsightCardState();
}

class _InsightCardState extends State<InsightCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final String confidencePercent = "${(widget.confidence * 100).round()}%";

    return GestureDetector(
      onTap: () {
        setState(() {
          _expanded = !_expanded;
        });
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeInOut,
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          color: AppColors.background,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border, width: 0.5),
        ),
        child: Stack(
          children: [
            if (widget.severity == 'critical')
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: 3,
                child: Container(color: AppColors.error),
              ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _SeverityPill(severity: widget.severity),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            confidencePercent,
                            style: const TextStyle(
                              fontFamily: 'Poppins',
                              fontWeight: FontWeight.w500,
                              fontSize: 14,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const Text(
                            "confidence",
                            style: TextStyle(
                              fontFamily: 'Poppins',
                              fontWeight: FontWeight.w400,
                              fontSize: 11,
                              color: AppColors.textSecondary,
                              height: 1.0,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    widget.title,
                    style: const TextStyle(
                      fontFamily: 'Poppins',
                      fontWeight: FontWeight.w500,
                      fontSize: 15,
                      color: AppColors.textPrimary,
                    ),
                    maxLines: null,
                  ),
                  AnimatedSize(
                    duration: const Duration(milliseconds: 250),
                    curve: Curves.easeInOut,
                    alignment: Alignment.topCenter,
                    child: _expanded
                        ? Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 10),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  widget.detail,
                                  style: const TextStyle(
                                    fontFamily: 'Poppins',
                                    fontWeight: FontWeight.w400,
                                    fontSize: 13,
                                    color: AppColors.textSecondary,
                                    height: 1.5,
                                  ),
                                ),
                              ),
                            ],
                          )
                        : const SizedBox.shrink(),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: widget.evidenceRefs.map((ref) {
                            return _EvidencePill(refText: ref);
                          }).toList(),
                        ),
                      ),
                      AnimatedRotation(
                        turns: _expanded ? 0.5 : 0.0,
                        duration: const Duration(milliseconds: 200),
                        child: const Icon(
                          Icons.keyboard_arrow_down_outlined,
                          size: 20,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SeverityPill extends StatelessWidget {
  final String severity;

  const _SeverityPill({required this.severity});

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color textColor;

    switch (severity.toLowerCase()) {
      case 'critical':
        bgColor = const Color(0xFFFDECEA);
        textColor = AppColors.error;
        break;
      case 'high':
        bgColor = const Color(0xFFFEF3E2);
        textColor = AppColors.warning;
        break;
      case 'medium':
        bgColor = const Color(0xFFEBF2FE);
        textColor = AppColors.primaryBlue;
        break;
      case 'low':
        bgColor = const Color(0xFFE8F5EE);
        textColor = AppColors.success;
        break;
      default:
        bgColor = AppColors.surface;
        textColor = AppColors.textSecondary;
    }

    String capitalized = severity.isNotEmpty
        ? '${severity[0].toUpperCase()}${severity.substring(1)}'
        : severity;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        capitalized,
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

class _EvidencePill extends StatelessWidget {
  final String refText;

  const _EvidencePill({required this.refText});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Text(
        refText,
        style: const TextStyle(
          fontFamily: 'Poppins',
          fontWeight: FontWeight.w400,
          fontSize: 11,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
