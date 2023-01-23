# drive-download-audio
Download audio files using Google Drive API

Avoid manually zipping and unzipping files when downloading large folder of nested audio files.
Preserves folder structure and original filenames. Currently only downloads audio files.

# Usage
main.py file takes a google drive folder as input with optional argument destination.

python main.py folderId --destination localDestination
