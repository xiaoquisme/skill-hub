/**
 * SkillHub i18n — lightweight translation system
 * Auto-detects browser locale; Chinese (zh) is the default.
 */
(function() {
    'use strict';

    var messages = {
        'en': null,
        'zh-CN': null
    };

    var currentLocale = 'en';

    function detectLocale() {
        var lang = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
        if (lang.startsWith('zh')) {
            return 'zh-CN';
        }
        return 'en';
    }

    function t(key) {
        var dict = messages[currentLocale] || messages['en'] || {};
        return dict[key] || key;
    }

    function init() {
        currentLocale = detectLocale();
        document.documentElement.lang = currentLocale === 'zh-CN' ? 'zh-CN' : 'en';
    }

    // Load translation files
    function loadLocale(locale, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/ui/locales/' + locale + '.json', true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                messages[locale] = JSON.parse(xhr.responseText);
                callback();
            }
        };
        xhr.send();
    }

    // Initialize and load both locales
    init();

    var pending = 2;
    function onLoaded() {
        pending--;
        if (pending === 0) {
            // Dispatch event so app.js can re-render
            document.dispatchEvent(new Event('i18n:ready'));
        }
    }

    loadLocale('en', onLoaded);
    loadLocale('zh-CN', onLoaded);

    // Expose globally
    window.t = t;
    window.getLocale = function() { return currentLocale; };
})();
