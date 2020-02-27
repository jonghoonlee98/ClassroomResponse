from channels import Group
from classroom.models import *
import threading
import random
import json
 
 
def ws_message(message):
    data = json.loads(message.content['text'])
    print(data)
    if (data['type'] == 'present'):
        question_pk = data['question_pk']
        question = Question.objects.get(pk=question_pk)
        send_data = {
            'type': 'present',
            'text': question.text,
            'course_pk': data['course_pk']
        }
        Group('classroom').send({'text':json.dumps(send_data)})

 
def ws_connect(message):
    Group('classroom').add(message.reply_channel)
    send_data = {
        'type:': 'connected'
    }
    Group('classroom').send({'text':json.dumps(send_data)})
 
 
def ws_disconnect(message):
    send_data = {
        'type:': 'disconnected'
    }
    Group('classroom').send({'text':json.dumps(send_data)})
    Group('classroom').discard(message.reply_channel)