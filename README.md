# ClassroomResponse

## Server Setup:

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

## Test accounts:
If you want to dive right in, here are some already created logins
Teacher:
* email: teacher@google.com, password: pass

Student:
* email: student@google.com, password: pass
* email: student2@google.com, password: pass

## Baseline code: open sourced django starter
Originally we had started from scratch. Our custom authentiation system became messy quickly, so we decided to look at how other django users implemented authentication across multiple pages. We came across [this](https://github.com/sibtc/django-multiple-user-types-example/) code that used the decorator design pattern which was much cleaner than what we originally had. Because we like this example so much, we cloned it and used it as our baseline.

## Key Features:
* Organize questions, quizzes, and classes
* Multiple choice and numeric questions
* Student Feedback on questions
* Websocket connection between professor and student
* Graphs to quickly analyze results of questions
* Download results of questions as a csv

**Commit "adding groups by classname"** -- Roy
* Implementation:
	* when sockets connect, they are added to group based on their class name
		* example group name: message.content['path'] = /classroom/ES4/, then the group name is message.content['path'].split('/')[-2]. Refer to consumer.py
* Test:
	* created jlee01 and etu01 users, jlee01 is in ES4 and etu01 is in ES5
	* created steve who owns ES4 and ES5, and created a question for each class
	* had jlee01 and etu01 waiting for a page, 
	* when steve presented a question from ES4, jlee01 received json while etu01 did not.
* Resource: https://channels.readthedocs.io/en/latest/topics/consumers.html
	

**Commit "added student-side response to professor-side"** -- Roy
* Implementation: 
	* students send back answers by pressing submit button.
		* student sends "answer" type message to the professor
		* ***professor-side response seeing not implemented yet***
* Test:
	* when jlee01 pressed the 'submit' button, professor browser displayed student response on console

