navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    if (!MediaRecorder.isTypeSupported('audio/webm'))
        return alert('Browser not supported')
    const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
    })
    const socket = new WebSocket('wss://livetranscription.onrender.com:80/listen')
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