from channels import Group
from classroom.models import *
import threading
import random
import json

from django.core import serializers

# Whatever's in this list is presented
presentedQuestionsMap = {}

def add_question(course, question):
    presentedQuestionsMap[course] = question

def delete_question(course):
    del presentedQuestionsMap[course]

# takes in a message and returns the class name.
# When a new socket is connected, the path variable is 
# 'ws://' + window.location.host + '/classroom/{{course_name}}/', 
# refer to course.html and question_view.html.
# This function extracts the course name from the path.
def get_coursecode(message):
    return message.content['path'].split('/')[-2]



 
def ws_message(message):
    data = json.loads(message.content['text'])
    if (data['type'] == 'present'):
        question_pk = data['question_pk']
        course_name = data['course_name']
        question = Question.objects.get(pk=question_pk)
        if question.question_type == 'MC':
            answers = Answer.objects.filter(question = question)
            send_data = {
                'type': 'present',
                'question_type': 'MC',
                'text': question.text,
                'course_pk': data['course_pk'],
                'answers': serializers.serialize('json', answers)
            }
            # adding the course from presentedQuestionsMap once professor presses present
            add_question(data['course_pk'], send_data)
            Group(get_coursecode(message)).send({'text':json.dumps(send_data)})
    # stop response for both professor and client
    elif (data['type'] == 'stop'):
        question_pk = data['question_pk']
        question = Question.objects.get(pk=question_pk)
        send_data = {
            'type': 'stop',
            'text': question.text,
            'course_pk': data['course_pk'],
        }
        # removing the course from presentedQuestionsMap once professor presses stop
        delete_question(data['course_pk'])
        Group(get_coursecode(message)).send({'text':json.dumps(send_data)})
    # student sending answer to professor
    elif (data['type'] == 'answer'):
        send_data = {
            'type': 'answer',
            'name': data['name'],
            'answer': data['answer'],
        }
        Group(get_coursecode(message)).send({'text':json.dumps(send_data)})

 
def ws_connect(message):
    course_code = get_coursecode(message)
    Group(course_code).add(message.reply_channel)
    send_data = {}
    # handling case where student joins the class late
    if int(course_code) in presentedQuestionsMap:        
        send_data = presentedQuestionsMap[int(course_code)]
    else:        
        send_data['type'] = 'professorStop'
    Group(course_code).send({'text':json.dumps(send_data)})

 
def ws_disconnect(message):
    send_data = {
        'type': 'disconnected'
    }
    Group(get_coursecode(message)).send({'text':json.dumps(send_data)})
    Group(get_coursecode(message)).discard(message.reply_channel)