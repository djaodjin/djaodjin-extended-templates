/** These are plumbing functions to connect the UI and API backends.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define(['exports', 'jQuery'], factory);
    } else if (typeof exports === 'object' && typeof exports.nodeName !== 'string') {
        // CommonJS
        factory(exports, require('jQuery'));
    } else {
        // Browser true globals added to `window`.
        factory(root, root.jQuery);
        // If we want to put the exports in a namespace, use the following line
        // instead.
        // factory((root.djResources = {}), root.jQuery);
    }
}(typeof self !== 'undefined' ? self : this, function (exports, jQuery) {

(function ($) {
    "use strict";

    function NotificationTest(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    NotificationTest.prototype = {
        init: function(){
            var self = this;
            self.$el.click(function(event) {
                var self = this;
                var id = self.$el.closest(".card").attr("id");
                $.ajax({
                    type: "POST",
                    url: self.options.url + id + "/",
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader("X-CSRFToken", getMetaCSRFToken());
                    },
                    data: null,
                    datatype: "json",
                    contentType: "application/json; charset=utf-8",
                    success: function(data) {
                        showMessages([data.detail], "info");
                    },
                    error: function(resp) { showErrorMessages(resp); },
                });
            });
        },

        _getCSRFToken: function() {
            var self = this;
            var crsfNode = self.el.find("[name='csrfmiddlewaretoken']");
            if( crsfNode.length > 0 ) {
                return crsfNode.val();
            }
            return getMetaCSRFToken();
        },
    };

    $.fn.notificationTest = function(options, custom){
        var opts = $.extend( {}, $.fn.notificationTest.defaults, options );
        return this.each(function() {
            $(this).data("notificationtest",
                new NotificationTest($(this), opts));
        });
    };

    $.fn.notificationTest.defaults = {
        url: null, // Url to send request to server
        onSuccess: function(element, resp){
            return true;
        },
        onError: function(resp){
            showErrorMessages(resp);
        },
    };

}( jQuery ));

}));
