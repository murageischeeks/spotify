@extends('layouts.app')

@section('content')
<div class="py-10 px-4 md:px-12 lg:px-20">
    <!-- Header -->
    <div class="max-w-6xl mx-auto mb-8">
        <h1 class="text-3xl md:text-4xl font-extrabold text-green-600 text-center mb-2">🎵 Spotify Clone</h1>
        <p class="text-center text-gray-600">You are logged in. Click a song card to open it on Spotify — or press Play to hear a preview (if available).</p>
    </div>

    <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <!-- Player panel (left / top) -->
        <div class="lg:col-span-1 bg-white rounded-2xl shadow-lg p-6 flex flex-col gap-4">
            <div class="flex items-center gap-4">
                <img id="nowArt" src="{{ asset('images/placeholder-album.png') }}" alt="album" class="w-20 h-20 rounded-md object-cover shadow-sm">
                <div>
                    <div id="nowTitle" class="font-semibold text-lg">Nothing playing</div>
                    <div id="nowArtist" class="text-sm text-gray-500">—</div>
                </div>
            </div>

            <div>
                <audio id="audioPlayer" controls class="w-full mt-2" preload="none">
                    <source id="audioSource" src="" type="audio/mpeg">
                    Your browser does not support audio playback.
                </audio>
            </div>

            <div class="flex items-center justify-between mt-3">
                <div id="nowMeta" class="text-xs text-gray-500">Preview player</div>
                <a id="nowSpotifyLink" href="#" target="_blank" class="text-sm text-green-600 hover:underline hidden">Open on Spotify ↗</a>
            </div>

            <div class="mt-4 text-xs text-gray-400">
                Notes: Clicking a card opens Spotify. Use the green Play button on a card to play preview audio inside this player (if the track has a preview URL).
            </div>
        </div>

        <!-- Songs grid (middle/right) -->
        <div class="lg:col-span-2">
            <div class="bg-white rounded-2xl shadow-lg p-5">
                <div class="flex items-center justify-between mb-4">
                    <h2 class="text-xl font-semibold">Tracks</h2>
                    <div class="text-sm text-gray-500">Found: <strong>{{ count($songs) }}</strong></div>
                </div>

                @if(count($songs) > 0)
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        @foreach($songs as $song)
                            @php
                                $title = $song['title'] ?? 'Untitled';
                                $artistName = $song['artist']['name'] ?? $song['artist']['artist_name'] ?? 'Unknown Artist';
                                $spotifyUrl = $song['spotify_data']['external_url'] ?? '';
                                $previewUrl = $song['spotify_data']['preview_url'] ?? '';
                                $albumImage = $song['spotify_data']['album_image'] ?? null;
                                $displayImage = $albumImage ?: asset('images/placeholder-album.png');
                            @endphp

                            <div
                                class="p-3 rounded-lg border hover:shadow-md transition cursor-pointer flex items-center gap-3"
                                onclick="openSpotifyFromCard(this)"
                                data-spotify="{{ $spotifyUrl }}"
                                data-preview="{{ $previewUrl }}"
                                data-title="{{ $title }}"
                                data-artist="{{ $artistName }}"
                                data-image="{{ $displayImage }}"
                            >
                                <img src="{{ $displayImage }}" alt="art" class="w-16 h-16 rounded-md object-cover flex-shrink-0">

                                <div class="flex-1">
                                    <div class="font-medium text-gray-800 leading-tight">{{ $title }}</div>
                                    <div class="text-sm text-gray-500">{{ $artistName }}</div>
                                </div>

                                <div class="flex items-center gap-2">
                                    @if($previewUrl)
                                        <button
                                            type="button"
                                            class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 text-sm"
                                            onclick="event.stopPropagation(); playPreviewFromButton(this);"
                                            data-preview="{{ $previewUrl }}"
                                            data-title="{{ $title }}"
                                            data-artist="{{ $artistName }}"
                                            data-image="{{ $displayImage }}"
                                        >
                                            ▶ Play
                                        </button>
                                    @else
                                        <button
                                            type="button"
                                            class="px-3 py-1 bg-gray-100 text-gray-600 rounded text-sm"
                                            onclick="event.stopPropagation(); openSpotifyFromButton(this);"
                                            data-spotify="{{ $spotifyUrl }}"
                                        >
                                            Open
                                        </button>
                                    @endif
                                </div>
                            </div>
                        @endforeach
                    </div>
                @else
                    <div class="py-10 text-center text-gray-500">
                        No songs available
                    </div>

                    <div class="mt-4 p-3 bg-gray-50 text-xs text-gray-600 rounded">
                        <strong>Debug response (Laravel got):</strong>
                        <pre class="whitespace-pre-wrap mt-2 text-xs">{{ $debug_raw ?? 'n/a' }}</pre>
                    </div>
                @endif
            </div>
        </div>
    </div>
</div>

<script>
/**
 * Card click: open Spotify in new tab (if spotify url present).
 * The card itself opens Spotify. Play button only plays the preview.
 */
function openSpotifyFromCard(cardEl) {
    const url = cardEl.dataset.spotify;
    if (url && url !== '') {
        window.open(url, '_blank');
    } else {
        // no spotify link - if preview exists we can play it
        const preview = cardEl.dataset.preview;
        if (preview && preview !== '') {
            playPreview(preview, cardEl.dataset.title, cardEl.dataset.artist, cardEl.dataset.image);
        } else {
            // nothing - small feedback
            alert('No Spotify link or preview available for this track.');
        }
    }
}

/** Play button handler (on-card play button) */
function playPreviewFromButton(btn) {
    const preview = btn.dataset.preview;
    const title = btn.dataset.title || 'Unknown';
    const artist = btn.dataset.artist || '';
    const image = btn.dataset.image || '';

    if (preview && preview !== '') {
        playPreview(preview, title, artist, image);
    } else {
        // fallback to opening spotify if preview missing
        openSpotifyFromButton(btn);
    }
}

/** If play button is "Open" because no preview, open Spotify */
function openSpotifyFromButton(btn) {
    const url = btn.dataset.spotify;
    if (url && url !== '') {
        window.open(url, '_blank');
    } else {
        alert('No Spotify URL available.');
    }
}

/** Actual player logic */
function playPreview(previewUrl, title, artist, image) {
    // normalize relative URLs (assume Django at :8001)
    try {
        new URL(previewUrl);
    } catch (e) {
        if (previewUrl.startsWith('/')) {
            previewUrl = window.location.protocol + '//' + window.location.hostname + ':8001' + previewUrl;
        } else {
            previewUrl = window.location.protocol + '//' + window.location.hostname + ':8001/' + previewUrl;
        }
    }

    // update UI
    document.getElementById('nowTitle').textContent = title;
    document.getElementById('nowArtist').textContent = artist;
    document.getElementById('nowArt').src = image || '{{ asset('images/placeholder-album.png') }}';
    document.getElementById('nowSpotifyLink').href = ''; // until set below
    document.getElementById('nowSpotifyLink').classList.add('hidden');

    // set audio src and play
    const player = document.getElementById('audioPlayer');
    const source = document.getElementById('audioSource');
    source.src = previewUrl;
    player.load();
    player.play().then(() => {
        // optionally show spotify link if we can construct one from current track
        document.getElementById('nowMeta').textContent = 'Playing preview';
    }).catch((err) => {
        console.warn('Playback failed:', err);
        document.getElementById('nowMeta').textContent = 'Preview unavailable (will open Spotify)';
        // fallback: open spotify if preview fails
        // window.open(spotifyUrl, '_blank');
    });
}
</script>
@endsection
