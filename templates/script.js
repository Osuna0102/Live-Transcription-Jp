let startTime = Date.now();
let wordCount = 0;

// Timer
setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    document.querySelector('#timer').textContent = `Time: ${minutes}:${seconds.toString().padStart(2, '0')}`;
}, 1000);

// Word Counter
setInterval(() => {
    const transcript = document.querySelector('#transcript-container');
    const text = transcript.textContent.trim();
    const characterCount = text.length;
    document.querySelector('#counter').textContent = `Characters: ${characterCount}`;
}, 1000);

// Words per Minute
setInterval(() => {
    const transcript = document.querySelector('#transcript-container');
    const text = transcript.textContent.trim();
    const characterCount = text.length;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = elapsed / 60;
    const wpm = Math.floor(characterCount / minutes);
    document.querySelector('#wpm').textContent = `WPM: ${wpm}`;
}, 1000);


navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    if (!MediaRecorder.isTypeSupported('audio/webm'))
        return alert('Browser not supported')
    const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
    })
    const socket = new WebSocket('wss://' + window.location.hostname + '/listen');
    const transcriptContainer = document.querySelector('#transcript-container');

    socket.onopen = () => {
        document.querySelector('#status').textContent = 'Status: Connected'
        mediaRecorder.addEventListener('dataavailable', async (event) => {
            if (event.data.size > 0 && socket.readyState == 1) {
                const arrayBuffer = await event.data.arrayBuffer();
                socket.send(arrayBuffer);
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


