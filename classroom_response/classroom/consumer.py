from channels import Group
from classroom.models import *
import threading
import random
import json

from django.core import serializers


# takes in a message and returns the class name.
# When a new socket is connected, the path variable is 
# 'ws://' + window.location.host + '/classroom/{{course_name}}/', 
# refer to course.html and question_view.html.
# This function extracts the course name from the path.
def get_classname(message):
    return message.content['path'].split('/')[-2]

 
def ws_message(message):
    data = json.loads(message.content['text'])
    print(data)
    if (data['type'] == 'present'):
        question_pk = data['question_pk']
        course_name = data['course_name']
        question = Question.objects.get(pk=question_pk)
        if question.question_type == 'MC':
            answers = Answer.objects.filter(question = question)
            print(answers)
            send_data = {
                'type': 'present',
                'question_type': 'MC',
                'text': question.text,
                'course_pk': data['course_pk'],
                'answers': serializers.serialize('json', answers)
            }
            Group(get_classname(message)).send({'text':json.dumps(send_data)})
    elif (data['type'] == 'stop'):
        question_pk = data['question_pk']
        question = Question.objects.get(pk=question_pk)
        send_data = {
            'type': 'stop',
            'text': question.text,
            'course_pk': data['course_pk'],
            'course_name': course_name
        }
        Group(get_classname(message)).send({'text':json.dumps(send_data)})
    elif (data['type'] == 'answer'):
        send_data = {
            'type': 'answer',
            'name': data['name'],
            'answer': 'TODO'
        }
        Group(get_classname(message)).send({'text':json.dumps(send_data)})

 
def ws_connect(message):
    Group(get_classname(message)).add(message.reply_channel)
    send_data = {
        'type:': 'connected'
    }
    Group(get_classname(message)).send({'text':json.dumps(send_data)})
 
 
def ws_disconnect(message):
    send_data = {
        'type:': 'disconnected'
    }
    Group(get_classname(message)).send({'text':json.dumps(send_data)})
    Group(get_classname(message)).discard(message.reply_channel)