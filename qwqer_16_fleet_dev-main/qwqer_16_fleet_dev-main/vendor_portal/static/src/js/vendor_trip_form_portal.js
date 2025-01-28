 document.addEventListener('DOMContentLoaded', function () {
                var editButton = document.getElementById('edit_button');
                var discardButton = document.getElementById('discard_button');
                var saveButton = document.getElementById('save_button');
                var formFields = document.querySelectorAll('#daily_trip_form input, #daily_trip_form textarea, #daily_trip_form select');
                var statusElements = document.querySelectorAll('.o_statusbar_status');
                var saveButton = document.getElementById('save_button');
                var createButton = document.getElementById('create_button');
                var form = document.getElementById('daily_trip_form');
                var trip_state = document.getElementById("trip_state").value;
                var tripId = document.getElementById("trip_id").value;
                var attachmentsDelButton =  document.querySelectorAll('.remove-attachment')
                var selectElement = document.querySelector('.vehicle-select');
                var initialValues = {};


// Function to store initial values of form fields
                function storeInitialValues() {
                    formFields.forEach(function (field) {
                        initialValues[field.id] = field.value;
                    });
                }

//Function to reset form fields to initial values
                function resetFormFields() {
                    formFields.forEach(function (field) {
                        field.value = initialValues[field.id];
                    });
                }
//Function to remove attachment delete buttons
                function removeAttachmentsDelButton() {
                    attachmentsDelButton.forEach(function (button) {
                        button.style.display = 'none';
                    });
                }
//Function to display attachment delete buttons
                function displayAttachmentsDelButton() {
                    attachmentsDelButton.forEach(function (button) {
                        button.style.display = 'inline-block';
                    });
                }

                function disableFields(){
                     formFields.forEach(function (field) {
                        if (!field.classList.contains('always-readonly')) {
                            field.setAttribute('readonly', 'readonly');
                            if (field.tagName === 'SELECT') {
                                field.setAttribute('disabled', 'disabled');
                                }
                        }
                        if (field.type === 'file') {
                            field.setAttribute('disabled', 'disabled');
                        }
                    });
                }

                function enableFields(){
                    formFields.forEach(function (field) {
                        if (!field.classList.contains('always-readonly')) {
                            field.removeAttribute('readonly');
                            if (field.tagName === 'SELECT') {
                                field.removeAttribute('disabled');
                            }
                        }
                        if (field.type === 'file') {
                            field.removeAttribute('disabled');
                        }
                    });
                }

                // Function to show buttons based on state
                function showButtonsBasedOnState(state) {
                    if (state !== 'new') {
                        editButton.style.display = 'none';
                        discardButton.style.display = 'none';
                        createButton.style.display = 'none';
                        removeAttachmentsDelButton();
                    } else if (state === 'new') {
                        editButton.style.display = 'inline-block';
                        createButton.style.display = 'inline-block';
                    }
                }

                attachmentsDelButton.forEach(function (button) {
                    button.addEventListener('click', function () {
                        const attachmentId = this.getAttribute('data-id');
                        // Add a hidden input to the form to track removed files
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'removed_attachments';
                        input.value = attachmentId;
                        this.closest('form').appendChild(input);
                        // Remove the attachment entry from the UI
                        this.parentElement.remove();
                    });
                });
                // Initially disable all form fields and store their initial values
                disableFields();
                //  disable button based on  record status
                removeAttachmentsDelButton();
                showButtonsBasedOnState(trip_state);

                editButton.addEventListener('click', function (e) {
                    e.preventDefault();
                    // Enable all form fields except those with the always-readonly class
                    enableFields();
                    displayAttachmentsDelButton();
                    // Show the Submit and Discard buttons and hide the Edit button
                    saveButton.style.display = 'inline-block';
                    discardButton.style.display = 'inline-block';
                    createButton.style.display = 'none';
                    editButton.style.display = 'none';
                    storeInitialValues();
                });


                discardButton.addEventListener('click', function (e) {

                    // Reset form fields to their initial values and make them read-only
                    disableFields();
                    // Show the Edit button and hide the Submit and Discard buttons
                    saveButton.style.display = 'none';
                    discardButton.style.display = 'none';
                    editButton.style.display = 'inline-block';
                    createButton.style.display = 'inline-block';
                    removeAttachmentsDelButton();
                    window.location.href = '/my/trip/' + tripId;
                });

            });

