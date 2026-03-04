/**
 * Smart Shiksha — Authentication module (Firebase + Backend JWT).
 *
 * Flow:
 *  1. User clicks "Sign in with Google"
 *  2. Firebase popup → Google account selection
 *  3. Firebase ID token sent to POST /api/auth/google
 *  4. Backend verifies, creates/updates user, returns JWT
 *  5. JWT stored in memory (+ localStorage for persistence)
 *  6. All subsequent API calls include Authorization header
 */
const SmartAuth = (() => {
    "use strict";

    // ── Firebase config ──────────────────────────
    // Replace with your Firebase project's web app config
    // from: Firebase Console → Project Settings → Web App
    const FIREBASE_CONFIG = {
        apiKey:      "YOUR_FIREBASE_API_KEY",          // ← REQUIRED: paste from Firebase Console
        authDomain:  "smart-shiksha.firebaseapp.com",
        projectId:   "smart-shiksha",
    };

    const API_BASE = "http://localhost:8000/api";

    // ── State ────────────────────────────────────
    let _jwt = null;
    let _user = null;            // backend user object { id, name, email, ... }
    let _onAuthChange = null;    // callback(user|null)

    // ── Public API ───────────────────────────────

    /**
     * Initialise Firebase and restore any persisted session.
     * @param {Function} onAuthChange  - called with user object or null
     */
    function init(onAuthChange) {
        _onAuthChange = onAuthChange;

        // Initialize Firebase (compat SDK loaded via <script> in HTML)
        if (!firebase.apps.length) {
            firebase.initializeApp(FIREBASE_CONFIG);
        }

        // Try restore JWT from localStorage
        const storedJwt = localStorage.getItem("ss_jwt");
        if (storedJwt) {
            _jwt = storedJwt;
            // Validate by calling /api/auth/me
            _fetchMe().then((user) => {
                if (user) {
                    _user = user;
                    _notify();
                } else {
                    // Token expired / invalid — clear
                    _clearSession();
                    _notify();
                }
            });
        } else {
            _notify();
        }
    }

    /**
     * Start Google Sign-In popup flow.
     * Resolves with user object on success, null on cancel/error.
     */
    async function signInWithGoogle() {
        try {
            const provider = new firebase.auth.GoogleAuthProvider();
            const result = await firebase.auth().signInWithPopup(provider);
            const idToken = await result.user.getIdToken(true);

            // Exchange with backend
            const resp = await fetch(`${API_BASE}/auth/google`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_token: idToken }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || "Sign-in failed");
            }

            const data = await resp.json();           // { access_token, user }
            _jwt = data.access_token;
            _user = data.user;
            localStorage.setItem("ss_jwt", _jwt);
            localStorage.setItem("ss_user_id", _user.id);
            _notify();
            return _user;
        } catch (err) {
            // User closed popup → code === "auth/popup-closed-by-user"
            if (err.code === "auth/popup-closed-by-user") return null;
            console.error("[SmartAuth] Sign-in error:", err);
            throw err;
        }
    }

    /**
     * Sign out of Firebase and clear local session.
     */
    async function signOut() {
        try {
            await firebase.auth().signOut();
        } catch { /* ignore */ }
        _clearSession();
        _notify();
    }

    /**
     * Returns headers object with Authorization bearer token.
     * Merge this into every authenticated fetch call.
     */
    function getAuthHeaders() {
        if (!_jwt) return {};
        return { Authorization: `Bearer ${_jwt}` };
    }

    /**
     * Returns the current backend JWT, or null.
     */
    function getToken() {
        return _jwt;
    }

    /**
     * Returns the current user object, or null.
     */
    function getUser() {
        return _user;
    }

    /**
     * True if user is signed in with a valid JWT.
     */
    function isSignedIn() {
        return !!_jwt && !!_user;
    }

    // ── Private helpers ──────────────────────────

    async function _fetchMe() {
        try {
            const resp = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${_jwt}` },
            });
            if (!resp.ok) return null;
            return await resp.json();
        } catch {
            return null;
        }
    }

    function _clearSession() {
        _jwt = null;
        _user = null;
        localStorage.removeItem("ss_jwt");
        localStorage.removeItem("ss_user_id");
    }

    function _notify() {
        if (typeof _onAuthChange === "function") {
            _onAuthChange(_user);
        }
    }

    // ── Expose ───────────────────────────────────
    return {
        init,
        signInWithGoogle,
        signOut,
        getAuthHeaders,
        getToken,
        getUser,
        isSignedIn,
    };
})();
