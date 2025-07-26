$(document).ready(function () {

    // Handle "Connect to Database" button click
    $('#connect-postgres-btn').click(function (e) {
        e.preventDefault();
        if ($(this).hasClass('disabled')) return;
        connectToDatabase('postgresql');
    });

    // Handle "Connect to SNOW" button click
    $('#connect-servicenow-btn').click(function (e) {
        e.preventDefault();
        if ($(this).hasClass('disabled')) return;
        connectToDatabase('servicenow');
    });

   // General handler for nav-link clicks
    $('.nav-link').click(function (e) {
        e.preventDefault();
        if ($(this).hasClass('disabled')) return;
        var dbType = $(this).data('db-type');
        var dbName = $(this).data('db-name');
        connectToDatabase(dbType, dbName);
    });

    function connectToDatabase(dbType, dbName) {
        let dbDisplayName = '';
        if (dbType === 'postgresql') dbDisplayName = 'PostgreSQL Database';
        else if (dbType === 'servicenow') dbDisplayName = 'ServiceNow Instance';
        else if (dbType === 'sqlite') dbDisplayName = 'SQLite Database';

        // Show spinner or loading indication
        showLoadingSpinner('Connecting to ' + dbName + ' (' + dbDisplayName + ')...');

        // Send AJAX request to connect
        $.ajax({
            url: '/connect_env',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ db_type: dbType }),
            success: function (data) {
                hideLoadingSpinner();
                if (data.success) {
                    // Connection successful, reload the page or update UI
                    location.reload();
                } else {
                    // Show error message
                    showAlert('Error', data.error);
                }
            },
            error: function () {
                hideLoadingSpinner();
                showAlert('Error', 'An error occurred while connecting to the database.');
            }
        });
    }

    // Handle "Connect to SQLite" button click
    $('#connect-sqlite-btn').click(function (e) {
        e.preventDefault();
        connectToDatabase('sqlite');
    });

    function showLoadingSpinner(message) {
        $('#loading-spinner').show();
        $('#loading-message').text(message);
    }

    function hideLoadingSpinner() {
        $('#loading-spinner').hide();
        $('#loading-message').text('');
    }

    function showAlert(title, message, type = 'danger') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                <strong>${title}:</strong> ${message}
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                 <span aria-hidden="true">&times;</span>
                </button>
            </div>`;
        // Append the alert to a container
        $('#alert-container').html(alertHtml);
    }


    // Handle form submission
    $('#chat-form').submit(function (e) {
        e.preventDefault();
        const userInput = $('#message-input').val().trim();
        if (userInput === '') return;
        appendMessage('You', userInput);
        $('#message-input').val('');

        // Show initial loading spinner
        showLoadingSpinner('Processing...');

        // Send message to the server
        $.ajax({
            url: '/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: userInput }),
            success: function (data) {
                if (data.error) {
                    hideLoadingSpinner();  // Hide spinner on error
                    appendMessage('Error', data.error);

                    if (data.error.includes('No database connection')) {
                        setTimeout(function () {
                            window.location.href = '/connect';
                        }, 2000);
                    }
                } else {
                    const statusUpdates = data.status_updates;
                    if (statusUpdates && statusUpdates.length > 0) {
                        let index = 0;
                        $('#loading-message').text(statusUpdates[index]); // Show first status
                        index++;
                        let spinnerInterval = setInterval(function() {
                            if (index < statusUpdates.length) {
                                $('#loading-message').text(statusUpdates[index]);
                                index++;
                            } else {
                                clearInterval(spinnerInterval);
                                hideLoadingSpinner();
                                // Now display assistant's message and results
                                const markdownContent = marked.parse(data.message);
                                const database_response = data.database_response;
                                appendMessage('Assistant', markdownContent, true, true);
                                updateLogs(data.logs);
                                displayResults(database_response);
                            }
                        }, 1000); // Adjust the duration as needed
                    } else {
                        hideLoadingSpinner();
                        // No status updates, proceed as usual
                        const markdownContent = marked.parse(data.message);
                        const database_response = data.database_response;
                        appendMessage('Assistant', markdownContent, true, true);
                        updateLogs(data.logs);
                        displayResults(database_response);
                    }
                }
            },
            error: function () {
                hideLoadingSpinner();  // Hide spinner on error
                appendMessage('Error', 'An error occurred while communicating with the server.');
            }
        });
    });

    // Function to append messages to the chat window
    function appendMessage(sender, message, database_response, isHTML = false, isAssistantMessage = false) {
        const messageElement = $('<div>').addClass('message');
        const senderElement = $('<strong>').text(`${sender}: `);
        messageElement.append(senderElement);

        if (isHTML) {
            messageElement.append(message);
        } else {
            messageElement.append(document.createTextNode(message));
        }

        // if (isAssistantMessage) {
        //     // Extract and display any markdown tables in the results pane
        //     displayResults(database_response);
        // }

        $('#messages').append(messageElement);
        // Scroll to the bottom
        $('#chat-window').scrollTop($('#chat-window')[0].scrollHeight);
    }

    function displayResults(markdownContent) {
        if (markdownContent && markdownContent.trim() !== '') {
            // Use marked.js to parse markdown
            const htmlContent = marked.parse(markdownContent);

            // Display in the results window
            $('#results-window').html(htmlContent);
        } else {
            // Clear the results window
            $('#results-window').html('');
        }
    }

    // Function to update logs
    function updateLogs(logs) {
        const logsWindow = $('#logs-window');
        logsWindow.empty(); // Clear previous logs
        logs.forEach(log => {
            const logElement = $('<div>').addClass('log-entry').text(log);
            logsWindow.append(logElement);
        });
        // Scroll to the bottom
        logsWindow.scrollTop(logsWindow[0].scrollHeight);
    }
});
