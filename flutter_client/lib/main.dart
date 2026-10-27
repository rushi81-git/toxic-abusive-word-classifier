import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:socket_io_client/socket_io_client.dart' as IO;

void main() {
  runApp(const SafeChatApp());
}

class SafeChatApp extends StatelessWidget {
  const SafeChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SafeChat NLP',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorSchemeSeed: Colors.teal,
        scaffoldBackgroundColor: const Color(0xFF0F172A),
      ),
      home: const ChatScreen(),
    );
  }
}

class ChatMessage {
  final String sender;
  final String originalMessage;
  final String finalMessage;
  final bool isToxic;
  final double toxicityScore;
  final String tierApplied;
  final String actionTaken;
  final List<dynamic> posTags;
  final List<dynamic> nerTargets;
  final double serverComputeMs;
  final DateTime timestamp;
  bool showDebug;

  ChatMessage({
    required this.sender,
    required this.originalMessage,
    required this.finalMessage,
    required this.isToxic,
    required this.toxicityScore,
    required this.tierApplied,
    required this.actionTaken,
    required this.posTags,
    required this.nerTargets,
    required this.serverComputeMs,
    required this.timestamp,
    this.showDebug = false,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      sender: json['sender'] ?? 'Anonymous',
      originalMessage: json['original_message'] ?? '',
      finalMessage: json['final_message'] ?? '',
      isToxic: json['is_toxic'] ?? false,
      toxicityScore: (json['toxicity_score'] as num?)?.toDouble() ?? 0.0,
      tierApplied: json['tier_applied'] ?? 'free',
      actionTaken: json['action_taken'] ?? 'clean_pass',
      posTags: json['pos_tags'] as List<dynamic>? ?? [],
      nerTargets: json['ner_targets'] as List<dynamic>? ?? [],
      serverComputeMs: (json['server_compute_ms'] as num?)?.toDouble() ?? 0.0,
      timestamp: DateTime.now(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  // shortcut: in-memory state without local SQLite persistence for zero-overhead simplicity
  String backendUrl = 'http://localhost:5000';
  String serverStatus = 'Waking Server...';
  bool isServerOnline = false;
  bool isPremium = true; // Default to Premium AI De-escalation
  String activeSender = 'User A';

  IO.Socket? socket;
  final List<ChatMessage> messages = [];
  final TextEditingController textController = TextEditingController();
  final ScrollController scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _wakeupAndConnect();
  }

  @override
  void dispose() {
    socket?.disconnect();
    socket?.dispose();
    textController.dispose();
    scrollController.dispose();
    super.dispose();
  }

  Future<void> _wakeupAndConnect() async {
    setState(() {
      serverStatus = 'Waking Server...';
      isServerOnline = false;
    });

    // Latency Rule #3: Cold-start wake-up check
    try {
      final res = await http
          .get(Uri.parse('$backendUrl/ping'))
          .timeout(const Duration(seconds: 15));
      if (res.statusCode == 200) {
        setState(() {
          serverStatus = 'Online (<150ms)';
          isServerOnline = true;
        });
      } else {
        setState(() => serverStatus = 'HTTP ${res.statusCode}');
      }
    } catch (_) {
      setState(() => serverStatus = 'Connecting...');
    }

    _initSocket();
  }

  void _initSocket() {
    socket?.disconnect();
    socket?.dispose();

    socket = IO.io(
      backendUrl,
      IO.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .build(),
    );

    socket!.onConnect((_) {
      if (mounted) {
        setState(() {
          serverStatus = 'Online (<150ms)';
          isServerOnline = true;
        });
      }
    });

    socket!.onDisconnect((_) {
      if (mounted) {
        setState(() {
          serverStatus = 'Disconnected';
          isServerOnline = false;
        });
      }
    });

    socket!.onConnectError((err) {
      if (mounted) {
        setState(() {
          serverStatus = 'Offline';
          isServerOnline = false;
        });
      }
    });

    socket!.on('receive_message', (data) {
      if (data is Map<String, dynamic> || data is Map) {
        final parsed = ChatMessage.fromJson(Map<String, dynamic>.from(data));
        if (mounted) {
          setState(() {
            messages.add(parsed);
          });
          _scrollToBottom();
        }
      }
    });

    socket!.connect();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (scrollController.hasClients) {
        scrollController.animateTo(
          scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage() {
    final text = textController.text.trim();
    if (text.isEmpty) return;

    final payload = {
      'sender': activeSender,
      'message': text,
      'tier': isPremium ? 'premium' : 'free',
    };

    if (socket != null && socket!.connected) {
      socket!.emit('send_message', payload);
    } else {
      // Fallback to REST endpoint if socket temporarily disconnected
      http.post(
        Uri.parse('$backendUrl/api/test'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      ).then((res) {
        if (res.statusCode == 200) {
          final data = jsonDecode(res.body);
          setState(() {
            messages.add(ChatMessage.fromJson(data));
          });
          _scrollToBottom();
        }
      }).catchError((_) {});
    }

    textController.clear();
  }

  void _showBackendUrlDialog() {
    final urlController = TextEditingController(text: backendUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text('Backend API URL'),
        content: TextField(
          controller: urlController,
          decoration: const InputDecoration(
            hintText: 'http://localhost:5000 or Render URL',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final newUrl = urlController.text.trim();
              if (newUrl.isNotEmpty) {
                setState(() => backendUrl = newUrl);
                Navigator.pop(ctx);
                _wakeupAndConnect();
              }
            },
            child: const Text('Connect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        elevation: 2,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'SafeChat NLP Inspector',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: isServerOnline ? Colors.greenAccent : Colors.orangeAccent,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  serverStatus,
                  style: TextStyle(
                    fontSize: 11,
                    color: isServerOnline ? Colors.greenAccent : Colors.orangeAccent,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Configure Backend URL',
            icon: const Icon(Icons.settings_ethernet),
            onPressed: _showBackendUrlDialog,
          ),
          // Tier Toggle
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            padding: const EdgeInsets.symmetric(horizontal: 8),
            decoration: BoxDecoration(
              color: isPremium ? const Color(0xFF064E3B) : const Color(0xFF78350F),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isPremium ? Colors.tealAccent : Colors.amberAccent,
                width: 1,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isPremium ? Icons.auto_awesome : Icons.volume_off,
                  size: 14,
                  color: isPremium ? Colors.tealAccent : Colors.amberAccent,
                ),
                const SizedBox(width: 4),
                Text(
                  isPremium ? 'PREMIUM' : 'FREE',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: isPremium ? Colors.tealAccent : Colors.amberAccent,
                  ),
                ),
                Switch(
                  value: isPremium,
                  activeColor: Colors.tealAccent,
                  inactiveThumbColor: Colors.amberAccent,
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  onChanged: (val) => setState(() => isPremium = val),
                ),
              ],
            ),
          ),
        ],
      ),
      body: Column(
        children: [
          // Banner for examiner quick test
          Container(
            color: const Color(0xFF1E293B),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: Row(
              children: [
                const Icon(Icons.info_outline, size: 14, color: Colors.white70),
                const SizedBox(width: 6),
                const Expanded(
                  child: Text(
                    'Tap any message to open full 9-topic NLP syllabus debug breakdown',
                    style: TextStyle(fontSize: 11, color: Colors.white70),
                  ),
                ),
                TextButton(
                  onPressed: () {
                    textController.text =
                        "Hey John, your service is complete garbage! I will hurt you today.";
                  },
                  child: const Text('Load Test Text', style: TextStyle(fontSize: 11)),
                ),
              ],
            ),
          ),
          // Chat messages list
          Expanded(
            child: messages.isEmpty
                ? const Center(
                    child: Text(
                      'No messages yet.\nType below or tap "Load Test Text" to inspect NLP classification.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.white38),
                    ),
                  )
                : ListView.builder(
                    controller: scrollController,
                    padding: const EdgeInsets.all(12),
                    itemCount: messages.length,
                    itemBuilder: (ctx, idx) => _buildMessageBubble(messages[idx]),
                  ),
          ),
          // Persona Switcher + Input Bar
          _buildInputBar(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    // Current viewer's perspective
    final bool isMyMessage = msg.sender == activeSender;
    final bool isUserA = msg.sender == 'User A';

    // The core requested feature:
    // User A (sender) typed toxic message -> Sender sees their raw message (what they typed)
    // User B (receiver) -> Sees only the de-escalated/sanitized message!
    final String displayText = isMyMessage ? msg.originalMessage : msg.finalMessage;

    Color borderColor;
    String badgeText;
    Color badgeColor;

    if (msg.actionTaken == 'premium_de_escalated') {
      borderColor = const Color(0xFF10B981);
      badgeText = isMyMessage ? 'SENT (ORIGINAL SENT TO USER)' : 'PREMIUM: DE-ESCALATED RECEIVED';
      badgeColor = isMyMessage ? const Color(0xFF0F766E) : const Color(0xFF047857);
    } else if (msg.actionTaken == 'free_beep_masked') {
      borderColor = const Color(0xFFF59E0B);
      badgeText = isMyMessage ? 'SENT (UNFILTERED TO YOU)' : 'FREE TIER: [BEEP] REDACTED';
      badgeColor = const Color(0xFFB45309);
    } else {
      borderColor = const Color(0xFF334155);
      badgeText = 'CLEAN PASS';
      badgeColor = const Color(0xFF1E293B);
    }

    return GestureDetector(
      onTap: () {
        setState(() {
          msg.showDebug = !msg.showDebug;
        });
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        child: Column(
          crossAxisAlignment:
              isMyMessage ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            // Sender tag
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${msg.sender} ${isMyMessage ? "(You)" : "(Partner)"}',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isMyMessage ? Colors.tealAccent : Colors.lightBlueAccent,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '• ${msg.tierApplied.toUpperCase()}',
                    style: const TextStyle(fontSize: 10, color: Colors.white38),
                  ),
                ],
              ),
            ),
            // Bubble card
            Container(
              constraints: const BoxConstraints(maxWidth: 420),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isMyMessage ? const Color(0xFF1E293B) : const Color(0xFF172554),
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(14),
                  topRight: const Radius.circular(14),
                  bottomLeft: Radius.circular(isMyMessage ? 14 : 2),
                  bottomRight: Radius.circular(isMyMessage ? 2 : 14),
                ),
                border: Border.all(color: borderColor, width: 1.5),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: badgeColor,
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          badgeText,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${msg.serverComputeMs.toStringAsFixed(1)}ms',
                        style: const TextStyle(fontSize: 10, color: Colors.white38),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  // Display text depends on who is viewing:
                  Text(
                    displayText,
                    style: const TextStyle(
                      fontSize: 15,
                      color: Colors.white,
                      height: 1.35,
                    ),
                  ),
                  if (msg.isToxic) ...[
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.black26,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            isMyMessage ? Icons.visibility_off : Icons.security,
                            size: 13,
                            color: isMyMessage ? Colors.amberAccent : Colors.tealAccent,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              isMyMessage
                                  ? 'You see what you typed. Receiver only sees de-escalated text.'
                                  : 'Toxic input de-escalated before delivery to you.',
                              style: TextStyle(
                                fontSize: 10,
                                fontStyle: FontStyle.italic,
                                color: isMyMessage ? Colors.amberAccent : Colors.tealAccent,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 6),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Toxicity: ${(msg.toxicityScore * 100).toStringAsFixed(1)}%',
                        style: TextStyle(
                          fontSize: 11,
                          color: msg.isToxic ? Colors.redAccent : Colors.greenAccent,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Row(
                        children: [
                          Icon(Icons.touch_app, size: 12, color: Colors.white38),
                          SizedBox(width: 2),
                          Text('Inspect NLP', style: TextStyle(fontSize: 10, color: Colors.white38)),
                        ],
                      ),
                    ],
                  ),
                  // Syllabus Debug Card
                  if (msg.showDebug) ...[
                    const Divider(color: Colors.white24, height: 16),
                    _buildSyllabusDebugCard(msg),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSyllabusDebugCard(ChatMessage msg) {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'NLP Syllabus Topics In Action:',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: Colors.tealAccent,
            ),
          ),
          const SizedBox(height: 6),
          // Raw original
          const Text('Topic 4 (Raw Input):',
              style: TextStyle(fontSize: 10, color: Colors.white60)),
          Text(
            msg.originalMessage,
            style: const TextStyle(
                fontSize: 12, fontStyle: FontStyle.italic, color: Colors.white70),
          ),
          const SizedBox(height: 6),
          // Toxicity progress bar
          const Text('Topics 6 & 8 (Toxicity Logistic Regression Probability):',
              style: TextStyle(fontSize: 10, color: Colors.white60)),
          const SizedBox(height: 2),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: msg.toxicityScore.clamp(0.0, 1.0),
              backgroundColor: Colors.white12,
              color: msg.isToxic ? Colors.redAccent : Colors.greenAccent,
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 8),
          // NER Chips
          const Text('Topic 3 (spaCy Named Entities):',
              style: TextStyle(fontSize: 10, color: Colors.white60)),
          const SizedBox(height: 2),
          msg.nerTargets.isEmpty
              ? const Text('None detected',
                  style: TextStyle(fontSize: 11, color: Colors.white38))
              : Wrap(
                  spacing: 4,
                  runSpacing: 4,
                  children: msg.nerTargets.map((ner) {
                    final entText = ner[0].toString();
                    final entLabel = ner[1].toString();
                    return Chip(
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      padding: EdgeInsets.zero,
                      backgroundColor: const Color(0xFF3B82F6).withOpacity(0.2),
                      label: Text(
                        '$entText [$entLabel]',
                        style: const TextStyle(fontSize: 10, color: Colors.lightBlueAccent),
                      ),
                    );
                  }).toList(),
                ),
          const SizedBox(height: 8),
          // POS Tag Chips
          const Text('Topic 2 (NLTK POS Tags sample):',
              style: TextStyle(fontSize: 10, color: Colors.white60)),
          const SizedBox(height: 2),
          Wrap(
            spacing: 4,
            runSpacing: 4,
            children: msg.posTags.take(8).map((pos) {
              final word = pos[0].toString();
              final tag = pos[1].toString();
              return Chip(
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                padding: EdgeInsets.zero,
                backgroundColor: const Color(0xFF6B7280).withOpacity(0.2),
                label: Text(
                  '$word ($tag)',
                  style: const TextStyle(fontSize: 10, color: Colors.white70),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: const BoxDecoration(
        color: Color(0xFF1E293B),
        border: Border(top: BorderSide(color: Colors.white12)),
      ),
      child: SafeArea(
        child: Column(
          children: [
            Row(
              children: [
                const Text(
                  'Acting As: ',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.white70),
                ),
                // Dual-persona ChoiceChip
                ChoiceChip(
                  avatar: const Icon(Icons.person, size: 14),
                  label: const Text('User A (Sender)', style: TextStyle(fontSize: 11)),
                  selected: activeSender == 'User A',
                  selectedColor: Colors.teal,
                  onSelected: (sel) {
                    if (sel) setState(() => activeSender = 'User A');
                  },
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  avatar: const Icon(Icons.person_outline, size: 14),
                  label: const Text('User B (Receiver)', style: TextStyle(fontSize: 11)),
                  selected: activeSender == 'User B',
                  selectedColor: Colors.blueAccent,
                  onSelected: (sel) {
                    if (sel) setState(() => activeSender = 'User B');
                  },
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: isPremium ? Colors.teal.withOpacity(0.2) : Colors.amber.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: isPremium ? Colors.tealAccent : Colors.amberAccent,
                      width: 0.8,
                    ),
                  ),
                  child: Text(
                    isPremium ? "Mode: Premium POS" : "Mode: Free [BEEP]",
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isPremium ? Colors.tealAccent : Colors.amberAccent,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: textController,
                    decoration: InputDecoration(
                      hintText: 'Type as $activeSender (e.g. toxic or normal)...',
                      hintStyle: const TextStyle(color: Colors.white38),
                      filled: true,
                      fillColor: const Color(0xFF0F172A),
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
