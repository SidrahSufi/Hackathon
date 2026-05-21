import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../models/outcome_model.dart';
import '../widgets/outcome_metric_card.dart';
import '../widgets/bottom_nav_bar.dart';
import '../services/api_services.dart';

class OutcomeScreen extends StatefulWidget {
  const OutcomeScreen({super.key});

  @override
  State<OutcomeScreen> createState() => _OutcomeScreenState();
}

class _OutcomeScreenState extends State<OutcomeScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  // Live data
  OutcomeModel? _data;
  bool _loading = true;
  String? _error;
  String? _runId;

  // Animations
  late Animation<double> _bannerOpacity;
  late Animation<Offset> _bannerOffset;

  late Animation<double> _cardsOpacity;
  late Animation<Offset> _cardsOffset;

  late Animation<double> _graphOpacity;

  late Animation<double> _economicsOpacity;
  late Animation<Offset> _economicsOffset;

  late List<Animation<double>> _actionOpacities;
  late List<Animation<Offset>> _actionOffsets;

  late Animation<double> _buttonsOpacity;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1250), // 0 to 950+300 = 1250ms
    );

    // 0ms: Region banner — fade + slide up 20px, 300ms
    _bannerOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.0, 0.24)), // 300/1250 = 0.24
    );
    _bannerOffset =
        Tween<Offset>(begin: const Offset(0, 20), end: Offset.zero).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.0, 0.24, curve: Curves.easeOut)),
    );

    // 150ms: Before/After cards — fade + slide up 20px, 300ms
    _cardsOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.12, 0.36)), // (150-450)/1250
    );
    _cardsOffset =
        Tween<Offset>(begin: const Offset(0, 20), end: Offset.zero).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.12, 0.36, curve: Curves.easeOut)),
    );

    // 300ms: Graph card — fade in, 300ms
    _graphOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.24, 0.48)), // (300-600)/1250
    );

    // 400ms: Graph line draw is handled inside CustomPainter, using an animation starting at 400ms for 600ms (0.32 to 0.80)

    // 450ms: Economics card — fade + slide up 20px, 300ms
    _economicsOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.36, 0.60)), // (450-750)/1250
    );
    _economicsOffset =
        Tween<Offset>(begin: const Offset(0, 20), end: Offset.zero).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.36, 0.60, curve: Curves.easeOut)),
    );

    // 550ms–950ms: Action rows — stagger 100ms each, fade + slide up 20px, 300ms each
    _actionOpacities = [];
    _actionOffsets = [];
    for (int i = 0; i < 5; i++) {
      double start = 0.44 + (i * 0.08); // 550ms + i*100ms -> 0.44 + 0.08*i
      double end = start + 0.24; // + 300ms -> + 0.24
      _actionOpacities.add(Tween<double>(begin: 0, end: 1).animate(
        CurvedAnimation(parent: _controller, curve: Interval(start, end)),
      ));
      _actionOffsets.add(
          Tween<Offset>(begin: const Offset(0, 20), end: Offset.zero).animate(
        CurvedAnimation(
            parent: _controller,
            curve: Interval(start, end, curve: Curves.easeOut)),
      ));
    }

    // 900ms: Buttons — fade in, 300ms
    _buttonsOpacity = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
          parent: _controller,
          curve: const Interval(0.72, 0.96)), // (900-1200)/1250
    );

    _controller.forward();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_runId == null) {
      final raw = ModalRoute.of(context)?.settings.arguments;
      if (raw is String) {
        _runId = raw;
      } else if (raw is Map) {
        _runId = raw['run_id'] as String?;
      }
      if (_runId != null) {
        _fetchOutcome(_runId!);
      } else {
        setState(() {
          _loading = false;
          _error = 'No run_id provided';
        });
      }
    }
  }

  Future<void> _fetchOutcome(String runId) async {
    try {
      final raw = await ApiService.getOutcome(runId);
      if (!mounted) return;
      // Map backend outcome.json → OutcomeModel
      final before = (raw['before'] as Map?) ?? const {};
      final after = (raw['after'] as Map?) ?? const {};
      final model = OutcomeModel(
        detectedRegion: (raw['detected_region'] as String?) ?? '—',
        ordersPerDayBefore:
            ((before['orders_per_day_14d_avg'] as num?) ?? 0).round(),
        revenueAtRiskPkr:
            ((before['revenue_at_risk_30d_pkr'] as num?) ?? 0).round(),
        ordersPerDayAfter:
            ((after['orders_per_day_projected_7d'] as num?) ?? 0).round(),
        projectedReach: ((after['projected_reach'] as num?) ?? 0).toInt(),
        revenueRecoveredPkr:
            ((after['revenue_recovery_projected_pkr'] as num?) ?? 0).round(),
        campaignCostPkr: ((raw['campaign_cost_pkr'] as num?) ?? 0).round(),
        roas: ((raw['projected_roas'] as num?) ?? 0).toDouble(),
        chainLatencyS: ((raw['chain_latency_s'] as num?) ?? 0).toDouble(),
        otherRegionsStatus: (raw['other_regions_status'] as String?) ??
            'All other regions unchanged',
      );
      setState(() {
        _data = model;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  /// Convenience getter — falls back to a placeholder while loading.
  OutcomeModel get data => _data ?? demoOutcome;

  String _formatNumber(int number) {
    // Indian-style grouping (lakh/crore) since the demo uses PKR
    if (number >= 100000) {
      final s = number.toString();
      final lakhs = s.length > 5 ? s.substring(0, s.length - 5) : '0';
      final rest = s.substring(s.length - 5);
      final thousands = rest.substring(0, 2);
      final hundreds = rest.substring(2);
      return '$lakhs,$thousands,$hundreds';
    }
    if (number >= 1000) {
      final s = number.toString();
      return '${s.substring(0, s.length - 3)},${s.substring(s.length - 3)}';
    }
    return number.toString();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        backgroundColor: AppColors.background,
        body: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null) {
      return Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(backgroundColor: AppColors.background, elevation: 0),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontFamily: 'Poppins',
                fontSize: 13,
                color: AppColors.error,
              ),
            ),
          ),
        ),
      );
    }
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        scrolledUnderElevation: 0,
        automaticallyImplyLeading: false, // no back button
        centerTitle: true,
        title: Column(
          children: [
            const Text(
              "Outcome",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                fontSize: 18,
                color: AppColors.textPrimary,
              ),
            ),
            Text(
              "${data.detectedRegion} · Run completed in ${data.chainLatencyS}s",
              style: const TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                fontSize: 13,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 2. REGION DETECTION BANNER
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _bannerOpacity.value,
                  child: Transform.translate(
                    offset: _bannerOffset.value,
                    child: child,
                  ),
                ),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    border: Border.all(color: AppColors.border, width: 0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.radar,
                          color: AppColors.primaryBlue, size: 28),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              "Underperforming region detected",
                              style: TextStyle(
                                fontFamily: 'Poppins',
                                fontSize: 12,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            Text(
                              data.detectedRegion.toUpperCase(),
                              style: const TextStyle(
                                fontFamily: 'Poppins',
                                fontWeight: FontWeight.w500,
                                fontSize: 22,
                                color: AppColors.primaryDark,
                              ),
                            ),
                            const Text(
                              "5 other regions stable · no action taken",
                              style: TextStyle(
                                fontFamily: 'Poppins',
                                fontSize: 12,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // 3. BEFORE vs AFTER CARDS
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _cardsOpacity.value,
                  child: Transform.translate(
                    offset: _cardsOffset.value,
                    child: child,
                  ),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: OutcomeMetricCard(
                        pillLabel: "BEFORE",
                        pillBgColor: AppColors.surface,
                        pillTextColor: AppColors.textSecondary,
                        primaryNumber: data.ordersPerDayBefore.toString(),
                        primaryNumberColor: AppColors.textPrimary,
                        primarySublabel: "orders/day",
                        secondaryNumber:
                            "₨ ${_formatNumber(data.revenueAtRiskPkr)}",
                        secondaryNumberColor: AppColors.error,
                        secondarySublabel: "at risk",
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.symmetric(horizontal: 12),
                      child: Icon(Icons.arrow_forward,
                          color: AppColors.textSecondary, size: 20),
                    ),
                    Expanded(
                      child: OutcomeMetricCard(
                        pillLabel: "PROJECTED",
                        pillBgColor: const Color(0xFFEBF2FE), // blue tint pill
                        pillTextColor: AppColors.primaryBlue,
                        primaryNumber: "↑ ${data.ordersPerDayAfter}",
                        primaryNumberColor: AppColors.success,
                        primarySublabel: "orders/day",
                        secondaryNumber:
                            "↑ ₨ ${_formatNumber(data.revenueRecoveredPkr)}",
                        secondaryNumberColor: AppColors.success,
                        secondarySublabel: "recovered",
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 4. RECOVERY GRAPH
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _graphOpacity.value,
                  child: child,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Recovery Projection",
                      style: TextStyle(
                        fontFamily: 'Poppins',
                        fontWeight: FontWeight.w500,
                        fontSize: 14,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Container(
                      height: 200,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        border: Border.all(color: AppColors.border, width: 0.5),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      padding: const EdgeInsets.only(
                          top: 24, right: 16, bottom: 20, left: 16),
                      child: AnimatedBuilder(
                        animation: _controller,
                        builder: (context, child) {
                          // Graph line animation: 400ms delay, 600ms duration
                          // Which corresponds to 0.32 to 0.8 in _controller space
                          double progress = 0.0;
                          if (_controller.value > 0.32) {
                            progress = (_controller.value - 0.32) / 0.48;
                            if (progress > 1.0) progress = 1.0;
                          }
                          return CustomPaint(
                            painter: RecoveryGraphPainter(
                              progress: progress,
                              beforeOrders: data.ordersPerDayBefore.toDouble(),
                              afterOrders: data.ordersPerDayAfter.toDouble(),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 5. CAMPAIGN ECONOMICS CARD
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _economicsOpacity.value,
                  child: Transform.translate(
                    offset: _economicsOffset.value,
                    child: child,
                  ),
                ),
                child: Container(
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    border: Border.all(color: AppColors.border, width: 0.5),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: IntrinsicHeight(
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _buildEconomicsCol(
                            "${_formatNumber(data.projectedReach)}",
                            AppColors.textPrimary,
                            "Projected Reach",
                            "impressions"),
                        const VerticalDivider(
                            color: AppColors.border, width: 1, thickness: 0.5),
                        _buildEconomicsCol(
                            "₨ ${_formatNumber(data.revenueRecoveredPkr)}",
                            AppColors.textPrimary,
                            "Revenue Recovered",
                            ""),
                        const VerticalDivider(
                            color: AppColors.border, width: 1, thickness: 0.5),
                        _buildEconomicsCol("${data.roas.toStringAsFixed(1)}×",
                            AppColors.success, "ROAS", "return"),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // 6. ACTION TRACE
              const Text(
                "Actions that caused this",
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w500,
                  fontSize: 14,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),
              ..._buildActionRows(),
              const SizedBox(height: 32),

              // 7. BOTTOM BUTTON ROW
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _buttonsOpacity.value,
                  child: child,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        height: 52,
                        decoration: BoxDecoration(
                          color: AppColors.background,
                          border: Border.all(color: AppColors.primaryBlue),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {},
                            borderRadius: BorderRadius.circular(8),
                            child: const Center(
                              child: Text(
                                "Download Report",
                                style: TextStyle(
                                  fontFamily: 'Poppins',
                                  fontWeight: FontWeight.w500,
                                  color: AppColors.primaryBlue,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Container(
                        height: 52,
                        decoration: BoxDecoration(
                          color: AppColors.primaryBlue,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              Navigator.pushNamedAndRemoveUntil(
                                context,
                                RouteNames.home,
                                (r) => false,
                              );
                            },
                            borderRadius: BorderRadius.circular(8),
                            child: const Center(
                              child: Text(
                                "New Analysis →",
                                style: TextStyle(
                                  fontFamily: 'Poppins',
                                  fontWeight: FontWeight.w500,
                                  color: Colors.white,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 2),
    );
  }

  Widget _buildEconomicsCol(
      String value, Color valueColor, String line1, String line2) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          value,
          style: TextStyle(
            fontFamily: 'Poppins',
            fontWeight: FontWeight.w500,
            fontSize: 20,
            color: valueColor,
            height: 1.2,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          line1,
          style: const TextStyle(
            fontFamily: 'Poppins',
            fontSize: 11,
            color: AppColors.textSecondary,
          ),
        ),
        if (line2.isNotEmpty)
          Text(
            line2,
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontSize: 11,
              color: AppColors.textSecondary,
            ),
          ),
      ],
    );
  }

  List<Widget> _buildActionRows() {
    final actions = [
      {
        "text": "Fix campaign delivery bug · Reach +40%",
        "icon": Icons.check_circle_outline,
        "color": AppColors.success,
        "pillText": "Done",
        "pillBg": const Color(0xFFE8F5EE),
        "pillTextColor": AppColors.success,
      },
      {
        "text": "Launch Lahore flash sale · Orders ↑",
        "icon": Icons.check_circle_outline,
        "color": AppColors.success,
        "pillText": "Done",
        "pillBg": const Color(0xFFE8F5EE),
        "pillTextColor": AppColors.success,
      },
      {
        "text": "Reallocate ₨ 3,20,000 budget · Applied",
        "icon": Icons.check_circle_outline,
        "color": AppColors.success,
        "pillText": "Done",
        "pillBg": const Color(0xFFE8F5EE),
        "pillTextColor": AppColors.success,
      },
      {
        "text": "Push loyalty SMS to 5,200 users · Sent",
        "icon": Icons.check_circle_outline,
        "color": AppColors.success,
        "pillText": "Done",
        "pillBg": const Color(0xFFE8F5EE),
        "pillTextColor": AppColors.success,
      },
      {
        "text": "Competitor pricing — monitor",
        "icon": Icons.warning_amber_outlined,
        "color": AppColors.warning,
        "pillText": "Review",
        "pillBg": const Color(0xFFFFF3E0),
        "pillTextColor": AppColors.warning,
      },
    ];

    return List.generate(actions.length, (index) {
      final action = actions[index];
      return AnimatedBuilder(
        animation: _controller,
        builder: (context, child) => Opacity(
          opacity: _actionOpacities[index].value,
          child: Transform.translate(
            offset: _actionOffsets[index].value,
            child: child,
          ),
        ),
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          decoration: BoxDecoration(
            color: AppColors.background,
            border: Border.all(color: AppColors.border, width: 0.5),
            borderRadius: BorderRadius.circular(8),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: Container(
              decoration: BoxDecoration(
                border: Border(
                  left: BorderSide(color: action["color"] as Color, width: 3),
                ),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
              child: Row(
                children: [
                  Icon(action["icon"] as IconData,
                      color: action["color"] as Color, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      action["text"] as String,
                      style: const TextStyle(
                        fontFamily: 'Poppins',
                        fontSize: 12,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: action["pillBg"] as Color,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      action["pillText"] as String,
                      style: TextStyle(
                        fontFamily: 'Poppins',
                        fontWeight: FontWeight.w500,
                        fontSize: 10,
                        color: action["pillTextColor"] as Color,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    });
  }
}

class RecoveryGraphPainter extends CustomPainter {
  final double progress;
  final double beforeOrders;
  final double afterOrders;

  RecoveryGraphPainter({
    required this.progress,
    this.beforeOrders = 142,
    this.afterOrders = 186,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // Y-axis: 100 to 220 -> range = 120
    // X-axis: Day 1 to Day 14
    const double minY = 100;
    const double maxY = 220;
    const double rangeY = maxY - minY;

    double yToPixels(double y) {
      return size.height - ((y - minY) / rangeY) * size.height;
    }

    // Draw Y-axis labels
    final textPainter = TextPainter(
      textDirection: TextDirection.ltr,
    );

    void drawLabel(String text, Offset offset,
        {TextAlign align = TextAlign.left}) {
      textPainter.text = TextSpan(
        text: text,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 10,
          fontFamily: 'Poppins',
        ),
      );
      textPainter.textAlign = align;
      textPainter.layout();
      textPainter.paint(canvas, offset);
    }

    // Draw grid and Y labels
    final yLabels = [200.0, 150.0, 100.0];
    const leftPadding = 24.0;
    final graphWidth = size.width - leftPadding;

    for (var y in yLabels) {
      final yPos = yToPixels(y);
      drawLabel("${y.toInt()}", Offset(0, yPos - 6));

      final gridPaint = Paint()
        ..color = AppColors.border
        ..strokeWidth = 0.5
        ..style = PaintingStyle.stroke;

      // Draw dashed horizontal line
      double x = leftPadding;
      while (x < size.width) {
        canvas.drawLine(Offset(x, yPos), Offset(x + 4, yPos), gridPaint);
        x += 8;
      }
    }

    // X-axis labels
    final bottomY = size.height + 8;
    drawLabel("Day 1", Offset(leftPadding, bottomY));
    drawLabel("Day 7", Offset(leftPadding + graphWidth / 2 - 14, bottomY));
    drawLabel("Day 14", Offset(size.width - 32, bottomY));

    // Vertical dotted line at Day 7 (center)
    final centerX = leftPadding + graphWidth / 2;
    final centerLinePaint = Paint()
      ..color = AppColors.warning
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;

    double y = 0;
    while (y < size.height) {
      canvas.drawLine(
          Offset(centerX, y), Offset(centerX, y + 4), centerLinePaint);
      y += 8;
    }

    // Label tag "Actions executed"
    textPainter.text = const TextSpan(
      text: "Actions executed",
      style: TextStyle(
        color: AppColors.warning,
        fontSize: 10,
        fontFamily: 'Poppins',
      ),
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(centerX - textPainter.width / 2, -16));

    // Lines
    final pathBefore = Path();
    pathBefore.moveTo(leftPadding, yToPixels(beforeOrders));
    pathBefore.lineTo(size.width, yToPixels(beforeOrders * 0.9));

    final beforeLinePaint = Paint()
      ..color = AppColors.textSecondary
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    // Draw dashed before line
    double distance = 0;
    const dashWidth = 5.0;
    const dashSpace = 5.0;
    final lengthBefore = (Offset(size.width, yToPixels(130)) -
            Offset(leftPadding, yToPixels(142)))
        .distance;
    double currentX = leftPadding;
    double currentY = yToPixels(beforeOrders);
    final dx = (size.width - leftPadding) / lengthBefore;
    final dy = (yToPixels(130) - yToPixels(142)) / lengthBefore;

    while (distance < lengthBefore) {
      canvas.drawLine(
        Offset(currentX, currentY),
        Offset(currentX + dx * dashWidth, currentY + dy * dashWidth),
        beforeLinePaint,
      );
      currentX += dx * (dashWidth + dashSpace);
      currentY += dy * (dashWidth + dashSpace);
      distance += dashWidth + dashSpace;
    }

    // After projection line
    if (progress > 0) {
      final pathAfter = Path();
      // Starts at Day 7 (center)
      pathAfter.moveTo(centerX, yToPixels(beforeOrders));

      // Control point for curve
      final endX = size.width;
      final endY = yToPixels(afterOrders);
      pathAfter.quadraticBezierTo(
          centerX + (endX - centerX) / 2, yToPixels(142), endX, endY);

      // Extract path up to progress
      final pathMetricsList = pathAfter.computeMetrics().toList();
      if (pathMetricsList.isNotEmpty) {
        final pathMetrics = pathMetricsList.first;
        final extractPath =
            pathMetrics.extractPath(0, pathMetrics.length * progress);

        // Draw Fill area
        final fillPath = Path.from(extractPath);
        final currentMetric =
            pathMetrics.getTangentForOffset(pathMetrics.length * progress);
        if (currentMetric != null) {
          fillPath.lineTo(currentMetric.position.dx, size.height);
          fillPath.lineTo(centerX, size.height);
          fillPath.close();

          final fillPaint = Paint()
            ..color = const Color(0xFFEBF2FE).withOpacity(0.4)
            ..style = PaintingStyle.fill;
          canvas.drawPath(fillPath, fillPaint);
        }

        // Draw solid line
        final afterLinePaint = Paint()
          ..color = AppColors.primaryBlue
          ..strokeWidth = 2.0
          ..style = PaintingStyle.stroke;
        canvas.drawPath(extractPath, afterLinePaint);

        // End dot
        if (progress >= 1.0) {
          final dotPaint = Paint()
            ..color = AppColors.primaryBlue
            ..style = PaintingStyle.fill;
          canvas.drawCircle(Offset(endX, endY), 4, dotPaint);
        }
      }
    }
  }

  @override
  bool shouldRepaint(covariant RecoveryGraphPainter oldDelegate) {
    return oldDelegate.progress != progress;
  }
}
