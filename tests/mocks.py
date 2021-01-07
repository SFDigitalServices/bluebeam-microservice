"""Mock objects for testing"""
# pylint: disable-all

FETCH_TOKEN_RESPONSE = {
    "access_token": "fake_token",
    "token_type": "bearer",
    "expires_in": 3599,
    "userName": "fake_user@user.com",
    "scope": "full_user",
    "refresh_token_expires_in": "5184000",
    ".issued": "Thu, 30 Jan 3020 22:08:47 GMT",
    ".expires": "Thu, 30 Jan 3020 23:08:47 GMT"
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
            "Id": 147572936,
            "Name": "2.ROUTING FORMS",
            "Path": "/CCSF EPR/A.PERMIT SUBMITTAL/2.ROUTING FORMS",
            "ParentFolderId": 147572934,
            "Created": "2020-05-18T23:12:19.887",
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
    "TotalCount": 8
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

CREATE_PROJECT_RESPONSE_INVALID_NAME = {
    "ErrorCode": 99996
}

CREATE_FOLDER_RESPONSE = {
    "Id": 135399569
}

INIT_FILE_UPLOAD_RESPONSE = {
    "Id": 1234,
    "UploadUrl": "https://upload.here.com",
    "UploadContentType": "application/pdf"
}

INIT_FILE_UPLOAD_INVALID_NAME_RESPONSE = {
    "ErrorCode":99996
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

SUBMISSION_POST_DATA_ZIP = {
    "project_name": "123 Zip St.",
    "email": "test@test.com",
    "phone": "415-867-5309",
    "name": "Jenny",
    "files": [{
        "url": "https://bucketeer.com/Archive.zip",
        "originalName": "Archive.zip"
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

BUCKETEER_SUBMISSION_POST_DATA = {
    "project_name": "1600 Pennsylvania Ave.",
    "email": "test@test.com",
    "phone": "415-867-5309",
    "name": "Jenny",
    "files": [{
        "url": "https://bucketeer.com/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
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

GET_PROJECT_USERS_RESPONSE = {
    "$id": "1",
    "ProjectUsers": [
        {
            "$id": "2",
            "Id": 984539,
            "Name": "John Doe",
            "Email": "user1@test.com",
            "IsProjectOwner": False,
            "RestrictedStatus": "Allow"
        },
        {
            "$id": "3",
            "Id": 1045175,
            "Name": "Jane Doe",
            "Email": "user2@test.com",
            "IsProjectOwner": True,
            "RestrictedStatus": "Allow"
        }
    ],
    "TotalCount": 2
}

USER_DOES_NOT_EXIST_RESPONSE = {
    "ErrorCode": 12001
}

BUILDING_PERMITS_EXPORT_QUERY = [
    {
        "_id": "xxxbd015fefa4f42fec2dxxx",
        "data": {
            "actionState": "Queued for Bluebeam",
            "bluebeamStatus": "",
            "ptsStatus": "",
            "permitType": "existingBuilding",
            "reviewOverTheCounter": "",
            "onlyFireDepartmentReview": "",
            "applicantType": "agent",
            "applicantFirstName": "test",
            "applicantLastName": "test",
            "applicantPhoneNumber": "(111) 111-1111",
            "applicantEmail": "test@test.test",
            "applicantAddress1": "",
            "applicantAddress2": "",
            "applicantCity": "",
            "Page2State": "",
            "applicantZipCode": "",
            "applicantContractorLicenseNumber": "",
            "applicantContractorLicenseExpirationDate": "",
            "applicantBTRC": "",
            "applicantArchitectLicenseNumber": "",
            "applicantArchitectLicenseExpirationDate": "",
            "applicantEngineerLicenseNumber": "",
            "applicantEngineerLicenseExpirationDate": "",
            "buildingPermitApplicationNumber": "",
            "existingProjectAddress1": "",
            "existingProjectAddress2": "",
            "existingProjectZipCode": "",
            "existingProjectDescribeApplicationChanges": "",
            "ownerName": "test",
            "ownerPhoneNumber": "",
            "ownerEmail": "test@test.test",
            "ownerAddress1": "test",
            "ownerAddress2": "",
            "ownerCity": "test",
            "ownerState": "",
            "ownerZipCode": "",
            "teamMembers": {
                "agent": "TRUE",
                "architect": "FALSE",
                "attorneyInFact": "FALSE",
                "contractor": "FALSE",
                "engineer": "FALSE"
            },
            "agentOrganizationName": "",
            "agentName": "",
            "agentEmail": "",
            "architectOrganizationName": "",
            "architectName": "",
            "architectEmail": "",
            "architectLicenseNumber": "",
            "architectLicenseExpirationDate": "",
            "attorneyOrganizationName": "",
            "attorneyName": "",
            "attorneyEmail": "",
            "contractorOrganizationName": "",
            "contractorName": "",
            "contractorEmail": "",
            "contractorLicenseNumber": "",
            "contractorLicenseExpirationDate": "",
            "contractorBTRC": "",
            "engineerOrganizationName": "",
            "engineerName": "",
            "engineerEmail": "",
            "engineerLicenseNumber": "",
            "engineerLicenseExpirationDate": "",
            "newBuildingLocation": "",
            "newBuildingBlockNumber": "",
            "newBuildingLotNumber": [
                ""
            ],
            "newBuildingLotFront": "",
            "newBuildingLotBack": "",
            "newBuildingLotAverageDepth": "",
            "newBuildingStreetFaced": "",
            "newBuildingStreetSide": "",
            "newBuildingNearestCrossStreet": "",
            "newBuildingCrossStreetDirection": "",
            "newBuildingCrossStreetDistance": "",
            "newBuildingLotHasOtherBuilding": "",
            "existingBuildingAddress1": "49 SOUTH VAN NESS AVE",
            "existingBuildingAddress2": "",
            "existingBuildingCity": "San Francisco",
            "existingBuildingState": "california",
            "existingBuildingZipCode": "94103",
            "existingBuildingBlockNumber": "3506",
            "existingBuildingLotNumber": [
                "008"
            ],
            "existingBuildingConstructionType": "iAFireResistiveNonCombustible",
            "existingBuildingDwellingUnits": "1",
            "existingBuildingOccupancyStories": "1",
            "existingBuildingBasementsAndCellars": "1",
            "existingBuildingPresentUse": "residential",
            "existingBuildingOccupancyClass": "a1AssemblyTheater",
            "sitePermitForm38": "no",
            "noticeOfViolation": "no",
            "estimatedCostOfProject": "1",
            "projectDescription": "test",
            "typeOfConstruction": "iAFireResistiveNonCombustible",
            "proposedDwellingUnits": "1",
            "proposedOccupancyStories": "1",
            "proposedBasementsAndCellars": "1",
            "proposedUse": "commercial",
            "occupancyClass": "a1AssemblyTheater",
            "constructionLenderName": "",
            "constructionLenderBranchDesignation": "",
            "constructionLenderAddress1": "",
            "constructionLenderAddress2": "",
            "constructionLenderCity": "",
            "constructionLenderState": "",
            "constructionLenderZipCode": "",
            "sitePermitForm12": "",
            "newEstimatedCostOfProject": "",
            "newProjectDescription": "",
            "newTypeOfConstruction": "",
            "newBuildingUse": "",
            "newOccupancyClass": "",
            "newGroundFloorArea": "",
            "newBuildingFrontHeight": "",
            "newDwellingUnits": "",
            "newOccupancyStories": "",
            "newBasements": "",
            "newConstructionLenderName": "",
            "newConstructionLenderBranchDesignation": "",
            "constructionLenderAddress3": "",
            "constructionLenderAddress4": "",
            "constructionLenderCity1": "",
            "constructionLenderState1": "",
            "constructionLenderZipCode1": "",
            "alterOrConstructDriveway": "no",
            "useStreetSpace": "no",
            "electricalWork": "no",
            "plumbingWork": "no",
            "additionalHeightOrStory": "no",
            "newCenterLineFrontHeight": "",
            "deckOrHorizontalExtension": "no",
            "groundFloorArea": "",
            "repairOrAlterSidewalk": "no",
            "extendBeyondPropertyLine": "no",
            "otherExistingBuildings": "no",
            "changeOfOccupancy": "no",
            "alterOrConstructDrivewayNew": "",
            "extendBeyondPropertyLineNew": "",
            "useStreetSpaceNew": "",
            "additionalStoriesNew": "",
            "howManyAdditionalStoriesNew": "",
            "useSidewalkSpaceNew": "",
            "affordableHousing": "",
            "developmentAgreement": "",
            "accessoryDwellingUnit": "",
            "uploadType": "",
            "bluebeamId": "",
            "optionalUploads": [
                {
                    "storage": "s3",
                    "name": "pdf-sample-debac3f6-41f6-4754-93f9-563a54c591cc.pdf",
                    "bucket": "bucketeer-123",
                    "key": "pdf-sample-debac3f6-41f6-4754-93f9-563a54c591cc.pdf",
                    "url": "https://bucketeer-123.s3.amazonaws.com/pdf-sample-debac3f6-41f6-4754-93f9-563a54c591cc.pdf",
                    "acl": "private",
                    "size": 7945,
                    "type": "application/pdf",
                    "originalName": "pdf-sample.pdf"
                }
            ],
            "requiredUploads": "",
            "noPlansPermit": "",
            "notes": "",
            "workersCompRadio": "Work_less_than_$100",
            "iHerebyCertifyCheckBox": "TRUE",
            "dateTime": "2020-09-23T22:43:47.000Z",
            "projectAddress": "49 SOUTH VAN NESS AVE",
            "projectLocation2": "",
            "fileLinks": [
                "https://ds-files.sfgov.org/pdf-sample-debac3f6-41f6-4754-93f9-563a54c591cc.pdf",
                "https://ds-files.sfgov.org/pdf-sample-8c0b8633-4160-40ee-b417-d73d56e74635.pdf"
            ],
            "confirmationUploads": [
                {
                    "storage": "s3",
                    "name": "pdf-sample-8c0b8633-4160-40ee-b417-d73d56e74635.pdf",
                    "bucket": "bucketeer-123",
                    "key": "pdf-sample-8c0b8633-4160-40ee-b417-d73d56e74635.pdf",
                    "url": "https://bucketeer-123.s3.amazonaws.com/pdf-sample-8c0b8633-4160-40ee-b417-d73d56e74635.pdf",
                    "acl": "private",
                    "size": 7945,
                    "type": "application/pdf",
                    "originalName": "pdf-sample.pdf"
                }
            ],
            "priorityProjectSelections": {
                "isInDevelopmentAgreement": "TRUE",
                "is100AffordableHousing": "FALSE"
            },
            "projectAddressNumber": "49",
            "projectAddressNumberSuffix": "",
            "projectAddressStreetName": "SOUTH VAN NESS",
            "projectAddressStreetType": "AVE",
            "projectAddressUnitNumber": "",
            "projectAddressBlock": "3506",
            "projectAddressLot": "008",
            "projectAddressZip": "94103"
        },
        "created": "2020-09-23T22:45:41.914Z",
        "modified": "2020-09-23T22:45:41.914Z"
    },
    {
        "_id": "xxx3ad97a8e23744aee3axxx",
        "data": {
            "actionState": "Queued for Bluebeam",
            "bluebeamStatus": "",
            "ptsStatus": "",
            "permitType": "existingPermitApplication",
            "reviewOverTheCounter": "",
            "onlyFireDepartmentReview": "",
            "applicantType": "permitConsultant",
            "applicantFirstName": "test",
            "applicantLastName": "test",
            "applicantPhoneNumber": "(111) 111-1111",
            "applicantEmail": "test@sfgov.org",
            "applicantAddress1": "",
            "applicantAddress2": "",
            "applicantCity": "",
            "Page2State": "",
            "applicantZipCode": "",
            "applicantContractorLicenseNumber": "",
            "applicantContractorLicenseExpirationDate": "",
            "applicantBTRC": "",
            "applicantArchitectLicenseNumber": "",
            "applicantArchitectLicenseExpirationDate": "",
            "applicantEngineerLicenseNumber": "",
            "applicantEngineerLicenseExpirationDate": "",
            "buildingPermitApplicationNumber": "111111111111",
            "existingProjectAddress1": "49 SOUTH VAN NESS AVE",
            "existingProjectAddress2": "",
            "existingProjectZipCode": "94103",
            "existingProjectDescribeApplicationChanges": "test",
            "ownerName": "",
            "ownerPhoneNumber": "",
            "ownerEmail": "",
            "ownerAddress1": "",
            "ownerAddress2": "",
            "ownerCity": "",
            "ownerState": "",
            "ownerZipCode": "",
            "teamMembers": {
                "agent": "",
                "architect": "",
                "attorneyInFact": "",
                "contractor": "",
                "engineer": ""
            },
            "agentOrganizationName": "",
            "agentName": "",
            "agentEmail": "",
            "architectOrganizationName": "",
            "architectName": "",
            "architectEmail": "",
            "architectLicenseNumber": "",
            "architectLicenseExpirationDate": "",
            "attorneyOrganizationName": "",
            "attorneyName": "",
            "attorneyEmail": "",
            "contractorOrganizationName": "",
            "contractorName": "",
            "contractorEmail": "",
            "contractorLicenseNumber": "",
            "contractorLicenseExpirationDate": "",
            "contractorBTRC": "",
            "engineerOrganizationName": "",
            "engineerName": "",
            "engineerEmail": "",
            "engineerLicenseNumber": "",
            "engineerLicenseExpirationDate": "",
            "newBuildingLocation": "",
            "newBuildingBlockNumber": "",
            "newBuildingLotNumber": [
                ""
            ],
            "newBuildingLotFront": "",
            "newBuildingLotBack": "",
            "newBuildingLotAverageDepth": "",
            "newBuildingStreetFaced": "",
            "newBuildingStreetSide": "",
            "newBuildingNearestCrossStreet": "",
            "newBuildingCrossStreetDirection": "",
            "newBuildingCrossStreetDistance": "",
            "newBuildingLotHasOtherBuilding": "",
            "existingBuildingAddress1": "",
            "existingBuildingAddress2": "",
            "existingBuildingCity": "",
            "existingBuildingState": "",
            "existingBuildingZipCode": "",
            "existingBuildingBlockNumber": "",
            "existingBuildingLotNumber": [
                ""
            ],
            "existingBuildingConstructionType": "",
            "existingBuildingDwellingUnits": "",
            "existingBuildingOccupancyStories": "",
            "existingBuildingBasementsAndCellars": "",
            "existingBuildingPresentUse": "",
            "existingBuildingOccupancyClass": "",
            "sitePermitForm38": "",
            "noticeOfViolation": "",
            "estimatedCostOfProject": "",
            "projectDescription": "",
            "typeOfConstruction": "",
            "proposedDwellingUnits": "",
            "proposedOccupancyStories": "",
            "proposedBasementsAndCellars": "",
            "proposedUse": "",
            "occupancyClass": "",
            "constructionLenderName": "",
            "constructionLenderBranchDesignation": "",
            "constructionLenderAddress1": "",
            "constructionLenderAddress2": "",
            "constructionLenderCity": "",
            "constructionLenderState": "",
            "constructionLenderZipCode": "",
            "sitePermitForm12": "",
            "newEstimatedCostOfProject": "",
            "newProjectDescription": "",
            "newTypeOfConstruction": "",
            "newBuildingUse": "",
            "newOccupancyClass": "",
            "newGroundFloorArea": "",
            "newBuildingFrontHeight": "",
            "newDwellingUnits": "",
            "newOccupancyStories": "",
            "newBasements": "",
            "newConstructionLenderName": "",
            "newConstructionLenderBranchDesignation": "",
            "constructionLenderAddress3": "",
            "constructionLenderAddress4": "",
            "constructionLenderCity1": "",
            "constructionLenderState1": "",
            "constructionLenderZipCode1": "",
            "alterOrConstructDriveway": "",
            "useStreetSpace": "",
            "electricalWork": "",
            "plumbingWork": "",
            "additionalHeightOrStory": "",
            "newCenterLineFrontHeight": "",
            "deckOrHorizontalExtension": "",
            "groundFloorArea": "",
            "repairOrAlterSidewalk": "",
            "extendBeyondPropertyLine": "",
            "otherExistingBuildings": "",
            "changeOfOccupancy": "",
            "alterOrConstructDrivewayNew": "",
            "extendBeyondPropertyLineNew": "",
            "useStreetSpaceNew": "",
            "additionalStoriesNew": "",
            "howManyAdditionalStoriesNew": "",
            "useSidewalkSpaceNew": "",
            "affordableHousing": "",
            "developmentAgreement": "",
            "accessoryDwellingUnit": "",
            "uploadType": "revision",
            "bluebeamId": "",
            "optionalUploads": "",
            "requiredUploads": [
                {
                    "storage": "s3",
                    "name": "pdf-sample-e16a76ad-793a-4736-8bcf-7ef419ae4cdb.pdf",
                    "bucket": "bucketeer-123",
                    "key": "pdf-sample-e16a76ad-793a-4736-8bcf-7ef419ae4cdb.pdf",
                    "url": "https://bucketeer-123.s3.amazonaws.com/pdf-sample-e16a76ad-793a-4736-8bcf-7ef419ae4cdb.pdf",
                    "acl": "private",
                    "size": 7945,
                    "type": "application/pdf",
                    "originalName": "pdf-sample.pdf"
                }
            ],
            "noPlansPermit": "",
            "notes": "",
            "workersCompRadio": "Work_less_than_$100",
            "iHerebyCertifyCheckBox": "TRUE",
            "dateTime": "2020-09-29T21:55:45.000Z",
            "projectAddress": "49 SOUTH VAN NESS AVE",
            "projectLocation2": "",
            "fileLinks": [
                "https://ds-files.sfgov.org/pdf-sample-e16a76ad-793a-4736-8bcf-7ef419ae4cdb.pdf",
                "https://ds-files.sfgov.org/pdf-sample-ce2643c6-7052-404c-9051-57d2f6abf76b.pdf"
            ],
            "confirmationUploads": [
                {
                    "storage": "s3",
                    "name": "pdf-sample-ce2643c6-7052-404c-9051-57d2f6abf76b.pdf",
                    "bucket": "bucketeer-123",
                    "key": "pdf-sample-ce2643c6-7052-404c-9051-57d2f6abf76b.pdf",
                    "url": "https://bucketeer-123.s3.amazonaws.com/pdf-sample-ce2643c6-7052-404c-9051-57d2f6abf76b.pdf",
                    "acl": "private",
                    "size": 7945,
                    "type": "application/pdf",
                    "originalName": "pdf-sample.pdf"
                }
            ],
            "priorityProjectSelections": {
                "isInDevelopmentAgreement": "FALSE",
                "is100AffordableHousing": "TRUE"
            },
            "projectAddressNumber": "49",
            "projectAddressNumberSuffix": "",
            "projectAddressStreetName": "SOUTH VAN NESS",
            "projectAddressStreetType": "AVE",
            "projectAddressUnitNumber": "",
            "projectAddressBlock": "3506",
            "projectAddressLot": "008",
            "projectAddressZip": "94103"
        },
        "created": "2020-09-29T21:56:39.004Z",
        "modified": "2020-09-29T21:56:39.005Z"
    }
]
