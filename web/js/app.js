/**
 * Smart Shiksha — Main application logic (Vanilla JS).
 *
 * Handles:
 *  - Authentication state ↔ UI visibility
 *  - Language selector ↔ i18n + API parameter
 *  - Question submission → POST /api/ask
 *  - Lesson rendering (Markdown → HTML)
 *  - Save/load lessons via API
 */
(() => {
    "use strict";

    // ── Config ────────────────────────────────────
    const API_BASE = "http://localhost:8000/api";

    // ── DOM refs ──────────────────────────────────
    const langSelect    = document.getElementById("lang-select");
    const askForm       = document.getElementById("ask-form");
    const questionInput = document.getElementById("question-input");
    const askBtn        = document.getElementById("ask-btn");
    const loadingEl     = document.getElementById("loading");
    const errorEl       = document.getElementById("error-msg");
    const lessonSection = document.getElementById("lesson-section");
    const lessonContent = document.getElementById("lesson-content");
    const lessonSources = document.getElementById("lesson-sources");
    const sourcesList   = document.getElementById("sources-list");
    const saveBtn       = document.getElementById("save-btn");
    const savedSection  = document.getElementById("saved-section");
    const savedList     = document.getElementById("saved-list");

    // Auth DOM refs
    const loginPrompt    = document.getElementById("login-prompt");
    const appContent     = document.getElementById("app-content");
    const signInBtn      = document.getElementById("sign-in-btn");
    const signInBtnMain  = document.getElementById("sign-in-btn-main");
    const signOutBtn     = document.getElementById("sign-out-btn");
    const userInfo       = document.getElementById("user-info");
    const userAvatar     = document.getElementById("user-avatar");
    const userName       = document.getElementById("user-name");

    // ── State ─────────────────────────────────────
    let currentLanguage = "en";
    let lastLesson = null;
    const savedLessonCache = new Map();

    // ── Init ──────────────────────────────────────
    async function init() {
        // Restore language preference
        const saved = localStorage.getItem("ss_lang");
        if (saved) {
            currentLanguage = saved;
            langSelect.value = saved;
        }

        // Initialize i18n
        await I18n.init(currentLanguage);

        // Wire up events
        langSelect.addEventListener("change", onLanguageChange);
        askForm.addEventListener("submit", onAskSubmit);
        saveBtn.addEventListener("click", onSaveLesson);
        signInBtn.addEventListener("click", handleSignIn);
        signInBtnMain.addEventListener("click", handleSignIn);
        signOutBtn.addEventListener("click", handleSignOut);

        // Initialize auth — pass callback to react to auth state
        SmartAuth.init(onAuthStateChanged);
    }

    // ── Auth State Change ─────────────────────────
    function onAuthStateChanged(user) {
        if (user) {
            // Signed in
            loginPrompt.classList.add("hidden");
            appContent.classList.remove("hidden");
            signInBtn.classList.add("hidden");
            userInfo.classList.remove("hidden");

            // Display user info
            userName.textContent = user.name || user.email || "Student";
            if (user.profile_picture_url) {
                userAvatar.src = user.profile_picture_url;
                userAvatar.alt = user.name || "User";
                userAvatar.classList.remove("hidden");
            } else {
                userAvatar.classList.add("hidden");
            }

            // Load saved lessons
            loadSavedLessons();
        } else {
            // Signed out
            loginPrompt.classList.remove("hidden");
            appContent.classList.add("hidden");
            signInBtn.classList.remove("hidden");
            userInfo.classList.add("hidden");
            userAvatar.classList.add("hidden");
        }
    }

    // ── Sign In / Out ─────────────────────────────
    async function handleSignIn() {
        try {
            hideError();
            await SmartAuth.signInWithGoogle();
        } catch (err) {
            showError(err.message || "Sign-in failed. Please try again.");
        }
    }

    async function handleSignOut() {
        await SmartAuth.signOut();
        lastLesson = null;
        savedLessonCache.clear();
        lessonSection.classList.add("hidden");
    }

    // ── Language Change ───────────────────────────
    async function onLanguageChange() {
        currentLanguage = langSelect.value;
        localStorage.setItem("ss_lang", currentLanguage);
        await I18n.setLocale(currentLanguage);
    }

    // ── Ask Question ──────────────────────────────
    async function onAskSubmit(e) {
        e.preventDefault();
        const question = questionInput.value.trim();
        if (!question) return;

        showLoading(true);
        hideError();
        lessonSection.classList.add("hidden");

        try {
            const resp = await fetch(`${API_BASE}/ask`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...SmartAuth.getAuthHeaders(),
                },
                body: JSON.stringify({
                    question,
                    target_language: currentLanguage,
                }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || `Server error (${resp.status})`);
            }

            lastLesson = await resp.json();
            renderLesson(lastLesson);
        } catch (err) {
            showError(err.message);
        } finally {
            showLoading(false);
        }
    }

    // ── Render Lesson ─────────────────────────────
    function renderLesson(lesson) {
        lessonContent.innerHTML = MarkdownRenderer.render(lesson.content);
        lessonSection.classList.remove("hidden");

        // Sources
        if (lesson.sources && lesson.sources.length > 0) {
            sourcesList.innerHTML = lesson.sources
                .map((url) => `<li><a href="${escapeAttr(url)}" target="_blank" rel="noopener">${escapeHtml(url)}</a></li>`)
                .join("");
            lessonSources.classList.remove("hidden");
        } else {
            lessonSources.classList.add("hidden");
        }

        // Scroll into view
        lessonSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    // ── Save Lesson ───────────────────────────────
    async function onSaveLesson() {
        if (!lastLesson) return;
        if (!SmartAuth.isSignedIn()) {
            showError("Please sign in to save lessons.");
            return;
        }

        try {
            const resp = await fetch(`${API_BASE}/lessons/save`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...SmartAuth.getAuthHeaders(),
                },
                body: JSON.stringify({
                    topic: lastLesson.topic,
                    content: lastLesson.content,
                    language_code: lastLesson.language,
                    source_urls: lastLesson.sources,
                }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || "Failed to save");
            }

            saveBtn.textContent = I18n.t("lessonSaved") || "✅ Saved!";
            setTimeout(() => {
                saveBtn.textContent = I18n.t("saveLesson") || "💾 Save Lesson";
            }, 2000);

            loadSavedLessons();
        } catch (err) {
            showError(err.message);
        }
    }

    // ── Load Saved Lessons ────────────────────────
    async function loadSavedLessons() {
        if (!SmartAuth.isSignedIn()) return;

        try {
            const resp = await fetch(`${API_BASE}/lessons/mine`, {
                headers: { ...SmartAuth.getAuthHeaders() },
            });
            if (!resp.ok) return;
            const lessons = await resp.json();

            if (lessons.length === 0) {
                savedList.innerHTML = `<p class="saved-list__empty" data-i18n="noSavedLessons">${I18n.t("noSavedLessons")}</p>`;
                return;
            }

            // Cache lesson data in JS map (not in DOM attributes) for security
            savedLessonCache.clear();
            savedList.innerHTML = lessons
                .map((l) => {
                    savedLessonCache.set(l.id, { content: l.content, sources: l.source_urls || [] });
                    return `
                    <div class="saved-card" data-lesson-id="${escapeAttr(l.id)}">
                        <div class="saved-card__topic">${escapeHtml(l.topic)}</div>
                        <div class="saved-card__meta">${escapeHtml(l.language_code.toUpperCase())} · ${new Date(l.created_at).toLocaleDateString()}</div>
                    </div>`;
                })
                .join("");

            // Click to re-render a saved lesson
            savedList.querySelectorAll(".saved-card").forEach((card) => {
                card.addEventListener("click", () => {
                    const lessonId = card.getAttribute("data-lesson-id");
                    const data = savedLessonCache.get(lessonId);
                    if (data) renderLesson(data);
                });
            });
        } catch {
            // Silently ignore — non-critical
        }
    }

    // ── Helpers ───────────────────────────────────
    function showLoading(show) {
        loadingEl.classList.toggle("hidden", !show);
        askBtn.disabled = show;
    }

    function showError(msg) {
        errorEl.textContent = msg;
        errorEl.classList.remove("hidden");
    }

    function hideError() {
        errorEl.classList.add("hidden");
    }

    function escapeHtml(str) {
        const d = document.createElement("div");
        d.textContent = str;
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#039;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // ── Boot ──────────────────────────────────────
    init();
})();
