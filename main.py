"""
Script for downloading wav files from Google Drive algorithmically to prevent zipping and unzipping.
Requires permissions for shared drive and google authorization credentials.

Script will check credentials and allow user to login if necessary. Takes folderId as input and destination
for download as another optional parameter. If no destination is specified, downloads to the current directory.

Matthew Hyer
"""
import argparse
import io
import os
import sys

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# from threading import Thread
from multiprocessing import Pool, set_start_method, cpu_count

# Necessary scope for drive
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def patient_execute(service):
    """
    Function to execute drive API calls with error handling in case of http error due to drive demand.
    Raises exception if execute fails more than 5 times.
    :param service: Function to be executed
    :return: Executed service
    """
    count = 0
    while count < 5: # Try 5 times
        try:
            service = service.execute()
            return service
        except HttpError:
            print('Backend http error. Trying again after 1 second...')
            time.sleep(1)
    raise Exception('HttpError. Drive backend would not respond after 5 tries.')

def check_credentials():
    """Checks user credentials in current directory.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
            except FileNotFoundError:
                sys.exit('No credentials.json file in current directory. Either change to correct directory, or setup credentials for this machine at console.cloud.google.com')
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def download_file(real_file_id, destination, title, creds):
    """
    From: https://developers.google.com/drive/api/guides/manage-downloads

    Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    try:
        file_id = real_file_id

        # pylint: disable=maybe-no-member
        serve = build('drive', 'v2', credentials=creds)
        request = serve.files().get_media(fileId=file_id)

        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    obj = file.getvalue()
    filename = destination + '/' + title

    # print(filename)

    with open(filename, "bw") as f:
        f.write(obj)


def search_children(file_id, destination, results):
    """Recursively searches a folder's children for wav files and deals with contents.

    Args:
        - file_id: id of folder to be searched. fileId means folderId according to drive api
    Returns:
        None
    """
    items = results.get('items', [])

    if not items:
        print('No files found.')
        return None

    assert len(items) == 1

    item = items[0]

    id = item['id']
    temp = service.files().get(fileId=id, supportsAllDrives=True)  # .execute()
    temp = patient_execute(temp)
    mime = temp.get('mimeType', [])
    title = temp.get('title', [])
    print(title)

    if 'folder' in mime:
        subdestination = destination + '/' + title
        os.makedirs(subdestination, exist_ok=True)
        subfolder = service.children().list(
            folderId=id, maxResults=1,
            orderBy='folder')  # .execute()
        subfolder = patient_execute(subfolder)

        search_children(id, subdestination, subfolder)

        if 'nextPageToken' in results:
            nextfolder = service.children().list(
                    folderId=file_id, maxResults=1,
                    orderBy='folder', pageToken=results['nextPageToken'])  # .execute()
            nextfolder = patient_execute(nextfolder)

            return search_children(file_id, destination, nextfolder)
        else:
            print('End of folder')
            return None

    elif 'audio' in mime:
        # thread = Thread(target=download_file, args=(id, destination, title))
        # thread.start()

        pool.apply_async(download_file, args=(id, destination, title, creds))

        if 'nextPageToken' in results:
            nextresults = service.children().list(
                folderId=file_id, maxResults=1,
                orderBy='folder', pageToken=results['nextPageToken'])  # .execute()
            nextresults = patient_execute(nextresults)

            return search_children(file_id, destination, nextresults)
        else:
            print('End of folder')
            return None
    else:
        if 'nextPageToken' in results:
            nextresults = service.children().list(
                folderId=file_id, maxResults=1,
                orderBy='folder', pageToken=results['nextPageToken'])  # .execute()
            nextresults = patient_execute(nextresults)

            return search_children(file_id, destination, nextresults)
        else:
            print('End of folder')
            return None


if __name__ == '__main__':
    import time
    start = time.time()

    set_start_method('spawn')

    global pool
    pool = Pool(processes=cpu_count())

    parser = argparse.ArgumentParser()

    parser.add_argument('folderId', type=str, help='fileId of Google Drive folder to be searched.')
    parser.add_argument('--destination', type=str, default='', help='Local destination for folder download. If no \
                                                                    destination is specified, uses currrent directory')

    args = parser.parse_args()

    creds = check_credentials()

    global service
    service = build('drive', 'v2', credentials=creds)

    global folderId
    folderId = args.folderId

    # Call the Drive v3 API
    results = service.children().list(
        folderId=folderId, maxResults=1,
        orderBy='folder')  # .execute()
    results = patient_execute(results)

    downloading = True
    while downloading:
        downloading = search_children(args.folderId, args.destination, results)

    pool.close()
    pool.join()

    print('Downloading complete.')
    end = time.time()
    print('Total time: ' + str(end-start))