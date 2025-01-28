document.addEventListener('DOMContentLoaded', function () {
                    var attachmentsDel =  document.querySelectorAll('.remove-attachment')
                    var attachmentsDelButton =  document.getElementById('remove_attachment')
                    var importButton = document.getElementById('import_button');
                    var submitButton = document.getElementById('submit_button');
                    var discardButton = document.getElementById('discard_button');
                    var cancelButton = document.getElementById('cancel_button');
                    var downloadTempButton = document.getElementById('template_button');
                    var fileInputField = document.getElementById('import_file');
                    var uploadState = document.getElementById('bulk_upload_state');
                    var import_id = document.querySelector('input[name="import_id"]')?.value;
                    var csrf_token = odoo.csrf_token;

                     // Function to show buttons based on state
                    function showButtonsBasedOnState(state) {
                        if (state !== 'draft') {
                            importButton.style.display = 'none';
                            attachmentsDelButton.style.display = 'none';
                            submitButton.style.display = 'none';
                            discardButton.style.display = 'none';
                            cancelButton.style.display = 'none';
                            downloadTempButton.style.display = 'none';
                            fileInputField.setAttribute('disabled', 'disabled');
                        }
                    }

                    function handleDiscardButtonClick() {
                        var url = import_id ? '/trip_bulk_upload/form/' + import_id : '/trip_bulk_upload/form/';
                        window.location.href = url;
                    }

                    function cancelImportClick() {
                        var url = import_id ? '/trip_bulk_upload/cancel/' + import_id : '';
                        window.location.href = url;
                    }

                    if (document.querySelector('.attachment-tile')) {
                        fileInputField.style.display = 'none';
                        submitButton.style.display = 'none';
                        downloadTempButton.style.display = 'none';
                        discardButton.style.display = 'none';
                        importButton.style.display = 'block';
                        cancelButton.style.display = 'block';
                    } else {
                         importButton.style.display = 'none'
                         cancelButton.style.display = 'none'
                    }
                    if (uploadState?.value) {
                        showButtonsBasedOnState(uploadState.value)
                    }

                     attachmentsDel.forEach(function (button) {
                        button.addEventListener('click', function () {
                            // Remove the attachment entry from the UI
                            this.closest('.attachment-tile').remove();
                            fileInputField.style.display = 'block';
                            submitButton.style.display = 'block';
                            discardButton.style.display = 'block';
                            downloadTempButton.style.display = 'block';
                            importButton.style.display = 'none';
                            cancelButton.style.display = 'none';
                        });
                     });

                    discardButton.addEventListener('click', function (e) {
                        handleDiscardButtonClick()
                    });

                    cancelButton.addEventListener('click', function (e) {
                        cancelImportClick()
                    });

                    importButton.addEventListener('click', function (e) {
//                        var import_id = document.getElementById("import_id").value;
                        console.log("test")
                        e.preventDefault();
                        var formData = new FormData();
                            formData.append('import_id', import_id);
                            formData.append('csrf_token', csrf_token);
                        var url = '/trip_bulk_upload/import/' + import_id;
                            $.ajax({
                                url: url,  // Your controller route
                                type: 'POST',
                                data: formData,
                                processData: false,
                                contentType: false,
                                 success: function (response) {
                                    var res = response;
                                        if (res.success) {
                                            window.location.href = '/trip_bulk_upload/form/' + import_id;
                                        } else if (res.error) {
                                             window.location.href = '/trip_bulk_upload/form/' + import_id + '?error=' + res.error;
                                        }
                                },
                        });
                    });
                });