navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    if (!MediaRecorder.isTypeSupported('audio/webm'))
        return alert('Browser not supported')
    const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
    })
    const socket = new WebSocket('ws://localhost:5555/listen')
    const transcriptContainer = document.querySelector('#transcript-container');

    socket.onopen = () => {
        document.querySelector('#status').textContent = 'Status: Connected'
        mediaRecorder.addEventListener('dataavailable', async (event) => {
            if (event.data.size > 0 && socket.readyState == 1) {
                socket.send(event.data)
            }
        })
        mediaRecorder.start(250)
    }
    socket.onmessage = async (message) => {
        const received = message.data;
        if (received) {
            const transcriptLine = document.createElement('p');
            transcriptLine.className = 'transcript-line';
            transcriptLine.textContent = received; // Set the received data as the text content of the new transcript line
            transcriptContainer.appendChild(transcriptLine); // Append the new transcript line to the container
        }
    };
})

function toggleCascade() {
    const cascadeMenu = document.querySelector('#cascade-menu');
    cascadeMenu.style.display = (cascadeMenu.style.display === 'none') ? 'block' : 'none';
  }



  // Define variables for audio context and microphone stream
let audioContext;
let microphoneStream;

// Function to start the microphone
function startMicrophone() {
    // Check if the browser supports the Web Audio API
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('Web Audio API is not supported in this browser.');
        return;
    }

    // Create an audio context
    audioContext = new AudioContext();

    // Get user media (microphone)
    navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then(function (stream) {
            // Save the microphone stream
            microphoneStream = stream;

            // Connect the microphone stream to the audio context
            const microphoneInput = audioContext.createMediaStreamSource(stream);
            microphoneInput.connect(audioContext.destination);
        })
        .catch(function (error) {
            console.error('Error accessing microphone:', error);
        });
}

// Function to stop the microphone
function stopMicrophone() {
    if (microphoneStream) {
        // Stop the microphone stream and close the audio context
        microphoneStream.getTracks().forEach(function (track) {
            track.stop();
        });
        audioContext.close().then(function () {
            audioContext = null;
        });
    }
}

// Toggle microphone state when clicking a button
const toggleMicrophoneButton = document.querySelector('#toggleMicrophoneButton');
let isMicrophoneMuted = false;

toggleMicrophoneButton.addEventListener('click', function () {
    if (isMicrophoneMuted) {
        // If the microphone is muted, start it
        startMicrophone();
        toggleMicrophoneButton.textContent = 'Mute Microphone';
    } else {
        // If the microphone is not muted, stop it
        stopMicrophone();
        toggleMicrophoneButton.textContent = 'Unmute Microphone';
    }

    // Toggle the microphone state
    isMicrophoneMuted = !isMicrophoneMuted;
});
