# Setting up A Facebook Pages Bot

### Assumptions:

* You've cloned and setup a venv in the repo's root directory
* You've activated and installed dependencies
* You have setup a token for a system user with admin privileges able to manage your page.

## Get the Page Access Token

1. Store that token as `SYSTEM_USER_TOKEN` in a `.env` file in this directory.
1. run `python3 get_page_token.py` and add the indicated values to `.env`

```json
{
    "data": [
        {
            "access_token": "save this as PAGE_ACCESS_TOKEN in .env",
            "category": "Visual Arts",
            "category_list": [
                {
                    "id": "1234567890",
                    "name": "Visual Arts"
                }
            ],
            "name": "My Page",
            "id": "save this as FACEBOOK_PAGE_ID in .env",
            "tasks": [
                "ADVERTISE",
                "ANALYZE",
                "CREATE_CONTENT",
                "MESSAGING",
                "MODERATE",
                "MANAGE"
            ]
        }
    ],
    "paging": {
        "cursors": {
            "before": "QVFIUkhBOG9NaFl0R3FsZA2NXSG1YbnpUS2RMbG9kbGRQLVlWQjdIcGhvX0w0YzQxUFlrVE5HZAS1yY0FSS0NOWmw1Q3VTc19MWm1IaTZAWalYxZAVNqTVpTT1B3",
            "after": "QVFIUmE5bjFyQmFKaUsyejdVMHYxblpSU2YxOFlCbzl2MzAtUnlvMC1QblJIcUJMLVNHb2JlWlh2ZAE13d0sybDZAjdTNPbmllbUJiWlYwUlpUNDEtQUcwNk9B"
        }
    }
}
```

If you have multiple assets assigned to your system user, you will see them here. Make note of the values associated with the asset you wish to automate.
