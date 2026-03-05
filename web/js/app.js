/**
 * Smart Shiksha - Main SPA app logic.
 *
 * Multi-view SPA matching the Flutter app layout:
 *   Login -> Onboarding -> Dashboard -> All Features
 */
(() => {
    "use strict";

    const API_BASE = "https://smartsiksha.onrender.com/api";

    // -- DOM refs: App Bar --
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

    // -- DOM refs: Views --
    const loginView         = document.getElementById("login-view");
    const onboardingView    = document.getElementById("onboarding-view");
    const dashboardView     = document.getElementById("dashboard-view");
    const tutorView         = document.getElementById("tutor-view");
    const savedView         = document.getElementById("saved-view");
    const lessonView        = document.getElementById("lesson-view");
    const lessonsBrowseView = document.getElementById("lessons-browse-view");
    const quizView          = document.getElementById("quiz-view");
    const examView          = document.getElementById("exam-view");
    const profileView       = document.getElementById("profile-view");

    // -- DOM refs: Login --
    const loginForm   = document.getElementById("login-form");
    const loginName   = document.getElementById("login-name");
    const loginEmail  = document.getElementById("login-email");
    const loginError  = document.getElementById("login-error");
    const loginBtn    = document.getElementById("login-btn");

    // -- DOM refs: Onboarding --
    const obStepCurriculum = document.getElementById("ob-step-curriculum");
    const obStepClass      = document.getElementById("ob-step-class");
    const obStepStream     = document.getElementById("ob-step-stream");
    const obCurriculaList  = document.getElementById("ob-curricula-list");
    const obClassList      = document.getElementById("ob-class-list");
    const obStreamList     = document.getElementById("ob-stream-list");
    const obProgressBar    = document.getElementById("ob-progress-bar");

    // -- DOM refs: Dashboard --
    const greetingName = document.getElementById("greeting-name");
    const greetingInfo = document.getElementById("greeting-info");

    // -- DOM refs: Tutor --
    const tutorChat  = document.getElementById("tutor-chat");
    const tutorEmpty = document.getElementById("tutor-empty");
    const tutorForm  = document.getElementById("tutor-form");
    const tutorInput = document.getElementById("tutor-input");
    const tutorSend  = document.getElementById("tutor-send");

    // -- DOM refs: Saved --
    const savedList = document.getElementById("saved-list");

    // -- DOM refs: Lesson --
    const lessonContent  = document.getElementById("lesson-content");
    const lessonSources  = document.getElementById("lesson-sources");
    const sourcesList    = document.getElementById("sources-list");
    const saveLessonBtn  = document.getElementById("save-lesson-btn");

    // -- DOM refs: Loading --
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingText    = document.getElementById("loading-text");

    // -- State --
    let currentLanguage = "en";
    let currentView     = "login";
    let lastLesson      = null;
    let isDark          = false;
    const navStack      = [];
    const savedLessonCache = new Map();

    // Onboarding state
    let obCurriculum = null;
    let obClassGrade = null;
    let obStream     = null;
    let allCurricula = [];

    // Lessons browse state
    let browseSubjects  = [];
    let browseChapters  = [];
    let currentSubject  = null;
    let currentChapter  = null;

    // Quiz state
    let quizQuestions = [];
    let quizSubmitted = false;

    // Exam state
    let examsList      = [];
    let currentExam    = null;
    let currentMockTest = null;
    let mockTimer       = null;
    let mockSeconds     = 0;

    const views = {
        login:           { el: loginView,         title: "Smart Shiksha" },
        onboarding:      { el: onboardingView,    title: "Setup" },
        dashboard:       { el: dashboardView,     title: "Smart Shiksha" },
        tutor:           { el: tutorView,         title: "AI Tutor" },
        saved:           { el: savedView,         title: "Saved Lessons" },
        lesson:          { el: lessonView,        title: "Lesson" },
        "lessons-browse":{ el: lessonsBrowseView, title: "Lessons" },
        quiz:            { el: quizView,          title: "Quizzes" },
        exam:            { el: examView,          title: "Exam Prep" },
        profile:         { el: profileView,       title: "Profile" },
    };

    // ===== VIEW MANAGEMENT =====

    function showView(name, opts) {
        opts = opts || {};
        Object.values(views).forEach(function(v) { if (v.el) v.el.classList.add("hidden"); });
        currentView = name;
        var view = views[name];
        if (!view) return;
        view.el.classList.remove("hidden");
        appBarTitle.textContent = opts.title || view.title;
        backBtn.classList.toggle("hidden", name === "login" || name === "dashboard" || name === "onboarding");
    }

    function navigateTo(name, opts) {
        if (currentView !== "login" && currentView !== "onboarding") navStack.push(currentView);
        showView(name, opts);
    }

    function navigateBack() {
        var prev = navStack.pop();
        showView(prev || "dashboard");
    }

    function showLoading(text) {
        loadingText.textContent = text || "Loading...";
        loadingOverlay.classList.remove("hidden");
    }

    function hideLoading() {
        loadingOverlay.classList.add("hidden");
    }

    // ===== INIT =====

    async function init() {
        var savedLang = localStorage.getItem("ss_lang");
        if (savedLang) { currentLanguage = savedLang; langSelect.value = savedLang; }
        if (localStorage.getItem("ss_theme") === "dark") toggleTheme(true);
        if (typeof I18n !== "undefined") await I18n.init(currentLanguage);

        // Wire events
        langSelect.addEventListener("change", onLanguageChange);
        themeToggle.addEventListener("click", function() { toggleTheme(); });
        signOutBtn.addEventListener("click", handleSignOut);
        loginForm.addEventListener("submit", handleLogin);
        backBtn.addEventListener("click", navigateBack);

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

        // Lessons browser
        var genLessonBtn = document.getElementById("generate-lesson-btn");
        if (genLessonBtn) genLessonBtn.addEventListener("click", onGenerateLesson);

        // Quiz
        var qSubmitBtn = document.getElementById("quiz-submit-btn");
        if (qSubmitBtn) qSubmitBtn.addEventListener("click", onQuizSubmit);

        // Exam
        var genMockBtn = document.getElementById("generate-mock-btn");
        if (genMockBtn) genMockBtn.addEventListener("click", onGenerateMockTest);
        var mSubmitBtn = document.getElementById("mock-submit-btn");
        if (mSubmitBtn) mSubmitBtn.addEventListener("click", onMockTestSubmit);

        // Profile
        var editBtn = document.getElementById("edit-academic-btn");
        if (editBtn) editBtn.addEventListener("click", openEditAcademicDialog);
        var editCancelBtn = document.getElementById("edit-cancel-btn");
        if (editCancelBtn) editCancelBtn.addEventListener("click", closeEditAcademicDialog);
        var editSaveBtn = document.getElementById("edit-save-btn");
        if (editSaveBtn) editSaveBtn.addEventListener("click", saveAcademicInfo);
        var profileThemeBtn = document.getElementById("profile-theme-toggle");
        if (profileThemeBtn) profileThemeBtn.addEventListener("click", function() { toggleTheme(); });
        var profileLangSel = document.getElementById("profile-lang-select");
        if (profileLangSel) profileLangSel.addEventListener("change", onProfileLangChange);
        var profileLogoutBtn = document.getElementById("profile-logout-btn");
        if (profileLogoutBtn) profileLogoutBtn.addEventListener("click", handleSignOut);

        // Init auth
        SmartAuth.init(onAuthStateChanged);
    }

    // ===== AUTH =====

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

            if (!user.onboarding_complete) {
                navStack.length = 0;
                loadOnboarding();
            } else {
                greetingInfo.textContent = (user.curriculum || "CBSE") + " \u2022 Class " + (user.class_grade || "10") + (user.stream ? " \u2022 " + capitalize(user.stream) : "");
                navStack.length = 0;
                showView("dashboard");
            }
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
        if (mockTimer) { clearInterval(mockTimer); mockTimer = null; }
        await SmartAuth.signOut();
        lastLesson = null;
        savedLessonCache.clear();
        navStack.length = 0;
        showView("login");
    }

    // ===== ONBOARDING =====

    async function loadOnboarding() {
        showView("onboarding");
        obCurriculum = null;
        obClassGrade = null;
        obStream     = null;

        try {
            var resp = await fetch(API_BASE + "/syllabus/curricula");
            var data = await resp.json();
            allCurricula = data.curricula || ["CBSE", "ICSE", "State Board"];
        } catch (ignore) {
            allCurricula = ["CBSE", "ICSE", "State Board"];
        }

        obCurriculaList.innerHTML = allCurricula.map(function(c) {
            return '<button class="ob-option-btn" data-val="' + escapeAttr(c) + '">' + escapeHtml(c) + '</button>';
        }).join("");

        obCurriculaList.querySelectorAll(".ob-option-btn").forEach(function(btn) {
            btn.addEventListener("click", function() {
                obCurriculum = btn.dataset.val;
                selectObOption(obCurriculaList, btn);
                showObStep(2);
            });
        });

        obClassList.innerHTML = "";
        for (var i = 6; i <= 12; i++) {
            var btn = document.createElement("button");
            btn.className = "ob-option-btn";
            btn.dataset.val = String(i);
            btn.textContent = "Class " + i;
            btn.addEventListener("click", (function(grade, b) {
                return function() {
                    obClassGrade = grade;
                    selectObOption(obClassList, b);
                    if (grade >= 11) {
                        showObStep(3);
                    } else {
                        completeOnboarding();
                    }
                };
            })(i, btn));
            obClassList.appendChild(btn);
        }

        obStreamList.innerHTML = "";
        ["science", "commerce", "arts"].forEach(function(s) {
            var btn = document.createElement("button");
            btn.className = "ob-option-btn";
            btn.dataset.val = s;
            btn.textContent = capitalize(s);
            btn.addEventListener("click", (function(stream, b) {
                return function() {
                    obStream = stream;
                    selectObOption(obStreamList, b);
                    completeOnboarding();
                };
            })(s, btn));
            obStreamList.appendChild(btn);
        });

        showObStep(1);
    }

    function showObStep(step) {
        obStepCurriculum.classList.toggle("hidden", step !== 1);
        obStepClass.classList.toggle("hidden", step !== 2);
        obStepStream.classList.toggle("hidden", step !== 3);
        obProgressBar.style.width = (step * 33) + "%";
    }

    function selectObOption(container, selected) {
        container.querySelectorAll(".ob-option-btn").forEach(function(b) {
            b.classList.toggle("ob-option-btn--selected", b === selected);
        });
    }

    async function completeOnboarding() {
        showLoading("Setting up your profile...");
        try {
            var resp = await fetch(API_BASE + "/auth/onboarding", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({
                    curriculum: obCurriculum || "CBSE",
                    class_grade: obClassGrade || 10,
                    stream: obStream || null,
                    language_preference: currentLanguage,
                }),
            });
            if (resp.ok) {
                var updatedUser = await resp.json();
                var stored = SmartAuth.getUser();
                if (stored) {
                    stored.onboarding_complete = true;
                    stored.curriculum = updatedUser.curriculum;
                    stored.class_grade = updatedUser.class_grade;
                    stored.stream = updatedUser.stream;
                }
                greetingInfo.textContent = (updatedUser.curriculum || "CBSE") + " \u2022 Class " + (updatedUser.class_grade || "10") + (updatedUser.stream ? " \u2022 " + capitalize(updatedUser.stream) : "");
            }
        } catch (ignore) { /* continue anyway */ }
        hideLoading();
        navStack.length = 0;
        showView("dashboard");
    }

    // ===== DASHBOARD =====

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
                loadLessonsBrowser();
                navigateTo("lessons-browse", { title: "Lessons" });
                break;
            case "quiz":
                loadQuizSubjects();
                navigateTo("quiz", { title: "Quizzes" });
                break;
            case "exam":
                loadExams();
                navigateTo("exam", { title: "Exam Prep" });
                break;
            case "profile":
                loadProfile();
                navigateTo("profile", { title: "Profile" });
                break;
            default:
                navigateTo("dashboard");
        }
    }

    // ===== THEME =====

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

    // ===== LANGUAGE =====

    async function onLanguageChange() {
        currentLanguage = langSelect.value;
        localStorage.setItem("ss_lang", currentLanguage);
        if (typeof I18n !== "undefined") await I18n.setLocale(currentLanguage);
        var profileLang = document.getElementById("profile-lang-select");
        if (profileLang) profileLang.value = currentLanguage;
    }

    async function onProfileLangChange() {
        var sel = document.getElementById("profile-lang-select");
        currentLanguage = sel.value;
        langSelect.value = currentLanguage;
        localStorage.setItem("ss_lang", currentLanguage);
        if (typeof I18n !== "undefined") await I18n.setLocale(currentLanguage);

        var user = SmartAuth.getUser();
        if (user) {
            try {
                await fetch(API_BASE + "/auth/profile", {
                    method: "PATCH",
                    headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                    body: JSON.stringify({ language_preference: currentLanguage }),
                });
            } catch (ignore) { }
        }
    }

    // ===== AI TUTOR =====

    var bubbleCounter = 0;

    async function onTutorSubmit(e) {
        e.preventDefault();
        var question = tutorInput.value.trim();
        if (!question) return;

        if (tutorEmpty) tutorEmpty.classList.add("hidden");
        addChatBubble(question, true);
        tutorInput.value = "";
        tutorSend.disabled = true;

        var loadingId = addChatBubble("Thinking\u2026", false, { loading: true });

        try {
            var resp = await fetch(API_BASE + "/ask", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({ question: question, target_language: currentLanguage }),
            });

            if (!resp.ok) {
                var errData = {};
                try { errData = await resp.json(); } catch(ignore) {}
                throw new Error(errData.detail || "Server error (" + resp.status + ")");
            }

            lastLesson = await resp.json();
            removeChatBubble(loadingId);

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
            ? MarkdownRenderer.render(lesson.content || lesson.content_markdown || "")
            : escapeHtml(lesson.content || lesson.content_markdown || "").replace(/\n/g, "<br>");

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
        saveLessonBtn.classList.toggle("hidden", !lesson.topic);
        navigateTo("lesson", { title: lesson.topic || lesson.title || "Lesson" });
    }

    // ===== SAVE / LOAD LESSONS =====

    async function onSaveLesson() {
        if (!lastLesson || !SmartAuth.isSignedIn()) return;

        try {
            var resp = await fetch(API_BASE + "/lessons/save", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({
                    topic: lastLesson.topic,
                    content: lastLesson.content,
                    language_code: lastLesson.language || currentLanguage,
                    source_urls: lastLesson.sources || [],
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
        } catch (ignore) { }
    }

    // ===== LESSONS BROWSER =====

    async function loadLessonsBrowser() {
        var user = SmartAuth.getUser();
        if (!user) return;

        var subjectsSection = document.getElementById("browse-subjects");
        var chaptersSection = document.getElementById("browse-chapters");
        var lessonsSection  = document.getElementById("browse-lessons");
        subjectsSection.classList.remove("hidden");
        chaptersSection.classList.add("hidden");
        lessonsSection.classList.add("hidden");

        var grid = document.getElementById("subjects-grid");
        grid.innerHTML = '<p class="browse-empty">Loading subjects...</p>';

        try {
            var params = "curriculum=" + encodeURIComponent(user.curriculum || "CBSE")
                       + "&class_grade=" + (user.class_grade || 10);
            if (user.stream) params += "&stream=" + encodeURIComponent(user.stream);

            var resp = await fetch(API_BASE + "/syllabus/subjects?" + params, {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load subjects");
            browseSubjects = await resp.json();

            if (!browseSubjects.length) {
                grid.innerHTML = '<p class="browse-empty">No subjects found for your class. Complete onboarding first.</p>';
                return;
            }

            grid.innerHTML = browseSubjects.map(function(s) {
                return '<button class="browse-card" data-sid="' + escapeAttr(s.id) + '">'
                    + '<div class="browse-card__icon">' + getSubjectIcon(s.name) + '</div>'
                    + '<div class="browse-card__name">' + escapeHtml(s.name) + '</div>'
                    + '</button>';
            }).join("");

            grid.querySelectorAll(".browse-card").forEach(function(card) {
                card.addEventListener("click", function() {
                    var subj = browseSubjects.find(function(s) { return String(s.id) === card.dataset.sid; });
                    if (subj) loadChapters(subj);
                });
            });
        } catch (err) {
            grid.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function loadChapters(subject) {
        currentSubject = subject;
        var chaptersSection = document.getElementById("browse-chapters");
        var lessonsSection  = document.getElementById("browse-lessons");
        var subjectsSection = document.getElementById("browse-subjects");

        subjectsSection.classList.add("hidden");
        chaptersSection.classList.remove("hidden");
        lessonsSection.classList.add("hidden");

        document.getElementById("chapters-title").textContent = "\uD83D\uDCD6 " + subject.name + " \u2014 Chapters";
        var list = document.getElementById("chapters-list");
        list.innerHTML = '<p class="browse-empty">Loading chapters...</p>';

        try {
            var resp = await fetch(API_BASE + "/syllabus/chapters/" + subject.id, {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load chapters");
            browseChapters = await resp.json();

            if (!browseChapters.length) {
                list.innerHTML = '<p class="browse-empty">No chapters available for this subject.</p>';
                return;
            }

            list.innerHTML = browseChapters.map(function(ch, idx) {
                return '<button class="browse-list-item" data-cid="' + escapeAttr(ch.id) + '">'
                    + '<span class="browse-list-item__num">' + (idx + 1) + '</span>'
                    + '<div class="browse-list-item__text">'
                    + '<strong>' + escapeHtml(ch.title) + '</strong>'
                    + (ch.description ? '<small>' + escapeHtml(ch.description) + '</small>' : '')
                    + '</div>'
                    + '</button>';
            }).join("");

            list.querySelectorAll(".browse-list-item").forEach(function(item) {
                item.addEventListener("click", function() {
                    var ch = browseChapters.find(function(c) { return String(c.id) === item.dataset.cid; });
                    if (ch) loadChapterLessons(ch);
                });
            });
        } catch (err) {
            list.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function loadChapterLessons(chapter) {
        currentChapter = chapter;
        var lessonsSection  = document.getElementById("browse-lessons");
        var chaptersSection = document.getElementById("browse-chapters");

        chaptersSection.classList.add("hidden");
        lessonsSection.classList.remove("hidden");

        document.getElementById("lessons-title").textContent = "\uD83D\uDCDD " + chapter.title;
        var list = document.getElementById("lessons-list");
        var empty = document.getElementById("lessons-empty");
        list.innerHTML = '<p class="browse-empty">Loading lessons...</p>';
        empty.classList.add("hidden");

        try {
            var resp = await fetch(API_BASE + "/syllabus/lessons/" + chapter.id, {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load lessons");
            var lessons = await resp.json();

            if (!lessons.length) {
                list.innerHTML = "";
                empty.classList.remove("hidden");
                return;
            }

            list.innerHTML = lessons.map(function(l, idx) {
                return '<button class="browse-list-item" data-lid="' + escapeAttr(l.id) + '">'
                    + '<span class="browse-list-item__num">' + (idx + 1) + '</span>'
                    + '<div class="browse-list-item__text">'
                    + '<strong>' + escapeHtml(l.title) + '</strong>'
                    + '<small>' + escapeHtml((l.language_code || "en").toUpperCase()) + ' \u2022 ' + new Date(l.created_at).toLocaleDateString() + '</small>'
                    + '</div>'
                    + '</button>';
            }).join("");

            list.querySelectorAll(".browse-list-item").forEach(function(item) {
                item.addEventListener("click", function() {
                    var lesson = lessons.find(function(l) { return String(l.id) === item.dataset.lid; });
                    if (lesson) {
                        showLessonDetail({
                            topic: lesson.title,
                            content: lesson.content_markdown,
                            sources: [],
                        });
                    }
                });
            });
        } catch (err) {
            list.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function onGenerateLesson() {
        if (!currentChapter) return;
        var btn = document.getElementById("generate-lesson-btn");
        btn.disabled = true;
        btn.textContent = "\u23F3 Generating...";

        try {
            var resp = await fetch(API_BASE + "/syllabus/generate/" + currentChapter.id, {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
            });
            if (!resp.ok) {
                var err = {};
                try { err = await resp.json(); } catch(ignore) {}
                throw new Error(err.detail || "Failed to generate lesson");
            }
            var lesson = await resp.json();
            showLessonDetail({
                topic: lesson.title,
                content: lesson.content_markdown,
                sources: [],
            });
        } catch (err) {
            alert(err.message || "Failed to generate lesson");
        } finally {
            btn.disabled = false;
            btn.textContent = "\u2728 Generate Lesson";
        }
    }

    // ===== QUIZZES =====

    async function loadQuizSubjects() {
        var user = SmartAuth.getUser();
        if (!user) return;

        var subjectsSection = document.getElementById("quiz-subjects");
        var chaptersSection = document.getElementById("quiz-chapters");
        var activeSection   = document.getElementById("quiz-active");
        subjectsSection.classList.remove("hidden");
        chaptersSection.classList.add("hidden");
        activeSection.classList.add("hidden");

        var grid = document.getElementById("quiz-subjects-grid");
        grid.innerHTML = '<p class="browse-empty">Loading subjects...</p>';

        try {
            var params = "curriculum=" + encodeURIComponent(user.curriculum || "CBSE")
                       + "&class_grade=" + (user.class_grade || 10);
            if (user.stream) params += "&stream=" + encodeURIComponent(user.stream);

            var resp = await fetch(API_BASE + "/syllabus/subjects?" + params, {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load subjects");
            var subjects = await resp.json();

            if (!subjects.length) {
                grid.innerHTML = '<p class="browse-empty">No subjects found. Complete onboarding first.</p>';
                return;
            }

            grid.innerHTML = subjects.map(function(s) {
                return '<button class="browse-card" data-sid="' + escapeAttr(s.id) + '">'
                    + '<div class="browse-card__icon">' + getSubjectIcon(s.name) + '</div>'
                    + '<div class="browse-card__name">' + escapeHtml(s.name) + '</div>'
                    + '</button>';
            }).join("");

            grid.querySelectorAll(".browse-card").forEach(function(card) {
                card.addEventListener("click", function() {
                    var subj = subjects.find(function(s) { return String(s.id) === card.dataset.sid; });
                    if (subj) loadQuizChapters(subj);
                });
            });
        } catch (err) {
            grid.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function loadQuizChapters(subject) {
        var chaptersSection = document.getElementById("quiz-chapters");
        var subjectsSection = document.getElementById("quiz-subjects");
        var activeSection   = document.getElementById("quiz-active");

        subjectsSection.classList.add("hidden");
        chaptersSection.classList.remove("hidden");
        activeSection.classList.add("hidden");

        document.getElementById("quiz-chapters-title").textContent = "\uD83D\uDCD6 " + subject.name + " \u2014 Chapters";
        var list = document.getElementById("quiz-chapters-list");
        list.innerHTML = '<p class="browse-empty">Loading chapters...</p>';

        try {
            var resp = await fetch(API_BASE + "/syllabus/chapters/" + subject.id, {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load chapters");
            var chapters = await resp.json();

            if (!chapters.length) {
                list.innerHTML = '<p class="browse-empty">No chapters available.</p>';
                return;
            }

            list.innerHTML = chapters.map(function(ch, idx) {
                return '<button class="browse-list-item" data-cid="' + escapeAttr(ch.id) + '">'
                    + '<span class="browse-list-item__num">' + (idx + 1) + '</span>'
                    + '<div class="browse-list-item__text">'
                    + '<strong>' + escapeHtml(ch.title) + '</strong>'
                    + '</div>'
                    + '<span class="browse-list-item__arrow">\u25B6</span>'
                    + '</button>';
            }).join("");

            list.querySelectorAll(".browse-list-item").forEach(function(item) {
                item.addEventListener("click", function() {
                    var ch = chapters.find(function(c) { return String(c.id) === item.dataset.cid; });
                    if (ch) startQuiz(ch);
                });
            });
        } catch (err) {
            list.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function startQuiz(chapter) {
        currentChapter = chapter;
        var chaptersSection = document.getElementById("quiz-chapters");
        var subjectsSection = document.getElementById("quiz-subjects");
        var activeSection   = document.getElementById("quiz-active");

        subjectsSection.classList.add("hidden");
        chaptersSection.classList.add("hidden");
        activeSection.classList.remove("hidden");

        document.getElementById("quiz-chapter-name").textContent = chapter.title;
        document.getElementById("quiz-question-area").innerHTML = '<div class="browse-empty"><div class="loading-spinner"></div><p>Loading quiz or generating questions...</p></div>';
        document.getElementById("quiz-results").classList.add("hidden");
        document.getElementById("quiz-submit-btn").classList.remove("hidden");
        document.getElementById("quiz-submit-btn").disabled = false;
        quizSubmitted = false;

        try {
            var resp = await fetch(API_BASE + "/quiz/flashcards/" + chapter.id, {
                headers: SmartAuth.getAuthHeaders(),
            });
            var flashcards = [];
            if (resp.ok) flashcards = await resp.json();

            if (!flashcards.length) {
                var genResp = await fetch(API_BASE + "/quiz/generate/" + chapter.id, {
                    method: "POST",
                    headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                });
                if (genResp.ok) flashcards = await genResp.json();
            }

            if (!flashcards.length) {
                document.getElementById("quiz-question-area").innerHTML = '<p class="browse-empty">No questions could be generated. Try again.</p>';
                return;
            }

            quizQuestions = flashcards;
            document.getElementById("quiz-progress-text").textContent = flashcards.length + " questions";
            renderQuizQuestions(flashcards);

        } catch (err) {
            document.getElementById("quiz-question-area").innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    function renderQuizQuestions(questions) {
        var area = document.getElementById("quiz-question-area");
        area.innerHTML = questions.map(function(q, idx) {
            var html = '<div class="quiz-card" data-qidx="' + idx + '">';
            html += '<div class="quiz-card__header">';
            html += '<span class="quiz-card__num">Q' + (idx + 1) + '</span>';
            html += '<span class="quiz-card__type quiz-card__type--' + q.question_type + '">' + q.question_type.toUpperCase() + '</span>';
            html += '</div>';
            html += '<p class="quiz-card__question">' + escapeHtml(q.question) + '</p>';

            if (q.question_type === "numerical") {
                html += '<input type="text" class="quiz-input" data-qidx="' + idx + '" placeholder="Enter your answer" />';
            } else if (q.options_json && q.options_json.length) {
                var inputType = q.question_type === "msq" ? "checkbox" : "radio";
                html += '<div class="quiz-options">';
                q.options_json.forEach(function(opt, oi) {
                    html += '<label class="quiz-option">';
                    html += '<input type="' + inputType + '" name="q' + idx + '" value="' + escapeAttr(opt.charAt(0)) + '" />';
                    html += '<span>' + escapeHtml(opt) + '</span>';
                    html += '</label>';
                });
                html += '</div>';
            }

            html += '<div class="quiz-card__explanation hidden" data-expl="' + idx + '"></div>';
            html += '</div>';
            return html;
        }).join("");
    }

    function onQuizSubmit() {
        if (quizSubmitted || !quizQuestions.length) return;
        quizSubmitted = true;

        var correct = 0;
        var total   = quizQuestions.length;

        quizQuestions.forEach(function(q, idx) {
            var card = document.querySelector('.quiz-card[data-qidx="' + idx + '"]');
            if (!card) return;
            var explanation = card.querySelector('[data-expl="' + idx + '"]');
            var userAnswer = "";

            if (q.question_type === "numerical") {
                var input = card.querySelector('.quiz-input[data-qidx="' + idx + '"]');
                userAnswer = input ? input.value.trim() : "";
            } else if (q.question_type === "msq") {
                var checked = card.querySelectorAll('input[name="q' + idx + '"]:checked');
                var selected = [];
                checked.forEach(function(c) { selected.push(c.value); });
                userAnswer = selected.sort().join(",");
            } else {
                var radio = card.querySelector('input[name="q' + idx + '"]:checked');
                userAnswer = radio ? radio.value : "";
            }

            var correctAnswer = (q.answer || "").trim();
            var isCorrect = false;

            if (q.question_type === "msq") {
                var correctParts = correctAnswer.split(",").map(function(s) { return s.trim().toUpperCase(); }).sort().join(",");
                isCorrect = userAnswer.toUpperCase() === correctParts;
            } else if (q.question_type === "numerical") {
                isCorrect = userAnswer === correctAnswer;
            } else {
                isCorrect = userAnswer.toUpperCase() === correctAnswer.toUpperCase();
            }

            if (isCorrect) correct++;
            card.classList.add(isCorrect ? "quiz-card--correct" : "quiz-card--wrong");

            if (explanation) {
                explanation.classList.remove("hidden");
                explanation.innerHTML = '<strong>' + (isCorrect ? "\u2705 Correct!" : "\u274C Wrong \u2014 Answer: " + escapeHtml(correctAnswer)) + '</strong>'
                    + (q.explanation ? '<p>' + escapeHtml(q.explanation) + '</p>' : '');
            }

            card.querySelectorAll("input").forEach(function(inp) { inp.disabled = true; });
        });

        var results = document.getElementById("quiz-results");
        var pct = Math.round((correct / total) * 100);
        results.innerHTML = '<div class="quiz-results__card">'
            + '<h3>Quiz Results</h3>'
            + '<div class="quiz-results__score">' + correct + ' / ' + total + '</div>'
            + '<div class="quiz-results__pct">' + pct + '%</div>'
            + '<div class="quiz-results__bar"><div class="quiz-results__fill" style="width:' + pct + '%;background:' + (pct >= 70 ? 'var(--success)' : pct >= 40 ? '#FF8F00' : 'var(--error)') + '"></div></div>'
            + '<button class="btn btn--outline btn--sm" id="quiz-retry-btn">\uD83D\uDD04 Try Another Quiz</button>'
            + '</div>';
        results.classList.remove("hidden");
        document.getElementById("quiz-submit-btn").classList.add("hidden");

        document.getElementById("quiz-retry-btn").addEventListener("click", function() {
            loadQuizSubjects();
        });

        updateProgress(currentChapter.id, { quiz_score: pct, flashcards_reviewed: total });
    }

    // ===== EXAM PREP =====

    async function loadExams() {
        var user = SmartAuth.getUser();
        var examListSection = document.getElementById("exam-list");
        var mockTestsSection = document.getElementById("exam-mock-tests");
        var takeTestSection = document.getElementById("exam-take-test");

        examListSection.classList.remove("hidden");
        mockTestsSection.classList.add("hidden");
        takeTestSection.classList.add("hidden");

        var grid = document.getElementById("exams-grid");
        var empty = document.getElementById("exams-empty");
        grid.innerHTML = '<p class="browse-empty">Loading exams...</p>';
        empty.classList.add("hidden");

        try {
            var url = API_BASE + "/exams/";
            if (user && user.class_grade) url += "?class_grade=" + user.class_grade;

            var resp = await fetch(url, { headers: SmartAuth.getAuthHeaders() });
            if (!resp.ok) throw new Error("Failed to load exams");
            examsList = await resp.json();

            if (!examsList.length) {
                grid.innerHTML = "";
                empty.classList.remove("hidden");
                return;
            }

            grid.innerHTML = examsList.map(function(ex) {
                var subjects = (ex.subjects_json || []).join(", ");
                return '<button class="browse-card browse-card--exam" data-eid="' + escapeAttr(ex.id) + '">'
                    + '<div class="browse-card__icon">\uD83C\uDFC6</div>'
                    + '<div class="browse-card__name">' + escapeHtml(ex.name) + '</div>'
                    + '<div class="browse-card__desc">' + escapeHtml(subjects) + '</div>'
                    + '</button>';
            }).join("");

            grid.querySelectorAll(".browse-card").forEach(function(card) {
                card.addEventListener("click", function() {
                    var exam = examsList.find(function(e) { return String(e.id) === card.dataset.eid; });
                    if (exam) loadMockTests(exam);
                });
            });
        } catch (err) {
            grid.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function loadMockTests(exam) {
        currentExam = exam;
        var mockTestsSection = document.getElementById("exam-mock-tests");
        var examListSection = document.getElementById("exam-list");
        var takeTestSection = document.getElementById("exam-take-test");

        examListSection.classList.add("hidden");
        mockTestsSection.classList.remove("hidden");
        takeTestSection.classList.add("hidden");

        document.getElementById("mock-tests-title").textContent = "\uD83D\uDCDD " + exam.name + " \u2014 Mock Tests";
        var list = document.getElementById("mock-tests-list");
        var empty = document.getElementById("mock-tests-empty");
        list.innerHTML = '<p class="browse-empty">Loading mock tests...</p>';
        empty.classList.add("hidden");

        try {
            var resp = await fetch(API_BASE + "/exams/" + exam.id + "/mock-tests", {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load mock tests");
            var tests = await resp.json();

            if (!tests.length) {
                list.innerHTML = "";
                empty.classList.remove("hidden");
                return;
            }

            list.innerHTML = tests.map(function(t, idx) {
                return '<button class="browse-list-item" data-tid="' + escapeAttr(t.id) + '">'
                    + '<span class="browse-list-item__num">' + (idx + 1) + '</span>'
                    + '<div class="browse-list-item__text">'
                    + '<strong>' + escapeHtml(t.title) + '</strong>'
                    + '<small>' + t.duration_minutes + ' min \u2022 ' + t.total_marks + ' marks \u2022 ' + (t.questions_json ? t.questions_json.length : 0) + ' questions</small>'
                    + '</div>'
                    + '<span class="browse-list-item__arrow">\u25B6</span>'
                    + '</button>';
            }).join("");

            list.querySelectorAll(".browse-list-item").forEach(function(item) {
                item.addEventListener("click", function() {
                    var test = tests.find(function(t) { return String(t.id) === item.dataset.tid; });
                    if (test) startMockTest(test);
                });
            });
        } catch (err) {
            list.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    async function onGenerateMockTest() {
        if (!currentExam) return;
        var btn = document.getElementById("generate-mock-btn");
        btn.disabled = true;
        btn.textContent = "\u23F3 Generating...";

        try {
            var resp = await fetch(API_BASE + "/exams/mock-tests/" + currentExam.id + "/generate", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
            });
            if (!resp.ok) {
                var err = {};
                try { err = await resp.json(); } catch(ignore) {}
                throw new Error(err.detail || "Failed to generate mock test");
            }
            var test = await resp.json();
            startMockTest(test);
        } catch (err) {
            alert(err.message || "Failed to generate mock test");
        } finally {
            btn.disabled = false;
            btn.textContent = "\u2728 Generate Mock Test";
        }
    }

    function startMockTest(test) {
        currentMockTest = test;
        var takeTestSection = document.getElementById("exam-take-test");
        var mockTestsSection = document.getElementById("exam-mock-tests");
        var examListSection = document.getElementById("exam-list");

        examListSection.classList.add("hidden");
        mockTestsSection.classList.add("hidden");
        takeTestSection.classList.remove("hidden");

        document.getElementById("mock-test-title").textContent = test.title;
        document.getElementById("mock-results").classList.add("hidden");
        document.getElementById("mock-submit-btn").classList.remove("hidden");
        document.getElementById("mock-submit-btn").disabled = false;

        var questions = test.questions_json || [];
        document.getElementById("mock-progress-text").textContent = questions.length + " questions \u2022 " + test.total_marks + " marks";

        mockSeconds = 0;
        if (mockTimer) clearInterval(mockTimer);
        mockTimer = setInterval(function() {
            mockSeconds++;
            var m = Math.floor(mockSeconds / 60);
            var s = mockSeconds % 60;
            document.getElementById("mock-timer").textContent = "Time: " + m + ":" + (s < 10 ? "0" : "") + s;
        }, 1000);

        renderMockQuestions(questions);
    }

    function renderMockQuestions(questions) {
        var area = document.getElementById("mock-question-area");
        area.innerHTML = questions.map(function(q, idx) {
            var html = '<div class="quiz-card" data-midx="' + idx + '">';
            html += '<div class="quiz-card__header">';
            html += '<span class="quiz-card__num">Q' + (idx + 1) + '</span>';
            html += '<span class="quiz-card__type quiz-card__type--mcq">MCQ</span>';
            html += '</div>';
            html += '<p class="quiz-card__question">' + escapeHtml(q.q || q.question || "Question " + (idx + 1)) + '</p>';

            var options = q.options || {};
            if (typeof options === "object" && !Array.isArray(options)) {
                html += '<div class="quiz-options">';
                Object.keys(options).forEach(function(key) {
                    html += '<label class="quiz-option">';
                    html += '<input type="radio" name="mock' + idx + '" value="' + escapeAttr(key) + '" />';
                    html += '<span>' + escapeHtml(key + ". " + options[key]) + '</span>';
                    html += '</label>';
                });
                html += '</div>';
            } else if (Array.isArray(options)) {
                html += '<div class="quiz-options">';
                options.forEach(function(opt) {
                    html += '<label class="quiz-option">';
                    html += '<input type="radio" name="mock' + idx + '" value="' + escapeAttr(opt.charAt(0)) + '" />';
                    html += '<span>' + escapeHtml(opt) + '</span>';
                    html += '</label>';
                });
                html += '</div>';
            }

            html += '<div class="quiz-card__explanation hidden" data-mexpl="' + idx + '"></div>';
            html += '</div>';
            return html;
        }).join("");
    }

    function onMockTestSubmit() {
        if (!currentMockTest) return;
        if (mockTimer) { clearInterval(mockTimer); mockTimer = null; }

        var questions = currentMockTest.questions_json || [];
        var score = 0;
        var answersJson = {};

        questions.forEach(function(q, idx) {
            var card = document.querySelector('.quiz-card[data-midx="' + idx + '"]');
            if (!card) return;
            var explanation = card.querySelector('[data-mexpl="' + idx + '"]');
            var radio = card.querySelector('input[name="mock' + idx + '"]:checked');
            var userAnswer = radio ? radio.value : "";
            var correctAnswer = (q.answer || "").trim();
            var qText = q.q || q.question || "";

            answersJson[qText] = userAnswer;

            var isCorrect = userAnswer.toUpperCase() === correctAnswer.toUpperCase();
            if (isCorrect) {
                score += 4;
            } else if (userAnswer) {
                score -= 1;
            }

            card.classList.add(isCorrect ? "quiz-card--correct" : (userAnswer ? "quiz-card--wrong" : ""));
            if (explanation) {
                explanation.classList.remove("hidden");
                explanation.innerHTML = '<strong>' + (isCorrect ? "\u2705 Correct! (+4)" : userAnswer ? "\u274C Wrong (-1) \u2014 Answer: " + escapeHtml(correctAnswer) : "\u26AA Unanswered \u2014 Answer: " + escapeHtml(correctAnswer)) + '</strong>';
            }

            card.querySelectorAll("input").forEach(function(inp) { inp.disabled = true; });
        });

        var results = document.getElementById("mock-results");
        var maxScore = questions.length * 4;
        var pct = maxScore > 0 ? Math.round((Math.max(0, score) / maxScore) * 100) : 0;
        var timeMins = Math.round(mockSeconds / 60);

        results.innerHTML = '<div class="quiz-results__card">'
            + '<h3>Mock Test Results</h3>'
            + '<div class="quiz-results__score">' + score + ' / ' + maxScore + '</div>'
            + '<div class="quiz-results__pct">' + pct + '% \u2022 ' + timeMins + ' min</div>'
            + '<div class="quiz-results__bar"><div class="quiz-results__fill" style="width:' + pct + '%;background:' + (pct >= 70 ? 'var(--success)' : pct >= 40 ? '#FF8F00' : 'var(--error)') + '"></div></div>'
            + '<p style="font-size:13px;color:var(--text-muted)">Scoring: +4 correct, -1 wrong, 0 unanswered</p>'
            + '<button class="btn btn--outline btn--sm" id="mock-back-btn">\u2190 Back to Exams</button>'
            + '</div>';
        results.classList.remove("hidden");
        document.getElementById("mock-submit-btn").classList.add("hidden");

        document.getElementById("mock-back-btn").addEventListener("click", function() { loadExams(); });

        submitMockAttempt(answersJson, score, timeMins);
    }

    async function submitMockAttempt(answersJson, score, timeMins) {
        try {
            await fetch(API_BASE + "/exams/mock-tests/" + currentMockTest.id + "/attempt", {
                method: "POST",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({
                    mock_test_id: currentMockTest.id,
                    answers_json: answersJson,
                    time_taken_minutes: timeMins,
                }),
            });
        } catch (ignore) { }
    }

    // ===== PROFILE =====

    async function loadProfile() {
        var user = SmartAuth.getUser();
        if (!user) return;

        document.getElementById("profile-name").textContent = user.name || "Student";
        document.getElementById("profile-email").textContent = user.email || "";
        document.getElementById("profile-curriculum").textContent = user.curriculum || "Not set";
        document.getElementById("profile-class").textContent = user.class_grade ? "Class " + user.class_grade : "Not set";
        document.getElementById("profile-stream").textContent = user.stream ? capitalize(user.stream) : "N/A";

        var langNames = { en: "English", hi: "Hindi", kn: "Kannada", te: "Telugu", ta: "Tamil" };
        document.getElementById("profile-language").textContent = langNames[user.language_preference] || user.language_preference || "English";
        document.getElementById("profile-lang-select").value = user.language_preference || "en";

        var avatarDiv = document.getElementById("profile-avatar");
        if (user.profile_picture_url) {
            avatarDiv.innerHTML = '<img src="' + escapeAttr(user.profile_picture_url) + '" alt="' + escapeAttr(user.name) + '" style="width:80px;height:80px;border-radius:50%;object-fit:cover" />';
        } else {
            avatarDiv.innerHTML = '<div style="width:80px;height:80px;border-radius:50%;background:var(--primary);color:white;display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:bold">' + (user.name ? user.name.charAt(0).toUpperCase() : "S") + '</div>';
        }

        loadProfileStats();
    }

    async function loadProfileStats() {
        var statsDiv = document.getElementById("profile-stats");
        var emptyDiv = document.getElementById("profile-stats-empty");
        statsDiv.innerHTML = '<p class="browse-empty">Loading stats...</p>';
        emptyDiv.classList.add("hidden");

        try {
            var resp = await fetch(API_BASE + "/progress/stats", {
                headers: SmartAuth.getAuthHeaders(),
            });
            if (!resp.ok) throw new Error("Failed to load stats");
            var stats = await resp.json();

            if (!stats.length) {
                statsDiv.innerHTML = "";
                emptyDiv.classList.remove("hidden");
                return;
            }

            statsDiv.innerHTML = stats.map(function(s) {
                var pct = s.total_chapters > 0 ? Math.round((s.chapters_completed / s.total_chapters) * 100) : 0;
                var timeMin = Math.round((s.total_time_spent_seconds || 0) / 60);
                return '<div class="stat-card">'
                    + '<div class="stat-card__header">'
                    + '<strong>' + escapeHtml(s.subject_name) + '</strong>'
                    + '<span>' + s.chapters_completed + '/' + s.total_chapters + ' chapters</span>'
                    + '</div>'
                    + '<div class="stat-card__bar"><div class="stat-card__fill" style="width:' + pct + '%"></div></div>'
                    + '<div class="stat-card__details">'
                    + '<span>\uD83D\uDCCA Quiz: ' + (s.avg_quiz_score != null ? s.avg_quiz_score + '%' : '\u2014') + '</span>'
                    + '<span>\uD83C\uDCCF Cards: ' + s.total_flashcards_reviewed + '</span>'
                    + '<span>\u23F1 ' + timeMin + ' min</span>'
                    + '</div>'
                    + '</div>';
            }).join("");

        } catch (err) {
            statsDiv.innerHTML = '<p class="browse-empty">' + escapeHtml(err.message) + '</p>';
        }
    }

    function openEditAcademicDialog() {
        var dialog = document.getElementById("edit-academic-dialog");
        var user = SmartAuth.getUser();

        var currSelect = document.getElementById("edit-curriculum");
        var curricula = allCurricula.length ? allCurricula : ["CBSE", "ICSE", "State Board"];
        currSelect.innerHTML = curricula.map(function(c) {
            return '<option value="' + escapeAttr(c) + '"' + (user && user.curriculum === c ? ' selected' : '') + '>' + escapeHtml(c) + '</option>';
        }).join("");

        if (user) {
            document.getElementById("edit-class").value = user.class_grade || "10";
            document.getElementById("edit-stream").value = user.stream || "";
        }

        dialog.classList.remove("hidden");
    }

    function closeEditAcademicDialog() {
        document.getElementById("edit-academic-dialog").classList.add("hidden");
    }

    async function saveAcademicInfo() {
        var curriculum = document.getElementById("edit-curriculum").value;
        var classGrade = parseInt(document.getElementById("edit-class").value);
        var stream     = document.getElementById("edit-stream").value || null;

        closeEditAcademicDialog();
        showLoading("Updating profile...");

        try {
            var resp = await fetch(API_BASE + "/auth/profile", {
                method: "PATCH",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify({
                    curriculum: curriculum,
                    class_grade: classGrade,
                    stream: stream,
                }),
            });
            if (resp.ok) {
                var updated = await resp.json();
                var user = SmartAuth.getUser();
                if (user) {
                    user.curriculum = updated.curriculum;
                    user.class_grade = updated.class_grade;
                    user.stream = updated.stream;
                    user.onboarding_complete = true;
                }
                loadProfile();
            }
        } catch (ignore) { }
        hideLoading();
    }

    // ===== PROGRESS TRACKING =====

    async function updateProgress(chapterId, data) {
        try {
            await fetch(API_BASE + "/progress/" + chapterId, {
                method: "PATCH",
                headers: Object.assign({ "Content-Type": "application/json" }, SmartAuth.getAuthHeaders()),
                body: JSON.stringify(data),
            });
        } catch (ignore) { }
    }

    // ===== HELPERS =====

    function escapeHtml(str) {
        var d = document.createElement("div");
        d.textContent = str;
        return d.innerHTML;
    }

    function escapeAttr(str) {
        return String(str).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#039;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function capitalize(str) {
        return str ? str.charAt(0).toUpperCase() + str.slice(1) : "";
    }

    function getSubjectIcon(name) {
        var n = name.toLowerCase();
        if (n.includes("math")) return "\uD83D\uDCD0";
        if (n.includes("physic")) return "\u269B\uFE0F";
        if (n.includes("chem")) return "\uD83E\uDDEA";
        if (n.includes("bio")) return "\uD83E\uDDEC";
        if (n.includes("english")) return "\uD83D\uDCD6";
        if (n.includes("hindi")) return "\uD83D\uDCDD";
        if (n.includes("history")) return "\uD83C\uDFDB\uFE0F";
        if (n.includes("geo")) return "\uD83C\uDF0D";
        if (n.includes("computer") || n.includes("cs")) return "\uD83D\uDCBB";
        if (n.includes("econ")) return "\uD83D\uDCC8";
        if (n.includes("account")) return "\uD83D\uDCCA";
        if (n.includes("science")) return "\uD83D\uDD2C";
        return "\uD83D\uDCDA";
    }

    // ===== BOOT =====
    init();
})();
