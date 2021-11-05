import sys

import email_searcher
import imessage_sender
import sms_sender


def send_alerts(login, password, number, carrier, keywords):
    # Get list of emails containing specific keywords
    matches = email_searcher.get_matching_emails(login, password, keywords)

    for keyword, sender, subject, text in matches:
        # Format message to be sent
        message = "From: {} **{}**\n".format(sender, keyword)
        message += "Subject: " + subject + "\n"
        message += text

        # OS X
        if sys.platform == "darwin":
            imessage_sender.send(number, message)
        # Windows / Linux
        else:
            sms_sender.send(login, password, carrier, number, message)
