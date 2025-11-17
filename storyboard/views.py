# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
# from django.core.urlresolvers import reverse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from storyboard.forms import *
from storyboard.models import *
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.models import User
import json
from django.http import HttpResponse, Http404, JsonResponse
from django.core.files import File
import sqlite3
import os
import numpy as np
import random
from django.utils import timezone

from os import listdir
from django.core.files import File
import re, math
from collections import Counter
from openai import OpenAI
import string


section_names = ['Section 1 (Profile)', 'Verb Conjugation Practice', 'Sentence Structure Practice', 'Chatbot',  ]
# Section 3 (Perform Your Own Error Analysis)'
totalnum_list = [6, 5, 5 ,4]
numberofquestions_list = [6, 5, 5 ,4]
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))  

SCENARIO_EVAL_SYSTEM_PROMPT = """
You are a helpful French tutor chatbot for BEGINNER students (A1–A2 level).
Your job has TWO parts:

1) Chat naturally in SIMPLE French in the given scenario (ordering at a café or meeting a new friend).
2) Evaluate the student's most recent message using a step-by-step internal reasoning process, but DO NOT show your reasoning.

Your internal reasoning (NOT in the output) must follow these steps:
- Understand the situation and time (present / past / future).
- Identify the subject (who is speaking, to whom, singular/plural, formal/informal).
- Check if the verb tense matches the time.
- Check subject–verb agreement.
- Check the word order and sentence structure.
- Check if the tone / formality fits the situation.

Based on that internal analysis, you MUST output ONLY a single JSON object with these keys:

- "reply_fr": your next message in French, using simple vocabulary.
- "feedback_en": short feedback in English about the student's LAST message (1–2 sentences).
- "error_category": one of:
    "none",
    "verb_conjugation",
    "verb_tense",
    "sentence_structure",
    "subject_verb_agreement",
    "formality_register",
    "vocabulary_choice",
    "multiple"
- "cognitive_step": the FIRST step where the error appears, one of:
    "time_reference",
    "subject_identification",
    "verb_tense_selection",
    "subject_verb_agreement",
    "sentence_order",
    "tone_formality",
    "none"
- "is_correct": true or false (whether the student's message is acceptable for a beginner in this context).

RULES:
- Always answer in beginner-friendly French for "reply_fr".
- "feedback_en" must be simple and supportive, and refer to the error_category.
- NEVER include explanations of your reasoning steps or any chain-of-thought in the JSON.
- DO NOT output anything that is not valid JSON.
"""
SCENARIO_SUMMARY_SYSTEM_PROMPT = """
You are a French tutor summarizing a short practice session.
You receive a list of turns with fields:
- role (student or tutor),
- message_fr,
- feedback_en,
- error_category,
- cognitive_step,
- is_correct.

Write a short summary in English for the student:
1) 2–3 sentences about what they did well.
2) 2–4 bullet points of specific things to improve, referencing error categories if helpful.

Be encouraging and concrete. Do NOT output JSON.
"""

@ensure_csrf_cookie
@login_required
def home(request):
    context = {}
    user = request.user
    participant = get_object_or_404(Participant, user=  user)
    displaylist = []
    for i in range(4):
        section = get_object_or_404(Section, id = i+1)
    #     progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-score")
    #     progress = progress_list[0]
    #     displaylist.append(progress)

    # context['displaylist'] = displaylist
    context['user'] = user
    print ("showshow")
    return render(request, 'storyboard/welcome.html', context)

@login_required
def section1(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 1)
    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if request.method == "GET":
        if progress.trial == 0:
            context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
        else:
            progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
            score= progress_highestscore.score
            context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."
        return render(request, 'storyboard/section1.html', context)
        
    else:    
        trial = progress.trial+1
        progress = Progress(student = user, section  = section, trial = trial, score = 0)
        progress.save()
        number_of_questions = section.numberofquestions
        for i in range(number_of_questions):
            question = Question.objects.filter(section = section).order_by("id")[i]
            response = Response(student = user, trial = trial, question = question, section = section)
            response.save()
        return redirect(reverse('section1_questionpage', args = (0,)))

@login_required
def section2(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 2)
    # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    # progress = progress_list[0]

    if request.method == "GET":
        return render(request, 'storyboard/section2.html')
    #     if progress.trial == 0:
    #         context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
    #     else:
    #         progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
    #         score= progress_highestscore.score
    #         context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."        
    #     return render(request, 'storyboard/section2.html', context)
        
    else:    
        # trial = progress.trial+1
        # progress = Progress(student = user, section  = section, trial = trial, score = 0)
        # progress.save()
        number_of_questions = section.numberofquestions
        for i in range(number_of_questions):
            question = VerbQuestion.objects.filter(id=i)[0]
            response = VerbResponse(id = i, student = user, question = question)
            response.save()
        return redirect(reverse('section2_questionpage', args = (0,0)))

@login_required
def section3(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 3)
    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if request.method == "GET":
        if progress.trial == 0:
            context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
        else:
            progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
            score= progress_highestscore.score
            context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."
        return render(request, 'storyboard/section3.html', context)

    else:    
        trial = progress.trial+1
        progress = Progress(student = user, section  = section, trial = trial, score = 0)
        progress.save()
        number_of_questions = section.numberofquestions
        for i in range(number_of_questions):
            question = Question.objects.filter(section = section).order_by("id")[i]
            response = Response(student = user, trial = trial, question = question, section = section)
            response.save()
        return redirect(reverse('section3_questionpage', args = (0,)))

@login_required
def section4(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 4)
    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if request.method == "GET":
        if progress.trial == 0:
            context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
        else:
            progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
            score= progress_highestscore.score
            context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."
        return render(request, 'storyboard/section4.html', context)

    else:    
        trial = progress.trial+1
        progress = Progress(student = user, section  = section, trial = trial, score = 0)
        progress.save()
        number_of_questions = section.numberofquestions
        for i in range(number_of_questions):
            question = Question.objects.filter(section = section).order_by("id")[i]
            response = Response(student = user, trial = trial, question = question, section = section)
            response.save()
        return redirect(reverse('section4_questionpage', args = (0,)))

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@login_required
@csrf_exempt   # if you prefer CSRF via header, you can drop this and use the token
def section4_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    scenario = data.get("scenario")
    student_message = data.get("message")
    history = data.get("history", [])  # optional: list of past turns (you can use later)

    if not scenario or not student_message:
        return JsonResponse({"error": "scenario and message are required"}, status=400)

    # Simple safety: keep scenario to known values
    if scenario not in ["cafe", "new_friend"]:
        return JsonResponse({"error": "Unknown scenario"}, status=400)

    # Build a short natural-language scenario description for the model
    if scenario == "cafe":
        scenario_description = (
            "Ordering food and drinks at a French café. "
            "The learner is the customer, talking to a server."
        )
    else:
        scenario_description = (
            "Introducing yourself to a new friend. "
            "The learner is meeting someone for the first time."
        )

    # You can optionally include a compact history, but for now we focus on the latest turn.
    user_payload = {
        "scenario": scenario,
        "scenario_description": scenario_description,
        "student_level": "beginner",
        "student_message": student_message,
    }

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",  # or gpt-4o-mini / gpt-4.1 if you want stronger eval
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SCENARIO_EVAL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False),
                },
            ],
        )

        raw = completion.choices[0].message.content
        result = json.loads(raw)

        # Light post-processing / defaults
        reply_fr = result.get("reply_fr", "")
        feedback_en = result.get("feedback_en", "")
        error_category = result.get("error_category", "none")
        cognitive_step = result.get("cognitive_step", "none")
        is_correct = bool(result.get("is_correct", False))

        return JsonResponse(
            {
                "reply_fr": reply_fr,
                "feedback_en": feedback_en,
                "error_category": error_category,
                "cognitive_step": cognitive_step,
                "is_correct": is_correct,
            }
        )

    except Exception as e:
        # You might want to log e in real code
        return JsonResponse(
            {"error": "Something went wrong talking to the AI."},
            status=500,
        )


@login_required
@csrf_exempt
def section4_summary(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    turns = data.get("turns", [])
    if not isinstance(turns, list) or len(turns) == 0:
        return JsonResponse({"error": "turns list required"}, status=400)

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SCENARIO_SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(turns, ensure_ascii=False),
                },
            ],
        )

        summary_text = completion.choices[0].message.content
        return JsonResponse({"summary": summary_text})

    except Exception:
        return JsonResponse(
            {"error": "Something went wrong generating the summary."},
            status=500,
        )


@login_required
def section1_questionpage(request, id):

    user = request.user
    section = get_object_or_404(Section, id= 1)
    context = {}


    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]
    trial = progress.trial

    question = Question.objects.filter(section = section).order_by("id")[int(id)]
    print(question.id)
    response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]

    optionlist = []
    optionlist.append(question.option1)
    optionlist.append(question.option2)
    optionlist.append(question.option3)
    optionlist.append(question.option4)

    print("mewmewresponse")
    print(response.response)

    if response.response!=0:
        form = QuestionForm(instance = response, optionlist = optionlist)
        attempted = True
        context["feedbackmessage"] = response.feedbackmessage
    else:
        form = QuestionForm(optionlist = optionlist)
        attempted = False


    context['user'] = user
    context['question'] = question
    context['form'] = form
    context['pageid'] = id
    context['section'] = section
    context['attempted'] = attempted
    # context["feedbackmessage"] = response.feedbackmessage

    image_v= question.img
    imagelist =[]

    if ";" in image_v:
        images = image_v.split(";")
        for image in images:
            imagelist.append(image.strip())
        context["imagelist"] = imagelist

    elif image_v!="None":
        imagelist.append(image_v.strip())
        context["imagelist"] = imagelist

    return render(request, 'storyboard/questionpage.html', context)

def get_form_tense_broad(question_obj, ans):
    question = "What is the tense of the above sentence?"
    options = ["Past", "Present", "Future"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_tense_specific(question_obj, ans):
    if ans == "-1": return "N/A"
    question = "More specifically, what is the tense of the above sentence?"
    past_options = ["Imparfait (imperfect)", "Passé composé (present perfect)", "Passé récent (Recent past)"]
    future_options = ["Futur simple (the simple future)", "Futur proche (the near future)"]
    options = {"Past": past_options, "Future": future_options}
    options = options[question_obj.tense_broad]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_subject(question_obj, ans):
    question = "What is the subject of the above sentence?"
    sentence = question_obj.sentence
    stripped_sent = sentence.translate(str.maketrans('', '', string.punctuation))
    words = stripped_sent.split(" ")
    options = [ans]
    for i in range(3):
        random_index = random.randrange(len(words))
        word = words.pop(random_index)
        options.append(word)
    return QuestionFormMC(question=question, optionlist=options)

def get_form_subject_type(question_obj, ans):
    question = "In what person are we referring to the subject?"
    options = ["First person", "Second person", "Third person"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_formality(question_obj, ans):
    if ans == "-1": return "N/A"
    question = "Should the subject be referred to formally or informally?"
    options = ["Formal", "Informal"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_gender_matter(question_obj, ans):
    question = "Does the gender of the subject matter in the conjugation of the verb?"
    options =  ["Yes", "No"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_gender(question_obj, ans):
    if ans == "-1": return "N/A"
    question = "Is the subject masculine or feminine?"
    options =  ["Feminine", "Masculine"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_pluraility(question_obj, ans):
    question = "Is the subject a singular or plural?"
    options = ["Singular", "Plural"]
    return QuestionFormMC(question=question, optionlist=options)

def get_form_conjugation(question_obj, ans):
    question = "What is the conjugation of the verb in context?"
    return AnswerForm(question=question)



@login_required
def section2_questionpage(request, id, step):

    user = request.user
    section = get_object_or_404(Section, id= 2)
    context = {}

    # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    # progress = progress_list[0]
    # trial = progress.trial

    id = int(id)
    step = int(step)

    question = get_object_or_404(VerbQuestion, id = id)
    question.sentence = question.sentence.replace("[blank]", "____________")
    question.save()

    questions = {
        'tense_broad': get_form_tense_broad, 
        'tense_specific': get_form_tense_specific, 
        'subject': get_form_subject, 
        "subject_type": get_form_subject_type, 
        "formality": get_form_formality, 
        "gender_matter": get_form_gender_matter, 
        "gender": get_form_gender, 
        "plurality": get_form_pluraility, 
        "conjugation": get_form_conjugation
    }

    ordered_fields = [
        'tense_broad', 'tense_specific', 'subject', 'subject_type', 
        'formality', 'gender_matter', 'gender', 'plurality', 'conjugation'
    ]

    
    active_fields = []
    for field in ordered_fields:
        field_ans = getattr(question, field)
        form = questions[field](question_obj=question, ans=field_ans)
        if form != "N/A":
            active_fields.append((field, form))

    # If step is past the last sub-Q → go to next VerbQuestion
    if step >= len(active_fields):
    # Finish this verb question → redirect to summary page
        return redirect(reverse("section2_summary", args=(id,)))

    # Unpack the current form
    current_field, current_form = active_fields[step]


    context['user'] = user
    context['question'] = question
    context['form'] = current_form
    context['qid'] = id
    context['section'] = section
    context['step'] = step
    context['total_steps'] = len(active_fields)



    return render(request, 'storyboard/questionpage2_one.html', context)
    
@login_required
def nextquestion2(request):
    print("nextquestion2 POST")
    print(request.POST)

    qid = int(request.POST.get("qid", 0))
    step = int(request.POST.get("step", 0))

    return redirect(reverse("section2_questionpage", args=(qid, step + 1)))

@login_required
def section2_summary(request, id):
    user = request.user

    question = get_object_or_404(VerbQuestion, id=id)
    section = get_object_or_404(Section, id=2)

    # Get all subquestions in the fixed order
    ordered_fields = [
        'tense_broad','tense_specific','subject','subject_type',
        'formality','gender_matter','gender','plurality','conjugation'
    ]

    # Collect results
    summary_items = []
    for field in ordered_fields:
        correct_answer = getattr(question, field)

        # USER ANSWER stored in VerbResponse
        try:
            resp = VerbResponse.objects.get(student=user, question=question)
            user_answer = resp.response
        except VerbResponse.DoesNotExist:
            user_answer = None

        if correct_answer == "-1":
            continue  # Skip disabled sub-questions

        summary_items.append({
            "subq_label": field.replace("_", " ").title(),
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": (str(user_answer).strip() == str(correct_answer).strip())
        })

    # Check if this was the last VerbQuestion
    is_last_question = (id + 1 >= section.numberofquestions)

    context = {
        "question": question,
        "summary_items": summary_items,
        "qid": id,
        "is_last_question": is_last_question,
    }

    return render(request, "storyboard/section2_summary.html", context)

@login_required
def section3_questionpage(request, id):

    user = request.user
    section = get_object_or_404(Section, id= 3)
    context = {}


    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]
    trial = progress.trial

    question = Question.objects.filter(section = section).order_by("id")[int(id)]
    response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]

    optionlist = []
    optionlist.append(question.option1)
    optionlist.append(question.option2)

    if response.response!=0:
        form = QuestionForm(instance = response, optionlist = optionlist)
        attempted = True
        context["feedbackmessage"] = response.feedbackmessage
    else:
        form = QuestionForm(optionlist = optionlist)
        attempted = False


    context['user'] = user
    context['question'] = question
    context['form'] = form
    context['pageid'] = id
    context['section'] = section
    context['attempted'] = attempted
    context["feedbackmessage"] = response.feedbackmessage

    image_v= question.img
    imagelist =[]

    if ";" in image_v:
        images = image_v.split(";")
        for image in images:
            imagelist.append(image.strip())
        context["imagelist"] = imagelist

    elif image_v!="None":
        imagelist.append(image_v.strip())
        context["imagelist"] = imagelist
    context["image0"] = imagelist[0]
    context["image1"] = imagelist[1]
    context["image2"] = imagelist[2]

    return render(request, 'storyboard/questionpage3.html', context)


@login_required
def section4_questionpage(request, id):

    user = request.user
    section = get_object_or_404(Section, id= 4)
    context = {}

    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]
    trial = progress.trial

    question = Question.objects.filter(section = section).order_by("id")[int(id)]
    response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]

    optionlist = []
    optionlist.append(question.option1)
    optionlist.append(question.option2)
    optionlist.append(question.option3)
    optionlist.append(question.option4)

    if response.response!=0:
        form = QuestionForm(instance = response, optionlist = optionlist)
        attempted = True
        context["feedbackmessage"] = response.feedbackmessage
    else:
        form = QuestionForm(optionlist = optionlist)
        attempted = False

    context['user'] = user
    context['question'] = question
    context['form'] = form
    context['pageid'] = id
    context['section'] = section
    context['attempted'] = attempted
    context["feedbackmessage"] = response.feedbackmessage

    image_v= question.img
    imagelist =[]

    if ";" in image_v:
        images = image_v.split(";")
        for image in images:
            imagelist.append(image.strip())
        context["imagelist"] = imagelist

    elif image_v!="None":
        imagelist.append(image_v.strip())
        context["imagelist"] = imagelist

    return render(request, 'storyboard/questionpage4.html', context)


@login_required
def nextpage(request):
    print ("nextpage")
    print (request.POST)
    user = request.user
    questionid = int(request.POST['questionid'])
    pageid = int(request.POST['pageid'])
    question = get_object_or_404(Question, id = questionid)
    section = question.section

    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if pageid>=section.numberofquestions-1:
        progress.complete = True
        progress.save()
        return redirect(reverse('section'+str(section.id)))
    else:

        responses = Response.objects.filter(student =user).filter(question = question).order_by("-updated_at")
        response = responses[0]
        response.justification = request.POST['justification']
        response.nextquestion_at= timezone.now()
        response.save()
        reversepage = "section1_questionpage"
        return redirect(reverse(reversepage, args = (str(pageid+1),)))


@login_required
def nextpage2(request):
    print ("nextpage")
    print (request.POST)
    user = request.user

    pageid = int(request.POST['pageid'])
    sectionid = int(request.POST['sectionid'])
    section = get_object_or_404(Section, id = sectionid)

    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if pageid>=section.numberofquestions-1:
        progress.complete = True
        progress.save()
        return redirect(reverse('section'+str(section.id)))
    else:
        empty_responses = VerbResponse.objects.filter(student =user).filter(correct = False).order_by("-updated_at")
        response = empty_responses[0]
        question = response.question
        response.nextquestion_at= timezone.now()
        response.save()
        reversepage = "section2_questionpage"
        return redirect(reverse(reversepage, args = (str(question.id),)))


@login_required
def nextpage3(request):
    print ("nextpage")
    print (request.POST)
    user = request.user
    questionid = int(request.POST['questionid'])
    sectionid = int(request.POST['sectionid'])
    print("section:")
    print(sectionid)

    pageid = int(request.POST['pageid'])
    question = get_object_or_404(Question, id = questionid)
    section = get_object_or_404(Section, id = sectionid)

    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if pageid>=section.numberofquestions-1:
        progress.complete = True
        progress.save()
        return redirect(reverse('section'+str(section.id)))
    else:

        responses = Response.objects.filter(student =user).filter(question = question).order_by("-updated_at")
        response = responses[0]
        response.justification = request.POST['justification']
        response.nextquestion_at= timezone.now()
        response.save()
        reversepage = "section3_questionpage"
        return redirect(reverse(reversepage, args = (str(pageid+1),)))


@login_required
def nextpage4(request):
    print ("nextpage")
    print (request.POST)
    user = request.user
    questionid = int(request.POST['questionid'])
    sectionid = int(request.POST['sectionid'])
    print("section:")
    print(sectionid)

    pageid = int(request.POST['pageid'])
    question = get_object_or_404(Question, id = questionid)
    section = get_object_or_404(Section, id = sectionid)

    progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    progress = progress_list[0]

    if pageid>=section.numberofquestions-1:
        progress.complete = True
        progress.save()
        return redirect(reverse('section'+str(section.id)))
    else:

        responses = Response.objects.filter(student =user).filter(question = question).order_by("-updated_at")
        response = responses[0]
        response.justification = request.POST['justification']
        response.nextquestion_at= timezone.now()
        response.save()
        reversepage = "section4_questionpage"
        return redirect(reverse(reversepage, args = (str(pageid+1),)))


@ensure_csrf_cookie
@login_required
def imagefeedback(request):
    user = request.user
    if request.method =="POST":
        print (request.POST)
        sectionid = int(request.POST['sectionid'])
        print (sectionid)
        section = get_object_or_404(Section, id= sectionid)
        
        progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
        progress = progress_list[0]
        trial = progress.trial

        questionid =int(request.POST["questionid"])
        question = get_object_or_404(Question, pk = questionid)
        
        response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]
        if response.response!=0:
            alertmessage = "True"
            response_text = '{ "alertmessage": "'+alertmessage+'"}'
            print ("yesyes")
            return HttpResponse(response_text, 'application/json')


        response_choice = int(request.POST['response'])
        if response_choice == int(question.correctanswer):
            feedbackmessage =  "<p style = 'color:green;'>Great! You picked the user need the student created this Storyboard for.</p>"
            correct = 1
        else:
            correctanswer = int(question.correctanswer)
            optionlist = []
            optionlist.append(question.option1)
            optionlist.append(question.option2)
            optionlist.append(question.option3)
            optionlist.append(question.option4)
            feedbackmessage = "<p style = 'color:red;'>Sorry, this Storyboard was created for the user need: <strong> #"+str(correctanswer)+"</strong></p>"
            correct = 0
        

        response.response = response_choice
        response.updated_at = timezone.now()
        response.correct = correct
        response.feedbackmessage = feedbackmessage
        response.save()

        pageid = int(request.POST['pageid'])

        if pageid>=section.numberofquestions-1:
            progress.complete = True
            progress.save()
        print (feedbackmessage)

        question_response_list = Response.objects.filter(student =user).filter(section = section).filter(trial = trial)
        score = 0
        for item in question_response_list:
            score = score+item.correct
        progress.score = score
        progress.save()

        response_text = '{ "feedbackmessage": "'+feedbackmessage+'"}'
        return HttpResponse(response_text, 'application/json')



@ensure_csrf_cookie
@login_required
def imagefeedback2(request):
    user = request.user
    if request.method =="POST":
        print (request.POST)
        sectionid = int(request.POST['sectionid'])
        print (sectionid)
        section = get_object_or_404(Section, id= sectionid)
        
        progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
        progress = progress_list[0]
        trial = progress.trial

        questionid =int(request.POST["questionid"])
        question = get_object_or_404(Question, pk = questionid)

        response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]
        if response.response!=0:
            alertmessage = "True"
            response_text = '{ "alertmessage": "'+alertmessage+'"}'
            print ("yesyes")
            return HttpResponse(response_text, 'application/json')

        response_choice = int(request.POST['response'])

        if response_choice == int(question.correctanswer):
            feedbackmessage = "<p style = 'color:green;'>Great! You picked the lead question written by the student who created this Storyboard. It's a good lead question to ask for this Storyboard."+ question.feedback+ "</p>"
            correct = 1
        else:
            correctanswer = int(question.correctanswer)
            optionlist = []
            optionlist.append(question.option1)
            optionlist.append(question.option2)
            optionlist.append(question.option3)
            optionlist.append(question.option4)

            feedbackmessage = "<p style = 'color:red;'>Sorry, the student who created this Storyboard used the lead question <strong> #"+str(correctanswer)+"</strong>" + question.feedback+ "</p>" 
            correct = 0


        response.response = response_choice
        response.updated_at = timezone.now()
        response.correct = correct
        response.feedbackmessage = feedbackmessage
        response.save()


        pageid = int(request.POST['pageid'])

        if pageid>=section.numberofquestions:
            progress.complete = True
            progress.save()
        print (feedbackmessage)

        question_response_list = Response.objects.filter(student =user).filter(section = section).filter(trial = trial)
        score = 0
        for item in question_response_list:
            score = score+item.correct
        progress.score = score
        progress.save()

        response_text = '{ "feedbackmessage": "'+feedbackmessage+'"}'
        return HttpResponse(response_text, 'application/json')


@ensure_csrf_cookie
@login_required
def imagefeedback3(request):
    user = request.user
    if request.method =="POST":
        print (request.POST)
        sectionid = int(request.POST['sectionid'])
        print (sectionid)
        section = get_object_or_404(Section, id= sectionid)
        
        progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
        progress = progress_list[0]
        trial = progress.trial

        questionid =int(request.POST["questionid"])
        question = get_object_or_404(Question, pk = questionid)

        response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]
        if response.response!=0:
            alertmessage = "True"
            response_text = '{ "alertmessage": "'+alertmessage+'"}'
            print ("yesyes")
            return HttpResponse(response_text, 'application/json')

        response_choice = int(request.POST['response'])
        print(question.feedback)
        if response_choice == int(question.correctanswer):
            feedbackmessage = "<p style = 'color:green;'>Great! You are right."+question.feedback+"</p>"
            correct = 1
        else:
            correctanswer = int(question.correctanswer)
            optionlist = []
            optionlist.append(question.option1)
            optionlist.append(question.option2)
            optionlist.append(question.option3)
            optionlist.append(question.option4)
            if correctanswer == 1:
                feedbackmessage = "<p style = 'color:red;'>Sorry, the three storyboards do follow a progression of riskiness. "+question.feedback+"</p>"
            else:
                feedbackmessage = "<p style = 'color:red;'>Sorry, the three storyboards do not show a progression of riskiness in the design. "+question.feedback+"</p>"
            correct = 0

        response.response = response_choice
        response.updated_at = timezone.now()
        response.correct = correct
        response.feedbackmessage = feedbackmessage
        response.save()

        pageid = int(request.POST['pageid'])

        if pageid>=section.numberofquestions:
            progress.complete = True
            progress.save()
        print (feedbackmessage)

        question_response_list = Response.objects.filter(student =user).filter(section = section).filter(trial = trial)
        score = 0
        for item in question_response_list:
            score = score+item.correct
        progress.score = score
        progress.save()

        response_text = '{ "feedbackmessage": "'+feedbackmessage+'"}'
        return HttpResponse(response_text, 'application/json')


@ensure_csrf_cookie
@login_required
def imagefeedback4(request):
    user = request.user
    if request.method =="POST":
        print (request.POST)
        sectionid = int(request.POST['sectionid'])
        print (sectionid)
        section = get_object_or_404(Section, id= sectionid)
        
        progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
        progress = progress_list[0]
        trial = progress.trial

        questionid =int(request.POST["questionid"])
        question = get_object_or_404(Question, pk = questionid)
        
        response = Response.objects.filter(student= user).filter(trial = trial).filter(section = section).filter(question = question)[0]
        if response.response!=0:
            alertmessage = "True"
            response_text = '{ "alertmessage": "'+alertmessage+'"}'
            print ("yesyes")
            return HttpResponse(response_text, 'application/json')

        response_choice = int(request.POST['response'])
        if response_choice == int(question.correctanswer):
            feedbackmessage = "<p style = 'color:green;'>Great! You gave the same feedback to this Storyboard as an instructor. "+ question.feedback+"</p>"
            correct = 1
        else:
            correctanswer= int(question.correctanswer)
            feedbackmessage = "<p style = 'color:red;'>Sorry, the instrucotr found the issue with this Storyboard to be  <strong> #"+str(correctanswer)+"</strong> " + question.feedback+ "</p>"
            correct = 0
  
        response.response = response_choice
        response.updated_at = timezone.now()
        response.correct = correct
        response.feedbackmessage = feedbackmessage
        response.save()


        pageid = int(request.POST['pageid'])

        if pageid>=section.numberofquestions:
            progress.complete = True
            progress.save()
        print (feedbackmessage)

        question_response_list = Response.objects.filter(student =user).filter(section = section).filter(trial = trial)
        score = 0
        for item in question_response_list:
            score = score+item.correct
        progress.score = score
        progress.save()

        response_text = '{ "feedbackmessage": "'+feedbackmessage+'"}'
        return HttpResponse(response_text, 'application/json')



def signform(request):
    user = request.user

    participant = get_object_or_404(Participant, user=  user)

    if "noaccess" in request.POST:
        participant.exclude = True
        participant.save()
    if "access" in request.POST:
        participant.share = True
        participant.save()


    for item in Section.objects.all():
        progress = Progress(student = user, section = item, complete= False, score = 0, trial = 0)
        progress.save()
    participant.signform = True
    participant.save()
    return redirect(reverse('home'))

###


####register all students with their andrewids and passwords
     
def batchregister():
    data = pd.read_csv("userlist.csv")
    for i in range(len(data)):
        entry = data.iloc[i]
        andrewid = str(entry["andrewid"]).strip()

        user, user_created = User.objects.get_or_create(username=andrewid)

        if user_created:
            user.set_password(andrewid)
            user.save()
        
        participant, part_created = Participant.objects.get_or_create(user=user)

    successmessage = "group2 registered"
    return successmessage

def batchregister_group1():
    data = pd.read_csv("group1.csv")

    for i in range(len(data)):
        entry = data.iloc[i]
        andrewid = str(entry["andrewid"]).strip()

        user, user_created = User.objects.get_or_create(username=andrewid)
        if user_created:
            user.set_password(andrewid)
            user.save()

        participant, part_created = Participant.objects.get_or_create(user=user)

    successmessage = "group1 registered"
    return successmessage


def importsections():
    for i in [2, 3, 4]:
        section = Section(sectionname = section_names[i-1], numberofquestions = numberofquestions_list[i-1], totalnum = totalnum_list[i-1])
        section.save()
        print(f"made section {i}")
    successmessage = "sections imported"
    return successmessage        


def import_questions_section2():
    data = pd.read_csv("verb_conjugation.csv", header =0, encoding = "UTF-8-SIG")
    print(data.columns)
    section = get_object_or_404(Section, pk=2)
    section.totalnum = len(data)
    section.numberofquestions = len(data)
    section.save()

    for i in range(len(data)):
        entry = data.iloc[i]
        question = VerbQuestion(id=i, sentence = entry["sentence"], verb = entry["verb"], verb_type = entry["verb_type"], context = entry["context"], tense_broad = entry["tense_broad"], tense_specific=  entry["tense_specific"], subject = entry["subject"], subject_type = entry["subject_type"], formality = entry["formality"], gender_matter = entry["gender_matter"], gender = entry["gender"], plurality = entry["plurality"], conjugation=  entry["conjugation"])
        question.save()

    successmessage = "section 2 questions imported"
    return successmessage


def import_questions_section3():
    data = pd.read_csv("sentence_structure.csv", header =0, encoding = "UTF-8-SIG")
    section = get_object_or_404(Section, pk=3)
    section.totalnum = len(data)
    section.numberofquestions = len(data)
    section.save()

    for i in range(len(data)):
        entry = data.iloc[i]
        question = StructureQuestion(id=i, sentence = entry["sentence"], context = entry["context"], type = entry["type"], subject = entry["subject"], noun = entry["noun"], gender = entry["gender"], plurality = entry["plurality"], answer = entry["answer"])
        question.save()

    successmessage = "section 3 questions imported"
    return successmessage

def register_new_user():
    name = "jesses1"

    user, user_created = User.objects.get_or_create(username=name)
    if user_created:
        user.set_password(name)
        user.save()

    participant, part_created = Participant.objects.get_or_create(user=user)
    
def startup():
    print (batchregister())
    print (importsections())

def import_questions():
    print (import_questions_section2())
    print (import_questions_section3())


def group1():
    print (batchregister_group1())

