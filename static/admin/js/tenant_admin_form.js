(function($) {
    'use strict';
    
    $(document).ready(function() {
        var $username = $('#id_username');
        var $schemaName = $('#id_schema_name');
        var $domainName = $('#id_domain_name');
        
        // Detectar si estamos en producción basado en la URL
        var isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
        var domainSuffix = isProduction ? '.zentoerp.com' : '.localhost';
        
        function cleanUsername(username) {
            return username.toLowerCase().replace(/[^a-z0-9_]/g, '');
        }
        
        function updateFields() {
            var username = $username.val();
            if (username) {
                var cleanName = cleanUsername(username);
                
                // Solo actualizar si los campos están vacíos
                if (!$schemaName.val()) {
                    $schemaName.val(cleanName);
                }
                if (!$domainName.val()) {
                    $domainName.val(cleanName + domainSuffix);
                }
            }
        }
        
        // Actualizar cuando cambie el username
        $username.on('input blur', updateFields);
        
        // Actualizar al cargar la página si hay un username
        updateFields();
    });
})(django.jQuery);
