
import yaml

import urllib
import flickrapi
import os
import sys
import random
import urllib2
import smtplib
import logging


# Here are the email package modules we'll need
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from twython import Twython

# config vals
gmail_user_name = ""
gmail_pass_word = ""
global flickr_api_key
global flickr_api_secret
tumblr_email = ""
url_template = 'http://farm%(farm_id)s.staticflickr.com/%(server_id)s/%(photo_id)s_%(secret)s.jpg'
random_word = ""
api_key = ""
api_secret = ""
oauth_token = ""
oauth_token_secret = ""


logging.basicConfig(filename='C:\Users\Administrator\Documents\GitHub\HourlyArt\hourlyArt.log',level=logging.DEBUG)

# For scope - I had to move the assignment of the yaml variables to here from loadConfigs()
f = open("app.yaml", 'r+')
datamap = yaml.load(f)
#f.close()
    
gmail_user_name = datamap['gmail_user_name']
gmail_pass_word = datamap['gmail_user_pass']
flickr_api_key = datamap['flickr_api_key']
print flickr_api_key
flickr_api_secret = datamap['flickr_api_secret']
print flickr_api_secret
tumblr_email = datamap['tumblr_email']
post_number = datamap['post_number']
processing_location = datamap['processing_location']
api_key = datamap['api_key']
api_secret = datamap['api_secret']
oauth_token = datamap['oauth_token']
oauth_token_secret = datamap['oauth_token_secret']

# close file - then reopen for writing
f.close()

f = open("app.yaml", 'w+')
#datamap = yaml.load(f)

# update post_number
post_number += 1
datamap['post_number'] = post_number

yaml.dump( datamap, f, default_flow_style=False )
f.close()

def loadConfig():
    """
    Yaml should look like this:
        flickr_api_key:
            api_key_numbers
        flickr_api_secret:
            api_secret_key

        tumblr_email:
            blogEmail@tumblr.com

        gmail_user_name:
            your email
        gmail_user_pass:
            your email pass
        post_number: 
            51
        processing_location: 
            location_of_processing_file            
    """

#Upload to Twitter
def uploadTwitter( random_word):
    twitter = Twython(api_key, api_secret,
                      oauth_token, oauth_token_secret)
     
    twitter.verify_credentials()
    #photo = open('C:\Users\Samuel Harper\Documents\GitHub\HourlyArt\HourlyArt\newImage\newImageChanged.jpg', 'rb')
    photo = open('HourlyArt/newImage/newImageChanged.jpg', 'rb')
    twitter.update_status_with_media(status='HourlyArt Post#' + str(post_number) + ' #' + random_word + ' #generative #generative art', media=photo)
    
#Get a random word
def getWord():
    response = urllib2.urlopen('http://randomword.setgetgo.com/get.php')
    #response = urllib2.urlopen('http://watchout4snakes.com/wo4snakes/Random/RandomWord')
    #print response.read()
    random_word = response.read()
    #print "random word: ", random_word
    return random_word

    

# get the image from Flickr
def getImage(random_word):
    # gets this image - need to randomize which image it uses
    #print flickr_api_key, " ", flickr_api_secret
    flickr = flickrapi.FlickrAPI(flickr_api_key, flickr_api_secret)
    print "word now: ", random_word
    # often this word generator gives words that don't match flickr - need to keep trying until it does
    # need to clean this up - but right now it works
    work = False
    while work == False:
        try:
            url =  url_for_photo(random.choice(flickr.photos_search(text=random_word, per_page=2)[0]))
            print "Found a word: " + random_word
            #logging.debug('Found a word')
            work = True
            break
        except Exception, e:
            print "Finding exception: ", e
            work = False
            print "Didn't find anything"
            #getImage(getWord())
            random_word = getWord()
        else:
            work = True
            break
            
    work = True        
        
    #url = url_for_photo(random.choice(flickr.photos.getRecent()[0]))
    #url = url_for_photo(random.choice(flickr._flickr_call(method='flickr.photos.getRecent', format='rest')))
    
    # Download the image:
    filename = None
    print 'Downloading %s' % url
    filein = urllib2.urlopen(url)
    try:
        image = filein.read(5000000)
    except Exception, e:
        print "Downloading error: " , e
    except MemoryError: # I sometimes get this exception. Why ?
        return None
        
    filein.close()
        # Check it.
    if len(image)==0:
        return None  # Sometimes flickr returns nothing.
    if len(image)==5000000:
        return None  # Image too big. Discard it.        
    if image.startswith('GIF89a'):
        return None # "This image is not available" image.
    
    # Save to disk.
    if not filename:
        filename = 'newImage/newImage.jpg' #url[url.rindex('/')+1:]
    fileout = open(filename,'w+b')
    fileout.write(image)
    fileout.close()
    
    return random_word
# start the processing job
# need to change director for the local server - will put into a yaml file
def startProcessing(processing_location):
    logging.debug('Start processing')
    #os.system("processing-java --sketch=..\..\..\..\GitHub\HourlyArt\HourlyArt --output=..\..\..\..\GitHub\HourlyArt\HourlyArtBuild --force --run")    
    os.system("processing-java --sketch=" + processing_location + " --output=" + processing_location + "\HourlyArtBuild --force --run")    
    #os.system("processing-java --sketch=c:\Users\Administrator\Documents\GitHub\HourlyArt\HourlyArt --output=c:\Users\Administrator\Documents\GitHub\HourlyArt\HourlyArtBuild --force --run")
    logging.debug('End processing')

# email this to tumblr
def emailTumblr(gmail_user_name, gmail_pass_word, random_word ):
  # now send the email to Tumblr
    # email set up
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()

    #Next, log in to the server
    #print "user: ", gmail_user_name
    #print "pass: ", gmail_pass_word
    server.login(gmail_user_name, gmail_pass_word)   
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'HourlyArt Post #' + str(post_number)
    me = gmail_user_name
    msg['From'] = me
    msg['To'] = tumblr_email
    tags = '#hourlyart #generative #generativeart #art #artistsontumblr #' + random_word.rstrip()
    msg.preamble = tags
    print tags
    print msg['Subject']

    img = MIMEImage(open('HourlyArt/newImage/newImageChanged.jpg',"rb").read(), _subtype="jpeg")
    img.add_header('Content-Disposition', 'attachment; filename="newImageChanged.jpg"')
    msg.attach(img)
    
    server.sendmail(me, tumblr_email, msg.as_string())
    server.quit()    

def url_for_photo(p):
    return url_template % {
        'server_id': p.get('server'),
        'farm_id': p.get('farm'),
        'photo_id': p.get('id'),
        'secret': p.get('secret'),
    }
    
def main():
    print( 'main')
    #print "Before ", flickr_api_key
    loadConfig()
    print "After ", flickr_api_key
    #getWord()
    random_word = getWord()
    print "Word ", random_word
    random_word = getImage(random_word)
    startProcessing(processing_location)
    emailTumblr(gmail_user_name, gmail_pass_word, random_word)
    uploadTwitter(random_word)

    
if __name__ == '__main__':
    main()
    