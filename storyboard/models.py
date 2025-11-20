
# Create your models here.


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
# -*- coding: utf-8 -*-



# Create your models here.
class Participant(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete = models.CASCADE, primary_key=True)
    conj_practice = models.CharField(max_length= 500, blank = True) # what tenses is user in conj practice mode for
    signform = models.BooleanField(default = False) 
    exclude = models.BooleanField(default = False) 
    share = models.BooleanField(default = False)
    updated_at = models.DateTimeField(auto_now = True, blank = True)
    group = models.CharField(max_length= 50, blank = True)
    def __unicode__(self):
        return 'id='+ str(self.pk)


class Section(models.Model):
    sectionname = models.CharField(max_length = 500, blank = True)
    totalnum = models.PositiveIntegerField(blank = True, default = 0)
    numberofquestions = models.PositiveIntegerField(blank = True, default = 0)
    numberofverbs = models.PositiveIntegerField(blank = True, default = 0)
    def __unicode__(self):
        return 'id='+ str(self.pk)


class Progress(models.Model):
    student = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, default = None, on_delete=models.CASCADE)
    question_order = models.CharField(max_length= 3000, blank = True)
    question_complete_list = models.CharField(max_length= 3000, blank = True)
    complete = models.BooleanField(default = False)
    score = models.PositiveIntegerField(default = 0, blank = True)
    numdone = models.PositiveIntegerField(default = 0, blank = True)
    trial = models.PositiveIntegerField(blank = True, default = 0)
    created_at = models.DateTimeField(auto_now_add= True, blank = True)
    updated_at = models.DateTimeField(auto_now = True, blank = True)

class VerbQuestion(models.Model):
    id = models.PositiveIntegerField(default = 0, blank = True, primary_key=True)
    sentence = models.CharField(max_length = 300000, blank = True)
    verb = models.CharField(max_length = 300000, blank = True)
    verb_type = models.CharField(max_length = 300000, blank = True)
    context = models.CharField(max_length = 300000, blank = True)
    tense_broad = models.CharField(max_length = 300000, blank = True)
    tense_specific = models.CharField(max_length = 300000, blank = True)
    subject = models.CharField(max_length = 300000, blank = True)
    subject_options = models.CharField(max_length = 300000, blank = True)
    subject_type = models.CharField(max_length = 300000, blank = True)
    formality = models.CharField(max_length = 300000, blank = True)
    gender_matter = models.CharField(max_length = 300000, blank = True)
    gender = models.CharField(max_length = 300000, blank = True)
    plurality = models.CharField(max_length = 300000, blank = True)
    conjugation = models.CharField(max_length = 300000, blank = True)

class VerbResponse(models.Model):
    id = models.PositiveIntegerField(default = 0, blank = True, primary_key=True)
    response = models.PositiveIntegerField(blank = True, default= 0)
    ans = models.CharField(max_length = 3000, blank = True)
    initial_ans_current = models.CharField(max_length = 3000, default="[]")
    tries = models.PositiveIntegerField(blank = True, default = 0)
    student = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    question = models.ForeignKey(VerbQuestion, default = None, on_delete=models.CASCADE)
    tense_broad = models.CharField(max_length = 300000, blank = True)
    tense_specific = models.CharField(max_length = 300000, blank = True)
    subject = models.CharField(max_length = 300000, blank = True)
    subject_type = models.CharField(max_length = 300000, blank = True)
    formality = models.CharField(max_length = 300000, blank = True)
    gender_matter = models.CharField(max_length = 300000, blank = True)
    gender = models.CharField(max_length = 300000, blank = True)
    plurality = models.CharField(max_length = 300000, blank = True)
    conjugation = models.CharField(max_length = 300000, blank = True)
    correct = models.BooleanField(blank = True, default = False)
    updated_at = models.DateTimeField(auto_now = True, blank = True)

class StructureQuestion(models.Model):
    id = models.PositiveIntegerField(default = 0, blank = True, primary_key=True)
    sentence = models.CharField(max_length = 300000, blank = True)
    context = models.CharField(max_length = 300000, blank = True)
    type = models.CharField(max_length = 300000, blank = True)
    subject_matter = models.CharField(max_length = 300000, blank = True)
    subject = models.CharField(max_length = 300000, blank = True)
    subject_options = models.CharField(max_length = 300000, blank = True)
    noun = models.CharField(max_length = 300000, blank = True)
    noun_options = models.CharField(max_length = 300000, blank = True)     
    gender = models.CharField(max_length = 300000, blank = True)
    plurality = models.CharField(max_length = 300000, blank = True)
    answer = models.CharField(max_length = 300000, blank = True)

class StructureResponse(models.Model):
    id = models.PositiveIntegerField(default = 0, blank = True, primary_key=True)
    student = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    initial_ans_current = models.CharField(max_length = 3000, default="[]")
    question = models.ForeignKey(StructureQuestion, default = None, on_delete=models.CASCADE)
    response = models.PositiveIntegerField(blank = True, default= 0)
    ans = models.CharField(max_length = 3000, blank = True)
    subject_matter = models.CharField(max_length = 300000, blank = True)
    subject = models.CharField(max_length = 300000, blank = True)
    noun = models.CharField(max_length = 300000, blank = True)
    gender = models.CharField(max_length = 300000, blank = True)
    plurality = models.CharField(max_length = 300000, blank = True)
    answer = models.CharField(max_length = 300000, blank = True)

class Question(models.Model):
    section = models.ForeignKey(Section, default = None ,on_delete=models.CASCADE)
    background = models.CharField(max_length = 3000, blank = True)
    q = models.CharField(max_length = 3000, blank = True)

    question_stem  = models.CharField(max_length = 300000, blank = True)
    question_stem_ctn  = models.CharField(max_length = 300000, blank = True)
    question_stem_ctn2 = models.CharField(max_length = 300000, blank = True)

    category= models.CharField(max_length = 500, blank = True, null = True)

    img= models.CharField(max_length = 500, blank = True, null = True)
    q_id = models.CharField(max_length = 500, blank = True)
    correctanswer = models.PositiveIntegerField(default = 0, blank = True)
    feedback = models.CharField(max_length = 3000, blank = True)
    option1 = models.CharField(max_length = 500, blank = True)
    option2 = models.CharField(max_length = 500, blank  = True)
    option3 = models.CharField(max_length = 500, blank = True)
    option4 = models.CharField(max_length = 500, blank = True)
    def __unicode__(self):
        return 'id='+ str(self.pk)

class ScreenshotUpload(models.Model):
    user = models.ForeignKey(User, default = None,on_delete=models.CASCADE)
    screenshot = models.FileField(upload_to="screenshots/", blank=True)
    complete= models.BooleanField(blank = True, default = False)



class Response(models.Model):
    student = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, default = None, on_delete=models.CASCADE)
    response = models.PositiveIntegerField(blank = True, default= 0)
    justification = models.CharField(max_length = 3000, blank = True)
    correct = models.BooleanField(blank= True, default=False)
    trial = models.PositiveIntegerField(blank = True, default = 0)
    section = models.ForeignKey(Section, default = None, on_delete=models.CASCADE)
    feedbackmessage = models.CharField(max_length = 1000, blank = True)
    checkanswer_at = models.DateTimeField(auto_now = False, blank = True, default = timezone.now)
    nextquestion_at = models.DateTimeField(auto_now = False, blank = True, default = timezone.now)
    updated_at = models.DateTimeField(auto_now = True, blank = True)
    def __unicode__(self):
        return 'id='+ str(self.pk)

class SeverityQuestion(models.Model):
    section = models.ForeignKey(Section, default = None, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, default = None, on_delete=models.CASCADE)
    
    response_text = models.CharField(max_length = 3000, blank = True)

    option1 = models.CharField(max_length = 3000, default = None)
    option2 = models.CharField(max_length = 3000, default = None)
    option3 = models.CharField(max_length = 3000, default = None)
    correctanswer = models.PositiveIntegerField(blank = True, default = 0)

class SeverityResponse(models.Model):
    student = models.ForeignKey(User, default = None, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, default = None, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField(blank = True, default = 0)
    question = models.ForeignKey(SeverityQuestion, default  = None, on_delete=models.CASCADE)
    response = models.PositiveIntegerField(blank = True, default = 0)
    justification = models.CharField(max_length = 3000, blank = True)
    correct = models.BooleanField(blank= True, default=False)
    feedbackmessage = models.CharField(max_length = 1000, blank = True)
    checkanswer_at = models.DateTimeField(auto_now = False, blank = True, default = timezone.now)
    nextquestion_at = models.DateTimeField(auto_now = False, blank = True, default = timezone.now)
    updated_at = models.DateTimeField(auto_now = True, blank = True)

class Section2Performance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(VerbQuestion, on_delete=models.CASCADE)

    accuracy_history = models.JSONField(default=list)  # list of 1/0
    history = models.JSONField(default=list)  # full log of attempts
    priority_score = models.FloatField(default=1.0)

    conjugation_errors = models.IntegerField(default=0)

    def update_score(self):
        if not self.accuracy_history:
            self.priority_score = 1.0
        else:
            last_k = self.accuracy_history[-5:]
            rate = sum(last_k) / len(last_k)
            base_score = 1.0 / (rate + 0.01)
        penalty = 0.2 * self.conjugation_errors
        self.priority_score = base_score + penalty
        self.save()

    def __str__(self):
        return f"{self.user} - {self.question} ({self.priority_score})"

class ConjugationPractice(models.Model):
    id = models.PositiveIntegerField(blank = True, default = 0, primary_key=True)
    verb = models.CharField(max_length = 1000, blank = True)
    tense = models.CharField(max_length = 1000, blank = True)
    type = models.CharField(max_length = 1000, blank = True)
    je = models.CharField(max_length = 1000, blank = True)
    tu = models.CharField(max_length = 1000, blank = True)
    il_elle_on = models.CharField(max_length = 1000, blank = True)
    nous = models.CharField(max_length = 1000, blank = True)
    vous = models.CharField(max_length = 1000, blank = True)
    ils_elles = models.CharField(max_length = 1000, blank = True)

class ConjugationResponse(models.Model):
    conj_id = models.PositiveIntegerField(blank = True, default = 0)
    tense =  models.CharField(max_length = 1000, blank = True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(ConjugationPractice, on_delete=models.CASCADE)
    correct = models.BooleanField(blank= True, default=False)


class Section3Performance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(StructureQuestion, on_delete=models.CASCADE)

    accuracy_history = models.JSONField(default=list)
    history = models.JSONField(default=list)
    priority_score = models.FloatField(default=1.0)

    def update_score(self):
        if not self.accuracy_history:
            self.priority_score = 1.0
        else:
            last_k = self.accuracy_history[-5:]
            rate = sum(last_k) / len(last_k)
            self.priority_score = 1.0 / (rate + 0.01)
        self.save()

    def __str__(self):
        return f"{self.user} - {self.question} ({self.priority_score})"

class ConceptPerformance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    concept = models.CharField(max_length=50)  # e.g. "subject_matter", "noun", "answer"

    accuracy_history = models.JSONField(default=list)
    priority_score = models.FloatField(default=1.0)

    def update_score(self):
        """Compute mastery difficulty for this concept."""
        if len(self.accuracy_history) == 0:
            self.priority_score = 1.0
            return

        correct_rate = sum(self.accuracy_history) / len(self.accuracy_history)

        # Higher score = higher priority = weaker mastery
        self.priority_score = 1 / (correct_rate + 0.01)

class ConjugationPerformace(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tense = models.CharField(max_length=50)
    # how many practice questions student has to do 
    # whenever they get everything correct except final answer
    #   if currently 0, set to 5 else up by 1
    practice_mode = models.PositiveIntegerField(blank = True, default = 0) 


class Section2HistoryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(VerbQuestion, on_delete=models.CASCADE)

    timestamp = models.DateTimeField()

    correct_rate = models.FloatField(default=0.0)

    # Priority score AFTER this question was answered
    priority_after = models.FloatField(default=1.0)

    # Full question metadata for clean table rows
    sentence = models.CharField(max_length=5000, blank=True)
    verb = models.CharField(max_length=500, blank=True)
    context = models.CharField(max_length=500, blank=True)

    tense_broad = models.CharField(max_length=200, blank=True)
    tense_specific = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    subject_type = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.username} - Q{self.question_id} @ {self.timestamp}"

class Section3HistoryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(StructureQuestion, on_delete=models.CASCADE)

    timestamp = models.DateTimeField(default=timezone.now)
    correct_rate = models.FloatField(default=0.0)
    priority_after = models.FloatField(default=1.0)

    # Store metadata
    sentence = models.CharField(max_length=2000, blank=True)
    context = models.CharField(max_length=500, blank=True)

    noun = models.CharField(max_length=200, blank=True)
    subject_matter = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    gender = models.CharField(max_length=200, blank=True)
    plurality = models.CharField(max_length=200, blank=True)
    answer = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.user.username} - Q{self.question_id} - {self.timestamp}"
