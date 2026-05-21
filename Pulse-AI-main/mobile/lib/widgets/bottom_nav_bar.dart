import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';

class BottomNavBar extends StatelessWidget {
  final int currentIndex;

  const BottomNavBar({super.key, required this.currentIndex});

  /// Pulls the current run_id from route arguments regardless of whether
  /// the previous screen passed it as a String or {'run_id': ...} map.
  static String? _currentRunId(BuildContext context) {
    final raw = ModalRoute.of(context)?.settings.arguments;
    if (raw is String) return raw;
    if (raw is Map) return raw['run_id'] as String?;
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(color: AppColors.border, width: 0.5),
        ),
      ),
      child: BottomNavigationBar(
        currentIndex: currentIndex,
        type: BottomNavigationBarType.fixed,
        backgroundColor: Colors.white,
        elevation: 0,
        selectedItemColor: AppColors.primaryBlue,
        unselectedItemColor: AppColors.textSecondary,
        onTap: (index) {
          if (index == currentIndex) return;
          final runId = _currentRunId(context);
          switch (index) {
            case 0:
              // Home doesn't need a run_id
              Navigator.pushReplacementNamed(context, RouteNames.home);
              break;
            case 1:
              // Trace = live agent trace; needs run_id
              Navigator.pushReplacementNamed(
                context,
                RouteNames.liveTrace,
                arguments: runId, // live_trace accepts String form
              );
              break;
            case 2:
              // Outcome = final metrics; needs run_id
              Navigator.pushReplacementNamed(
                context,
                RouteNames.outcome,
                arguments: runId,
              );
              break;
          }
        },
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            activeIcon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.timeline_outlined),
            activeIcon: Icon(Icons.timeline),
            label: 'Trace',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.check_circle_outline),
            activeIcon: Icon(Icons.check_circle),
            label: 'Outcome',
          ),
        ],
      ),
    );
  }
}
