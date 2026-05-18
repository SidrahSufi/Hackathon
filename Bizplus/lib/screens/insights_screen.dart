import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/insight_card.dart';

// DEMO DATA — remove when backend ready
final List<Map<String, dynamic>> demoInsights = [
  {
    'id': 'i-1',
    'title': 'Lahore: orders −25% over 30 days',
    'detail':
        '5 other regions show ±5% noise. Lahore is the only statistically significant outlier. POS and analytics agree.',
    'severity': 'critical',
    'confidence': 0.94,
    'evidence_refs': ['src-2', 'src-4']
  },
  {
    'id': 'i-2',
    'title': 'Most-affected: women\'s casual wear, ages 22–32',
    'detail':
        'SKU clustering narrows the decline to this segment. Other categories stable.',
    'severity': 'high',
    'confidence': 0.87,
    'evidence_refs': ['src-2']
  },
  {
    'id': 'i-3',
    'title': 'Marketing reach −40% despite full budget',
    'detail':
        'Spend going out but delivery broken. Campaign platform issue, not a budget issue.',
    'severity': 'high',
    'confidence': 0.91,
    'evidence_refs': ['src-4', 'src-6']
  },
  {
    'id': 'i-4',
    'title': 'Competitor opened 3 stores in Lahore — April 2026',
    'detail':
        'Timing correlates with start of decline. Pricing perception shifting in support tickets.',
    'severity': 'medium',
    'confidence': 0.72,
    'evidence_refs': ['src-3', 'src-5']
  },
  {
    'id': 'i-5',
    'title': '5 other regions stable — no action needed',
    'detail':
        'Karachi, Islamabad, Rawalpindi, Faisalabad, Multan all within ±5% normal band.',
    'severity': 'low',
    'confidence': 0.99,
    'evidence_refs': ['src-2']
  },
];

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen>
    with TickerProviderStateMixin {
  String activeFilter = 'all';

  late AnimationController _screenController;
  late Animation<double> _screenFade;
  late Animation<double> _screenSlide;

  final Map<String, AnimationController> _cardControllers = {};

  @override
  void initState() {
    super.initState();

    _screenController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _screenFade = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _screenController, curve: Curves.easeOut),
    );
    _screenSlide = Tween<double>(begin: 20.0, end: 0.0).animate(
      CurvedAnimation(parent: _screenController, curve: Curves.easeOut),
    );

    _screenController.forward();
  }

  @override
  void dispose() {
    _screenController.dispose();
    for (var controller in _cardControllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  AnimationController _getCardController(String id, int index) {
    if (!_cardControllers.containsKey(id)) {
      final controller = AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 300),
      );
      _cardControllers[id] = controller;

      Future.delayed(Duration(milliseconds: index * 150), () {
        if (mounted) {
          controller.forward();
        }
      });
    }
    return _cardControllers[id]!;
  }

  List<Map<String, dynamic>> get filteredInsights {
    final sorted = [...demoInsights]..sort((a, b) {
        const order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3};
        return order[a['severity']]!.compareTo(order[b['severity']]!);
      });
    if (activeFilter == 'all') return sorted;
    return sorted.where((i) => i['severity'] == activeFilter).toList();
  }

  void _onFilterChanged(String filter) {
    setState(() {
      activeFilter = filter;
      // Reset animations for the new filtered list
      for (var controller in _cardControllers.values) {
        controller.dispose();
      }
      _cardControllers.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final args = ModalRoute.of(context)?.settings.arguments as Map?;
    final String runId = args?['run_id'] ?? 'demo-run-001';

    final insights = filteredInsights;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: false,
        iconTheme: const IconThemeData(color: AppColors.textPrimary),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Insights",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
                fontSize: 17,
              ),
            ),
            Text(
              "5 findings · Lahore flagged",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 0),
      body: AnimatedBuilder(
        animation: _screenController,
        builder: (context, child) {
          return Opacity(
            opacity: _screenFade.value,
            child: Transform.translate(
              offset: Offset(0, _screenSlide.value),
              child: child,
            ),
          );
        },
        child: Column(
          children: [
            _buildAgentStatusBanner(),
            _buildKeyInsightsSummary(),
            _buildFilterChips(),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.only(
                    left: 16, right: 16, top: 12, bottom: 8),
                child: Column(
                  children: List.generate(insights.length, (index) {
                    final item = insights[index];
                    final controller = _getCardController(item['id'], index);

                    return AnimatedBuilder(
                      animation: controller,
                      builder: (context, child) {
                        final fade =
                            Tween<double>(begin: 0.0, end: 1.0).animate(
                          CurvedAnimation(
                              parent: controller, curve: Curves.easeOut),
                        );
                        final slide =
                            Tween<double>(begin: 20.0, end: 0.0).animate(
                          CurvedAnimation(
                              parent: controller, curve: Curves.easeOut),
                        );
                        return Opacity(
                          opacity: fade.value,
                          child: Transform.translate(
                            offset: Offset(0, slide.value),
                            child: child,
                          ),
                        );
                      },
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: 8.0),
                        child: InsightCard(
                          id: item['id'],
                          title: item['title'],
                          detail: item['detail'],
                          severity: item['severity'],
                          confidence: item['confidence'],
                          evidenceRefs:
                              List<String>.from(item['evidence_refs']),
                        ),
                      ),
                    );
                  }),
                ),
              ),
            ),
            _buildPinnedButton(runId),
          ],
        ),
      ),
    );
  }

  Widget _buildAgentStatusBanner() {
    return Container(
      margin: const EdgeInsets.only(left: 16, right: 16, top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5EE),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Row(
        children: [
          Icon(
            Icons.check_circle_outline,
            size: 16,
            color: AppColors.success,
          ),
          SizedBox(width: 8),
          Text(
            "Insight Agent: complete  ·  94% avg confidence",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 13,
              color: AppColors.success,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKeyInsightsSummary() {
    return Container(
      margin: const EdgeInsets.only(left: 16, right: 16, top: 16),
      padding: const EdgeInsets.all(16),
      width: double.infinity,
      decoration: BoxDecoration(
        color: AppColors.background,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.auto_awesome, size: 16, color: AppColors.primaryBlue),
              SizedBox(width: 8),
              Text(
                "Executive Summary",
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w500,
                  fontSize: 14,
                  color: AppColors.primaryDark,
                ),
              ),
            ],
          ),
          SizedBox(height: 12),
          Text(
            "The 25% decline in Lahore orders is a statistically significant outlier directly linked to competitor expansion. Other regions remain stable. Marketing delivery issues are also present but are secondary.",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w400,
              fontSize: 13,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    final filters = [
      {'label': 'All (5)', 'value': 'all'},
      {'label': 'Critical (1)', 'value': 'critical'},
      {'label': 'High (2)', 'value': 'high'},
      {'label': 'Medium (1)', 'value': 'medium'},
      {'label': 'Low (1)', 'value': 'low'},
    ];

    return Container(
      margin: const EdgeInsets.only(top: 16),
      padding: const EdgeInsets.symmetric(horizontal: 16),
      width: double.infinity,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        clipBehavior: Clip.none,
        child: Row(
          children: filters.map((f) {
            final isActive = activeFilter == f['value'];
            return Padding(
              padding: const EdgeInsets.only(right: 8.0),
              child: GestureDetector(
                onTap: () => _onFilterChanged(f['value']!),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: isActive ? AppColors.primaryBlue : AppColors.surface,
                    borderRadius: BorderRadius.circular(20),
                    border: isActive
                        ? null
                        : Border.all(color: AppColors.border, width: 0.5),
                  ),
                  child: Text(
                    f['label']!,
                    style: TextStyle(
                      fontFamily: 'Poppins',
                      fontWeight: isActive ? FontWeight.w500 : FontWeight.w400,
                      fontSize: 12,
                      color: isActive ? Colors.white : AppColors.textSecondary,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildPinnedButton(String runId) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: AppColors.background,
        border: Border(
          top: BorderSide(color: AppColors.border, width: 0.5),
        ),
      ),
      child: SizedBox(
        width: double.infinity,
        height: 52,
        child: ElevatedButton(
          onPressed: () {
            Navigator.pushNamed(
              context,
              RouteNames.contradictions,
              arguments: {'run_id': runId},
            );
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppColors.primaryBlue,
            foregroundColor: Colors.white,
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: const Text(
            "View Contradictions  →",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 15,
            ),
          ),
        ),
      ),
    );
  }
}
