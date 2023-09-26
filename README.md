# Live Transcription With Python, Flask 2.0 and Deepgram

This is a modified version with additional features of deepgrams base python flask public repository!
The objective of this application is to help measure the amount of output a user does when studying a lenguage. (In this case, japanese)

To run this project create a virtual environment by running the below commands.
```
mkdir [% NAME_OF_YOUR_DIRECTORY %]
cd [% NAME_OF_YOUR_DIRECTORY %]
python3 -m venv venv
source venv/bin/activate
```

Make sure your virtual environment is activated and install the dependencies in the requirements.txt file inside.

`pip install -r requirements.txt`

Make sure you're in the directory with the main.py file and run the project in the development server.

`python main.py`

Pull up a browser and go to your localhost, `http://127.0.0.1:8000/`.

Allow access to your microphone and start speaking. A transcript of your audio will appear in the browser.
On top left the connection status is shown. If its working it will display "connected".
On top right it will display the amount of characters, the amount of time, and the characters/time to check speed.
