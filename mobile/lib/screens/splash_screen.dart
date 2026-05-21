import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with TickerProviderStateMixin {
  late AnimationController _contentController;
  late AnimationController _cardsController;
  late AnimationController _chartController;
  late AnimationController _ringController;
  late AnimationController _streakController;

  late Animation<double> _contentOpacity;
  late Animation<Offset> _contentSlide;
  late Animation<double> _cardsOpacity;
  late Animation<Offset> _cardsSlide;
  late Animation<double> _chartOpacity;
  late Animation<Offset> _chartSlide;
  late Animation<double> _ringOpacity;

  @override
  void initState() {
    super.initState();

    _ringController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 6000),
    )..repeat(reverse: true);
    _ringOpacity = Tween<double>(begin: 1.0, end: 0.35).animate(
      CurvedAnimation(parent: _ringController, curve: Curves.easeInOut),
    );

    _streakController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 5000),
    )..repeat();

    _contentController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _contentOpacity = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _contentController, curve: Curves.easeOut),
    );
    _contentSlide =
        Tween<Offset>(begin: const Offset(0, 0.15), end: Offset.zero).animate(
          CurvedAnimation(
            parent: _contentController,
            curve: const Cubic(0.22, 1, 0.36, 1),
          ),
        );

    _cardsController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _cardsOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _cardsController, curve: Curves.easeOut));
    _cardsSlide = Tween<Offset>(begin: const Offset(0, 0.10), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _cardsController,
            curve: const Cubic(0.22, 1, 0.36, 1),
          ),
        );

    _chartController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _chartOpacity = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(parent: _chartController, curve: Curves.easeOut));
    _chartSlide = Tween<Offset>(begin: const Offset(0, 0.12), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _chartController,
            curve: const Cubic(0.22, 1, 0.36, 1),
          ),
        );

    _runSequence();
  }

  Future<void> _runSequence() async {
    _contentController.forward();
    await Future.delayed(const Duration(milliseconds: 200));
    _cardsController.forward();
    await Future.delayed(const Duration(milliseconds: 120));
    _chartController.forward();
    await Future.delayed(const Duration(milliseconds: 2500));
    if (mounted) {
      Navigator.pushReplacementNamed(context, RouteNames.home);
    }
  }

  @override
  void dispose() {
    _contentController.dispose();
    _cardsController.dispose();
    _chartController.dispose();
    _ringController.dispose();
    _streakController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;
    final pad = MediaQuery.of(context).padding;

    return Scaffold(
      backgroundColor: const Color(0xFF070E1C),
      body: Stack(
        children: [
          // Background
          const Positioned.fill(child: _Background()),

          // Grid
          Positioned.fill(
            child: Opacity(
              opacity: 0.035,
              child: CustomPaint(painter: _GridPainter()),
            ),
          ),

          // Rings
          Center(
            child: AnimatedBuilder(
              animation: _ringOpacity,
              builder: (_, __) => Stack(
                alignment: Alignment.center,
                children: [
                  _Ring(size: 500, opacity: _ringOpacity.value),
                  _Ring(size: 340, opacity: _ringOpacity.value * 0.65),
                ],
              ),
            ),
          ),

          // Dot clusters
          const Positioned(top: 58, left: 26, child: _DotCluster()),
          const Positioned(bottom: 72, right: 26, child: _DotCluster()),

          // Streaks
          _Streak(
            controller: _streakController,
            left: size.width * 0.22,
            top: size.height * 0.07,
            height: 110,
            phase: 0.0,
          ),
          _Streak(
            controller: _streakController,
            left: size.width * 0.70,
            top: size.height * 0.14,
            height: 75,
            phase: 0.38,
          ),
          _Streak(
            controller: _streakController,
            left: size.width * 0.46,
            top: size.height * 0.74,
            height: 90,
            phase: 0.66,
          ),

          // Floating stat cards
          FadeTransition(
            opacity: _cardsOpacity,
            child: SlideTransition(
              position: _cardsSlide,
              child: Stack(
                children: [
                  // Revenue card — left
                  Positioned(
                    bottom: size.height * 0.245,
                    left: 32,
                    child: _StatCard(
                      value: 'PKR 2.4M',
                      valueAccent: ' ↑12%',
                      label: 'Revenue',
                    ),
                  ),
                  // Regions card — right
                  Positioned(
                    bottom: size.height * 0.245,
                    right: 28,
                    child: _StatCard(value: '6 Regions', label: 'Monitored'),
                  ),
                ],
              ),
            ),
          ),

          // Bar chart illustration
          Positioned(
            bottom: size.height * 0.175,
            left: 0,
            right: 0,
            child: FadeTransition(
              opacity: _chartOpacity,
              child: SlideTransition(
                position: _chartSlide,
                child: const Center(child: _BarChart()),
              ),
            ),
          ),

          // Version
          Positioned(
            top: pad.top + 16,
            right: 24,
            child: const Text(
              'v1.0.0',
              style: TextStyle(
                fontFamily: 'Poppins',
                fontSize: 10,
                fontWeight: FontWeight.w400,
                color: Color(0x2EFFFFFF),
                letterSpacing: 0.5,
              ),
            ),
          ),

          // Main logo + name + tagline
          Center(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 80),
              child: FadeTransition(
                opacity: _contentOpacity,
                child: SlideTransition(
                  position: _contentSlide,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const _LogoIcon(),
                      const SizedBox(height: 26),
                      _AppName(),
                      const SizedBox(height: 12),
                      const Text(
                        'The Pulse of Smarter Business',
                        style: TextStyle(
                          fontFamily: 'Poppins',
                          fontSize: 13,
                          fontWeight: FontWeight.w400,
                          color: Color(0x6BFFFFFF),
                          letterSpacing: 0.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),

          // Footer
          Positioned(
            bottom: pad.bottom + 16,
            left: 0,
            right: 0,
            child: const Center(
              child: Text(
                'AISeekho 2026 · Google Antigravity Hackathon',
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontSize: 10,
                  fontWeight: FontWeight.w400,
                  color: Color(0x29FFFFFF),
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Background
// ---------------------------------------------------------------------------

class _Background extends StatelessWidget {
  const _Background();
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(0, -0.28),
          radius: 1.15,
          colors: [Color(0xFF0D2154), Color(0xFF070E1C)],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Grid
// ---------------------------------------------------------------------------

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = Colors.white
      ..strokeWidth = 0.5;
    for (double x = 0; x <= size.width; x += 36) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), p);
    }
    for (double y = 0; y <= size.height; y += 36) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), p);
    }
  }

  @override
  bool shouldRepaint(_) => false;
}

// ---------------------------------------------------------------------------
// Ring
// ---------------------------------------------------------------------------

class _Ring extends StatelessWidget {
  final double size, opacity;
  const _Ring({required this.size, required this.opacity});
  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: opacity,
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(
            color: AppColors.primaryBlue.withOpacity(0.15),
            width: 0.5,
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Dot cluster
// ---------------------------------------------------------------------------

class _DotCluster extends StatelessWidget {
  const _DotCluster();
  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: 0.15,
      child: SizedBox(
        width: 48,
        height: 38,
        child: GridView.count(
          crossAxisCount: 4,
          crossAxisSpacing: 9,
          mainAxisSpacing: 9,
          physics: const NeverScrollableScrollPhysics(),
          children: List.generate(
            12,
            (_) => Container(
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.primaryBlue,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Streak
// ---------------------------------------------------------------------------

class _Streak extends StatelessWidget {
  final AnimationController controller;
  final double left, top, height, phase;
  const _Streak({
    required this.controller,
    required this.left,
    required this.top,
    required this.height,
    required this.phase,
  });

  @override
  Widget build(BuildContext context) {
    return Positioned(
      left: left,
      top: top,
      child: AnimatedBuilder(
        animation: controller,
        builder: (_, __) {
          final t = (controller.value + phase) % 1.0;
          double opacity;
          if (t < 0.2)
            opacity = t / 0.2;
          else if (t < 0.8)
            opacity = 1.0 - (t - 0.2) * 0.5 / 0.6;
          else
            opacity = 0.0;
          final dy = (t * 48.0) - 18.0;
          return Transform.translate(
            offset: Offset(0, dy),
            child: Opacity(
              opacity: opacity.clamp(0.0, 1.0),
              child: Container(
                width: 1,
                height: height,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      AppColors.primaryBlue.withOpacity(0.5),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Floating stat card
// ---------------------------------------------------------------------------

class _StatCard extends StatelessWidget {
  final String value, label;
  final String? valueAccent;
  const _StatCard({required this.value, required this.label, this.valueAccent});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.primaryBlue.withOpacity(0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: AppColors.primaryBlue.withOpacity(0.30),
          width: 0.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                value,
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
              if (valueAccent != null)
                Text(
                  valueAccent!,
                  style: const TextStyle(
                    fontFamily: 'Poppins',
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: AppColors.success,
                  ),
                ),
            ],
          ),
          Text(
            label,
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontSize: 9,
              fontWeight: FontWeight.w400,
              color: Color(0x8CFFFFFF),
              letterSpacing: 0.3,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Bar chart illustration
// ---------------------------------------------------------------------------

class _BarChart extends StatelessWidget {
  const _BarChart();

  // DEMO DATA — remove when backend ready
  static const _bars = [
    _BarData(height: 38, isOutlier: false, isTop: false),
    _BarData(height: 52, isOutlier: false, isTop: false),
    _BarData(height: 28, isOutlier: true, isTop: false),
    _BarData(height: 60, isOutlier: false, isTop: false),
    _BarData(height: 44, isOutlier: false, isTop: false),
    _BarData(height: 72, isOutlier: false, isTop: true),
  ];

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 90,
      child: Stack(
        alignment: Alignment.bottomCenter,
        children: [
          // Baseline
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 0.5,
              color: Colors.white.withOpacity(0.10),
            ),
          ),

          // Trend line
          Positioned.fill(child: CustomPaint(painter: _TrendLinePainter())),

          // Bars row
          Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: _bars.map((b) => _BarWidget(data: b)).toList(),
          ),
        ],
      ),
    );
  }
}

class _BarData {
  final double height;
  final bool isOutlier, isTop;
  const _BarData({
    required this.height,
    required this.isOutlier,
    required this.isTop,
  });
}

class _BarWidget extends StatefulWidget {
  final _BarData data;
  const _BarWidget({required this.data});
  @override
  State<_BarWidget> createState() => _BarWidgetState();
}

class _BarWidgetState extends State<_BarWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _glowCtrl;
  late Animation<double> _glowAnim;

  @override
  void initState() {
    super.initState();
    _glowCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _glowAnim = Tween<double>(
      begin: 0.7,
      end: 0.25,
    ).animate(CurvedAnimation(parent: _glowCtrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _glowCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final b = widget.data;
    final barColor = b.isOutlier
        ? AppColors.error
        : b.isTop
        ? AppColors.success
        : AppColors.primaryBlue;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 3.5),
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.topCenter,
        children: [
          // Growth arrow for top bar
          if (b.isTop)
            Positioned(
              top: -22,
              child: Column(
                children: [
                  Text(
                    '+25%',
                    style: const TextStyle(
                      fontFamily: 'Poppins',
                      fontSize: 9,
                      fontWeight: FontWeight.w500,
                      color: AppColors.success,
                    ),
                  ),
                  AnimatedBuilder(
                    animation: _glowAnim,
                    builder: (_, __) => Transform.translate(
                      offset: Offset(0, (_glowAnim.value - 0.5) * 4),
                      child: CustomPaint(
                        painter: _ArrowPainter(),
                        size: const Size(8, 7),
                      ),
                    ),
                  ),
                ],
              ),
            ),

          // Bar
          Container(
            width: 14,
            height: b.height,
            decoration: BoxDecoration(
              color: barColor.withOpacity(
                b.isOutlier
                    ? 0.35
                    : b.isTop
                    ? 0.40
                    : 0.42,
              ),
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(3),
              ),
              border: Border.all(
                color: barColor.withOpacity(
                  b.isOutlier
                      ? 0.60
                      : b.isTop
                      ? 0.65
                      : 0.55,
                ),
                width: 0.5,
              ),
            ),
          ),

          // Glow dot on outlier and top
          if (b.isOutlier || b.isTop)
            Positioned(
              top: -6,
              child: AnimatedBuilder(
                animation: _glowAnim,
                builder: (_, __) => Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: barColor,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: barColor.withOpacity(_glowAnim.value),
                        blurRadius: 8,
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ArrowPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppColors.success
      ..style = PaintingStyle.fill;
    final path = Path()
      ..moveTo(size.width / 2, 0)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(_) => false;
}

class _TrendLinePainter extends CustomPainter {
  // DEMO DATA — remove when backend ready
  static const _points = [
    Offset(10, 52),
    Offset(31, 38),
    Offset(52, 62),
    Offset(73, 28),
    Offset(94, 44),
    Offset(115, 8),
  ];

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.15)
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke
      ..strokeJoin = StrokeJoin.round
      ..strokeCap = StrokeCap.round;

    final path = Path();
    final offsetX = (size.width - 125) / 2;
    for (int i = 0; i < _points.length; i++) {
      final p = Offset(_points[i].dx + offsetX, _points[i].dy);
      if (i == 0)
        path.moveTo(p.dx, p.dy);
      else
        path.lineTo(p.dx, p.dy);
    }

    final dashPath = Path();
    const dashLen = 3.0, gapLen = 3.0;
    for (final metric in path.computeMetrics()) {
      double dist = 0;
      while (dist < metric.length) {
        final end = (dist + dashLen).clamp(0.0, metric.length);
        dashPath.addPath(metric.extractPath(dist, end), Offset.zero);
        dist += dashLen + gapLen;
      }
    }
    canvas.drawPath(dashPath, paint);
  }

  @override
  bool shouldRepaint(_) => false;
}

// ---------------------------------------------------------------------------
// Logo icon
// ---------------------------------------------------------------------------

class _LogoIcon extends StatefulWidget {
  const _LogoIcon();
  @override
  State<_LogoIcon> createState() => _LogoIconState();
}

class _LogoIconState extends State<_LogoIcon>
    with SingleTickerProviderStateMixin {
  late AnimationController _c;
  late Animation<double> _glow;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat(reverse: true);
    _glow = Tween<double>(
      begin: 0.7,
      end: 0.3,
    ).animate(CurvedAnimation(parent: _c, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          width: 88,
          height: 88,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFF3D7AEE), Color(0xFF1A4FC8)],
            ),
            border: Border.all(
              color: Colors.white.withOpacity(0.10),
              width: 0.5,
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.primaryBlue.withOpacity(0.55),
                blurRadius: 40,
              ),
              BoxShadow(
                color: Colors.black.withOpacity(0.4),
                blurRadius: 32,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                _IBar(width: 16, opacity: 0.55),
                SizedBox(height: 6),
                _IBar(width: 26, opacity: 0.80),
                SizedBox(height: 6),
                _IBar(width: 36, opacity: 1.0),
              ],
            ),
          ),
        ),
        Positioned(
          top: -4,
          right: -4,
          child: AnimatedBuilder(
            animation: _glow,
            builder: (_, __) => Container(
              width: 11,
              height: 11,
              decoration: BoxDecoration(
                color: AppColors.success,
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF070E1C), width: 2.5),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.success.withOpacity(_glow.value),
                    blurRadius: 10,
                    spreadRadius: 1,
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _IBar extends StatelessWidget {
  final double width, opacity;
  const _IBar({required this.width, required this.opacity});
  @override
  Widget build(BuildContext context) {
    return Opacity(
      opacity: opacity,
      child: Container(
        width: width,
        height: 5,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(3),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// App name
// ---------------------------------------------------------------------------

class _AppName extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return RichText(
      text: const TextSpan(
        style: TextStyle(
          fontFamily: 'Poppins',
          fontSize: 40,
          fontWeight: FontWeight.w500,
          letterSpacing: -1.0,
          height: 1,
        ),
        children: [
          TextSpan(
            text: 'Pulse',
            style: TextStyle(color: Colors.white),
          ),
          TextSpan(
            text: '_AI',
            style: TextStyle(color: Color(0xFF4D8EF0)),
          ),
        ],
      ),
    );
  }
}
