import 'package:flutter/material.dart';
import '../utils/app_colors.dart';

class ContradictionCard extends StatefulWidget {
  final String id;
  final String title;
  final Map<String, dynamic> sourceA;
  final Map<String, dynamic> sourceB;
  final String resolution;
  final String? winner;
  final String? winnerLabel;
  final String rationale;

  const ContradictionCard({
    super.key,
    required this.id,
    required this.title,
    required this.sourceA,
    required this.sourceB,
    required this.resolution,
    this.winner,
    this.winnerLabel,
    required this.rationale,
  });

  @override
  State<ContradictionCard> createState() => _ContradictionCardState();
}

class _ContradictionCardState extends State<ContradictionCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    bool isReview = widget.resolution == 'needs_human_review';

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
            if (isReview)
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: 3,
                child: Container(color: AppColors.warning),
              ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      _StatusPill(resolution: widget.resolution),
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
                  ),
                  const SizedBox(height: 12),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        child: _SourceMiniCard(
                          source: widget.sourceA,
                          side: 'a',
                          winner: widget.winner,
                        ),
                      ),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 8),
                        child: Text(
                          "vs",
                          style: TextStyle(
                            fontFamily: 'Poppins',
                            fontWeight: FontWeight.w500,
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ),
                      Expanded(
                        child: _SourceMiniCard(
                          source: widget.sourceB,
                          side: 'b',
                          winner: widget.winner,
                        ),
                      ),
                    ],
                  ),
                  AnimatedSize(
                    duration: const Duration(milliseconds: 250),
                    curve: Curves.easeInOut,
                    alignment: Alignment.topCenter,
                    child: _expanded
                        ? Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 12),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: isReview
                                      ? const Color(0xFFFEF3E2)
                                      : AppColors.surface,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Text(
                                          isReview
                                              ? "⚠️  Human Review Required"
                                              : "🧠  Agent Rationale",
                                          style: const TextStyle(
                                            fontFamily: 'Poppins',
                                            fontWeight: FontWeight.w500,
                                            fontSize: 12,
                                            color: AppColors.textPrimary,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      widget.rationale,
                                      style: const TextStyle(
                                        fontFamily: 'Poppins',
                                        fontWeight: FontWeight.w400,
                                        fontSize: 13,
                                        color: AppColors.textSecondary,
                                        height: 1.5,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          )
                        : const SizedBox.shrink(),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          if (isReview) ...[
                            const Icon(Icons.help_outline,
                                size: 14, color: AppColors.warning),
                            const SizedBox(width: 4),
                            const Text(
                              "Winner: —",
                              style: TextStyle(
                                fontFamily: 'Poppins',
                                fontWeight: FontWeight.w400,
                                fontSize: 13,
                                color: AppColors.warning,
                              ),
                            ),
                          ] else ...[
                            const Text(
                              "Winner: ",
                              style: TextStyle(
                                fontFamily: 'Poppins',
                                fontWeight: FontWeight.w400,
                                fontSize: 13,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            Text(
                              widget.winnerLabel ?? "—",
                              style: const TextStyle(
                                fontFamily: 'Poppins',
                                fontWeight: FontWeight.w500,
                                fontSize: 13,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ],
                        ],
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

class _SourceMiniCard extends StatelessWidget {
  final Map<String, dynamic> source;
  final String side;
  final String? winner;

  const _SourceMiniCard({
    required this.source,
    required this.side,
    this.winner,
  });

  @override
  Widget build(BuildContext context) {
    bool iWon = (winner == 'source_a' && side == 'a') ||
        (winner == 'source_b' && side == 'b');
    bool bothTrue = winner == 'both';
    bool needsReview = winner == null;

    Color valueColor;
    if (bothTrue) {
      valueColor = AppColors.primaryBlue;
    } else if (needsReview) {
      valueColor = AppColors.warning;
    } else if (iWon) {
      valueColor = AppColors.success;
    } else {
      valueColor = AppColors.error;
    }

    bool showStrikethrough = !iWon && !bothTrue && !needsReview;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            source['name'] ?? '',
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 11,
              color: AppColors.textPrimary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 6),
          Text(
            source['value'] ?? '',
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 13,
              color: valueColor,
              decoration: showStrikethrough
                  ? TextDecoration.lineThrough
                  : TextDecoration.none,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            children: [
              _CredibilityDot(
                  credibility:
                      (source['credibility'] as num?)?.toDouble() ?? 0.0),
              const SizedBox(width: 4),
              Text(
                "${source['credibility']}",
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w400,
                  fontSize: 11,
                  color: AppColors.textSecondary,
                ),
              ),
              Text(
                "  ·  ${source['age_hours']} hrs ago",
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w400,
                  fontSize: 11,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CredibilityDot extends StatelessWidget {
  final double credibility;

  const _CredibilityDot({required this.credibility});

  @override
  Widget build(BuildContext context) {
    Color dotColor;
    if (credibility >= 0.80) {
      dotColor = AppColors.success;
    } else if (credibility >= 0.50) {
      dotColor = AppColors.warning;
    } else {
      dotColor = AppColors.error;
    }

    return Container(
      width: 6,
      height: 6,
      decoration: BoxDecoration(
        color: dotColor,
        shape: BoxShape.circle,
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  final String resolution;

  const _StatusPill({required this.resolution});

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color textColor;
    String label;

    if (resolution == 'resolved') {
      bgColor = const Color(0xFFE8F5EE);
      textColor = AppColors.success;
      label = "Resolved";
    } else if (resolution == 'needs_human_review') {
      bgColor = const Color(0xFFFDECEA);
      textColor = AppColors.error;
      label = "Needs Review";
    } else {
      bgColor = AppColors.surface;
      textColor = AppColors.textSecondary;
      label = resolution;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
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
