# drive-download-audio
Download audio files using Google Drive API

Avoid manually zipping and unzipping files when downloading large folder of nested audio files.
Preserves folder structure and original filenames. Currently only downloads audio files.

# Get Started
Download Google Drive API via:
```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Script uses OAuth 2.0 for verifying user credentials. The correct credentials.json file must be in the current directory and Google Drive API must be activated for the corresponding folder/drive.

See: https://developers.google.com/people/quickstart/python for help with OAuth 2.0


# Usage
main.py file takes a google drive folder as input with optional argument destination.
```
python main.py folderId --destination localDestination
```
A folder's folderId is the unique url ending that can be found via a sharing link or the browser's url bar i.e.


https://drive.google.com/drive/folders/folderId or https://drive.google.com/drive/folders/folderId?usp=sharing

# ToDo:
Currently, script cannot handle the case where a used is not authorized. The OAuth 2.0 flow will display the correct screen saying a user does not have access to a Drive folder, but the pyton script will hang and reject ctrl+c cancellation. The python session must be terminated.
