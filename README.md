# family_phone_bill_automation

This repository contains a Python script that parses T-Mobile bills and sends a summary email to a designated recipient. The script uses the imaplib library to connect to an IMAP email server, retrieve the latest bill email, and extract the relevant information. The extracted data is then used to generate a summary email, which is sent using the smtplib library.

## How to
1. Get the gmail app password
   a) Go to gmail settings and Enable IMAP.
   b) Go to google account settings and get the app password. (only available after switching on 2-factor authentication)
2. Fill in the configs with the email addresses you care about

Now you can either download docker and build and run a docker image or simply create a virtual environment and install the relevant libraries in the requirements.txt file and then run the main.py file. 

## Components
The repository includes the following components:

- configs.yml: A YAML configuration file that stores sensitive information such as email credentials and API keys.
- get_bill_from_email.py: This script logs in to your email and finds the tmobile bill email and downloads the attachment.
- analyze_bill.py: This script converts the bill summary table on the second image into an image and parses text from the image. It then formats the
text as a pandas dataframe and performs the operations to summarize the bill.
- send_summary_email.py: The final Python script that sends the summary email to the recipient.
- main.py: Entrypoint to the app which calls all of the above scripts.

## Considerations
I hosted this app on a free online python cloud compute platform like [pythonanywhere.com](https://www.pythonanywhere.com/), and made it to run chronologically every month. It makes it easy to split the bill.
The repository is designed to be used with a T-Mobile bill email that has the standard bill as an attachment (see the mock bill in the attachments folder), and may require modifications to work with other types of emails.

## Shout outs
If you want to learn follow these videos/channels to do more such automation. 
[Gmail + python](https://youtu.be/K21BSZPFIjQ?si=1RTgdKi8G3R6Mo76)
[Python Anywhere tutorial](https://youtu.be/0G8bjcY4lBM?si=CVgiiHVA4V3Q1toW)







