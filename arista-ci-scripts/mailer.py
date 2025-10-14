#!/usr/bin/python3

import os
import sys
import argparse
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

parser = argparse.ArgumentParser(
    description="This script takes in arguments to send an email"
)
parser.add_argument(
    "--mail_to", help="Comma-separated list of email addresses", required=True
)
parser.add_argument("--subject", help="Subject of the mail", required=True)
parser.add_argument("--body", help="Body of the mail")
parser.add_argument("--body_text_file", help="text file that contains Body of the mail")
parser.add_argument(
    "--sender_mail_id",
    help="Username of gmail account used to send mail",
    required=True,
)
parser.add_argument(
    "--sender_mail_password",
    help="Password of gmail account used to send mail",
    required=True,
)
parser.add_argument(
    "--attachment_path", help="File path of the attachment", required=False
)
args = parser.parse_args()


def mail(to, subject, body, mail_id, mail_password, attachment_path=None):
    recipients = [m.strip() for m in to.split(",")]
    file_path = attachment_path
    msg = MIMEMultipart()
    from_address = "srv-openbmc-robot@arista.com"
    msg["From"] = from_address
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    body = body
    msg.attach(MIMEText(body, "plain"))
    p = MIMEBase("application", "octet-stream")
    if attachment_path:
        try:
            attachment = open(file_path, "rb")
            p.set_payload((attachment).read())

            encoders.encode_base64(p)
            p.add_header(
                "Content-Disposition",
                "attachment; filename= %s" % os.path.basename(file_path),
            )

        except IOError:
            print("IOError when attaching file")
    msg.attach(p)
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.ehlo()
    s.starttls()
    s.login(mail_id, mail_password)
    s.sendmail(from_address, recipients, msg.as_string())
    s.quit()

if __name__ == "__main__":
    if not args.body_text_file and not args.body:
        sys.exit("--body argument missing. Either --body_text_file or --body is required")

    email_body = ""
    if args.body_text_file:
        with open( args.body_text_file, "r" ) as f:
            email_body = f.read()
    else:
        email_body = args.body

    mail(
        args.mail_to,
        args.subject,
        email_body,
        args.sender_mail_id,
        args.sender_mail_password,
        attachment_path=args.attachment_path,
    )
