from channels import Group
from classroom.models import *
import threading
import random
 
def sendmsg(num):
    Group('classroom').send({'text':num})
 
t = 0
 
def periodic():
    global t;
    n = random.randint(10,200);
    sendmsg(str(n))
    t = threading.Timer(5, periodic)
    t.start()
 
def ws_message(message):
    global t
    print(message.content['text'])
    if ( message.content['text'] == 'start'):
        periodic()
    elif ( message.content['text'].startswith('present')):
        question_pk = message.content['text'].split("present")[1]
        print(question_pk)
        question = Question.objects.get(pk=question_pk)
        Group('classroom').send({'text':question.text})
    else:
        t.cancel()
 
def ws_connect(message):
    Group('classroom').add(message.reply_channel)
    Group('classroom').send({'text':'connected'})
 
 
def ws_disconnect(message):
    Group('classroom').send({'text':'disconnected'})
    Group('classroom').discard(message.reply_channel)