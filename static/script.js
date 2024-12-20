document.addEventListener('DOMContentLoaded', function () {
    const askButton = document.getElementById('ask-question-btn');
    const resultBox = document.getElementById('result-box');
    const loaderContainer = document.getElementById('loader-container');
    const selectedFile = document.getElementById('selected_file');
    const selectedLanguage = document.getElementById('selected_language');
    const queryText = document.getElementById('query_text');
    const docSelectionMessage = document.getElementById('doc-selection-message');

    // Convert URLs in text to clickable hyperlinks
    function convertTextToHyperlinks(text) {
        const urlPattern = /(https?:\/\/[^\s]+)/g; // Regex to detect URLs
        return text.replace(urlPattern, (url) => {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
    }

    function updateButtonVisibility() {
        askButton.style.display = (selectedFile.value !== '' && selectedLanguage.value !== '') ? 'block' : 'none';
    }

    // Function to handle sending data to answers.json
    function sendToAnswersJson(prompt, chatAns, humanAns) {
        const answerData = {
            Prompt: prompt,
            "Chat-Ans": chatAns,
            "Human-Ans": humanAns
        };

        fetch('/save_answers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(answerData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Answer data saved:', data);
        })
        .catch(error => {
            console.error('Error saving answer data:', error);
        });
    }

    askButton.addEventListener('click', function () {
        if (selectedFile.value === '') {
            docSelectionMessage.textContent = 'Please select a document.';
            return;
        } else {
            docSelectionMessage.textContent = ''; // Clear message if valid
        }

        // Show loader and hide ask button
        loaderContainer.style.display = 'flex';
        askButton.style.display = 'none';

        const formData = new FormData();
        formData.append('query_text', queryText.value);
        formData.append('selected_file', selectedFile.value);
        formData.append('selected_language', selectedLanguage.value);

        fetch('/ask', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const question = queryText.value;
            const answer = convertTextToHyperlinks(data.answer);

            // Append the question and answer to the result box
            resultBox.innerHTML += `
            <div class="message-block">
                <div class="message user">${question}</div>
                <div class="message bot">${answer}</div>
                <div class="feedback-section">
                    <div class="feedback-icons">
                        <span class="feedback correc">&#128077;</span> <!-- Thumbs Up -->
                        <span class="feedback wrong">&#128078;</span> <!-- Thumbs Down -->
                    </div>
                    <div class="feedback-box" style="display: none;">
                        <div class="feedback-input">
                            <textarea class="feedback-text" placeholder="Please provide your feedback..."></textarea>
                            <button class="submit-feedback">Submit</button>
                        </div>
                        <span class="feedback-error" style="color:red; display:none;">Please provide feedback.</span>
                    </div>
                </div>
            </div>`;

            // Scroll to the bottom of the chatbox
            resultBox.scrollTop = resultBox.scrollHeight;

            // Add event listeners for feedback buttons
            document.querySelectorAll('.feedback.correc').forEach((correctButton, index) => {
                correctButton.addEventListener('click', function () {
                    const correctQuestion = document.querySelectorAll('.message.user')[index]?.textContent || "Unknown Question";
                    const correctAnswer = document.querySelectorAll('.message.bot')[index]?.textContent || "Unknown Answer";

                    sendToAnswersJson(correctQuestion, correctAnswer, "");
                    showSuccessPopup("Thank you for your response!");
                });
            });

            document.querySelectorAll('.feedback.wrong').forEach((wrongButton, index) => {
                wrongButton.addEventListener('click', function () {
                    const feedbackBox = document.querySelectorAll('.feedback-box')[index];
                    feedbackBox.style.display = 'block';

                    const submitFeedbackButton = feedbackBox.querySelector('.submit-feedback');
                    const submitFeedbackHandler = function () {
                        const feedbackText = feedbackBox.querySelector('.feedback-text').value;
                        const feedbackError = feedbackBox.querySelector('.feedback-error');

                        if (feedbackText.trim() === '') {
                            feedbackError.style.display = 'block';
                        } else {
                            feedbackError.style.display = 'none';
                            const wrongQuestion = document.querySelectorAll('.message.user')[index].textContent;
                            const wrongAnswer = document.querySelectorAll('.message.bot')[index].textContent;

                            sendToAnswersJson(wrongQuestion, wrongAnswer, feedbackText);
                            feedbackBox.style.display = 'none';
                            showSuccessPopup("Your feedback has been submitted successfully!");
                            submitFeedbackButton.removeEventListener('click', submitFeedbackHandler);
                        }
                    };

                    submitFeedbackButton.addEventListener('click', submitFeedbackHandler);
                });
            });

            queryText.value = ''; // Clear input
        })
        .catch(error => {
            console.error('Error:', error);
        })
        .finally(() => {
            loaderContainer.style.display = 'none';
            askButton.style.display = 'block';
        });
    });

    queryText.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            if (event.shiftKey) {
                return;
            } else {
                askButton.click();
                event.preventDefault();
            }
        }
    });

    selectedFile.addEventListener('change', updateButtonVisibility);
    selectedLanguage.addEventListener('change', updateButtonVisibility);
    updateButtonVisibility();

    function showSuccessPopup(message) {
        const feedbackPopup = document.createElement('div');
        feedbackPopup.classList.add('feedback-popup');
        feedbackPopup.textContent = message;
        document.body.appendChild(feedbackPopup);

        setTimeout(() => {
            feedbackPopup.remove();
        }, 3000);
    }
});
