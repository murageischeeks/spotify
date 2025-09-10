<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class SongController extends Controller
{
    public function index()
    {
        // Fetch songs from Django API
        $response = Http::get('http://127.0.0.1:8001/songs/'); // Django server on port 8001
        $songs = $response->json();

        // Pass to Blade view
        return view('dashboard', ['songs' => $songs['songs'] ?? []]);
    }
}
