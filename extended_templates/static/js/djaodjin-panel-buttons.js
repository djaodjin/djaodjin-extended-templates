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


    /** Sliding panel

        HTML requirements:

        <button data-target="#_panel_" data-default-width="300"></button>
        <div id="#_panel_"></div>
     */
    function PanelButton(el, options){
        this.element = $(el);
        this.options = options;
        this.defaultWidth = 300;
        this.init();
    }

    PanelButton.prototype = {
        init: function () {
            var self = this;

            var target = $(document.querySelector(
                self.element.attr("data-target")));
            if( typeof self.options.defaultWidth !== "undefined" ) {
                self.defaultWidth = self.options.defaultWidth;
            } else {
                var defaultWidth = self.element.attr("data-default-width");
                if( defaultWidth ) {
                    self.defaultWidth = parseInt(defaultWidth);
                }
            }

            target.find(".dj-close").click(function() {
                self.element.css({right: 0});
            });

            self.element.click(function(event) {
                event.preventDefault();
                var $djgallery = target.data("djgallery");
                if( target.css('display') == 'none' ) {
                    if( $djgallery ) {
                        $djgallery.showGallery();
                    } else {
                        target.show();
                        target.find('.content').trigger("pages.loadresources");
                        target.css({right: 0, width: self.defaultWidth}).addClass("visible-gallery");
                    }
                } else {
                    if( $djgallery ) {
                        $djgallery.hideGallery();
                    } else {
                        target.hide();
                        target.css({right: -self.defaultWidth, width: self.defaultWidth}).removeClass("visible-gallery");
                    }
                }
            });
        }
    };

    $.fn.panelButton = function(options) {
        var opts = $.extend( {}, $.fn.panelButton.defaults, options );
        return this.each(function() {
            if (!$.data(this, "panelButton")) {
                $.data(this, "panelButton", new PanelButton(this, opts));
            }
        });
    };

    $.fn.panelButton.defaults = {
//        defaultWidth: 300
    };

})(jQuery);

}));
