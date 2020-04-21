ckan.module('external-storage-upload', function($) {
    'use strict';
    return {

        options: {
            serverUrl: null,
            storagePrefix: null,
            authzScope: null,
            i18n: {
            }
        },

        initialize: function () {
            console.log('Initializing external-storage-upload CKAN JS module');
            $.proxyAll(this, /_on/);

            // this._url = $('#field-image-url');
            this._form = this.$('form');
            this._save = $('[name=save]');
            this._id = $('input[name=id]');
            this._file = null;

            var self = this;
            $('#field-image-upload').on('change', function(event) {
                if (! window.FileList) {
                    return;
                }
                self._file = event.target.files[0];
            });

            this._save.on('click', this._onFormSubmit);
        },

        _onFormSubmit: function(event) {
            // Check if we have anything to upload
            if (! this._file) {
                return;
            }

            event.preventDefault();

            var file = new ckanUploader.FileAPI.HTML5File(this._file);

            var prefix = this.options.storagePrefix.split('/');
            var scopes = [this.options.authzScope];
            var serverUrl = this.options.serverUrl;

            this._getAuthzToken(scopes)
                .then(function(token) {     
                    console.log(token);           
                    const uploader = new ckanUploader.DataHub(token, prefix[0], prefix[1], serverUrl);
                    return uploader.push(file, token)
                }).then(function(response) {
                    // Add the oid and size (file.sha256() and file.size()) to form data
                    // Submit the form to update / create the resource

                    var data = new FormData();
                    data.append("oid", response.objects[0].oid);
                    data.append("size", response.objects[0].size);
                    console.log(...data)
                });
        },

        _getAuthzToken: function (scopes) {
            var dfd = $.Deferred();

            this.sandbox.client.call(
                'POST',
                'authz_authorize',
                {scopes: scopes},

                function (data) {
                    // TODO: Check that we got the scopes we need
                    dfd.resolve(data.result.token);
                },

                function (error) {
                    console.log(error);
                    dfd.reject(error);
                }
            );

            return dfd.promise();
        }
    };
});
