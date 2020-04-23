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
            var formData = this._form.serializeArray().reduce(
                function (result, item) {
                    result[item.name] = item.value;
                    return result;
            }, {});

            this._getAuthzToken(scopes)
                .then(function(token) {     
                    var uploader = new ckanUploader.DataHub(token, prefix[0], prefix[1], serverUrl);
                    var pushResponse = uploader.push(file, token);
                    return pushResponse;
                }).then(function(response) {

                    // TODO: Throw error in the SDK
                    // if (response.verifyAction.error || response.cloudStorage.error) {
                    //    return response.verifyAction.error ? alert(response.verifyAction.message) : alert(response.cloudStorage.message)
                    // }

                    // Add the oid and size (file.sha256() and file.size()) to form data
                    // Submit the form to update / create the resource
                    formData.multipart_name = file.file.name;
                    formData.url = file.file.name;
                    formData.size = file.file.size;
                    formData.url_type = 'upload';
                    formData._sha256 = file._sha256;
                    var action = formData.id ? 'resource_update' : 'resource_create';
                    console.log("FormData: ", formData)
                    console.log("")
                    console.log("")
                    console.log("Response: ", response)
                    console.log("File: ", file)
                    console.log("Action: ", action)
                }).catch(function(error) { 
                    alert(error);
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
