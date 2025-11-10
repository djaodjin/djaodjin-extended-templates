/**
   Functionality related to the wysiwyg editor in djaodjin-extended-templates.

   djUpload and djGallery are used to upload media files.

   These are based on jquery.
 */

/* global jQuery */
/* global showErrorMessages */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define('djEditors', ['exports', 'jQuery'], factory);
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
}(typeof self !== 'undefined' ? self : this, function (exports, jQuery, djResources) {


(function ($) {
    "use strict";

    /** Live editor based on HTML5 `contenteditable` that saves the content
        through an API call once the element looses focus.
     */
    function Editor(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    Editor.prototype = {
        init: function(){
            var self = this;
            if( self.options.editionTool ) {
                self.$el.append(self.options.editionTool);
            }
            self.$el.on("click", function(){
                self.toggleEdition();
            });
            self.$el.on("blur", function(){
                self.saveEdition();
            });
            self.$el.on("mouseover mouseleave", function(event){
                self.hoverElement(event);
            });
            if( self.options.focus ) {
                self.toggleEdition();
            }
        },

        elementUrl: function() {
            var self = this;

            var baseUrl = self.$el.data("url");
            if( !baseUrl ) {
                baseUrl = self.$el.parents("[data-url]").data("url");
            }
            if( baseUrl ) return baseUrl;

            baseUrl = self.options.baseUrl;
            baseUrl = baseUrl.replace(/\/+$/, "");

            const path = self.getId();
            // We make sure that if either `baseUrl` or `path` ends with,
            // respectively starts with, a '/' or not, concatenation will
            // not result in a '//'.
            return baseUrl + ((path.indexOf('/') != 0) ? '/' + path : path);
        },

        getId: function() {
            var self = this;
            var slug = self.$el.attr(self.options.uniqueIdentifier);
            if( !slug ) {
                slug = self.$el.parents(
                    "[" + self.options.uniqueIdentifier + "]").attr(
                        self.options.uniqueIdentifier);
            }
            if( !slug ) {
                slug = "undefined";
            }
            return slug;
        },

        hoverElement: function(event){
            var self = this;
            if (event.type === "mouseover"){
                self.$el.addClass("hover-editable");
            }else{
                self.$el.removeClass("hover-editable");
            }
        },

        getOriginText: function(){
            var self = this;
            self.originText = $.trim(self.$el[0].outerHTML);
            return self.originText;
        },

        toogleStartOptional: function(){
            return true;
        },

        toogleEndOptional: function(){
            return true;
        },

        toggleEdition: function(){
            var self = this;
            self.getOriginText();
            self.$el.attr("placeholder", self.options.emptyInputText);
            self.$el.attr("contenteditable", true);
            self.$el.focus();
        },

        getSavedText: function(){
            var self = this;
            return $.trim(self.$el.html());
        },

        checkInput: function(){
            var self = this;
            if (self.getSavedText() === ""){
                return false;
            }else{
                return true;
            }
        },

        formatDisplayedValue: function(){
            return true;
        },

        saveEdition: function() {
            var self = this;
            if( !self.checkInput() ) {
                return false;
            }

            var data = {};
            var method = "PUT";
            var savedText = self.getSavedText();
            if( self.$el.attr("data-key") ) {
                data[self.$el.attr("data-key")] = savedText;
            } else {
                data = {
                    slug: self.getId(),
                    text: savedText
                };
            }
            if( self.options.hints ) {
                data['hints'] = self.options.hints;
            }
            djApi.put(self.elementUrl(), data,
            function(resp) {
                self.options.onSuccess(self, resp);
                self.$el.removeAttr("contenteditable");
                self.formatDisplayedValue();
            }, self.options.onError);
        }
    };

    /** Special editor that checks for currency formatting
     */
    function CurrencyEditor(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    CurrencyEditor.prototype = $.extend({}, Editor.prototype, {

        getSavedText: function(){
            var self = this;
            if( self.$el.attr("data-key") ) {
                const enteredValue = self.$el.text();
                return parseInt(
                    (parseFloat(enteredValue.replace(/[^0-9\.]+/g, ""))
                     * 100).toFixed(2));
            }
            return $.trim(self.$el.text());
        },

        formatDisplayedValue: function(){
            var self = this;
            var defaultCurrencyUnit = "$";
            var defaultCurrencyPosition = "before";
            if (self.$el.data("currency-unit")){
                defaultCurrencyUnit = self.$el.data("currency-unit");
            }

            if (self.$el.data("currency-position")){
                defaultCurrencyPosition = self.$el.data("currency-position");
            }

            var amount = String((self.getSavedText() / 100).toFixed(2));
            if (defaultCurrencyPosition === "before"){
                amount = defaultCurrencyUnit + amount;
            }else if(defaultCurrencyPosition === "after"){
                amount = amount + defaultCurrencyUnit;
            }
            self.$el.html(amount);
        }
    });


    /** Special editor that checks for date formatting
     */
    function DateEditor(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    DateEditor.prototype = $.extend({}, Editor.prototype, {

        valueSelector: function() {
            var self = this;
            self.$valueSelector = $(self.options.templates.dateSelector);

            self.$valueSelector.on("blur", function(event){
                self.saveEdition();
                self.$valueSelector.remove();
                self.$valueSelector = null;
                event.stopPropagation();
            });

            return self.$valueSelector;
        },

        getSavedText: function(){
            var self = this;
            var enteredValue = self.$el.text();
            var amount = parseInt(
                (parseFloat(enteredValue.replace(/[^0-9\.]+/g, "")) * 100).toFixed(2));
            return amount;
        },

        toggleEdition: function(){
            var self = this;
            if (self.$valueSelector){
                self.$valueSelector.blur();
            }else{
//                self.getOriginText();
                self.$el.append(self.valueSelector());
                self.$valueSelector.focus();
            }
        }
    });


    /** Special editor that checks for an integer range
     */
    function RangeEditor(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    RangeEditor.prototype = $.extend({}, Editor.prototype, {
        valueSelector: function(){
            var self = this;
            self.$valueSelector = $(self.options.templates.rangeSelector);

            self.$valueSelector.on("blur", function(event) {
                event.stopPropagation();
                self.saveEdition();
                const text = self.getHumanizedSavedText();
                self.$el.data("range-value", self.$valueSelector.val());
                self.$valueSelector.remove();
                self.$valueSelector = null;
                self.$el.text(text);
            });

            return self.$valueSelector;
        },

        getHumanizedSavedText: function() {
            var self = this;
            const minVal = self.$el.data("range-min");
            const newVal = self.$valueSelector.val();
            const updatedVal = minVal ? newVal - minVal : newVal;
            var values = self.$el.data("range-values");
            if( values ) {
                const item = values[updatedVal];
                if( item ) {
                    return item[1];
                }
            }
            return newVal;
         },

        getSavedText: function() {
            var self = this;
            const minVal = self.$el.data("range-min");
            const newVal = self.$valueSelector.val();
            const updatedVal = minVal ? newVal - minVal : newVal;
            var values = self.$el.data("range-values");
            if( values ) {
                const item = values[updatedVal];
                if( item ) {
                    return item[0];
                }
            }
            return newVal;
         },

        toggleEdition: function() {
            var self = this;
            if( self.$valueSelector ) {
                self.$valueSelector.blur();
            } else {
                self.$el.empty();
                self.$el.append(self.valueSelector());
                var initVal = self.$el.data("range-min");
                const initRangeValue = self.$el.data("range-value");
                if( initRangeValue !== "undefined" ) {
                    initVal = parseInt(initRangeValue);
                    if( false ) {
                    const values = self.$el.data("range-values");
                    if( values ) {
                        for( let idx = 0; idx < values.length; ++idx ) {
                            if( values[idx][0] == initRangeValue ) {
                                initVal = idx;
                                break
                            }
                        }
                    }
                    }
                }
                self.$valueSelector
                    .attr("min", self.$el.data("range-min"))
                    .attr("max", self.$el.data("range-max"))
                    .attr("step", self.$el.data("range-step"))
                    .val(initVal);
                if (self.options.rangePosition === "middle"){
                    self.$valueSelector.css({top: (self.$el.offset().top + (self.$el.height() / 2)) + "px"});
                }else if (self.options.rangePosition === "bottom"){
                    self.$valueSelector.css({top: (self.$el.offset().top + self.$el.height()) + "px"});
                }else if (self.options.rangePosition === "top"){
                    self.$valueSelector.css({top: self.$el.offset().top + "px"});
                }
                self.$valueSelector.focus();
            }
        }
    });

    /** Editor to upload media asset (img, video, etc.)

        relies on `djupload` in djaodjin-upload.js
     */
    function MediaEditor(element, options){
        var self = this;
        self.el = element;
        self.$el = $(element);
        self.options = options;
        self.init();
        return self;
    }

    MediaEditor.prototype = $.extend({}, Editor.prototype, {

        init: function(){
            var self = this;
            self.$el.click(function() {
                var mediaGallery = $(self.options.mediaGallerySelector);
                if( mediaGallery.length > 0 ) {
                    var djgallery = mediaGallery.data("djgallery");
                    djgallery.showGallery();
                    mediaGallery.off("djgallery.select");
                    mediaGallery.on("djgallery.select",
                    function(gallery, location) {
                        self.updateMediaSource(location);
                    });
                }
            });

            self.$el.on('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
            });

            self.$el.on('dragenter', function(e) {
                e.preventDefault();
                e.stopPropagation();
            });

            self.$el.on('drop', function(event) {
                event.preventDefault();
                if(event.originalEvent.dataTransfer &&
                   event.originalEvent.dataTransfer.files.length ) {
                    event.stopPropagation();
                    /*UPLOAD FILES HERE*/
                    var mediaGallery = $(self.options.mediaGallerySelector);
                    if( mediaGallery.length > 0 ) {
                        var djgallery = mediaGallery.data("djgallery");
                        var djupload = mediaGallery.data("djupload");
                        djgallery.showGallery();
                        mediaGallery.on("djgallery.select", function(gallery, location) {
                            self.updateMediaSource(location);
                            mediaGallery.off("djgallery.select");
                        });
                        const files = event.originalEvent.dataTransfer.files;
                        djupload.uploadFiles(files);
                    }
                } else {
                    const location = event.originalEvent.dataTransfer.getData('text/plain');
                    self.updateMediaSource(location);
                    var mediaGallery = $(self.options.mediaGallerySelector);
                    if( mediaGallery.length > 0 ) {
                        mediaGallery.off("djgallery.select");
                    }
                }
            });
        },

        getSavedText: function(){
            var self = this;
            return self.$el.attr("src");
        },

        updateMediaSource: function(location) {
            var self = this;
            if( self.$el.prop("tagName") === "IMG" ) {
                if( self.options.acceptedImages.some(function(ext) {
                    return location.indexOf(ext) >= 0; })) {
                    self.$el.attr("src", location);
                    self.saveEdition();
                }
            } else if( self.$el.prop("tagName") === "VIDEO" ) {
                if (self.options.acceptedVideos.some(function(ext) {
                    return location.indexOf(ext) >= 0; })){
                    self.$el.attr("src", location);
                    self.saveEdition();
                }
            }
        }

    });


    $.fn.editor = function(options, custom){
        var opts = $.extend( {}, $.fn.editor.defaults, options );
        return this.each(function() {
            if (!$.data($(this), "editor")) {
                if ($(this).hasClass("edit-currency")){
                   $.data($(this), "editor", new CurrencyEditor($(this), opts));
                }else if ($(this).hasClass("edit-date")){
                    $.data($(this), "editor", new DateEditor($(this), opts));
                }else if ($(this).hasClass("edit-range")){
                    $.data($(this), "editor", new RangeEditor($(this), opts));
                }else if ($(this).hasClass("edit-media")){
                    $.data($(this), "editor", new MediaEditor($(this), opts));
                }else{
                    $.data($(this), "editor", new Editor($(this), opts));
                }
            }
        });
    };


    $.fn.editor.defaults = {
        /** URL to persist changes in the document */
        baseUrl: null,
        /** URL to upload media assets */
        uploadUrl: null,
        editionTool: null,
        emptyInputText: "placeholder, type to overwrite...",
        uniqueIdentifier: "id",
        hints: null,
        mediaGallerySelector: "#media-gallery",
        acceptedImages: [".jpg", ".png", ".gif"],
        acceptedVideos: [".mp4"],
        onSuccess: function(element, resp){
            return true;
        },
        onError: function(resp){
            showErrorMessages(resp);
        },
        rangePosition: "middle", // position of range input from element "middle", "top" or "bottom"
        delayMarkdownInit: 0, // Add ability to delay the get request for markdown
        debug: false,
        focus: false,
        templates: {
            dateSelector: '<input class="djaodjin-editor" style="width:auto;" type="date">',
            rangeSelector: '<input class="djaodjin-editor" style="width:auto;" type="range">',
        }
    };

}( jQuery ));

}));
