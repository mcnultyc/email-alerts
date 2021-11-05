import base64
import email
import imaplib
import quopri
import re
import string

import lxml.html
from lxml import etree
from lxml.html.clean import Cleaner


def get_matching_emails(login, password, keywords):
    # Helper function to remove punctuation
    def clean(s):
        return s.translate(str.maketrans("", "", string.punctuation))

    matching_emails = []

    # Create imap session
    imap_server = "imap.gmail.com"
    port = 993  # SSL port
    imap = imaplib.IMAP4_SSL(imap_server, port)

    # Login to server
    imap.login(login, password)
    imap.select("inbox")

    # Search unseen emails from inbox
    search_code, data = imap.search(None, "(UNSEEN)")

    if search_code == "OK":

        for num in data[0].split():
            # Fetch email without setting \Seen flag
            fetch_code, fetch_data = imap.fetch(num, "(BODY.PEEK[])")

            if fetch_code == "OK":

                for segment in fetch_data:
                    if isinstance(segment, tuple):

                        # Convert string to email message
                        msg = email.message_from_bytes(segment[1])

                        # Get sender and subject
                        sender = decode_header(msg.get("from", ""))
                        subject = decode_header(msg.get("subject", ""))

                        # Get body from email
                        text = get_text(msg)

                        # Check for matches in sender, subject, and body
                        match = get_msg_match(keywords, clean(sender), clean(subject), text)
                        if match is not None:
                            keyword, count = match
                            matching_emails.append((keyword, sender, subject, text))

    imap.logout()
    return matching_emails


def decode_header(header):
    decoded_parts = email.header.decode_header(header)

    if len(decoded_parts) > 0:
        # Only decode first part of header
        decoded, charset = decoded_parts[0]

        # Check for utf-8 encoding
        if charset is not None:
            # Decode header
            decoded = decoded.decode(charset)
        return decoded

    return ""


def get_text(msg):
    cleaner = Cleaner()
    cleaner.javascript = True  # Remove script tags
    cleaner.style = True  # Remove css

    body = ""
    for part in msg.walk():
        # Check mime type for text
        if part.get_content_maintype() == "text":
            body += part.get_payload()

    # Get the transfer encoding used
    transfer_encoding = msg.get("Content-transfer-encoding")
    if transfer_encoding:
        # Decode transfer encoding header
        transfer_encoding = decode_header(transfer_encoding)
        if transfer_encoding.lower() == "base64":
            # Base64 transfer decoding
            body = base64.b64decode(body)

            # Quoted-printable transfer decoding
    html = quopri.decodestring(body).decode("utf-8", "ignore")

    # Check if body is empty
    if html.strip() != "":
        # Create document from html
        document = lxml.html.document_fromstring(html)

        # Clean html and get text
        text = "\n".join(etree.XPath("//text()")(cleaner.clean_html(document)))
        # Remove blank lines from text
        text = "\n".join(filter(lambda x: not re.match(r'^\s*$', x), text.splitlines()))

        return text

    return ""


def get_match(keywords, text):
    match_counts = []

    for keyword in keywords:

        # Create regex pattern used for matching
        pattern = r'\b{}\b'.format(keyword)

        # Get matches for keyword
        matches = re.findall(pattern, text, re.IGNORECASE)

        if len(matches) > 0:
            # Add keyword and # of matches to list
            match_counts.append((keyword, len(matches)))

    if len(match_counts) > 0:

        # Get the keyword with the most matches
        keyword, count = match_counts[0]
        for k, c in match_counts:
            if c > count:
                keyword = k
                count = c

        return keyword, count

    return None


def get_msg_match(keywords, sender, subject, text):
    from collections import defaultdict

    # All matches for email
    matches = defaultdict(int)

    # Get matches from parts of email
    for s in [sender, subject, text]:
        match = get_match(keywords, s)
        if match is not None:
            keyword, count = match
            matches[keyword] += count

    if len(matches) > 0:
        # Get the keyword with most overall matches
        keyword = None
        count = 0
        for k, c in matches.items():
            if c > count:
                keyword = k
                count = c
        return keyword, count

    return None
