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
            this._file = $('#field-image-upload');

            this._save.on('click', this._onFormSubmit);
        },

        _onFormSubmit: function(event) {
            // Check if we have anything to upload
            if (! window.FileList || ! this._file || ! this._file.val()) {
                return;
            }

            event.preventDefault();
            var prefix = this.options.storagePrefix.split('/');
            var scopes = [this.options.authzScope];
            var serverUrl = this.options.serverUrl;

            this._getAuthzToken(scopes).then(function(token) {
                console.log(token);

                const test = new ckanUploader.DataHub(
                    token,
                    prefix[0],
                    prefix[1],
                    serverUrl
                );

                const resources = {
                  basePath: 'test/fixtures',
                  path: 'sample.csv',
                };

                return test.push(resources);
            }).then(function(result) {
                console.log(result);
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
