(function() {
    // Desabilitar reporting
    window.reporting = null;
    window.WTM = null;

    // Interceptar e prevenir eventos de reporting
    window.addEventListener('load', function() {
        const originalAdd = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type === 'mousedown' && (listener+'').includes('reporting')) {
                return;
            }
            return originalAdd.call(this, type, listener, options);
        };
    }, true);
})();
