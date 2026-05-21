import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/app_colors.dart';

/// A single node in the execution DAG.
/// Visual appearance is entirely driven by [status].
///
/// Statuses: pending | running | done | failed | retry
class ActionDagCard extends StatelessWidget {
  final String id;
  final String title;
  final int costPkr;
  final int latencyS;
  final String status;

  const ActionDagCard({
    super.key,
    required this.id,
    required this.title,
    required this.costPkr,
    required this.latencyS,
    this.status = 'pending',
  });

  // ─── Status-driven colors ─────────────────────────────────
  Color get _borderColor {
    switch (status) {
      case 'running':
        return AppColors.primaryBlue;
      case 'done':
        return AppColors.success;
      case 'failed':
        return AppColors.error;
      case 'retry':
        return AppColors.warning;
      default: // pending
        return AppColors.border;
    }
  }

  Color get _bgColor {
    switch (status) {
      case 'running':
        return AppColors.runningBg;
      case 'done':
        return AppColors.doneBg;
      case 'failed':
        return AppColors.failedBg;
      case 'retry':
        return AppColors.warningBg;
      default: // pending
        return AppColors.background;
    }
  }

  Color get _badgeColor {
    switch (status) {
      case 'running':
        return AppColors.primaryBlue;
      case 'done':
        return AppColors.success;
      case 'failed':
        return AppColors.error;
      case 'retry':
        return AppColors.warning;
      default: // pending
        return AppColors.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minWidth: 140, maxWidth: 148),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: _bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: _borderColor, width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // ─── Top row: badge + status dot ───────────────────
          Row(
            children: [
              // ID badge pill
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: _badgeColor,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  id,
                  style: GoogleFonts.poppins(
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                    color: AppColors.background,
                  ),
                ),
              ),
              const Spacer(),

              // Status dot
              if (status == 'running')
                _PulsingDot(color: _badgeColor)
              else
                Container(
                  width: 7,
                  height: 7,
                  decoration: BoxDecoration(
                    color: _badgeColor,
                    shape: BoxShape.circle,
                  ),
                ),
            ],
          ),

          const SizedBox(height: 6),

          // ─── Title ─────────────────────────────────────────
          Text(
            title,
            style: GoogleFonts.poppins(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color: AppColors.textPrimary,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),

          const SizedBox(height: 6),

          // ─── Meta pills row ────────────────────────────────
          Row(
            children: [
              // Cost pill
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.costPillBg,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  costPkr == 0 ? 'Free' : '${(costPkr / 1000).round()}k PKR',
                  style: GoogleFonts.poppins(
                    fontSize: 10,
                    fontWeight: FontWeight.w400,
                    color: AppColors.primaryDark,
                  ),
                ),
              ),
              const SizedBox(width: 6),

              // Latency pill
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '~${latencyS}s',
                  style: GoogleFonts.poppins(
                    fontSize: 10,
                    fontWeight: FontWeight.w400,
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ═════════════════════════════════════════════════════════════
// Pulsing status dot — animates only for 'running' status
// ═════════════════════════════════════════════════════════════

class _PulsingDot extends StatefulWidget {
  final Color color;
  const _PulsingDot({required this.color});

  @override
  State<_PulsingDot> createState() => _PulsingDotState();
}

class _PulsingDotState extends State<_PulsingDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _opacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);

    _opacity = Tween<double>(begin: 1.0, end: 0.3).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _opacity,
      child: Container(
        width: 7,
        height: 7,
        decoration: BoxDecoration(
          color: widget.color,
          shape: BoxShape.circle,
        ),
      ),
    );
  }
}
