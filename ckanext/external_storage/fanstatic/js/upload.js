ckan.module("external-storage-upload", function ($) {
  "use strict";
  return {
    options: {
      packageId: null,
      serverUrl: null,
      storagePrefix: null,
      authzScope: null,
      i18n: {
        'resource_updated': 'Resource updated successfully'
      },
    },

    _clickedBtn: null,
    _redirect_url: null,

    initialize: function () {
      console.log("Initializing external-storage-upload CKAN JS module");
      $.proxyAll(this, /^_/);
      this._url = $('#field-image-url');
      this._form = this.$("form");
      this._save = $("[name=save]");
      this._id = $("input[name=id]");
      this._file = null;
      this._progress = $('<div>', {
        class: 'form-group controls progress progress-striped active',
        style: 'display: none'
      });
      this._bar = $('<div>', {
        class: 'progress-bar bar',
        style: 'min-width:2em'}).text('0%');
      this._progress.append(this._bar);
      this._progress.insertAfter(this._url.parent().parent());

      var self = this;

      $("#field-image-upload").on("change", function (event) {
        if (! window.FileList) {
          return;
        }
        self._file = event.target.files[0];
      });

      this._save.on("click", this._onFormSubmit);
    },

    _onFormSubmit: function (event) {
      // Check if we have anything to upload
      if (! this._file) {
        return;
      }

      event.preventDefault();
    ;
      this._clickedBtn = $(event.target).attr('value');

      if (this._clickedBtn == 'go-dataset') {
        // User clicked to go back to the dataset
        this._setSaveDisabled(false);
        var url = this.sandbox.url('/dataset/edit/' + this.options.packageId);
        window.location = url;
      } else {
        // User clicked "Finish" or "Save and Add"
        try {
          this._setSaveDisabled(true);
          this._saveResource();
        } catch(error){
          this._handleError(error);
          this._setSaveDisabled(false);
        }
      }
    },

    _saveResource: function () {
      var scopes = [this.options.authzScope];
      var self = this;
      
      this._generateAuthToken(scopes)
        .then(this._uploadFileToStorage)
        .then(this._updateResourceMetadata)
        .then(function (resourceData) {
          console.log(resourceData);
          self._setSaveDisabled(false);

          if (resourceData.package_id && resourceData.id){
            self.sandbox.notify('Success', self.i18n('resource_updated'), 'success');
            self._setProgressType('success', self._progress);
            if (self._clickedBtn == 'again') {
              return self.sandbox.url('/dataset/new_resource/' + resourceData.package_id);
            } else {
              // Call package_patch to set state = 'active'
              return self._updateDatasetState(resourceData.package_id)
                .then(function() {
                  return self.sandbox.url('/dataset/' + resourceData.package_id);
                });
            }
          }
        })
        .then(function (redirectUrl) {
          
          // Use form.submit() to avoid being asked if we want to leave the page
          self._form.attr('action', redirectUrl);
          self._form.attr('method', 'GET');
          self.$('[name]').attr('name', null);
          setTimeout(function() {
            self._form.submit();
          }, 3000);
        })
        .catch(function (error) {
          self._handleError(error);
        });
    },

    _updateDatasetState: function (packageId) {
      var dfd = $.Deferred();
      this.sandbox.client.call(
        'POST',
        'package_patch',
        {
          "id": packageId, 
          "state": "active"
        },
        function (data) {
          if (data.success) {
            dfd.resolve(data.result);
          } else {
            console.log(data);
            dfd.reject("Failed to update dataset state to 'active'");
          }
        },
        function (err, st, msg) {
          dfd.reject(msg);
        }
      );
      return dfd.promise();
    },

    _updateResourceMetadata: function (pushResult) {
      var formData = this._form
        .serializeArray()
        .reduce(function (result, item) {
          result[item.name] = item.value;
          return result;
        }, {});

      formData.package_id = this.options.packageId;
      formData.url_type = "upload";
      formData.url = pushResult.name;
      formData.size = pushResult.size;
      formData.sha256 = pushResult.oid;

      var action = formData.id ? "resource_update" : "resource_create";

      if (pushResult.fileExists) {
        this.sandbox.notify("File already exists in storage", "it will not be re-uploaded", "success");
      }
      
      var dfd = $.Deferred();
      this.sandbox.client.call(
        'POST',
        action,
        formData,
        function (data) {
          if (data.success) {
            dfd.resolve(data.result);
          } else {
            console.log(data);
            dfd.reject("Failed to save resource");
          }
        },
        function (err, st, msg) {
          dfd.reject(msg);
        }
      );

      return dfd.promise();
    },

    _uploadFileToStorage: function (authToken) {
        var serverUrl = this.options.serverUrl;
        var prefix = this.options.storagePrefix.split("/");
        var file = new ckanUploader.FileAPI.HTML5File(this._file);

        var uploader = new ckanUploader.DataHub(authToken, prefix[0], prefix[1], serverUrl);
        this._setProgressType('info', this._progress);
        this._progress.show('slow')
        return uploader.push(file, authToken, this._onProgress);
    },

    _onProgress: function(progressEvent) {
      var progress = + (progressEvent.loaded / progressEvent.total) * 100;
      this._setProgress(progress, this._bar);
      console.log(Math.round(progress, 2) + "%")
    },

    _setProgress: function (progress, bar) {
      bar.css('width', progress + '%');
      bar.text(Math.round(progress) + '%');
    },

    _setProgressType: function (type, progress) {
      progress
          .removeClass('progress-success progress-danger progress-info')
          .addClass('progress-' + type);
    },

    _generateAuthToken: function (scopes) {
      var dfd = $.Deferred();

      this.sandbox.client.call(
        "POST",
        "authz_authorize",
        { scopes: scopes },

        function (data) {
          // TODO: Check that we got the scopes we need
          dfd.resolve(data.result.token);
        },

        function (error) {
          dfd.reject(error);
        }
      );

      return dfd.promise();
    },

    _handleError: function (msg) {
      this.sandbox.notify("Error", msg, "error");
      console.log("Error: ", msg);
      this._setSaveDisabled(false);
    },

    _setSaveDisabled: function (value) {
      this._save.attr("disabled", value);
    },
  };
});
