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

            // this._url = $('#field-image-url');
            this._form = this.$('form');
            this._save = $('[name=save]');
            this._id = $('input[name=id]');
            this._file = $('#field-image-upload');

            this._save.on('click', this._onFormSubmit);
        },

        _onFormSubmit: function(event, pass) {
            // Check if we have anything to upload
            // if (pass || ! window.FileList || ! this._file || ! this._file.val()) {
            //     return;
            // }
            event.preventDefault();
            console.log($(this._form));

            var prefix = this.options.storagePrefix.split('/');
            console.log(this._getAuthzToken());
        },

        _getAuthzToken: function () {
            this.sandbox.client.call(
                'POST',
                'authz_authorize',
                {scopes: [this.options.authzScope]},

                function (data) {
                    console.log(data)
                },

                function (error) {
                    console.log(error);
                }
            );
        }
    };
});
