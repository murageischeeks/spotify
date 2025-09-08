@extends('layouts.app')

@section('content')
<div class="text-center py-16">
    <h1 class="text-4xl font-extrabold text-green-600 mb-4">🎶 Welcome to Spotify Clone 🎶</h1>
    <p class="text-gray-600 mb-6">Your music streaming project starts here.</p>

    <div class="flex justify-center gap-3">
        @guest
            <a href="{{ route('login') }}" class="px-6 py-2 bg-gray-800 text-white rounded">Login</a>
            <a href="{{ route('register') }}" class="px-6 py-2 bg-green-600 text-white rounded">Register</a>
        @else
            <a href="{{ route('dashboard') }}" class="px-6 py-2 bg-green-600 text-white rounded">Go to Dashboard</a>
        @endguest
    </div>
</div>
@endsection
