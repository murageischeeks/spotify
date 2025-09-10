<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class DashboardController extends Controller
{
    public function index()
    {
        $endpoint = 'http://127.0.0.1:8001/songs/'; // correct Django endpoint
        $songs = [];

        try {
            $response = Http::timeout(15)->get($endpoint);

            if ($response->successful()) {
                $data = $response->json();
                $songs = $data['songs'] ?? [];
            }
        } catch (\Exception $e) {
            $songs = [];
        }

        return view('dashboard', compact('songs'));
    }
}
