/**
 * Smart Shiksha — Authentication module (Auth0 + Backend JWT).
 *
 * Flow:
 *  1. User clicks "Sign in with Google"
 *  2. Auth0 popup → Google account selection
 *  3. Auth0 ID token sent to POST /api/auth/login
 *  4. Backend verifies via JWKS, creates/updates user, returns JWT
 *  5. JWT stored in memory (+ localStorage for persistence)
 *  6. All subsequent API calls include Authorization header
 */
const SmartAuth = (() => {
    "use strict";

    // ── Auth0 config ─────────────────────────────
    const AUTH0_DOMAIN    = "dev-vzwcjg03kzp4d44m.us.auth0.com";
    const AUTH0_CLIENT_ID = "ZzN4EGlsBIuOie0tru5LEOZKZh920eMw";

    const API_BASE = "http://localhost:8000/api";

    // ── State ────────────────────────────────────
    let _auth0Client = null;
    let _jwt = null;
    let _user = null;            // backend user object { id, name, email, ... }
    let _onAuthChange = null;    // callback(user|null)

    // ── Public API ───────────────────────────────

    /**
     * Initialise Auth0 client and restore any persisted session.
     * @param {Function} onAuthChange  - called with user object or null
     */
    async function init(onAuthChange) {
        _onAuthChange = onAuthChange;

        // Initialize Auth0 SPA client (loaded via <script> in HTML)
        try {
            _auth0Client = await auth0.createAuth0Client({
                domain: AUTH0_DOMAIN,
                clientId: AUTH0_CLIENT_ID,
                cacheLocation: "localstorage",
            });
        } catch (err) {
            console.error("[SmartAuth] Failed to init Auth0:", err);
            _notify();
            return;
        }

        // Try restore JWT from localStorage
        const storedJwt = localStorage.getItem("ss_jwt");
        if (storedJwt) {
            _jwt = storedJwt;
            // Validate by calling /api/auth/me
            const user = await _fetchMe();
            if (user) {
                _user = user;
                _notify();
            } else {
                // Token expired / invalid — clear
                _clearSession();
                _notify();
            }
        } else {
            _notify();
        }
    }

    /**
     * Start Google Sign-In via Auth0 popup.
     * Resolves with user object on success, null on cancel/error.
     */
    async function signInWithGoogle() {
        if (!_auth0Client) throw new Error("Auth0 not initialized");

        try {
            // Open Auth0 popup with Google connection
            await _auth0Client.loginWithPopup({
                authorizationParams: {
                    connection: "google-oauth2",
                },
            });

            // Get the ID token from Auth0
            const claims = await _auth0Client.getIdTokenClaims();
            const idToken = claims.__raw;

            // Exchange with backend
            const resp = await fetch(`${API_BASE}/auth/login`, {
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
            // User closed popup
            if (err.message && err.message.includes("Popup closed")) return null;
            console.error("[SmartAuth] Sign-in error:", err);
            throw err;
        }
    }

    /**
     * Sign out of Auth0 and clear local session.
     */
    async function signOut() {
        try {
            if (_auth0Client) {
                await _auth0Client.logout({ logoutParams: { localOnly: true } });
            }
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
