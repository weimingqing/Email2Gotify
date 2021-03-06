#!/usr/bin/python3
from settings import *
import email

while True:
    imap = IMAP4_SSL(host=url, ssl_context=context)
    print("Logging into mailbox...")
    retcode, d = imap.login(user, password)
    assert retcode == 'OK', 'login failed'
    print(f"Select folder: {folder}.")
    imap.select(folder)
    while True:
        try:
            retcode, messages = imap.search(None, '(UNSEEN)')
            assert retcode == 'OK', 'search messages failed'
            uids = messages[0].split()
            print(f"Found new mail(s) in folder: {uids}")
            for i in uids:
                typ, data = imap.fetch(i, '(RFC822)')
                encodes = ['utf-8', 'GB2312', 'US-ASCII']
                for encode in encodes:
                    try:
                        message = email.message_from_string(data[0][1].decode(encode))
                    except:
                        print(f"Cannot decode with {encode}")
                    else:
                        messageEncoding = encode
                        break
                if not messageEncoding:
                    raise Exception('No encoding can decode the message')
                subject = message['Subject']
                date = email.utils.parsedate_to_datetime(message['Date']) if message['Date'] else None
                sender = email.utils.parseaddr(message['From'])[1]
                receivers = email.utils.parseaddr(message['To'])[1]
                header, encoding = email.header.decode_header(subject)[0]
                if encoding:
                    subject = header.decode(encoding)                
                if message['CC']:
                    carboncopy = [email.utils.parseaddr(i)[1] for i in message['CC'].split(',')]
                else:
                    carboncopy = None

                print("A mail received:")
                print(f"Subject:   {subject}")
                print(f"Date:      {date}")
                print(f"Sender:    {sender}")
                print(f"Receivers: {receivers}")
                print(f"CC:        {carboncopy}")    

                for part in message.walk():
                    if part.is_multipart():
                        filename = part.get_filename()  # attachment file name
                        if filename:
                            filename, encoding = email.header.decode_header(filename)[0]
                            if encoding:
                                filename = filename.decode(encoding)
                            # sample code if downloading attachment
                            # data = part.get_payload(decode=True)
                            # f = open(filename, 'wb')
                            # f.write(data)
                            # f.close()
                    else:
                        if part.get_content_subtype() == 'plain':
                            content = part.get_payload(decode=True).decode(part.get_content_charset())
                        elif part.get_content_subtype() == 'html':
                            content = part.get_payload(decode=True).decode(part.get_content_charset())
                        else:
                            content = "unknown content type"

                # push message to Gotify
                title = "{0}{1}".format(msgprefix,subject)
                resp = requests.post(
                    gotifyurl,
                    headers=headers,
                    data={
                        'title': title,
                        'message': {content},
                        'priority': 5})
                if (resp.status_code != 200):
                    print(f"Gotify message was not successfully sent: {resp}")
                else:
                    print("Gotify message is sent for the mail successfully.")
                # mark mail as Read so it won't be pushed to Gotify again
                imap.store(i, '+FLAGS', '\Seen')
        except Exception as e:
            print(f"Got exception: {e}.")
            if infiniteloop:
                print("Wait and trying to re-establish connection...")
                time.sleep(60)
            break
        else:
            if (not infiniteloop): 
                break
            else:
                print("Sleep 60 seconds...")
                time.sleep(60)
    if (not infiniteloop): 
        break
print("Logging out mailbox...")
imap.close()
imap.logout()
