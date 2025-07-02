# family_phone_bill_automation

### What is this

Learn more [here](https://asadhusain97.github.io/projects/mobilefamilybill.html)

This repository contains a Python script that parses T-Mobile bills and sends a summary email to a designated recipient. The repository is designed to be used with an email having a specific subject line and sent from a specific email address that has the standard bill as an attachment (see the mock bill in the attachments folder) and the summary email is then sent to the specified emails. It runs every 30 mins automatically through github actions and can run for limited number of times per day (set as 1 for now).

### How I use it

I get the bill from the T-mobile app and send it to the receiving email address (asadeveloper10) with the specific subject (stock) and then wait. Every day at 12, the cron job runs and I get back the summary result for splitting the bill in the set email addresses.

### How is this made

The script uses the imaplib library to connect to an IMAP email server, retrieve the latest bill email, and extract the relevant information. The extracted data is then used to generate a summary email, which is sent using the smtplib library.

## How to

1. Get the gmail app password
   a) Go to gmail settings and Enable IMAP.
   b) Go to google account settings and get the app password. (only available after switching on 2-factor authentication)
2. Make the .env file with the password, numbers, and emails addresses you care about
3. Modify the config if necessary

Now you can simply create a virtual environment with requirements.txt file and then run the main.py file to test.
Follow the tutorials linked below to set it up automatically using any free tool.

## Components

The repository includes the following components:

- configs.yml: A YAML configuration file that stores sensitive information such as email credentials and API keys.
- get_bill_from_email.py: This script logs in to your email and finds the tmobile bill email and downloads the attachment.
- analyze_bill.py: This script converts the bill summary table on the second page into text. It then formats the text as a pandas dataframe and performs the operations to summarize the bill.
- send_summary_email.py: The final Python script that sends the summary email to the recipient.
- main.py: Entrypoint to the app which calls all of the above scripts.

## Considerations

I hosted this app on a free online python cloud compute platform like Github Actions or [pythonanywhere.com](https://www.pythonanywhere.com/). It makes it easy to split the bill.
Make sure to check the env, config, and actions file before adapting this.

## Shout outs

If you want to learn follow these videos/channels to do more such automation.

- [Gmail + python](https://youtu.be/K21BSZPFIjQ?si=1RTgdKi8G3R6Mo76)
- [Github Actions tutorial](https://youtu.be/PaGp7Vi5gfM?si=YlXAVeVIsx7hy3cR)
- [Python Anywhere tutorial](https://youtu.be/0G8bjcY4lBM?si=CVgiiHVA4V3Q1toW)
