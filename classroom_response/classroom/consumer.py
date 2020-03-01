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
        course_name = data['course_name']
        question = Question.objects.get(pk=question_pk)
        send_data = {
            'type': 'present',
            'text': question.text,
            'course_pk': data['course_pk'],
            'course_name': course_name
        }
        Group(message.content['path'].split('/')[-2]).send({'text':json.dumps(send_data)})

 
def ws_connect(message):
    print('ws_connect')
    print(message.content['path'].split('/')[-2]);
    Group(message.content['path'].split('/')[-2]).add(message.reply_channel)
    send_data = {
        'type:': 'connected'
    }
    Group(message.content['path'].split('/')[-2]).send({'text':json.dumps(send_data)})
 
 
def ws_disconnect(message):
    send_data = {
        'type:': 'disconnected'
    }
    print("closed")
    Group(message.content['path'].split('/')[-2]).send({'text':json.dumps(send_data)})
    Group(message.content['path'].split('/')[-2]).discard(message.reply_channel)