# Building an Instagram Bot

## Overview

This guide covers the basics of setting up Meta/Facebook/Instagram so that you can automate posts programmatically. This opens up possibilities beyond merely scheduling posts such as randomly assembling posts from a database of content that you manage or generatively creating and posting content from an application hosted on a remote server.

The goal I had when setting out to make my first bots was to randomly generate and publish posts from a data base of existing content.

### My Approach Involves a Few Ingredients:

* A remote server with a static IP address.
* A domain with DNS configured to point to that server.
* A reverse proxy on that server configured to server static content (media files) as hosted content.
* A database that contains references to the hosted content along with other data including tags, descriptions, image names, filename, groups, and other useful bits of data.
* Accounts on Facebook and Instagram managed with Meta Business Suite.

This guide will not cover setting up infrastructure remotely. Local setup for the database, bot code, and publishing content already hosted on other sites will be covered.

### The Key Steps In Building Our Bot:

1. Setup Facebook/Instagram/Meta Business Suite
2. Setup The Development Environment
	* Mongo Database
	* Python3.10+
		* pip
		* pymongo
		* python-decouple
3. Use a spreadsheet to create/update database entries
4. Write a simple script to create/publish a single image post	
5. Write a script to create/publish a carousel post with multiple images

## Setup Facebook/Instagram/Meta Business Suite

### 1. Setup a Business Portfolio in Meta Business Suite (if you don't already have one)
* [Meta Business Suite](https://www.facebook.com/business/tools/meta-business-suite) - Click the Get Started Link and complete setup flow
	* More resources:
		* [Create a business portfolio in Meta Business Suite and Business Manager](https://www.facebook.com/business/help/1710077379203657)
		* [Set up and manage your business portfolio and business assets](https://www.facebook.com/business/help/586400082815745/)

### 2. Sign up for an Instagram Account (if you don't already have one)

1. [Instagram Account Sign Up](https://www.instagram.com/accounts/emailsignup/)

### 3. Setup a new Facebook Page to link your Instagram Account To:
1. Log into [facebook buisness](https://business.facebook.com/)
1. Expand dropdown in upper left panel to show your business portfolio
1. Click **Settings Icon** next to your business portfolio
1. Click **Accounts Icon**
1. Click **Pages**
1. Click **+ Add**
1. Click **Create a new Facebook Page** and complete setup flow

### 4. Connect an Instagram Account to your new Facebook Page

1. From the **Accounts > Pages** section, select the page you just created.
1. Click **Connect assets**
1. Click **Instagram account** and complete connection flow

### 5. Create an App for your post automation

1. Under **Accounts**, click **Apps**
1. Click **Add**
1. Click **Create a new app ID**
	1. Select the appropriate business portfolio, click **Next**
	1. Select **Other**, click **Next**
	1. Select **Business**, click **Next**
	1. Give you app a name and connect it to the portfolio above, click **Create app**
1. Navigate to [Apps Dashboard](https://developers.facebook.com/apps) and click the app you just setup
1. Click **App settings**
1. Click **Basic**
1. Note that this is where you can find your `App ID` and `App secret`

### 6. Create a System User and Assign to Page, App, and IG accounts

1. Click Users
1. Click System Users
1. Give a name and set System user role to Admin
1. Click the **...** button and **Assign assets**
1. Click **Pages**
1. Select a Page to assign to the System User
1. Enable **Content** under **Partial access**
1. Click **Apps**
1. Select an App to assign to the System User
1. Enable **Manage App** under **Full Control**
1. Click **Instgram accounts**
1. Select an Account to assign to the System User
1. Enable **Content** under **Partial access**
1. Click **Save**

### 7. Generate access token for the System User for your App.

1. Under **Users > System Users**, click the appropriate system user
1. Click **Generate token**
1. Select the appropriate App, click **Next**
1. Select expires **Never**, click **Next**
1. Assign Permissions by checking the following, or all if you want:

```
instagram_basic
instagram_content_publish
pages_read_engagement
pages_show_list
ads_management
business_management
catalog_management
instagram_shopping_tag_products
```
1. Click "Generate token"
1. Click "Copy" and store in a secure place... like a password manager as `SYSTEM_USER_TOKEN` or something.

### 8. Find your Instagram Account ID

1. Click **Accounts > Instagram accounts**
2. Click on the appropriate account
3. Copy the ID value as `INSTAGRAM_ACCOUNT_ID`.

### 9. Take stock of the important and sensitive variables

You should have 4 key variables that we'll need to make API calls to the instagram content endpoints:

1. `INSTAGRAM_ACCOUNT_ID`
2. `APP_ID`
3. `APP_SECRET`
4. `SYSTEM_USER_TOKEN`

Create a folder for your bot codebase and add a `.env`

```
INSTAGRAM_ACCOUNT_ID="<paste your instagram account id here>"
APP_ID="<paste your app id here>"
APP_SECRET="<paste your app secret here>"
SYSTEM_USER_TOKEN="<paste your system user token here>"
```

Because these basically give anyone in their possession the ability to control your account programmatically, consider securing your device as these are in plain-text.

TIPS:

* Use are really strong password to secure access to your computer.
* Lock your device or sign out of your sessions when leaving your workstation.
* Restrict access to your device. Disable remote access services like `ssh` or Remote Desktop unless you absolutely need them and have taken necessary security precautions.

## Setup The Development Environment

### Install MongoDB Community Edition

MongoDB is really pushing their cloud service, Atlas. It's probably really awesome, but unless you're scaling to enterprise levels, you'll want to start working with the Community Edition.

If your system isn't supported by homebrew or if you don't have homebrew installed, it can be downloaded from [here](https://www.mongodb.com/try/download/community), by selecting the **Version**, **Platform**, and **Package** and clicking **Download**.

Otherwise run:

1. `brew install mongodb-community`
1. `brew services start mongodb/brew/mongodb-community` 

Configuring the Database:

1. Open the CLI shell by running: `mongosh`
1. Setup your new database by running: `use <your database name goes here>`
1. Then create a new user with read/write privileges by running:
 
```
db.createUser({
	user: "<your username goes here>",
	pwd: passwordPrompt(),
	roles: [
		{ role: "readWrite", db: "<your database name goes here>" }
	]
})
```

1. Enter your password when prompted, which should result in an `{ ok: 1 }`
1. 	run `exit`
1. Enable Authentication: `sudo nano /etc/mongo.conf` if on Linux or `sudo nano /opt/homebrew/etc/mongo.conf` if installed with homebrew on MacOS. Set and save:

```
security:
  authorization: enabled
```	

1. `brew services restart mongodb/brew/mongodb-community`

There! Your MongoDB Database is setup.

#### Manually Managing Your Database

1. `mongsh`
1. `use <your database name goes here>`
1. `db.auth('<your username goes here>', passwordPrompt())`
1. Enter your password when prompted...

Have a look [here](https://www.mongodb.com/developer/products/mongodb/cheat-sheet/) for common commands.

### Install Python3 and Dependencies

You could install from [here](https://www.python.org/downloads/macos/), but I prefer installing from a package manager.

`brew install python@3.12`

If you already have python installed, check the version: `python3 -V`

[Setup a virtual environment](https://python.land/virtual-environments/virtualenv)

Create a virtual environment: `python3 -m venv venv`
Activate the virtual environment: `source venv/bin/activate`
Install dependencies via pip: `pip install pymongo python-decouple requests`