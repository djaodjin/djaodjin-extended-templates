/* jshint multistr: true */
/* global getMetaCSRFToken jQuery :true */

/* relies on:
    - jquery.js
    - djupload.js
    - dropzone.js (transitively through djupload.js)
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

    /**
       A UI element to interact with a media gallery

       This UI element is based on jQuery, Djupload and Dropzone.

       The HTML tree this UI element is attached to should contain the following
       HTML elements for the logic to work:

       - `<div class="dj-gallery-items"></div>` so media assets
       can be displayed as thumbnails and selected for different actions.

       - `<button class="dj-close"></button>` so the gallery disapears when it
         is not needed.

       - `<button class="dj-gallery-delete-item"></button>` so a media asset
         can be deleted from the gallery.

       - `<button class="dj-gallery-copy-location"></button>` so the location
       of a media asset can be copied to the clipboard.

       - `<input type="text" class="dj-gallery-filter"></input>` so media
       assets displayed in the gallery can be filtered by tags.

       - `<div class="dj-gallery-upload-progress"><div class="progress-bar"></div></div>`
         so upload progress of a media asset can be displayed.

       - `<span class="dj-gallery-message"></span>` so messages returned
       by the API calls can be displayed.

       - `<input class="dj-gallery-location-input" />` so the location
       of the selected media asset can be displayed.

       - `<input class="dj-gallery-tag-input" />` so the tags of the selected
       media asset can be displayed. When `Tagify` is installed, the input
       field to enter tags will be decorated with `Tagify`.

       - `<div class="dj-gallery-info-preview"></button>` so an asset can
         be previewed in actual size.

       - `<div class="dj-gallery-info-item-selected"></div>` and
       `<div class="dj-gallery-info-item-empty"></div>` to switch
       between selected and unselected items in the contextual information
       widget.

       Data sources
       ------------

       The options 'url' must be configured as an API endpoint to list and
       delete media assets, as well as update their meta tags
       (ex: [/api/themes/assets/](https://github.com/djaodjin/djaodjin-extended-templates/blob/9e7c44a50818d46141270fb2d6aa7339178ea174/extended_templates/api/upload_media.py#L43)).
       'url' is also used to upload media assets unless 'S3DirectUploadUrl'
       is configured.

       Optionally, 'S3DirectUploadUrl' can be configured as an API endpoint
       to upload directly to the media assets storage.
    */
    function Djgallery(element, options){
        var self = this;
        self.el = element;
        self.$el = $(self.el);
        self.options = options;
        self.selectedMedia = null;
        self.tagify = null;
        self.init();
        return self;
    }

    Djgallery.prototype = {
        init: function() {
            var self = this;

            if( !self.options.url ) {
                console.warn("[djgallery] listing media assets will not work because 'url' is undefined.");
            }

            self.clearSelection();

            // attach the event handlers

            self.$el.on("click", ".dj-close", function(event) {
                self.hideGallery();
            });
            self.$el.on("click", ".dj-gallery-delete-item", function(event) {
                self.deleteMedia(event);
            });
            self.$el.on("click", ".dj-gallery-copy-location", function(event) {
                const location = self.getMediaLocationFromItem(
                    self.selectedMedia);
                if( navigator.clipboard && navigator.clipboard.writeText ) {
                    navigator.clipboard.writeText(location);
                }
            });
            self.$el.on("keyup", ".dj-gallery-filter", function(event) {
                self._loadMedias();
            });
            self.$el.on("click", ".dj-gallery-item-container", function(event) {
                self.selectMedia($(this));
            });
            self.$el.on("djgallery.loadresources", function(event) {
                self._loadMedias();
            });

            try {
                self.tagify = new Tagify(
                    self.$el.find(".dj-gallery-tag-input")[0]);
                self.tagify.on('blur', function(event) {
                    var tagString = "";
                    var sep = "";
                    for( let idx = 0; idx < self.tagify.value.length; ++idx ) {
                        tagString += sep + self.tagify.value[idx].value;
                        sep = ",";
                    }
                    self.tagMedia(tagString);
                });
            } catch(Exception) {
                self.$el.find(".dj-gallery-tag-input").blur(function(event) {
                    self.tagMedia();
                });
            }

            // prepares helper components to upload media assets

            var uploadUrl = self.options.url;
            if( self.options.S3DirectUploadUrl &&
                self.options.S3DirectUploadUrl.indexOf("/api/auth/") >= 0 ) {
                uploadUrl = self.options.S3DirectUploadUrl;
                if( uploadUrl.indexOf("?public=1") >= 0 ) {
                    self.options.acl = "public-read";
                }
            }

            self.$el.djupload({
                uploadUrl: uploadUrl,
                csrfToken: self.options.csrfToken,
                uploadZone: "body",
                uploadClickableZone: self.options.clickableArea,
                uploadParamName: "file",

                // S3 direct upload
                accessKey: self.options.accessKey,
                mediaPrefix: self.options.mediaPrefix,
                securityToken: self.options.securityToken,
                acl: self.options.acl,
                policy: self.options.policy,
                signature: self.options.signature,
                amzCredential: self.options.amzCredential,
                amzDate: self.options.amzDate,

                // callback
                uploadSuccess: function(file, response){
                    var status = file.xhr.status;
                    $(".dz-preview").remove();
                    var lastIndex = $(".dj-gallery-items .dj-gallery-item-container").length;
                    var filename = file.name;
                    var location = response.location;
                    if( [201, 204].indexOf(status) >= 0 ){
                        self.addMediaItem(response, lastIndex, false);
                        self.galleryMessage(
                            self.options.uploadSuccessMessage(
                                filename, location));
                    } else if( status === 200 ) {
                        const $mediaItem = self.$el.find(
                          '.dj-gallery-item-container [src="' + location + '"]'
                        ).parent();
                        self.selectMedia($mediaItem);
                        self.galleryMessage(
                            self.options.uploadPreviousSuccessMessage(
                                filename, location));
                    }
                },
                uploadError: function(file, resp){
                    var message = resp;
                    if( typeof resp.detail !== "undefined" ) {
                        message = resp.detail;
                    }
                    self.galleryMessage(message, "error");
                },
                uploadProgress: function(file, progress) {
                    var djGalleryUploadProgress = self.$el.find(
                        ".dj-gallery-upload-progress");
                    var progressBar = djGalleryUploadProgress.find(
                        ".progress-bar")
                    djGalleryUploadProgress.slideDown();
                    progress = progress.toFixed();
                    progressBar.css("width", progress + "%");
                    if( progress == 100 ){
                        progressBar.text(this.uploadCompleteLabel);
                        setTimeout(function() {
                            djGalleryUploadProgress.slideUp();
                            progressBar.text("").css("width", "0%");
                        }, 2000);
                    }
                    self.options.itemUploadProgress(progress);
                }
            });
        }, // init

        _csrfToken: function() {
            var self = this;
            return self.options.csrfToken ?
                self.options.csrfToken : getMetaCSRFToken();
        },

        // XXX Removes query parameters on private S3 URLs ?
        _mediaLocation: function(url) {
            var parser = document.createElement('a');
            parser.href = url;
            var result = parser.pathname;
            if( parser.host != location.hostname ) {
                result = parser.host + result;
                if( parser.protocol ) {
                    result = parser.protocol + "//" + result;
                }
            }
            return result;
        },

        /** Load the meta information for media assets (URL, tags, etc.)
            through `self.options.url`.
         */
        _loadMedias: function() {
            var self = this;
            var $element = $(self.$el);
            var mediaFilterUrl = self.options.url;
            var $filter = $element.find(".dj-gallery-filter");
            if( $filter.val() !== "") {
                mediaFilterUrl = self.options.url + "?q=" + $filter.val();
            }
            $.ajax({
                method: "GET",
                url: mediaFilterUrl,
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", self._csrfToken());
                },
                datatype: "json",
                contentType: "application/json; charset=utf-8",
                success: function(data){
                    $(".dj-gallery-items").empty();
                    $.each(data.results, function(index, file){
                        self.addMediaItem(file, index, true);
                    });
                },
                error: function(resp) {
                    self.galleryMessage(resp, 'error');
                }
            });
        },

        addMediaItem: function(file, index, init){
            var self = this;
            var mediaItem = null;
            var tags = file.tags;
            if (typeof tags === "undefined"){
                tags = "";
            }
            var ext = null;
            var parser = document.createElement('a');
            parser.href = file.location;
            var filename = parser.pathname.toLowerCase();
            var extIdx = filename.lastIndexOf('.');
            if( extIdx > 0 ) {
                ext = filename.substr(extIdx);
            }
            var location = file.location;
            if( self.options.acl === "public-read" ) {
                location = self._mediaLocation(location);
            }
            if( ext ) {
                if( self.options.acceptedVideos.some(function(v) {
                    return ext.toLowerCase().indexOf(v) >= 0; })) {
                    mediaItem = self.options.itemTemplateVideo.replace(
                        '${index}', index).replace(
                        '${location}', location).replace(
                        '${tags}', tags);
                } else if( self.options.acceptedImages.some(function(v) {
                    return ext.toLowerCase().indexOf(v) >= 0; })) {
                    mediaItem = self.options.itemTemplateImg.replace(
                        '${index}', index).replace(
                        '${location}', location).replace(
                        '${tags}', tags);
                }
            }
            if( !mediaItem ) {
                mediaItem = self.options.itemTemplateUnknown.replace(
                    '${index}', index).replace(
                    '${location}', location).replace(
                    '${tags}', tags);
            }
            if( mediaItem ) {
                var $mediaItem = $(mediaItem);
                $(".dj-gallery-items").prepend($mediaItem);
                $mediaItem.on('dragstart', function(event) {
                    event.originalEvent.dataTransfer.setData('text/plain',
                        self.getMediaLocationFromItem($(this)));
                });
                if( !init ) {
                    self.selectMedia($mediaItem);
                }
            }
        },

        clearSelection: function() {
            // Display contextual information for the selected item
            var self = this;
            self.selectedMedia = null;
            self.$el.find(".dj-gallery-info-item-selected").hide();
            self.$el.find(".dj-gallery-info-item-empty").show();
        },

        galleryMessage: function(message, type) {
            var self = this;
            var $elem = self.$el.find(".dj-gallery-message");
            $elem.text(message);
            if( type == 'error' ) {
                $elem.addClass('text-danger');
            } else {
                $elem.removeClass('text-danger');
            }
            setTimeout(function() {
                $elem.text("");
            }, 2000);
            return self.options.galleryMessage(message);
        },

        /** Returns the URL location for the media asset shown in `item`.
         */
        getMediaLocationFromItem: function(item) {
            var self = this;
            const refElem = item.find("[data-location]");
            const location = refElem.length > 0 ?
                self._mediaLocation(refElem.data("location")) :
                self._mediaLocation(item.find("[src]").attr("src"));
            return location;
        },

        /**
           Highlights the selected item in the media gallery.

           `item` is the jQuery element wrapping HTML nodes with class
           'dj-gallery-item-container'.

           `self.options.selectedMediaClass` is the class to highlight
           the active selection.
         */
        selectMedia: function(item) {
            var self = this;
            var $elem = self.$el;
            // Removes highlights for previously selected media
            $elem.find(".dj-gallery-item-container").not(item).removeClass(
                self.options.selectedMediaClass);

            self.selectedMedia = item;
            item.addClass(self.options.selectedMediaClass);

            // Prepares the preview UI element
            var content = item.children().clone();
            $elem.find('.dj-gallery-info-preview').empty();
            $elem.find('.dj-gallery-info-preview').append(content);

            // Populates contextual information for the selected item
            // set the input fields in the contextual information
            const location = self.getMediaLocationFromItem(item);
            $elem.find(".dj-gallery-location-input").val(location);
            const tags = item.find("[data-tags]").data("tags");
            if( tags ) {
                $elem.find(".dj-gallery-tag-input").val(tags);
            }

            // Display contextual information for the selected item
            $(".dj-gallery-info-item-selected").show();
            $(".dj-gallery-info-item-empty").hide();

            $elem.trigger("djgallery.select", location);
        },

        /** Deletes the selected media item
         */
        deleteMedia: function(event){
            var self = this;
            event.preventDefault();
            var deletedMedia = self.selectedMedia;
            const location = self.getMediaLocationFromItem(deletedMedia);
            $.ajax({
                method: "DELETE",
                url: self.options.url + "?location=" + location,
                datatype: "json",
                contentType: "application/json; charset=utf-8",
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", self._csrfToken());
                },
                success: function(resp){
                    deletedMedia.remove();
                    self.clearSelection();
                    self.galleryMessage(resp.detail);
                },
                error: function(resp) {
                    self.galleryMessage(resp, 'error');
                }
            });
        },

        /** Sets 'tags' in the media meta data.
         */
        tagMedia: function(value) {
            var self = this;
            var tags = (value ? value
                : $(".dj-gallery-tag-input").val()).split(",");
            for( var idx = 0; idx < tags.length; ++idx ) {
                tags[idx] = $.trim(tags[idx]);
            }

            var tagged = self.selectedMedia.find('[data-tags]');
            const location = self.getMediaLocationFromItem(
                self.selectedMedia);
            $.ajax({
                type: "PUT",
                url: self.options.url,
                data: JSON.stringify({
                    "items": [{
                        "location": location
                    }],
                    "tags": tags}),
                datatype: "json",
                contentType: "application/json; charset=utf-8",
                beforeSend: function(xhr, settings) {
                    xhr.setRequestHeader("X-CSRFToken", self._csrfToken());
                },
                success: function(resp){
                    if( tagged.length > 0 ) {
                        tagged.data('tags', tags);
                    }
                },
                error: function(resp) {
                    self.galleryMessage(resp, 'error');
                }
            });
        },

        hideGallery: function(speed, easing, callback) {
            var self = this;
            self.$el.animate({right: '-' + self.defaultWidth + 'px'});
            self.$el.hide();
            self.$el.off("djgallery.select");
        },

        showGallery: function(speed, easing, callback) {
            var self = this;
            self.$el.trigger("djgallery.loadresources");
            self.$el.css('right', '-' + self.defaultWidth + 'px');
            self.$el.show();
            self.$el.animate({right: 0});
        },
    };

    $.fn.djgallery = function(options) {
        var opts = $.extend( {}, $.fn.djgallery.defaults, options );
        return this.each(function() {
            var $this = $(this);
            if( !$this.data("djgallery") ) {
                $this.data("djgallery", new Djgallery(this, opts));
            }
        });
    };

    $.fn.djgallery.defaults = {

        // djgallery required options

        url: null, // URL to list, update meta tags and delete media assets,
                   // as well as upload a file when 'S3DirectUploadUrl' is
                   // undefined.

        // default options that can be overridden

        csrfToken: null,  // csrfToken passed back to the API

        selectedMediaClass: "dj-gallery-active-item",

        itemTemplateVideo: '<div id="image_${index}" class="dj-gallery-item-container card thumbnail-gallery" draggable="true"><video class="image dj-gallery-item image_media img-thumbnail" src="${location}" data-tags="${tags}"></video></div>',
        itemTemplateImg: '<div id="image_${index}" class="dj-gallery-item-container card thumbnail-gallery" draggable="true"><img class="image dj-gallery-item image_media img-thumbnail" src="${location}" data-tags="${tags}"></div>',
        itemTemplateUnknown: '<div id="image_${index}" class="dj-gallery-item-container card thumbnail-gallery" draggable="true"><img class="image dj-gallery-item image_media img-thumbnail" src="/assets/img/generic-document.png" data-location="${location}" data-tags="${tags}"></div>',

        acceptedImages: [".jpg", ".png", ".gif"],
        acceptedVideos: [".mp4"],
        maxFilesizeUpload: 256,
        paramNameUpload: "file",
        clickableArea: ".clickable-area",

        // S3 direct upload
        S3DirectUploadUrl: null,     // URL for uploads when different from
                                     // `url` option.
        accessKey: null,
        mediaPrefix: "",
        securityToken: null,
        acl: "private",
        policy: "",
        signature: null,
        amzCredential: null,
        amzDate: null,

        itemUploadProgress: function(progress) { return true; },
        galleryMessage: function(message, type) { return true; },

        // messages generated by djgallery
        // This functions can be overriden in order to implement
        // internationalization / locale.

        uploadSuccessMessage: function(filename, location) {
          return '"${filename}" uploaded sucessfully to "${location}"'.replace(
              '${filename}', filename).replace('${location}', location);
        },

        uploadPreviousSuccessMessage: function(filename, location) {
          return '"${filename}" has previously been uploaded to "${location}"'.replace(
              '${filename}', filename).replace('${location}', location);
        },
        placeholderAcceptsErrorMessage: function(filetypes) {
          return 'This placeholder accepts only: ${filetypes} files.'.replace(
              '${filetypes}', filetypes);
        }
    };

})(jQuery);

}));
