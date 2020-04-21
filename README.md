# ClassroomResponse

Link: https://classroomresponsesystem.herokuapp.com/

## Server Setup local:

1. clone the repo
2. pip3 install -r requirements.txt
3. brew update
4. brew install redis
5. brew services start redis
6. cd classroom_response
7. python3 manage.py makemigrations classroom
8. python3 manage.py migrate classroom
9. http://localhost:8000/
**Note: you must have python 3.6.5**

# Deploying to Heroku:
Automatic deploys from this github are enabled. Just push to this repo the changes will be pushed to prod

## Key Features:
* Organize questions, quizzes, and classes
* Multiple choice and numeric questions
* Student Feedback on questions
* Websocket connection between professor and student
* Graphs to quickly analyze results of questions
* Download results of questions as a csv

## Test accounts:
If you want to dive right in, here are some already created logins
Teacher:
* email: teacher@google.com, password: pass

Student:
* email: student@google.com, password: pass
* email: student2@google.com, password: pass
* email: student3@google.com, password: pass
* email: student4@google.com, password: pass

## Baseline code: open sourced django starter
Originally we had started from scratch. Our custom authentiation system became messy quickly, so we decided to look at how other django users implemented authentication across multiple pages. We came across [this](https://github.com/sibtc/django-multiple-user-types-example/) code that used the decorator design pattern which was much cleaner than what we originally had. Because we like this example so much, we cloned it and used it as our baseline. The key file that this baseline contributed to our project is [decorators.py](https://github.com/jonghoonlee98/ClassroomResponse/blob/master/classroom_response/classroom/decorators.py). We also kept the existing CSS.

#Screenshots:
#### Adding a question page: Note the organizational hierarchy
![Add Question displaying organizational hierarchy](https://github.com/jonghoonlee98/ClassroomResponse/blob/master/Images/present_question.png)
#### What a student sees when answering a question
![What a student sees when answering a question](https://github.com/jonghoonlee98/ClassroomResponse/blob/master/Images/student_answer.png)
#### Professor can view results of multiple choice question
![What a professor sees when viewing the results of a multiple choice question](https://github.com/jonghoonlee98/ClassroomResponse/blob/master/Images/mc_result.png)
#### Professor can view results of a numeric question
![What a professor sees when viewing the results of a numeric question](https://github.com/jonghoonlee98/ClassroomResponse/blob/master/Images/numeric_result.png)


