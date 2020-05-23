import os			# Operating system
import glob			# used for file searching
import picamera			# camera module
import RPi.GPIO as GPIO		# General Purpose Input Ouput for PI sensor
import smtplib			# Used for sending email
import time			# time commands
import requests			# http requests - used for App notifocation
import dropbox			# used for dropbox
import nexmo			# used for sms

from time import sleep		# for sleep between detection

# MIME - Used for sending attachments in email based on intermnet standard
# Using MIME to attach the image of intruder

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders


######  THIS SECTION CONTAINS ALL THE CONFIG RELATED TO NOTIFICATIONS #########

# Mail config
mail_sender = '**********'
mail_password = '*******'
mail_receiver = '*************'

# SMS config
sms_key='*****'
sms_secret='********'
sms_from='****'
sms_to='********'

# DropBox config
DROPBOX_APP_ACCESS_TOKEN = '*********************'

#  App Notification config - Pushbullet
IFTTT_API_TOKEN = '******************'
IFTTT_APP_NAME='***********'	# change if the app name is different

#######################  END OF CONFIG ######################################


# set the directory (relative to the current directory) where the images are captured
IMAGE_DIR = './images/'


# GPIO Config
GPIO.setwarnings(False)		# disable warnings
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)		# Pin for PI sensor


# Function to get the name of the next image file
def get_filename():
	# Create image directory if does not exist
	if not os.path.exists(IMAGE_DIR):
		os.makedirs(IMAGE_DIR)

	# Look for files of pattern 'image[d][d][d][d]'.jpg - Can have upto 9999 files
	# Get an ordered list of files based  on the criteria
	file_list = sorted(glob.glob(os.path.join(IMAGE_DIR + 'image[0-9][0-9][0-9][0-9].jpg')))

	# getting the last file number by getting the last filename and increment it to get the name of next file
	# get 4 digits from 8th position from the right in filename
	# e.g.,  if image0000.jpg -> 0000  and adding 1 gives 0001

	start_pos=8		# requires a change iof file naming is changed
	nbr_of_char=4

	file_count=0
	if len(file_list) > 0:
		file_count = int(file_list[-1][-start_pos:-nbr_of_char])+1

	# geting the new filename
	filename = os.path.join(IMAGE_DIR + 'image' + '%04d.jpg' % file_count)

	return filename


# Function to capture the image of the intruder when detected
def capture_image(filename):
	with picamera.PiCamera() as camera:
		camera.resolution=(1920,1080)		# set image resolution
		camera.annotate_text='INTRUDER!!'	# annotate text
		camera.annotate_text_size=100		# text size, makking it bigger (default of 40)
		camera.capture(filename)		# capture the image


# Function to send email
def send_mail(filename):
	print 'Sending email with the attachment'

	msg = MIMEMultipart()
	msg['From'] = mail_sender
	msg['To'] = mail_receiver
	msg['Subject'] = 'INTRUDER Movement detected'

	# standard config for emailing with attachment
	body = 'INTRUDER Picture is attached'
	msg.attach(MIMEText(body, 'plain'))
	attachment = open(filename, 'rb')
	part = MIMEBase('application', 'octet-stream')
	part.set_payload((attachment).read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', 'attachment; filename=%s' % filename)
	msg.attach(part)
	server = smtplib.SMTP('smtp.gmail.com', 587)	# Gmail SMTP port is 587
	server.starttls()
	server.login(mail_sender, mail_password)
	text = msg.as_string()
	server.sendmail(mail_sender, mail_receiver, text)
	server.quit()


# Functiion to send SMS message
def send_sms():
	print "Sending SMS message"

	client=nexmo.Client(key=sms_key,secret=sms_secret)	# connect to the client library
	responseData=client.send_message ({			# client API to send message
	"from": sms_from,
	"to": sms_to,
	"text": "An INTRUDER has been detected!!",
	})

	if responseData["messages"][0]["status"] == "0":
		print ("Message sent successfully")
	else:
		print ("Message failed with error: {responseData['messages'][0]['error-text']}") 


# Function to send App notification on phone
def send_app_notification():
	print "Sending PushBullet Notification on Phone"
	post_string = "https://maker.ifttt.com/trigger/" + IFTTT_APP_NAME + "/with/key/" + IFTTT_API_TOKEN	# HTTP POST
	r=requests.post(post_string, params={"value1":"none","value2":"none","value3":"none"})	#  other parameters are set blank

# Function to upload file to Dropbox
def upload_to_dropbox(filename):
	print "Uploading image to Dropbox"
	main_dbx = dropbox.Dropbox(DROPBOX_APP_ACCESS_TOKEN)
	data_file = open(filename, 'rb')
	data = data_file.read()
	head, tail = os.path.split(filename)	# Get the filename correct for Drobox
	db_filename="/"+tail

	try:
        	main_dbx.files_upload(data,db_filename,dropbox.files.WriteMode.overwrite)
	except:
	       	print time.strftime('%d/%m/%y %H:%M:%S: ', time.localtime(time.time())) + 'Dropbox files_upload exception'

	data_file.close()


#  Main function

while True:
	i = GPIO.input(11)	#  PI sensor input, read  pin 11 of GPIO

	# No voltage detected
	if i == 0:
		print "NO intruders detected"
		sleep(2)

	# voltage detected
	elif i == 1:
		print "INTRUDER DETECTED!!"

		fn=get_filename()		# call function to get the filename of the image file to write to
		capture_image(fn)		# call function to capture image using the camera
		send_mail(fn)			# call function to send email
		send_sms()			# call function to send sms
		send_app_notification()		# call function to send app notification
		upload_to_dropbox(fn)		# call function to to upload image file to dropbox
