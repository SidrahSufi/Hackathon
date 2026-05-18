import 'package:flutter/material.dart';
import 'screens/home.dart';
import 'screens/insights_screen.dart';
import 'screens/contradictions_screen.dart';
import 'screens/action_plan_screen.dart';
import 'screens/outcome_screen.dart';
import 'screens/live_trace_screen.dart';
import 'utils/route_names.dart';
import 'utils/app_colors.dart';

void main() {
  runApp(const BizPulseApp());
}

class BizPulseApp extends StatelessWidget {
  const BizPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BizPulse',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Poppins',
        scaffoldBackgroundColor: AppColors.background,
        appBarTheme: const AppBarTheme(
          backgroundColor: AppColors.background,
          elevation: 0,
          scrolledUnderElevation: 0,
          surfaceTintColor: Colors.transparent,
        ),
        useMaterial3: true,
      ),
      initialRoute: RouteNames.home,
      onGenerateRoute: _onGenerateRoute,
    );
  }

  Route<dynamic>? _onGenerateRoute(RouteSettings settings) {
    Widget page;

    switch (settings.name) {
      case RouteNames.home:
        page = const SourcesScreen();
        break;
      case RouteNames.insights:
        page = const InsightsScreen();
        break;
      case RouteNames.contradictions:
        page = const ContradictionsScreen();
        break;
      case RouteNames.actionPlan:
        page = const ActionPlanScreen();
        break;
      case RouteNames.liveTrace:
        page = const LiveTraceScreen();
        break;
      case RouteNames.outcome:
        page = const OutcomeScreen();
        break;
      default:
        page = const SourcesScreen();
    }

    return PageRouteBuilder(
      settings: settings,
      pageBuilder: (context, animation, secondaryAnimation) => page,
      transitionsBuilder: (context, animation, secondaryAnimation, child) {
        final slideTween = Tween<Offset>(
          begin: const Offset(0, 0.05),
          end: Offset.zero,
        ).animate(
          CurvedAnimation(parent: animation, curve: Curves.easeOut),
        );
        return FadeTransition(
          opacity: animation,
          child: SlideTransition(position: slideTween, child: child),
        );
      },
      transitionDuration: const Duration(milliseconds: 300),
    );
  }
}
