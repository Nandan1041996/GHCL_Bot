

// document.addEventListener('DOMContentLoaded', function () {
//     const askButton = document.getElementById('ask-question-btn');
//     const resultBox = document.getElementById('result-box');
//     const loaderContainer = document.getElementById('loader-container');
//     const selectedFile = document.getElementById('selected_file');
//     const selectedLanguage = document.getElementById('selected_language');
//     const queryText = document.getElementById('query_text');
//     console.log(queryText)
//     const docSelectionMessage = document.getElementById('doc-selection-message');
//            // Select the chatbox container and the move to top button
//     const chatboxContainer = document.getElementById('chatbox-container');
//     const moveToTopBtn = document.createElement('button');
//     moveToTopBtn.classList.add('move-to-top-btn');
//     moveToTopBtn.innerHTML = 'Move to Top';

//     // Append the button to the right-panel (or whichever container you're using)
//     document.querySelector('.right-panel').appendChild(moveToTopBtn);

//     // Initially hide the button
//     moveToTopBtn.style.display = 'none';

//     // Show the "Move to Top" button when user scrolls down 5px or more
//     chatboxContainer.addEventListener('scroll', function () {
//         // Check if the user has scrolled down 5px or more
//         if (chatboxContainer.scrollTop > 5) {
//             moveToTopBtn.style.display = 'block';  // Show button
//         } else {
//             moveToTopBtn.style.display = 'none';  // Hide button
//         }
//     });

//     // Function to scroll to the top of the chatbox container
//     function moveToTop() {
//         chatboxContainer.scrollTo({
//             top: 0, 
//             behavior: 'smooth'  // Smooth scrolling to top
//         });
//     }

//     // Add the event listener to the button to trigger the move to top function
//     moveToTopBtn.addEventListener('click', moveToTop);
//     function updateButtonVisibility() {
//         askButton.style.display = (selectedFile.value !== '' && selectedLanguage.value !== '') ? 'block' : 'none';
//     }

//     // Convert URLs in text to clickable hyperlinks
//     function convertTextToHyperlinks(text) {
//         const urlPattern = /(https?:\/\/[^\s]+)/g; // Regex to detect URLs
//         return text.replace(urlPattern, (url) => {
//             return `<a href="${url}" target="_blank">${url}</a>`;
//         });
//     }

//     // Function to handle sending data to answers.json
//     function sendToAnswersJson(prompt, chatAns, humanAns) {
//         const answerData = {
//             Prompt: prompt,
//             "Chat-Ans": chatAns,
//             "Human-Ans": humanAns
//         };

//         fetch('/save_answers', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(answerData)
//         })
//         .then(response => response.json())
//         .then(data => {
//             console.log('Answer data saved:', data);
//         })
//         .catch(error => {
//             console.error('Error saving answer data:', error);
//         });
//     }

//     askButton.addEventListener('click', function () {
//         // Show loader and hide ask button
//         loaderContainer.style.display = 'flex'; // Show loader as flex to center it
//         askButton.style.display = 'none'; // Hide ask button
    
//         const formData = new FormData();
//         formData.append('query_text', queryText.value);
//         formData.append('selected_language', selectedLanguage.value);
    
//         // If selectedFile is empty, we don't append it
//         if (selectedFile && selectedFile.value) {
//             formData.append('selected_file', selectedFile.value);
//         }
    
//         fetch('/ask', {
//             method: 'POST',
//             body: formData
//         })
//         .then(response => response.json())
//         .then(data => {
//             const question = data.question;
//             const answer = convertTextToHyperlinks(data.answer);
    
//             // Show question in chatbox
//             resultBox.innerHTML += `
//             <div class="message-block">
//                 <div class="message user">${question}</div>
//                 <div class="message bot">${answer}</div>
//                 <div class="feedback-section">
//                     <div class="feedback-icons">
//                         <span class="feedback correc">&#128077;</span> <!-- Thumbs Up -->
//                         <span class="feedback wrong">&#128078;</span> <!-- Thumbs Down -->
//                     </div>
//                     <div class="feedback-box" style="display: none;">
//                         <div class="feedback-input">
//                             <textarea class="feedback-text" placeholder="Please provide your feedback..."></textarea>
//                             <button class="submit-feedback">Submit</button>
//                         </div>
//                         <span class="feedback-error" style="color:red; display:none;">Please provide feedback.</span>
//                     </div>
//                 </div>
//             </div>`;
    
//             // Scroll to the bottom of the chatbox
//             resultBox.scrollTop = resultBox.scrollHeight;
    
//             // Handle correct answer feedback
//             document.querySelectorAll('.feedback.correc').forEach((correctButton, index) => {
//                 correctButton.addEventListener('click', function () {
//                     const correctQuestion = document.querySelectorAll('.message.user')[index]?.textContent || "Unknown Question";
//                     const correctAnswer = document.querySelectorAll('.message.bot')[index]?.textContent || "Unknown Answer";
    
//                     sendToAnswersJson(correctQuestion, correctAnswer, ""); // Human answer is empty for correct
//                     saveFeedback(correctQuestion, correctAnswer, true);
    
//                     showSuccessPopup("Thank you for your response!");
//                 });
//             });
    
//             // Handle wrong answer feedback
//             document.querySelectorAll('.feedback.wrong').forEach((wrongButton, index) => {
//                 wrongButton.addEventListener('click', function () {
//                     const feedbackBox = document.querySelectorAll('.feedback-box')[index];
//                     feedbackBox.style.display = 'block';
    
//                     const submitFeedbackButton = feedbackBox.querySelector('.submit-feedback');
//                     const submitFeedbackHandler = function () {
//                         const feedbackText = feedbackBox.querySelector('.feedback-text').value;
//                         const feedbackError = feedbackBox.querySelector('.feedback-error');
    
//                         if (feedbackText.trim() === '') {
//                             feedbackError.style.display = 'block'; // Show error message
//                         } else {
//                             feedbackError.style.display = 'none'; // Hide error message
    
//                             const wrongQuestion = document.querySelectorAll('.message.user')[index].textContent;
//                             const wrongAnswer = document.querySelectorAll('.message.bot')[index].textContent;
    
//                             sendToAnswersJson(wrongQuestion, wrongAnswer, feedbackText); // Include feedback
//                             saveFeedback(wrongQuestion, wrongAnswer, false, feedbackText);
    
//                             feedbackBox.style.display = 'none';
    
//                             showSuccessPopup("Your feedback has been submitted successfully!");
    
//                             submitFeedbackButton.removeEventListener('click', submitFeedbackHandler);
//                         }
//                     };
    
//                     submitFeedbackButton.addEventListener('click', submitFeedbackHandler);
//                 });
//             });
    
//             // Clear the input text area after sending the question
//             queryText.value = '';
//         })
//         .catch(error => {
//             console.error('Error:', error);
//         })
//         .finally(() => {
//             loaderContainer.style.display = 'none'; // Hide loader
//             askButton.style.display = 'block'; // Show ask button again
//         });
    
    
//     // Function to display the success popup message
//     function showSuccessPopup(message) {
//         const feedbackPopup = document.createElement('div');
//         feedbackPopup.classList.add('feedback-popup');
//         feedbackPopup.style.position = 'fixed';
//         feedbackPopup.style.top = '50%';
//         feedbackPopup.style.left = '50%';
//         feedbackPopup.style.transform = 'translate(-50%, -50%)';
//         feedbackPopup.style.backgroundColor = '#96DFF7';
//         feedbackPopup.style.color = 'black';
//         feedbackPopup.style.padding = '20px';
//         feedbackPopup.style.borderRadius = '5px';
//         feedbackPopup.style.zIndex = '1000';
//         feedbackPopup.textContent = message;
    
//         document.body.appendChild(feedbackPopup);
    
//         // Hide popup after 3 seconds
//         setTimeout(function () {
//             feedbackPopup.style.display = 'none';
//             document.body.removeChild(feedbackPopup);
//         }, 3000);
//     }
    
// document.querySelectorAll('.feedback.wrong').forEach((wrongButton, index) => {
//   wrongButton.addEventListener('click', function () {
//       // Show feedback box for wrong answers
//       const feedbackBox = document.querySelectorAll('.feedback-box')[index];
//       feedbackBox.style.display = 'block';

//       // Handle submit feedback
//       const submitFeedbackButton = feedbackBox.querySelector('.submit-feedback');
//       const submitFeedbackHandler = function () {
//           const feedbackText = feedbackBox.querySelector('.feedback-text').value;
//           const feedbackError = feedbackBox.querySelector('.feedback-error');

//           // Check if feedback is empty
//           if (feedbackText.trim() === '') {
//               feedbackError.style.display = 'block'; // Show error message
//           } else {
//               feedbackError.style.display = 'none'; // Hide error message

//               const wrongQuestion = document.querySelectorAll('.message.user')[index].textContent;
//               const wrongAnswer = document.querySelectorAll('.message.bot')[index].textContent;

//               sendToAnswersJson(wrongQuestion, wrongAnswer, feedbackText); // Include feedback
//               saveFeedback(wrongQuestion, wrongAnswer, false, feedbackText);

//               // Hide the feedback box after submission
//               feedbackBox.style.display = 'none';

//               // Display "Your feedback has been submitted successfully!" popup for wrong answer feedback
//               showSuccessPopup("Your feedback has been submitted successfully!");

//               // Remove the event listener to prevent multiple submissions for the same feedback
//               submitFeedbackButton.removeEventListener('click', submitFeedbackHandler);
//           }
//       };

//       submitFeedbackButton.addEventListener('click', submitFeedbackHandler);
//   });
// });

//     // Clear the input text area after sending the question
//             queryText.value = ''; 
//         })
//         .catch(error => {
//             console.error('Error:', error);
//         })
//         .finally(() => {
//             loaderContainer.style.display = 'none'; // Hide loader
//             askButton.style.display = 'block'; // Show ask button again
//         });


//   // Handle Enter and Shift+Enter in the textarea
// queryText.addEventListener('keypress', function (event) {
//     if (event.key === 'Enter') {
//         if (event.shiftKey) {
//             // Allow new line if Shift + Enter is pressed
//             return;
//         } else {
//             // Trigger ask button click when Enter is pressed without Shift
//             askButton.click();
//             event.preventDefault(); // Prevent new line when Enter is pressed without Shift
//         }
//     }
// });


//     selectedFile.addEventListener('change', function () {
//         if (selectedFile.value === '') {
//             docSelectionMessage.textContent = 'Please select a document.';
//         } else {
//             docSelectionMessage.textContent = '';
//         }
//         updateButtonVisibility();
//     });

//     selectedLanguage.addEventListener('change', function () {
//         updateButtonVisibility();
//     });

//     // Initialize button visibility on page load
//     updateButtonVisibility();

//     // Function to save feedback in a JSON file
//     function saveFeedback(question, answer, isCorrect, feedback = '') {
//         const feedbackData = {
//             question: question,
//             answer: answer,
//             isCorrect: isCorrect,
//             feedback: feedback
//         };

//         fetch('/save_feedback', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify(feedbackData)
//         })
//         .then(response => response.json())
//         .then(data => {
//             console.log('Feedback saved:', data);
//         })
//         .catch(error => {
//             console.error('Error saving feedback:', error);
//         });
//     }

// });




document.addEventListener('DOMContentLoaded', function () {
    const askButton = document.getElementById('ask-question-btn');
    const resultBox = document.getElementById('result-box');
    const loaderContainer = document.getElementById('loader-container');
    const selectedFile = document.getElementById('selected_file');
    const selectedLanguage = document.getElementById('selected_language');
    const queryText = document.getElementById('query_text');
    const docSelectionMessage = document.getElementById('doc-selection-message');
    


    document.getElementById('clearBtn').addEventListener('click', function() {
        // Send a POST request to the '/clear' route
        fetch('/clear', {
            method: 'POST',  // Use POST method for the request
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            // Once the request is successful, reload the chat page
            if (response.ok) {
                window.location.href = '/chatpage';  // Redirect to the chat page
            } else {
                console.error('Failed to clear the data');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    // // Select the chatbox container and the move to top button
    // const chatboxContainer = document.getElementById('chatbox-container');
    // const moveToTopBtn = document.createElement('button');
    // moveToTopBtn.classList.add('move-to-top-btn');
    // moveToTopBtn.innerHTML = 'Move to Top';

    // // Append the button to the right-panel (or whichever container you're using)
    // document.querySelector('.right-panel').appendChild(moveToTopBtn);

    // // Initially hide the button
    // moveToTopBtn.style.display = 'none';

    // // Show the "Move to Top" button when user scrolls down 5px or more
    // chatboxContainer.addEventListener('scroll', function () {
    //     if (chatboxContainer.scrollTop > 5) {
    //         moveToTopBtn.style.display = 'block';  // Show button
    //     } else {
    //         moveToTopBtn.style.display = 'none';  // Hide button
    //     }
    // });

    // // Function to scroll to the top of the chatbox container
    // function moveToTop() {
    //     chatboxContainer.scrollTo({
    //         top: 0, 
    //         behavior: 'smooth'  // Smooth scrolling to top
    //     });
    // }

    // // Add the event listener to the button to trigger the move to top function
    // moveToTopBtn.addEventListener('click', moveToTop);


    
    // Function to update button visibility
    function updateButtonVisibility() {
        askButton.style.display = (selectedFile.value !== '' && selectedLanguage.value !== '') ? 'block' : 'none';
    }

    // Convert URLs in text to clickable hyperlinks
    function convertTextToHyperlinks(text) {
        const urlPattern = /(https?:\/\/[^\s]+)/g; // Regex to detect URLs
        return text.replace(urlPattern, (url) => {
            return `<a href="${url}" target="_blank">${url}</a>`;
        });
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
        // Show loader and hide ask button
        loaderContainer.style.display = 'flex'; // Show loader as flex to center it
        askButton.style.display = 'none'; // Hide ask button

        const formData = new FormData();
        formData.append('query_text', queryText.value);
        formData.append('selected_language', selectedLanguage.value);

        // If selectedFile is empty, we don't append it
        if (selectedFile && selectedFile.value) {
            formData.append('selected_file', selectedFile.value);
        }

        fetch('/ask', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const question = data.question;
            const answer = convertTextToHyperlinks(data.answer);

            // Show question in chatbox
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

            // Handle correct answer feedback
            document.querySelectorAll('.feedback.correc').forEach((correctButton, index) => {
                correctButton.addEventListener('click', function () {
                    const correctQuestion = document.querySelectorAll('.message.user')[index]?.textContent || "Unknown Question";
                    const correctAnswer = document.querySelectorAll('.message.bot')[index]?.textContent || "Unknown Answer";

                    sendToAnswersJson(correctQuestion, correctAnswer, ""); // Human answer is empty for correct
                    saveFeedback(correctQuestion, correctAnswer, true);

                    showSuccessPopup("Thank you for your response!");
                });
            });

            // Handle wrong answer feedback
            document.querySelectorAll('.feedback.wrong').forEach((wrongButton, index) => {
                wrongButton.addEventListener('click', function () {
                    const feedbackBox = document.querySelectorAll('.feedback-box')[index];
                    feedbackBox.style.display = 'block';

                    const submitFeedbackButton = feedbackBox.querySelector('.submit-feedback');
                    const submitFeedbackHandler = function () {
                        const feedbackText = feedbackBox.querySelector('.feedback-text').value;
                        const feedbackError = feedbackBox.querySelector('.feedback-error');

                        if (feedbackText.trim() === '') {
                            feedbackError.style.display = 'block'; // Show error message
                        } else {
                            feedbackError.style.display = 'none'; // Hide error message

                            const wrongQuestion = document.querySelectorAll('.message.user')[index].textContent;
                            const wrongAnswer = document.querySelectorAll('.message.bot')[index].textContent;

                            sendToAnswersJson(wrongQuestion, wrongAnswer, feedbackText); // Include feedback
                            saveFeedback(wrongQuestion, wrongAnswer, false, feedbackText);

                            feedbackBox.style.display = 'none';

                            showSuccessPopup("Your feedback has been submitted successfully!");

                            submitFeedbackButton.removeEventListener('click', submitFeedbackHandler);
                        }
                    };

                    submitFeedbackButton.addEventListener('click', submitFeedbackHandler);
                });
            });

            // Clear the input text area after sending the question
            queryText.value = '';
        })
        .catch(error => {
            console.error('Error:', error);
        })
        .finally(() => {
            loaderContainer.style.display = 'none'; // Hide loader
            askButton.style.display = 'block'; // Show ask button again
        });
    });

    // Function to display the success popup message
    function showSuccessPopup(message) {
        const feedbackPopup = document.createElement('div');
        feedbackPopup.classList.add('feedback-popup');
        feedbackPopup.style.position = 'fixed';
        feedbackPopup.style.top = '50%';
        feedbackPopup.style.left = '50%';
        feedbackPopup.style.transform = 'translate(-50%, -50%)';
        feedbackPopup.style.backgroundColor = '#96DFF7';
        feedbackPopup.style.color = 'black';
        feedbackPopup.style.padding = '20px';
        feedbackPopup.style.borderRadius = '5px';
        feedbackPopup.style.zIndex = '1000';
        feedbackPopup.textContent = message;

        document.body.appendChild(feedbackPopup);

        // Hide popup after 3 seconds
        setTimeout(function () {
            feedbackPopup.style.display = 'none';
            document.body.removeChild(feedbackPopup);
        }, 3000);
    }

    // Handle Enter and Shift+Enter in the textarea for submitting the query
    queryText.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            if (event.shiftKey) {
                // Allow new line if Shift + Enter is pressed
                return;
            } else {
                // Trigger ask button click when Enter is pressed without Shift
                askButton.click();
                event.preventDefault(); // Prevent new line when Enter is pressed without Shift
            }
        }
    });

    selectedFile.addEventListener('change', function () {
        if (selectedFile.value === '') {
            docSelectionMessage.textContent = 'Please select a document.';
        } else {
            docSelectionMessage.textContent = '';
        }
        updateButtonVisibility();
    });

    selectedLanguage.addEventListener('change', function () {
        updateButtonVisibility();
    });

    // Initialize button visibility on page load
    updateButtonVisibility();

    // Function to save feedback in a JSON file
    function saveFeedback(question, answer, isCorrect, feedback = '') {
        const feedbackData = {
            question: question,
            answer: answer,
            isCorrect: isCorrect,
            feedback: feedback
        };

        fetch('/save_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback saved:', data);
        })
        .catch(error => {
            console.error('Error saving feedback:', error);
        });
    }
});
