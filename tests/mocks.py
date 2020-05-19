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
            "Id": 147572933,
            "Name": "CCSF EPR",
            "Path": "/CCSF EPR",
            "ParentFolderId": 147572931,
            "Created": "2020-05-18T23:12:17.873",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "3",
            "Id": 147572934,
            "Name": "A.PERMIT SUBMITTAL",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL",
            "ParentFolderId": 147572933,
            "Created": "2020-05-18T23:12:18.357",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "4",
            "Id": 147572940,
            "Name": "B.APPROVED DOCUMENTS",
            "Path": "/CCSF EPR/B.APPROVED DOCUMENTS",
            "ParentFolderId": 147572933,
            "Created": "2020-05-18T23:12:20.67",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "5",
            "Id": 147572935,
            "Name": "1.PERMIT FORMS",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/1.PERMIT FORMS",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:18.887",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "6",
            "Id": 147572937,
            "Name": "2.ROUTING FORMS",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/2.ROUTING FORMS",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:19.403",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "7",
            "Id": 147572938,
            "Name": "3.DOCUMENTS FOR REVIEW",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/3.DOCUMENTS FOR REVIEW",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:19.887",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "8",
            "Id": 147572943,
            "Name": "1.BUILDING PERMIT DOCUMENTS",
            "Path": "/CCSF EPR/B.APPROVED DOCUMENTS/1.BUILDING PERMIT DOCUMENTS",
            "ParentFolderId": 147572940,
            "Created": "2020-05-18T23:12:21.153",
            "Permission": "ReadWriteDelete"
        }
    ],
    "TotalCount": 7
}

GET_FOLDERS_RESPONSE_NO_UPLOAD = {
    "$id": "1",
    "ProjectFolders": [
        {
            "$id": "2",
            "Id": 147572933,
            "Name": "CCSF EPR",
            "Path": "/CCSF EPR",
            "ParentFolderId": 147572931,
            "Created": "2020-05-18T23:12:17.873",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "3",
            "Id": 147572934,
            "Name": "A.PERMIT SUBMITTAL",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL",
            "ParentFolderId": 147572933,
            "Created": "2020-05-18T23:12:18.357",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "4",
            "Id": 147572940,
            "Name": "B.APPROVED DOCUMENTS",
            "Path": "/CCSF EPR/B.APPROVED DOCUMENTS",
            "ParentFolderId": 147572933,
            "Created": "2020-05-18T23:12:20.67",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "5",
            "Id": 147572935,
            "Name": "1.PERMIT FORMS",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/1.PERMIT FORMS",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:18.887",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "6",
            "Id": 147572937,
            "Name": "2.ROUTING FORMS",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/2.ROUTING FORMS",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:19.403",
            "Permission": "ReadWriteDelete"
        },
        {
            "$id": "7",
            "Id": 147572943,
            "Name": "1.BUILDING PERMIT DOCUMENTS",
            "Path": "/CCSF EPR/B.APPROVED DOCUMENTS/1.BUILDING PERMIT DOCUMENTS",
            "ParentFolderId": 147572940,
            "Created": "2020-05-18T23:12:21.153",
            "Permission": "ReadWriteDelete"
        }
    ],
    "TotalCount": 6
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
    "project_name": "123 Market St.",
    "email": "test@test.com",
    "phone": "415-867-5309",
    "name": "Jenny",
    "files": [{
        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "originalName": "dummy.pdf"
    }]
}

RESUBMISSION_POST_DATA = {
    "project_name": "1231 Stevenson",
    "project_id": "123-456-789",
    "email": "resubmit-test@test.com",
    "phone": "415-867-5309",
    "name": "Jenny",
    "files": [{
        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "originalName": "dummy.pdf"
    }]
}

ACCESS_TOKEN_RESPONSE = {
    "access_token": "SECRET-TOKEN",
    "token_type": "bearer",
    "expires_in": 3599,
    "refresh_token": "REFRESH-TOKEN",
    "userName": "user@user.com",
    "client_id": "client-id",
    "scope": "full_prime",
    "refresh_token_expires_in": "5184000",
    ".issued": "Wed, 08 Apr 2020 23:56:52 GMT",
    ".expires": "Thu, 09 Apr 2020 00:56:52 GMT"
}

INVALID_GRANT_RESPONSE = {
    "error": "invalid_grant"
}
