import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "🌿 GroBack",
          style: TextStyle(
            fontWeight: FontWeight.bold,
          ),
        ),
      ),

      body: Padding(
        padding: const EdgeInsets.all(20),

        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,

          children: [

            const Text(
              "Good Morning 👋",
              style: TextStyle(
                fontSize: 26,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            const Text(
              "Ready to track your groceries?",
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),

            const SizedBox(height: 30),

            ElevatedButton.icon(
              onPressed: () {},

              icon: const Icon(Icons.camera_alt),

              label: const Text(
                "Scan New Item",
                style: TextStyle(fontSize: 18),
              ),
            ),

            const SizedBox(height: 30),

            const Text(
              "Today's Inventory",
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 15),

            Expanded(
              child: ListView(
                children: const [

                  ListTile(
                    leading: CircleAvatar(
                      child: Text("🍎"),
                    ),
                    title: Text("Apple"),
                    subtitle: Text("430 g"),
                  ),

                  ListTile(
                    leading: CircleAvatar(
                      child: Text("🍌"),
                    ),
                    title: Text("Banana"),
                    subtitle: Text("820 g"),
                  ),

                  ListTile(
                    leading: CircleAvatar(
                      child: Text("🥕"),
                    ),
                    title: Text("Carrot"),
                    subtitle: Text("300 g"),
                  ),

                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}