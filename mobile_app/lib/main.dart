// lib/main.dart (Flutter App Entry Point)
import 'package:flutter/material.dart';

void main() {
  runApp(const SmartTraderApp());
}

class SmartTraderApp extends StatelessWidget {
  const SmartTraderApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Trader Hub',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const LoginPage(), // Start with a login page placeholder
    );
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  String _username = '';
  String _password = '';

  void _login() {
    if (_formKey.currentState!.validate()) {
      _formKey.currentState!.save();
      // TODO: Implement actual login logic using API client
      // For now, simulate login and navigate to dashboard
      print('Logging in with User: $_username, Pass: $_password');
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const DashboardPage()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login - Smart Trader')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              TextFormField(
                decoration: const InputDecoration(labelText: 'Email or Mobile'),
                validator: (value) => value!.isEmpty ? 'Please enter email/mobile' : null,
                onSaved: (value) => _username = value!,
              ),
              const SizedBox(height: 16),
              TextFormField(
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
                validator: (value) => value!.isEmpty ? 'Please enter password' : null,
                onSaved: (value) => _password = value!,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _login,
                child: const Text('Login'),
              ),
              TextButton(
                onPressed: () {
                  // TODO: Navigate to Signup Page
                  print('Navigate to Signup page');
                },
                child: const Text('Don\'t have an account? Sign Up'),
              )
            ],
          ),
        ),
      ),
    );
  }
}

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              // TODO: Implement logout logic
              print('Logout');
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(builder: (context) => const LoginPage()),
              );
            },
          )
        ],
      ),
      body: const Center(
        child: Text(
          'Welcome to your Smart Trader Dashboard!',
          style: TextStyle(fontSize: 20),
        ),
      ),
    );
  }
}

// TODO: Create separate files for pages/widgets
// TODO: Implement API client (e.g., using http or dio package)
// TODO: Implement state management (Provider, BLoC, Riverpod, etc.)
// TODO: Add Signup page and navigation
// TODO: Add actual authentication logic and token handling.
