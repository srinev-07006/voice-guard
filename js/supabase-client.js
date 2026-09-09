// VoiceGuard — shared Supabase client.
// Single source of truth for credentials. Loaded by index.html and dashboard.html
// AFTER the Supabase CDN <script> but BEFORE any page script that uses the client.
//
// The anon key is safe to ship to the browser — it is protected by Row Level
// Security policies on the Supabase side, not by being secret.

(function () {
    const SUPABASE_URL = 'https://hrtvynadaqgrflrogybr.supabase.co';
    const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhydHZ5bmFkYXFncmZscm9neWJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg5NDg5MTIsImV4cCI6MjEwNDUyNDkxMn0.p3D2aKV9i5BTbQNVpPiMyp4X04JypxdWdvrwElk66G0';

    let client = null;

    if (!window.supabase || typeof window.supabase.createClient !== 'function') {
        console.error('[VoiceGuard] Supabase JS v2 did not load. Check the CDN <script> tag and your network.');
    } else {
        try {
            client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        } catch (err) {
            // createClient throws synchronously on a malformed URL. Without this
            // catch the exception would kill the rest of the page's scripts.
            console.error('[VoiceGuard] Could not create Supabase client:', err.message);
        }
    }

    window.supabaseClient = client;
})();
