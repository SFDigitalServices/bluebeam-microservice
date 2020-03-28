"""Mock objects for testing"""

FETCH_TOKEN_RESPONSE = {
    "access_token": "fake_token",
    "token_type": "bearer",
    "expires_in": 3599,
    "userName": "fake_user@user.com",
    "scope": "full_user",
    "refresh_token_expires_in": "5184000",
    ".issued": "Thu, 30 Jan 2020 22:08:47 GMT",
    ".expires": "Thu, 30 Jan 2020 23:08:47 GMT"
}

GET_PROJECTS_RESPONSE = {
    "$id": "1",
    "Projects": [
        {
            "$id": "3",
            "Id": "234-097-916",
            "Guid": "gFR_1Amn1ECEGsggH1i1gg",
            "Name": "project20200130_150257",
            "Restricted": True,
            "Created": "2020-01-30T23:02:57.733",
            "OwnerNameIdentifier": "1a1bc1f1-1111-1111-1111-1011f111ecc1",
            "OwnerEmail": "fake_user@user.com",
            "PrimeId": 1418530
        },
        {
            "$id": "4",
            "Id": "633-048-880",
            "Guid": "Z1jI111Ah1SYyHq1NrRrzg",
            "Name": "project20200130_150512",
            "Restricted": True,
            "Created": "2020-01-30T23:05:13.167",
            "OwnerNameIdentifier": "1a1bc1f1-1111-1111-1111-1011f111ecc1",
            "OwnerEmail": "fake_user@user.com",
            "PrimeId": 1418530
        }
    ],
    "TotalCount": 2
}

GET_FOLDERS_RESPONSE = {
    "$id": "1",
    "ProjectFolders": [
        {
            "$id": "2",
            "Id": 135399569,
            "Name": "my-awesome-folder",
            "Path": "/my-awesome-folder",
            "ParentFolderId": 135399567,
            "Created": "2020-01-30T23:19:57.64",
            "Permission": "ReadWriteDelete"
        }
    ],
    "TotalCount": 1
}

CREATE_PROJECT_RESPONSE = {
    "Id": "234-097-916"
}

CREATE_FOLDER_RESPONSE = {
    "Id": 135399569
}

INIT_FILE_UPLOAD_RESPONSE = {
    "Id": 1234,
    "UploadUrl": "https://upload.here.com",
    "UploadContentType": "application/pdf"
}

SUBMISSION_POST_DATA = {
    "address": "123 Market St.",
    "email": "test@test.com",
    "phone": "415-867-5309",
    "name": "Jenny"
}
