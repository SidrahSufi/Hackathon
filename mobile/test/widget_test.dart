import 'package:flutter_test/flutter_test.dart';
import 'package:pulse_ai/main.dart';


void main() {
  testWidgets('App launches', (WidgetTester tester) async {
    await tester.pumpWidget(const pulseAIApp());
    await tester.pump(const Duration(seconds: 5));
  });
}


