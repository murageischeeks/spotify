<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{{ config('app.name', 'Spotify Clone') }}</title>

    {{-- Vite (recommended) --}}
    @vite(['resources/css/app.css', 'resources/js/app.js'])

    {{-- Quick fallback (uncomment if you don't want Vite): --}}
    {{-- <script src="https://cdn.tailwindcss.com"></script> --}}
</head>
<body class="font-sans antialiased bg-gray-50 text-gray-900">
    <div class="min-h-screen flex flex-col">
        <!-- NAV -->
        <nav class="bg-white border-b">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex h-16 items-center justify-between">
                    <div class="flex items-center space-x-6">
                        <a href="{{ url('/') }}" class="flex items-center gap-2 text-lg font-bold text-green-600">
                            <!-- small logo -->
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M12 3C7.03 3 3 7.03 3 12s4.03 9 9 9 9-4.03 9-9-4.03-9-9-9zM9.5 10.5c.67 0 1.2-.54 1.2-1.2 0-.67-.54-1.2-1.2-1.2-.67 0-1.2.54-1.2 1.2 0 .67.54 1.2 1.2 1.2zm5 0c.67 0 1.2-.54 1.2-1.2 0-.67-.54-1.2-1.2-1.2-.67 0-1.2.54-1.2 1.2 0 .67.54 1.2 1.2 1.2zM8 15c.55 0 1-.45 1-1s-.45-1-1-1-1 .45-1 1 .45 1 1 1zm8 0c.55 0 1-.45 1-1s-.45-1-1-1-1 .45-1 1 .45 1 1 1z"/></svg>
                            <span>Spotify Clone</span>
                        </a>

                        <a href="{{ url('/') }}" class="text-sm text-gray-600 hover:text-green-600">Home</a>
                        <a href="{{ url('/songs') }}" class="text-sm text-gray-600 hover:text-green-600">Songs</a>
                    </div>

                    <div class="flex items-center space-x-4">
                        @auth
                            <span class="text-sm text-gray-700">Hi, {{ Auth::user()->name }}</span>
                            <a href="{{ route('dashboard') }}" class="text-sm text-gray-600 hover:text-green-600">Dashboard</a>

                            <form method="POST" action="{{ route('logout') }}" class="inline">
                                @csrf
                                <button type="submit" class="text-sm text-red-600 hover:text-red-700 ml-3">Logout</button>
                            </form>
                        @else
                            <a href="{{ route('login') }}" class="text-sm text-gray-600 hover:text-green-600">Login</a>
                            <a href="{{ route('register') }}" class="ml-2 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">Register</a>
                        @endauth
                    </div>
                </div>
            </div>
        </nav>

        <!-- Flash message -->
        @if(session('success'))
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
                <div class="bg-green-50 border border-green-200 text-green-800 px-4 py-2 rounded">
                    {{ session('success') }}
                </div>
            </div>
        @endif
        @if(session('error'))
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
                <div class="bg-red-50 border border-red-200 text-red-800 px-4 py-2 rounded">
                    {{ session('error') }}
                </div>
            </div>
        @endif

        <!-- Page content -->
        <main class="flex-1 mt-6">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                @yield('content')
            </div>
        </main>

        <footer class="bg-white border-t mt-8">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-sm text-gray-500">
                &copy; {{ date('Y') }} Spotify Clone — prototype
            </div>
        </footer>
    </div>
</body>
</html>
