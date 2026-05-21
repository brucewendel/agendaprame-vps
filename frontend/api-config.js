(function () {
    function defaultApiBaseUrl() {
        const host = window.location.hostname;
        const protocol = window.location.protocol;

        return '/api';
    }

    const configuredApiBaseUrl = window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL;
    window.API_BASE_URL = configuredApiBaseUrl || defaultApiBaseUrl();
})();
