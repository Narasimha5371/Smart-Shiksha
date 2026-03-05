/**
 * Smart Shiksha — Main SPA app logic.
 *
 * Multi-view SPA matching the Flutter app layout:
 *   Login → Dashboard → AI Tutor / Saved Lessons / Lesson Detail
 */
(() => {
    "use strict";

    const API_BASE = "http://localhost:8001/api";

    // ── DOM refs: App Bar ──
    const appBarTitle   = document.getElementById("app-bar-title");
    const backBtn       = document.getElementById("back-btn");
    const langSelect    = document.getElementById("lang-select");
    const themeToggle   = document.getElementById("theme-toggle");
    const iconSun       = document.getElementById("icon-sun");
    const iconMoon      = document.getElementById("icon-moon");
    const userInfo      = document.getElementById("user-info");
    const userAvatar    = document.getElementById("user-avatar");
    const userName      = document.getElementById("user-name");
    const signOutBtn    = document.getElementById("sign-out-btn");

    // ── DOM refs: Views ──
    const loginView      = document.getElementById("login-view");
    const dashboardView  = document.getElementById("dashboard-view");
    const tutorView      = document.getElementById("tutor-view");
    const savedView      = document.getElementById("saved-view");
    const lessonView     = document.getElementById("lesson-view");
    const comingSoonView = document.getElementById("coming-soon-view");

    // ── DOM refs: Login ──
    const loginForm   = document.getElementById("login-form");
    const loginName   = document.getElementById("login-name");
    const loginEmail  = document.getElementById("login-email");
    const loginError  = document.getElementById("login-error");
    const loginBtn    = document.getElementById("login-btn");

    // ── DOM refs: Dashboard ──
    const greetingName = document.getElementById("greeting-name");
    const greetingInfo = document.getElementById("greeting-info");

    // ── DOM refs: Tutor ──
    const tutorChat  = document.getElementById("tutor-chat");
    const tutorEmpty = document.getElementById("tutor-empty");
    const tutorForm  = document.getElementById("tutor-form");
    const tutorInput = document.getElementById("tutor-input");
    const tutorSend  = document.getElementById("tutor-send");

    // ── DOM refs: Saved ──
    const savedList = document.getElementById("saved-list");

    // ── DOM refs: Lesson ──
    const lessonContent  = document.getElementById("lesson-content");
    const lessonSources  = document.getElementById("lesson-sources");
    const sourcesList    = document.getElementById("sources-list");
    const saveLessonBtn  = document.getElementById("save-lesson-btn");

    // ── DOM refs: Coming soon ──
    const comingSoonTitle = document.getElementById("coming-soon-title");
    const comingSoonBack  = document.getElementById("coming-soon-back");

    // ── State ──
    let currentLanguage = "en";
    let currentView = "login";
    let lastLesson = null;
    let isDark = false;
    const navStack = [];
    const savedLessonCache = new Map();

    const views = {
        login:        { el: loginView,      title: "Smart Shiksha" },
        dashboard:    { el: dashboardView,  title: "Smart Shiksha" },
        tutor:        { el: tutorView,      title: "AI Tutor" },
        saved:        { el: savedView,      title: "Saved Lessons" },
        lesson:       { el: lessonView,     title: "Lesson" },
        "coming-soon":{ el: comingSoonView, title: "Coming Soon" },
    };

    // ═══════════════════════════════════════════
    // VIEW MANAGEMENT
    // ═══════════════════════════════════════════

    function showView(name, opts) {
        opts = opts || {};
        Object.values(views).forEach(function(v) { v.el.classList.add("hidden"); });
        currentView = name;
        var view = views[name];
        if (!view) return;
        view.el.classList.remove("hidden");
        appBarTitle.textContent = opts.title || view.title;
        backBtn.classList.toggle("hidden", name === "login" || name === "dashboard");
    }

    function navigateTo(name, opts) {
        if (currentView !== "login") navStack.push(currentView);
        showView(name, opts);
    }

    function navigateBack() {
        var prev = navStack.pop();
        showView(prev || "dashboard");
    }

    // ═══════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════

    async function init() {
        // Restore language
        var savedLang = localStorage.getItem("ss_lang");
        if (savedLang) { currentLanguage = savedLang; langSelect.value = savedLang; }

        // Restore theme
        if (localStorage.getItem("ss_theme") === "dark") toggleTheme(true);

        // Init i18n
        if (typeof I18n !== "undefined") await I18n.init(currentLanguage);

        // Wire events
        langSelect.addEventListener("change", onLanguageChange);
        themeToggle.addEventListener("click", function() { toggleTheme(); });
        signOutBtn.addEventListener("click", handleSignOut);
        loginForm.addEventListener("submit", handleLogin);
        backBtn.addEventListener("click", navigateBack);
        comingSoonBack.addEventListener("click", function() { showView("dashboard"); navStack.length = 0; });

        // Dashboard cards
        document.querySelectorAll(".dash-card").forEach(function(card) {
            card.addEventListener("click", function() { onDashCardClick(card.dataset.view); });
        });

        // Tutor
        tutorForm.addEventListener("submit", onTutorSubmit);
        document.querySelectorAll(".chip[data-q]").forEach(function(chip) {
            chip.addEventListener("click", function() {
                tutorInput.value = chip.dataset.q;
                tutorForm.dispatchEvent(new Event("submit"));
            });
        });

        // Save lesson
        saveLessonBtn.addEventListener("click", onSaveLesson);

        // Init auth
        SmartAuth.init(onAuthStateChanged);
    }

    // ═══════════════════════════════════════════
    // AUTH
    // ═══════════════════════════════════════════

    function onAuthStateChanged(user) {
        if (user) {
            userInfo.classList.remove("hidden");
            userName.textContent = user.name || user.email || "Student";
            if (user.profile_picture_url) {
                userAvatar.src = user.profile_picture_url;
                userAvatar.alt = user.name || "User";
                userAvatar.classList.remove("hidden");
            } else {
                userAvatar.classList.add("hidden");
            }
            greetingName.textContent = "Hello, " + (user.name || "Student") + "! \uD83D\uDC4B";
            greetingInfo.textContent = "Ready to learn something new today?";
            navStack.length = 0;
            showView("dashboard");
        } else {
            userInfo.classList.add("hidden");
            userAvatar.classList.add("hidden");
            navStack.length = 0;
            showView("login");
        }
    }

    async function handleLogin(e) {
        e.preventDefault();
        var name  = loginName.value.trim();
        var email = loginEmail.value.trim();
        if (!name || !email) return;

        loginError.classList.add("hidden");
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="bubble__spinner" style="width:18px;height:18px;display:inline-block;vertical-align:middle;margin-right:8px;"></span> Signing in\u2026';

        try {
            await SmartAuth.signInWithEmail(name, email);
        } catch (err) {
            loginError.textContent = err.message || "Sign-in failed";
            loginError.classList.remove("hidden");
        } finally {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg><span>Sign In</span>';
        }
    }

    async function handleSignOut() {
        await SmartAuth.signOut();
        lastLesson = null;
        savedLessonCache.clear();
        navStack.length = 0;
        showView("login");
    }

    // ═══════════════════════════════════════════
    // DASHBOARD
    // ═══════════════════════════════════════════

    function onDashCardClick(view) {
        switch (view) {
            case "tutor":
                navigateTo("tutor");
                break;
            case "saved":
                loadSavedLessons();
                navigateTo("saved");
                break;
            case "lessons-browse":
                navigateTo("coming-soon", { title: "Lessons" });
                comingSoonTitle.textContent = "Lessons Browser \u2014 Coming Soon";
                break;
            case "quiz":
                navigateTo("coming-soon", { title: "Quizzes" });
                comingSoonTitle.textContent = "Quizzes \u2014 Coming Soon";
                break;
            case "exam":
                navigateTo("coming-soon", { title: "Exam Prep" });
                comingSoonTitle.textContent = "Exam Prep \u2014 Coming Soon";
                break;
            case "profile":
                navigateTo("coming-soon", { title: "Profile" });
                comingSoonTitle.textContent = "Profile \u2014 Coming Soon";
                break;
            default:
                navigateTo("coming-soon");
                comingSoonTitle.textContent = "Coming Soon";
        }
    }

    // ═══════════════════════════════════════════
    // THEME
    // ═══════════════════════════════════════════

    function toggleTheme(forceDark) {
        isDark = forceDark !== undefined ? forceDark : !isDark;
        if (isDark) {
            document.body.setAttribute("data-theme", "dark");
        } else {
            document.body.removeAttribute("data-theme");
        }
        iconSun.classList.toggle("hidden", isDark);
        iconMoon.classList.toggle("hidden", !isDark);
        localStorage.setItem("ss_theme", isDark ? "dark" : "light");
    }

    // ═══════════════════════════════════════════
    // LANGUAGE
    // ═══════════════════════════════════════════

    async function onLanguageChange() {
        currentLanguage = langSelect.value;
        localStorage.setItem("ss_lang", currentLanguage);
        if (typeof I18n !== "undefined") await I18n.setLocale(currentLanguage);
    }

    // ═══════════════════════════════════════════
    // AI TUTOR
    // ═══════════════════════════════════════════

    var bubbleCounter = 0;

    async function onTutorSubmit(e) {
        e.preventDefault();
        var question = tutorInput.value.trim();
        if (!question) return;

        // Hide empty state
        if (tutorEmpty) tutorEmpty.classList.add("hidden");

        // User bubble
        addChatBubble(question, true);
        tutorInput.value = "";
        tutorSend.disabled = true;

        // Loading bubble
        var loadingId = addChatBubble("Thinking\u2026", false, { loading: true });

        try {
            var resp = await fetch(API_BASE + "/ask", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({ question: question, target_language: currentLanguage }),
            });

            if (!resp.ok) {
                var errData = {};
                try { errData = await resp.json(); } catch(_) {}
                throw new Error(errData.detail || "Server error (" + resp.status + ")");
            }

            lastLesson = await resp.json();
            removeChatBubble(loadingId);

            // Bot reply — preview
            var preview = lastLesson.content.substring(0, 250);
            if (lastLesson.content.length > 250) preview += "\u2026";
            addChatBubble(preview, false, { lesson: lastLesson });

        } catch (err) {
            removeChatBubble(loadingId);
            addChatBubble("\u26A0\uFE0F " + (err.message || "Failed to get response"), false, { error: true });
        } finally {
            tutorSend.disabled = false;
            tutorInput.focus();
        }
    }

    function addChatBubble(text, isUser, opts) {
        opts = opts || {};
        var id = "bubble-" + (++bubbleCounter);
        var div = document.createElement("div");
        div.id = id;
        div.className = "bubble " + (isUser ? "bubble--user" : "bubble--bot") + (opts.loading ? " bubble--loading" : "");

        if (opts.loading) {
            div.innerHTML = '<div class="bubble__spinner"></div><span>' + escapeHtml(text) + '</span>';
        } else if (opts.error) {
            div.textContent = text;
            div.style.borderLeft = "3px solid var(--error)";
        } else {
            div.textContent = text;
            if (opts.lesson) {
                var actions = document.createElement("div");
                actions.className = "bubble__actions";
                var btn = document.createElement("button");
                btn.className = "bubble__view-btn";
                btn.textContent = "\uD83D\uDCC4 View Full Lesson";
                btn.addEventListener("click", function() { showLessonDetail(opts.lesson); });
                actions.appendChild(btn);
                div.appendChild(actions);
            }
        }

        tutorChat.appendChild(div);
        tutorChat.scrollTop = tutorChat.scrollHeight;
        return id;
    }

    function removeChatBubble(id) {
        var el = document.getElementById(id);
        if (el) el.remove();
    }

    function showLessonDetail(lesson) {
        lessonContent.innerHTML = (typeof MarkdownRenderer !== "undefined")
            ? MarkdownRenderer.render(lesson.content)
            : escapeHtml(lesson.content).replace(/\n/g, "<br>");

        if (lesson.sources && lesson.sources.length > 0) {
            sourcesList.innerHTML = lesson.sources
                .map(function(url) { return '<li><a href="' + escapeAttr(url) + '" target="_blank" rel="noopener">' + escapeHtml(url) + '</a></li>'; })
                .join("");
            lessonSources.classList.remove("hidden");
        } else {
            lessonSources.classList.add("hidden");
        }

        lastLesson = lesson;
        saveLessonBtn.textContent = "\uD83D\uDCBE Save Lesson";
        navigateTo("lesson", { title: lesson.topic || "Lesson" });
    }

    // ═══════════════════════════════════════════
    // SAVE / LOAD LESSONS
    // ═══════════════════════════════════════════

    async function onSaveLesson() {
        if (!lastLesson || !SmartAuth.isSignedIn()) return;

        try {
            var resp = await fetch(API_BASE + "/lessons/save", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({
                    topic: lastLesson.topic,
                    content: lastLesson.content,
                    language_code: lastLesson.language,
                    source_urls: lastLesson.sources,
                }),
            });
            if (!resp.ok) throw new Error("Failed to save");

            saveLessonBtn.textContent = "\u2705 Saved!";
            setTimeout(function() { saveLessonBtn.textContent = "\uD83D\uDCBE Save Lesson"; }, 2000);
        } catch (err) {
            saveLessonBtn.textContent = "\u274C Failed";
            setTimeout(function() { saveLessonBtn.textContent = "\uD83D\uDCBE Save Lesson"; }, 2000);
        }
    }

    async function loadSavedLessons() {
        if (!SmartAuth.isSignedIn()) return;

        try {
            var resp = await fetch(API_BASE + "/lessons/mine", {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) return;
            var lessons = await resp.json();

            if (!lessons.length) {
                savedList.innerHTML = '<p class="saved-lessons__empty">No saved lessons yet. Ask the AI Tutor a question first!</p>';
                return;
            }

            savedLessonCache.clear();
            savedList.innerHTML = lessons.map(function(l) {
                savedLessonCache.set(String(l.id), { content: l.content, sources: l.source_urls || [], topic: l.topic });
                return '<div class="saved-card" data-lid="' + escapeAttr(l.id) + '">'
                    + '<div class="saved-card__topic">' + escapeHtml(l.topic) + '</div>'
                    + '<div class="saved-card__meta">' + escapeHtml(l.language_code.toUpperCase()) + ' \u00B7 ' + new Date(l.created_at).toLocaleDateString() + '</div>'
                    + '</div>';
            }).join("");

            savedList.querySelectorAll(".saved-card").forEach(function(card) {
                card.addEventListener("click", function() {
                    var data = savedLessonCache.get(card.dataset.lid);
                    if (data) showLessonDetail(data);
                });
            });
        } catch (_) {
            // silently ignore
        }
    }

    // ═══════════════════════════════════════════
    // HELPERS
    // ═══════════════════════════════════════════

    function escapeHtml(str) {
        var d = document.createElement("div");
        d.textContent = str;
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#039;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    // ═══════════════════════════════════════════
    // BOOT
    // ═══════════════════════════════════════════
    init();
})();
