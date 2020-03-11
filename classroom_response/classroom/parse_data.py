import json

from django.core import serializers
from classroom.models import *

def parse_MC(question):
    answers = Answer.objects.filter(question = question)
    answer = None
    if len(answers):
    	data = json.loads(answers[0].data)
    	answer = data['answer']
    	for a in answer:
    		del a['is_correct']
    send_data = {
        'type': 'present',
        'question_type': 'MC',
        'text': question.text,
        'latex': question.latex,
        'answers': answer,
        'question_pk': question.pk
    }
    return send_data

def parse_NU(question):
    answers = Answer.objects.filter(question = question)
    units = None
    if len(answers):
        data = json.loads(answers[0].data)
        answer = data['answer']
        if 'units' in data:
            units = data['units']
    send_data = {
        'type': 'present',
        'question_type': 'NU',
        'text': question.text,
        'latex': question.latex,
        'units': units,
        'question_pk': question.pk
    }
    return send_data