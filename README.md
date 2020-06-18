# email-alerts
Script to read Gmail inbox and send text message alerts for employer correspondence.

## Install dependencies
`python3 -m pip install -r requirements.txt`

## Usage
The EmailSearcher class is given keywords by the programmer
to search for. The code provided loads these keywords from an excel
file, but that's just an example. After creating the EmailSearcher
class with the right Gmail credentials, the script can be executed
with `python3 emails-alerts.py`. There's no specific reason that
Gmail was used. With some minor changes it should be able to
support other email providers.

## Security
This script was intended to be used for
automated cron jobs. That being said, 
storing your Gmail credentials in plaintext
is not a good idea. Consider, at the very least, locking the
script behind POSIX permissions.
