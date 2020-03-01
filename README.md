# ClassroomResponse

How to run the application:

1. clone the repo
2. pip3 install -r requirements.txt
3. brew update
4. brew install redis
5. brew services start redis
6. python3 manage.py makemigrations classroom
7. python3 manage.py migrate classroom




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

**BLOCKED, NOT COMMITTED "present question to late student (Bug Fix)"** -- Roy
* Implementation: 
	* when student joins after professor presses present button, they can't see the question.
	* added a hash map that stores course_name -> question_text in consumer.py
		* ***removing a course_name -> question_text pair after professor disconnect not implemented**
	* ***BLOCK: msg['course_pk'] == {{ course.pk }} in course.html has to go off for this to be pushed***
		* How I am implementing this is, if the map contains the course_name, I send the question json to the socket in ws_connect, bypassing waiting for ws_message from professor
* Test:
	* After stevie pressed the 'present' button, jlee01, late to class, should see the question. 

