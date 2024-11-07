# Neptyne

Welcome to Neptyne, the Python based spreadsheet. Here's how to get up and running quickly.

### Method 1: Use docker

The easiest way to get started is to use the docker image. This will give you a fully functional Neptyne environment with all the bells and whistles.

```shell

docker-compose up -d

```

Only need to build it once. After that, you can just run `docker-compose up`.

### Method 2: pip install

In a clean Python 3.11 environment, run:

```shell
pip install neptyne
```

After which you can start neptyne with:
    
```shell
python -m neptyne
```

### Method 3: From source

You know the drill. Clone the repo, and run:

```shell
pip install -r requirements.txt
```

After which you can start neptyne with:
    
```shell
PYTHONPATH=. python server/application.py
```

## Using Neptyne with Google Sheets

Neptyne works as a standalone spreadsheet but can also be used in conjunction with Google Sheets.
To make this work, you'll need to first install the Neptyne GSheets Add-on. You can find it
[here](https://workspace.google.com/marketplace/app/neptyne_python_for_sheets/891309878867).

After installing, open the configure server menu and enter the shared secret that Neptyne
prints when it starts up. This will allow the GSheets Add-on to communicate with your Neptyne
instance. You also need to enter a publicly accessible URL for your Neptyne instance. If you
don't have a public URL, you can use a service like [ngrok](https://ngrok.com/) to create one.


## Authorizing GSheets

To talk to GSheets through the Python REPL, either use a service account credential file or an OAuth client config. For service accounts, make sure the sheet is shared with the account, and add the credential file to ~/.config/neptyne/service_account.json. For OAuth, add the credential file to ~/.config/neptyne/oauth_credentials.json.
