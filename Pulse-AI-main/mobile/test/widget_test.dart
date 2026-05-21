import 'package:flutter_test/flutter_test.dart';
import 'package:pulseAI/main.dart';

void main() {
  testWidgets('App launches', (WidgetTester tester) async {
    await tester.pumpWidget(const pulseAIApp());
  });
}
