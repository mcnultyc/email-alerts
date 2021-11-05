import smtplib
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send(login, password, carrier, number, message):
    # SMS gateways for U.S. carriers
    sms_gateways = {"att": "txt.att.net",
                    "boost mobile": "sms.myboostmobile.com",
                    "cricket wireless": "mms.cricketwireless.net",
                    "metro pcs": "mymetropcs.com",
                    "sprint": "messaging.sprintpcs.com",
                    "tmobile": "tmomail.net",
                    "us cellular": "email.uscc.net",
                    "verizon wireless": "vtext.com",
                    "virgin mobile": "vmobl.com"}

    # Create smtp session
    smtp_server = "smtp.gmail.com"
    port = 587  # TLS port

    smtp = smtplib.SMTP(smtp_server, port)
    smtp.ehlo()
    # Start smtp in TLS mode
    smtp.starttls()
    smtp.ehlo()

    # Login to server
    smtp.login(login, password)

    # Remove punctuation from carrier
    carrier_key = carrier.translate(str.maketrans("", "", string.punctuation))

    # Get domain of sms gateway
    domain = sms_gateways.get(carrier_key)

    if domain is not None:
        # Append sms gateway domain to number
        receiver = "{}@{}".format(number, domain)

        # Structure message
        msg = MIMEMultipart()
        msg["From"] = login
        msg["To"] = receiver
        msg["Subject"] = ""

        # Add body of message
        msg.attach(MIMEText(message, "plain"))

        # Send message to email server
        smtp.sendmail(login, receiver, msg.as_string())

        # Quit the server
        smtp.quit()
