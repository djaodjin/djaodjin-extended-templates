// djaodjin-upload.js

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

    function Djupload(el, options){
        this.element = $(el);
        this.options = options;
        this.init();
    }

    /* UI element to upload files directly to S3.

       <div data-complete-url="">
       </div>
     */
    Djupload.prototype = {

        _csrfToken: function() {
            var self = this;
            if( self.options.csrfToken ) { return self.options.csrfToken; }
            return getMetaCSRFToken();
        },

        _uploadSuccess: function(file, resp) {
            var self = this;
            self.element.trigger("djupload.success", resp.location);
            if( self.options.uploadSuccess &&
                {}.toString.call(self.options.uploadSuccess)
                === '[object Function]' ) {
                self.options.uploadSuccess(file, resp, self.element);
            } else {
                if( resp.detail ) {
                    showMessages(resp.detail, "success");
                } else {
                    showMessages([self.options.uploadSuccessMessage(
                        file.name, resp.location)], "success");
                }
            }
            return true;
        },

        _uploadError: function(file, resp) {
            var self = this;
            self.element.trigger("djupload.error", [file.name, resp]);
            if( self.options.uploadError ) {
                self.options.uploadError(file, resp, self.element);
            } else {
                showErrorMessages(resp);
            }
        },

        _uploadProgress: function(file, progress) {
            var self = this;
            self.element.trigger("djupload.progress", [file.name, progress]);
            if( self.options.uploadProgress ) {
                self.options.uploadProgress(file, progress, self.element);
            }
            return true;
        },

        init: function(){
            var self = this;
            if( !self.options.uploadUrl ) {
                console.warning("[djupload] uploading assets will not work because 'uploadUrl' is undefined.");
                return;
            }
            if( self.options.mediaPrefix !== ""
                && !self.options.mediaPrefix.match(/\/$/)){
                self.options.mediaPrefix += "/";
            }
            if( self.options.uploadUrl.indexOf("/api/auth/") >= 0 ) {
                $.ajax({
                    method: "GET",
                    url: self.options.uploadUrl +
                        (self.options.acl === "public-read" ? "?public=1" : ""),
                    datatype: "json",
                    contentType: "application/json; charset=utf-8",
                    success: function(data) {

                        var parser = document.createElement('a');
                        parser.href = data.location;
                        self.options.uploadUrl = parser.host + "/";
                        if( parser.protocol ) {
                            self.options.uploadUrl = parser.protocol + "//"
                                + self.options.uploadUrl;
                        }
                        self.options.mediaPrefix = parser.pathname;
                        if( self.options.mediaPrefix === 'undefined'
                            || self.options.mediaPrefix === null ) {
                            self.options.mediaPrefix = "";
                        }
                        if( self.options.mediaPrefix !== ""
                            && self.options.mediaPrefix.match(/^\//)){
                            self.options.mediaPrefix = self.options.mediaPrefix.substring(1);
                        }
                        if( self.options.mediaPrefix !== ""
                            && !self.options.mediaPrefix.match(/\/$/)){
                            self.options.mediaPrefix += "/";
                        }

                        self.options.accessKey = data.access_key;
                        self.options.policy = data.policy;
                        self.options.amzCredential = data.x_amz_credential;
                        self.options.amzDate = data.x_amz_date;
                        self.options.amzServerSideEncryption = data.x_amz_server_side_encryption;
                        self.options.securityToken = data.security_token;
                        self.options.signature = data.signature;
                        self.initDropzone();
                    },
                    error: function(resp) {
                        showErrorMessages(resp);
                    }
                });
            } else {
                self.initDropzone();
            }
        },

        initDropzone: function() {
            var self = this;
            var dropzoneUrl = (self.options.accessKey ? self.options.uploadUrl
                : (self.element.attr("data-complete-url") ?
                    self.element.attr("data-complete-url")
                    : self.options.uploadUrl));
            if( !dropzoneUrl ) {
                showErrorMessages(self.options.configError);
                throw new Error(self.options.configError);
            }
            self.element.dropzone({
                paramName: self.options.uploadParamName,
                url: dropzoneUrl,
                maxFilesize: self.options.uploadMaxFileSize,
                clickable: self.options.uploadClickableZone,
                createImageThumbnails: false,
                previewTemplate: "<div></div>",
                init: function() {
                    if( self.options.accessKey ) {
                        // We are going to remove extra input files that AWS
                        // would reject (ex: csrftoken).
                        var fields = this.element.querySelectorAll(
                            "input, textarea, select, button");
                        for( var idx = 0; idx < fields.length; ++idx ) {
                            if( fields[idx].getAttribute("name")
                                && (fields[idx].getAttribute("name")
                                    !== self.options.uploadParamName) ) {
                                fields[idx].parentNode.removeChild(fields[idx]);
                            }
                        }
                    }

                    this.on("sending", function(file, xhr, formData){
                        if( self.options.accessKey ) {
                            formData.append(
                                "key", self.options.mediaPrefix + file.name);
                            formData.append("policy", self.options.policy);
                            formData.append(
                                "x-amz-algorithm", "AWS4-HMAC-SHA256");
                            formData.append(
                                "x-amz-credential", self.options.amzCredential);
                            formData.append("x-amz-date", self.options.amzDate);
                            formData.append("x-amz-security-token",
                                self.options.securityToken);
                            formData.append(
                                "x-amz-signature", self.options.signature);
                            if( self.options.acl ) {
                                formData.append("acl", self.options.acl);
                            } else {
                                formData.append("acl", "private");
                            }
                            if( self.options.amzServerSideEncryption ) {
                                formData.append("x-amz-server-side-encryption",
                                    self.options.amzServerSideEncryption);
                            } else if( !self.options.acl
                                || self.options.acl !== "public-read" ) {
                                formData.append("x-amz-server-side-encryption",
                                    "AES256");
                            }
                            var ext = file.name.slice(
                                file.name.lastIndexOf('.')).toLowerCase();
                            if( ext === ".jpg" ) {
                                formData.append("Content-Type", "image/jpeg");
                            } else if( ext === ".png" ) {
                                formData.append("Content-Type", "image/png");
                            } else if( ext === ".gif" ) {
                                formData.append("Content-Type", "image/gif");
                            } else if( ext === ".mp4" ) {
                                formData.append("Content-Type", "video/mp4");
                            } else {
                                formData.append(
                                    "Content-Type", "binary/octet-stream");
                            }
                        } else {
                            formData.append(
                                "csrfmiddlewaretoken", self._csrfToken());
                            var data = self.element.data();
                            for( var key in data ) {
                                if( data.hasOwnProperty(key)
                                    && key != 'djupload' ) {
                                    formData.append(key, data[key]);
                                }
                            }
                        }
                    });

                    this.on("success", function(file, response){
                        if( self.options.accessKey) {
                            // With a direct upload to S3, we need to build
                            // a custom response with location url ourselves.
                            response = {
                                location: file.xhr.responseURL + self.options.mediaPrefix + file.name
                            };
                            // We will also call back a completion url
                            // on the server.
                            var completeUrl = self.element.attr(
                                "data-complete-url");
                            if( completeUrl ) {
                                var data = {};
                                [].forEach.call(self.element[0].attributes, function(attr) {
                                    if (/^data-/.test(attr.name)) {
                                        var camelCaseName = attr.name.substr(5).replace(/-(.)/g, function ($0, $1) {
                                            return $1.toUpperCase();
                                        });
                                        data[camelCaseName] = attr.value;
                                    }
                                });
                                for( var key in data ) {
                                    if( data.hasOwnProperty(key)
                                        && key != 'djupload' ) {
                                        response[key] = data[key];
                                    }
                                }
                                $.ajax({
                                    type: "POST",
                                    url: completeUrl,
                                    beforeSend: function(xhr) {
                                        xhr.setRequestHeader(
                                            "X-CSRFToken", self._csrfToken());
                                    },
                                    data: JSON.stringify(response),
                                    datatype: "json",
                                    contentType: "application/json; charset=utf-8",
                                    success: function(resp) {
                                        self._uploadSuccess(file, resp);
                                    },
                                    error: function(resp) {
                                        self._uploadError(file, resp);
                                    }
                                });
                            } else {
                                self._uploadSuccess(file, response);
                            }
                        } else {
                            self._uploadSuccess(file, response);
                        }
                    });

                    this.on("error", function(file, message){
                        self._uploadError(file, message);
                    });

                    this.on("uploadprogress", function(file, progress){
                        self._uploadProgress(file, progress);
                    });
                }
            });
        }
    };

    $.fn.djupload = function(options) {
        var opts = $.extend( {}, $.fn.djupload.defaults, options );
        return this.each(function() {
            if (!$.data(this, "djupload")) {
                $.data(this, "djupload", new Djupload(this, opts));
            }
        });
    };

    $.fn.djupload.defaults = {
        // location
        uploadUrl: null,
        mediaPrefix: "",

        uploadZone: "body",
        uploadClickableZone: true,
        uploadParamName: "file",
        uploadMaxFileSize: 250,

        // Django upload
        csrfToken: null,

        // S3 direct upload
        accessKey: null,
        securityToken: null,
        acl: null, // defaults to "private".
        policy: "",
        signature: null,
        amzCredential: null,
        amzDate: null,
        amzServerSideEncryption: null,

        // callback
        uploadSuccess: null,
        uploadError: null,
        uploadProgress: null,

        // messages
        uploadSuccessMessage: function(filename, location) {
            return '"${filename}" uploaded sucessfully to ${location}'.replace(
                '${filename}', filename).replace(
                '${location}', location);
        },
        configError: "instantiated djupload() with no uploadUrl specified."

    };

    Dropzone.autoDiscover = false;

})(jQuery);

}));
