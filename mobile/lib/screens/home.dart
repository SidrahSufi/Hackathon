import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/route_names.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/source_card.dart';
import 'package:file_picker/file_picker.dart'; // add to pubspec.yaml
import '../services/api_services.dart';
import '../services/api_config.dart';

class SourcesScreen extends StatefulWidget {
  const SourcesScreen({super.key});

  @override
  State<SourcesScreen> createState() => _SourcesScreenState();
}

class _SourcesScreenState extends State<SourcesScreen>
    with TickerProviderStateMixin {
  final List<Map<String, String>> uploadedFiles = [];
  final TextEditingController urlController = TextEditingController();

  /// Which seed region to send to the backend.
  /// (For the demo, files dropped on this screen are illustrative — the
  /// backend uses its baked-in mock data for the scenario selected here.)
  String _seedRegion = ApiConfig.defaultSeedRegion;
  bool _starting = false;

  late AnimationController _pageAnimationController;
  late Animation<double> _pageFadeAnimation;
  late Animation<double> _pageSlideAnimation;

  @override
  void initState() {
    super.initState();
    _pageAnimationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _pageFadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _pageAnimationController, curve: Curves.easeOut),
    );
    _pageSlideAnimation = Tween<double>(begin: 20.0, end: 0.0).animate(
      CurvedAnimation(parent: _pageAnimationController, curve: Curves.easeOut),
    );

    _pageAnimationController.forward();
  }

  @override
  void dispose() {
    _pageAnimationController.dispose();
    urlController.dispose();
    super.dispose();
  }

  void _pickFiles() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
      );

      if (result != null) {
        setState(() {
          for (var file in result.files) {
            String extension = file.extension ?? 'FILE';
            uploadedFiles.add({
              'name': file.name,
              'type': extension.toUpperCase(),
            });
          }
        });
      }
    } catch (e) {
      debugPrint("Error picking files: $e");
    }
  }

  void _addUrl() {
    if (urlController.text.isEmpty) return;
    setState(() {
      uploadedFiles.add({'name': urlController.text, 'type': 'URL'});
      urlController.clear();
    });
  }

  void _removeFile(int index) {
    setState(() {
      uploadedFiles.removeAt(index);
    });
  }

  /// POST /api/scenarios/run to the backend, then navigate to insights
  /// with the real run_id.
  Future<void> _startAnalysis() async {
    setState(() => _starting = true);
    try {
      final runId = await ApiService.startRun(seedRegion: _seedRegion);
      if (!mounted) return;
      Navigator.pushNamed(
        context,
        RouteNames.insights,
        arguments: {'run_id': runId},
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not start: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    } finally {
      if (mounted) setState(() => _starting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        automaticallyImplyLeading: false, // no back button
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "HOME",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                color: AppColors.textPrimary,
                fontSize: 20,
              ),
            ),
            Text(
              "Add your sources to begin",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                color: AppColors.textSecondary,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: const BottomNavBar(currentIndex: 0),
      body: AnimatedBuilder(
        animation: _pageAnimationController,
        builder: (context, child) {
          return Opacity(
            opacity: _pageFadeAnimation.value,
            child: Transform.translate(
              offset: Offset(0, _pageSlideAnimation.value),
              child: child,
            ),
          );
        },
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding:
                    const EdgeInsets.only(left: 16.0, right: 16.0, top: 20.0),
                child: Column(
                  children: [
                    if (uploadedFiles.isEmpty) _buildEmptyState(),
                    if (uploadedFiles.isEmpty) const SizedBox(height: 32),
                    _buildUploadCard(),
                    const SizedBox(height: 16),
                    _buildUrlInput(),
                    const SizedBox(height: 16),
                    _buildSeedPicker(),
                    if (uploadedFiles.isNotEmpty) const SizedBox(height: 16),
                    if (uploadedFiles.isNotEmpty) _buildFileList(),
                  ],
                ),
              ),
            ),
            _buildStartAnalysisButton(),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: const BoxDecoration(
                  color: Color(0xFFEBF2FE),
                  shape: BoxShape.circle,
                ),
                child: const Center(
                  child: Text(
                    "👋",
                    style: TextStyle(fontSize: 24),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    "Hi! Sidrah",
                    style: TextStyle(
                      fontFamily: 'Poppins',
                      fontWeight: FontWeight.w500,
                      fontSize: 22,
                      color: AppColors.primaryDark,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border, width: 0.5),
            ),
            child: const Row(
              children: [
                Icon(
                  Icons.auto_awesome_outlined,
                  color: AppColors.primaryBlue,
                  size: 24,
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    "Upload a file below to start your analysis.",
                    style: TextStyle(
                      fontFamily: 'Poppins',
                      fontWeight: FontWeight.w400,
                      fontSize: 14,
                      color: AppColors.textPrimary,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUploadCard() {
    return GestureDetector(
      onTap: _pickFiles,
      child: Container(
        width: double.infinity,
        height: 180,
        decoration: BoxDecoration(
          color: const Color(0xFFEBF2FE),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: AppColors.primaryBlue,
            width: 1.5,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.upload_file_outlined,
              size: 36,
              color: AppColors.primaryBlue,
            ),
            const SizedBox(height: 12),
            const Text(
              "Drop files here",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                fontSize: 15,
                color: AppColors.primaryBlue,
              ),
            ),
            const Text(
              "or tap to browse",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                fontSize: 13,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _buildTypePill("PDF"),
                const SizedBox(width: 6),
                _buildTypePill("CSV"),
                const SizedBox(width: 6),
                _buildTypePill("JSON"),
                const SizedBox(width: 6),
                _buildTypePill("TXT"),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypePill(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border, width: 0.5),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontFamily: 'Poppins',
          fontWeight: FontWeight.w400,
          fontSize: 11,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }

  Widget _buildUrlInput() {
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: urlController,
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w400,
              fontSize: 13,
              color: AppColors.textPrimary,
            ),
            decoration: InputDecoration(
              contentPadding:
                  const EdgeInsets.symmetric(vertical: 16.5, horizontal: 12),
              isDense: true,
              prefixIcon: const Icon(
                Icons.link_outlined,
                color: AppColors.textSecondary,
              ),
              hintText: "Paste a URL (news article, feed...)",
              hintStyle: const TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w400,
                fontSize: 13,
                color: AppColors.textSecondary,
              ),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide:
                    const BorderSide(color: AppColors.border, width: 0.5),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide:
                    const BorderSide(color: AppColors.border, width: 0.5),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
                borderSide:
                    const BorderSide(color: AppColors.primaryBlue, width: 1.0),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        SizedBox(
          height: 52,
          child: OutlinedButton(
            onPressed: _addUrl,
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.primaryBlue,
              side: const BorderSide(color: AppColors.primaryBlue, width: 1),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
            child: const Text(
              "Add",
              style: TextStyle(
                fontFamily: 'Poppins',
                fontWeight: FontWeight.w500,
                fontSize: 14,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSeedPicker() {
    Widget chip(String value, String label) {
      final active = _seedRegion == value;
      return Expanded(
        child: GestureDetector(
          onTap: () => setState(() => _seedRegion = value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: active ? AppColors.primaryBlue : AppColors.surface,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: active ? AppColors.primaryBlue : AppColors.border,
                width: active ? 1.5 : 0.5,
              ),
            ),
            child: Center(
              child: Text(
                label,
                style: TextStyle(
                  fontFamily: 'Poppins',
                  fontWeight: FontWeight.w500,
                  fontSize: 13,
                  color: active ? Colors.white : AppColors.textSecondary,
                ),
              ),
            ),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            "Scenario seed",
            style: TextStyle(
              fontFamily: 'Poppins',
              fontWeight: FontWeight.w500,
              fontSize: 13,
              color: AppColors.textSecondary,
            ),
          ),
        ),
        Row(
          children: [
            chip('lahore', 'Lahore outlier'),
            const SizedBox(width: 8),
            chip('karachi', 'Karachi outlier'),
          ],
        ),
      ],
    );
  }

  Widget _buildFileList() {
    return Column(
      children: List.generate(uploadedFiles.length, (index) {
        final file = uploadedFiles[index];
        return _AnimatedListItem(
          key:
              UniqueKey(), // Use UniqueKey to ensure animation plays for newly added items
          index: index,
          child: Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: SourceCard(
              fileName: file['name'] ?? '',
              fileType: file['type'] ?? '',
              onRemove: () => _removeFile(index),
            ),
          ),
        );
      }),
    );
  }

  Widget _buildStartAnalysisButton() {
    final bool isEnabled = uploadedFiles.isNotEmpty;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        width: double.infinity,
        height: 52,
        decoration: BoxDecoration(
          color: isEnabled ? AppColors.primaryBlue : AppColors.border,
          borderRadius: BorderRadius.circular(8),
        ),
        child: ElevatedButton(
          onPressed: (isEnabled && !_starting) ? _startAnalysis : null,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent,
            shadowColor: Colors.transparent,
            foregroundColor: isEnabled ? Colors.white : AppColors.textSecondary,
            disabledForegroundColor: AppColors.textSecondary,
            disabledBackgroundColor: Colors.transparent,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: _starting
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const Text(
                  "Start Analysis  →",
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

class _AnimatedListItem extends StatefulWidget {
  final int index;
  final Widget child;

  const _AnimatedListItem(
      {super.key, required this.index, required this.child});

  @override
  State<_AnimatedListItem> createState() => _AnimatedListItemState();
}

class _AnimatedListItemState extends State<_AnimatedListItem>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<double> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );
    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
    _slideAnimation = Tween<double>(begin: 20.0, end: 0.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );

    // Staggered animation: delay based on index. Capped at a reasonable max delay.
    final delay = (widget.index * 150).clamp(0, 600);
    Future.delayed(Duration(milliseconds: delay), () {
      if (mounted) {
        _controller.forward();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Opacity(
          opacity: _fadeAnimation.value,
          child: Transform.translate(
            offset: Offset(0, _slideAnimation.value),
            child: child,
          ),
        );
      },
      child: widget.child,
    );
  }
}
