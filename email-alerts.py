#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 16:44:53 2020

@author: Carlos A. McNulty
"""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas
import string
import base64
import lxml.html
from lxml import etree
from lxml.html.clean import Cleaner
import quopri
import re

class EmailSearcher:
  
  # SMS gateways for U.S. carriers
  sms_gateways = {"att":"txt.att.net",
             "boost mobile": "sms.myboostmobile.com",
             "cricket wireless":"mms.cricketwireless.net",
             "metro pcs": "mymetropcs.com",
             "sprint": "messaging.sprintpcs.com",
             "us cellular": "email.uscc.net",
             "verizon wireless": "vtext.com",
             "virgin mobile": "vmobl.com"}
  
  
  
  def __init__(self, keywords, login, password, number, carrier):
    self.login = login
    self.password = password
    self.keywords = keywords
    self.number = number
    self.carrier = carrier
 
  
  def decode_header(self, header):
    
    decoded_parts = email.header.decode_header(header)
    
    if len(decoded_parts) > 0:
      # Only decode first part of header
      decoded, charset = decoded_parts[0]
      
      # Check for utf-8 encoding
      if charset != None:
        # Decode header
        decoded = decoded.decode(charset)
      return decoded
    
    return ""
 
  
  def get_text(self, msg):
    
    cleaner = Cleaner()
    cleaner.javascript = True # Remove script tags
    cleaner.style = True # Remove css

    body = ""
    for part in msg.walk():
      # Check mime type for text
      if part.get_content_maintype() == "text":
        body += part.get_payload()

    # Get the transfer encoding used
    transfer_encoding = msg.get("Content-transfer-encoding")      
    if transfer_encoding:
      # Decode transfer encoding header
      transfer_encoding = self.decode_header(transfer_encoding)
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
  
  
  def get_match(self, text):
    
    match_counts = []
    
    for keyword in self.keywords:
      
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
  
  
  def get_msg_match(self, sender, subject, text):
    
    from collections import defaultdict 
    
    # All matches for email
    matches = defaultdict(int) 
    
    # Get matches from parts of email
    for s in [sender, subject, text]:
      match = self.get_match(s)
      if match != None:
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
  
  
  def search_inbox(self):
 
    # Helper function to remove punctuation
    def clean(s):
      return s.translate(str.maketrans("","", string.punctuation))
    
    # Create imap session
    imap_server = "imap.gmail.com"
    port = 993 # SSL port
    imap = imaplib.IMAP4_SSL(imap_server, port)
    
    # Login to server
    imap.login(self.login, self.password)
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
              sender = self.decode_header(msg.get("from", ""))
              subject = self.decode_header(msg.get("subject", ""))

              # Get body from email
              text = self.get_text(msg)
              
              # Check for matches in sender, subject, and body
              match = self.get_msg_match(clean(sender), clean(subject), text)
              if match != None:
                keyword, count = match
                sms_message = "From: {} **{}**\n".format(sender, keyword)
                sms_message += "Subject: " + subject +"\n"
                self.send_sms(sms_message)
    
    imap.logout()
  
  
  def send_sms(self, message):
    
    # Create smtp session
    smtp_server = "smtp.gmail.com"
    port = 587 # TLS port
    
    smtp = smtplib.SMTP(smtp_server, port)
    smtp.ehlo()
    # Start smtp in TLS mode
    smtp.starttls()
    smtp.ehlo()
    
    # Login to server
    smtp.login(self.login, self.password)
    
    # Remove punctuation from carrier
    carrier_key = self.carrier.translate(str.maketrans("","", string.punctuation))
    
    # Get domain of sms gateway
    domain = self.sms_gateways.get(carrier_key)
    if domain != None:
      # Append sms gateway domain to number
      receiver = "{}@{}".format(self.number,domain)
      
      # Structure message
      msg = MIMEMultipart()
      msg["From"] = self.login
      msg["To"] = receiver
      
      # Add body of message
      msg.attach(MIMEText(message, "plain"))
      
      # Send message to email server
      smtp.sendmail(self.login, receiver, msg.as_string())
       
      # Quit the server
      smtp.quit()
  


def clean_company_name(name):
  
  # Convert name to lowercase
  name = name.lower()
  
  # Remove punctuation from name
  name = name.translate(str.maketrans("","", string.punctuation))
  
  # Remove 'inc' and 'llc' from name
  name = name.replace("inc", "").replace("llc", "").strip()
  
  return name
 

def decode_base64(base64_message, encoding):
  
  # Decode base64 messages
  base64_bytes = base64_message.encode(encoding)
  message_bytes = base64.b64decode(base64_bytes)
  decoded = message_bytes.decode(encoding)
  return decoded


if __name__ == "__main__":

  login="GMAIL LOGIN"
  
  # Decode base64 encoded baseword (for shoulder creeps)  
  password = decode_base64("BASE 64 ENCODED GMAIL PASSWORD", "ascii")  

  # Get names of all companies with pending applications
  names = ["state farm", "google", "bitwise"]
  
  a = EmailSearcher(names, login, password, "PHONE #", "CARRIER")
  # Search inbox for matching company names
  a.search_inbox()  
