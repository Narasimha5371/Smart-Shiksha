/**
 * Lightweight JSON-based i18n for the Web Portal.
 *
 * How it works:
 *  1. Reads locale JSON files from /locales/<code>.json
 *  2. Finds all elements with [data-i18n] and replaces innerText
 *  3. Finds all elements with [data-i18n-placeholder] and replaces placeholder attr
 *
 * Usage:
 *   I18n.init("en");            // load English on page load
 *   I18n.setLocale("hi");       // switch to Hindi
 *   I18n.t("askButton");        // get a translated string programmatically
 */
const I18n = (() => {
    let _currentLocale = "en";
    let _strings = {};
    const _cache = {};           // locale → dict (avoids re-fetching)

    /** Load a locale file and apply translations to the DOM. */
    async function setLocale(code) {
        _currentLocale = code;

        if (_cache[code]) {
            _strings = _cache[code];
        } else {
            try {
                const resp = await fetch(`locales/${code}.json`);
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                _strings = await resp.json();
                _cache[code] = _strings;
            } catch (err) {
                console.warn(`[i18n] Failed to load locale "${code}", falling back to en.`, err);
                if (code !== "en") return setLocale("en");
                _strings = {};
            }
        }

        _applyToDom();
    }

    /** Initialize with a default locale. */
    async function init(code = "en") {
        await setLocale(code);
    }

    /** Get the current locale code. */
    function getLocale() {
        return _currentLocale;
    }

    /** Translate a key (returns the key itself if not found). */
    function t(key) {
        return _strings[key] || key;
    }

    /** Walk the DOM and update all [data-i18n] / [data-i18n-placeholder] elements. */
    function _applyToDom() {
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (_strings[key]) el.textContent = _strings[key];
        });
        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (_strings[key]) el.placeholder = _strings[key];
        });
        // Update html lang attribute
        document.documentElement.lang = _currentLocale;
    }

    return { init, setLocale, getLocale, t };
})();
