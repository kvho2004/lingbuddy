# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pandas as pd
from django.contrib import messages
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
import ast

from os import listdir
from django.core.files import File
import re, math
from collections import Counter
from openai import OpenAI
import string
import random




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
    print("here")
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

    context = {}

    concept_history = []
    for cp in ConceptPerformance.objects.filter(user=user):
        if cp.accuracy_history:
            acc = 100 * sum(cp.accuracy_history) / len(cp.accuracy_history)
        else:
            acc = 0

        concept_history.append({
            "concept": cp.concept.replace("_", " ").title(),
            "accuracy": acc,
            "priority_score": cp.priority_score,
        })

    # Practice History (Section 2 + 3 rows merged)
    section2_history = []
    section3_history = []


    # Section 2
    for perf in Section2HistoryEntry.objects.filter(user=user):
        q = perf.question
        section2_history.append({
            "timestamp": perf.timestamp,
            "sentence": q.sentence,
            "verb": q.verb,
            "context": q.context,
            "correct_rate": perf.correct_rate,
            "priority_after": perf.priority_after,
        })

    # Section 3
    for perf in Section3HistoryEntry.objects.filter(user=user):
        q = perf.question
        section3_history.append({
            "timestamp": perf.timestamp,
            "sentence": q.sentence,
                "context": q.context,
                "noun": q.noun,
                "subject_matter": q.subject_matter,
                "subject": q.subject,
                "gender": q.gender,
                "plurality": q.plurality,
                "correct_rate": perf.correct_rate,
                "priority_after": perf.priority_after,
            })

    # Sort descending by time
    section
    section3_history.sort(key=lambda x: x["timestamp"], reverse=True)

    # Add to context
    context["concept_history"] = concept_history
    context["conjugation_history"] = section2_history
    context["structure_history"] = section3_history


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
    user = request.user
    section = get_object_or_404(Section, id= 2)

    if request.method == "GET":
        # 1) per question rows
        history_rows = []

        entries = Section2HistoryEntry.objects.filter(user=user).order_by("-timestamp")

        for entry in entries:
            q = entry.question
            history_rows.append({
                "timestamp": entry.timestamp,
                "sentence": q.sentence,
                "verb": q.verb,
                "context": q.context,
                "correct_rate": entry.correct_rate,
                "priority_after": entry.priority_after,
            })

        # Newest first
        history_rows.sort(key=lambda x: x["timestamp"], reverse=True)


        # 2) accuracy per concept
        concept_rows = []
        concepts = ConceptPerformance.objects.filter(user=user)
        for cp in concepts:
            acc_history = cp.accuracy_history
            if acc_history:
                accuracy = 100 * sum(acc_history) / len(acc_history)
            else:
                accuracy = 0
            
            concept_rows.append({
                "concept": cp.concept.replace("_", " ").title(),
                "accuracy": accuracy,
                "priority_score": cp.priority_score
            })

        context = {
            "user": user,
            "practice_history": history_rows,
            "concept_history": concept_rows,
        }
        return render(request, "storyboard/section2.html", context)


    if not VerbResponse.objects.filter(student=user).exists():
        num_q = section.numberofquestions
        for i in range(num_q):
            q = VerbQuestion.objects.get(id=i)
            VerbResponse.objects.get_or_create(student=user, question=q)
            Section2Performance.objects.get_or_create(user=user, question=q)

        # number_of_verbs = section.numberofverbs
        # for i in range(number_of_verbs*3):
        #     verb = ConjugationPractice.objects.filter(id=i)[0]
        #     response = ConjugationResponse(id = i, user = user, question = verb)
        #     response.save()
    next_q = get_next_section2_question(user)
    return redirect(reverse('section2_questionpage', args = (next_q.id,0)))
    
def get_next_section2_question(user):
    perfs = list(Section2Performance.objects.filter(user=user))

    if not perfs:
        return VerbQuestion.objects.order_by("id").first()
    
    if len(perfs) < VerbQuestion.objects.count():
        # some questions not yet attempted: pick one at random
        attempted_q_ids = {perf.question.id for perf in perfs}
        unattempted_questions = VerbQuestion.objects.exclude(id__in=attempted_q_ids)
        return random.choice(unattempted_questions)

    # otherwise: weakest mastery first
    perfs.sort(key=lambda p: p.priority_score)
    return perfs[0].question

import random

def get_next_section3_question(user):

    if StructureQuestion.objects.count() == 0:
        return None

    attempted_ids = set(
        Section3Performance.objects.filter(user=user)
        .values_list("question_id", flat=True)
    )
    all_ids = set(StructureQuestion.objects.values_list("id", flat=True))

    unattempted = list(all_ids - attempted_ids)
    if unattempted:
        return StructureQuestion.objects.get(id=random.choice(unattempted))

    weakest_concept = (
        ConceptPerformance.objects.filter(user=user)
        .order_by("-priority_score")   # highest score = weakest mastery
        .first()
    )

    if weakest_concept:
        concept = weakest_concept.concept

        # Find all questions that contain this concept
        # and are valid (not "-1")
        field_filter = {f"{concept}__isnull": False}
        qs = StructureQuestion.objects.filter(**field_filter).exclude(
            **{concept: "-1"}
        )

        if qs.exists():
            # For those questions, rank by Section3Performance priority_score
            perf_map = {
                p.question.id: p.priority_score
                for p in Section3Performance.objects.filter(user=user)
            }

            # Pick the weakest question for this concept
            qs_sorted = sorted(qs, key=lambda q: perf_map.get(q.id, 1.0))
            return qs_sorted[0]

    perfs = list(Section3Performance.objects.filter(user=user))

    # If all priority scores are the same → choose randomly
    unique_scores = {p.priority_score for p in perfs}
    if len(unique_scores) == 1:
        return random.choice(perfs).question

    # Otherwise choose weakest mastery question
    perfs.sort(key=lambda p: p.priority_score)
    return perfs[0].question



@login_required
def section3(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 3)
    # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    # progress = progress_list[0]

    if request.method == "GET":
        logs = Section3HistoryEntry.objects.filter(user=user).order_by("-timestamp")

        history_rows = []
        for h in logs:
            history_rows.append({
                "timestamp": h.timestamp,
                "sentence": h.sentence,
                "context": h.context,
                "noun": h.noun,
                "subject_matter": h.subject_matter,
                "subject": h.subject,
                "gender": h.gender,
                "plurality": h.plurality,
                "correct_rate": h.correct_rate,
                "priority_after": h.priority_after,
            })

        context = {
            "user": user,
            "practice_history": history_rows,
        }

        return render(request, "storyboard/section3.html", context)
        # if progress.trial == 0:
        #     context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
        # else:
        #     progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
        #     score= progress_highestscore.score
        #     context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."
        # return render(request, 'storyboard/section3.html', context)

    else:
        # trial = progress.trial+1
        # progress = Progress(student = user, section  = section, trial = trial, score = 0)
        # progress.save()
        for q in StructureQuestion.objects.all():
            StructureResponse.objects.get_or_create(student=user, question=q)
            Section3Performance.objects.get_or_create(user=user, question=q)
        next_q = get_next_section3_question(user)
        return redirect(reverse("section3_questionpage", args=(next_q.id, 0)))

@login_required
def section4(request):
    context = {}
    user = request.user
    section = get_object_or_404(Section, id= 4)
    # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    # progress = progress_list[0]

    if request.method == "GET":
        # if progress.trial == 0:
        #     context['sectionstatus'] = "You haven't started this section yet. Please click on the button to start this section."         
        # else:
        #     progress_highestscore = Progress.objects.filter(student = user).filter(section = section).order_by("-score")[0]
        #     score= progress_highestscore.score
        #     context["sectionstatus"] = "Your current score for this section is "+str(score)+". You can work on the section again to earn a new score."
        return render(request, 'storyboard/section4.html', context)

    else:    
        # trial = progress.trial+1
        # progress = Progress(student = user, section  = section, trial = trial, score = 0)
        # progress.save()
        # number_of_questions = section.numberofquestions
        # for i in range(number_of_questions):
        #     question = Question.objects.filter(section = section).order_by("id")[i]
        #     response = Response(student = user, trial = trial, question = question, section = section)
        #     response.save()
        return redirect(reverse('section4_chat', args = (0,)))

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
    form_ans = options.index(ans.capitalize()) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def normalize_tense(s):
    return s.lower().replace(" ", "").replace("(", "").replace(")", "")

def get_form_tense_specific(question_obj, ans):
    if ans == "-1":
        return ("N/A", -1, -1)
    question = "More specifically, what is the tense of the above sentence?"
    past_options = [
        "Imparfait (imperfect)",
        "Passé composé (present perfect)",
        "Passé récent (recent past)",
    ]
    future_options = [
        "Futur simple (the simple future)",
        "Futur proche (the near future)",
    ]
    broad = question_obj.tense_broad.strip().lower()
    if broad == "past":
        options = past_options
    else:
        options = future_options
    ans_norm = normalize_tense(ans)
    options_norm = [normalize_tense(x) for x in options]
    if ans_norm not in options_norm:
        print("WARNING: tense_specific CSV mismatch:", ans, "not in", options)
        form_ans = 1  # default to first
    else:
        form_ans = options_norm.index(ans_norm) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_subject(question_obj, ans):
    if ans == "-1": return ("N/A", -1, -1)
    question = "What is the subject of the above sentence?"
    if question_obj.subject_options == "":
        sentence = question_obj.sentence
        stripped_sent = sentence.translate(str.maketrans('', '', string.punctuation))
        words = stripped_sent.split(" ")
        words = [word for word in words if word not in ["", ans]]
        options = [ans]
        for i in range(3):
            if len(words) == 0: break
            random_index = random.randrange(len(words))
            word = words.pop(random_index)
            options.append(word)
        question_obj.subject_options = str(options)
        question_obj.save()
    else:
        options = ast.literal_eval(question_obj.subject_options)
    form_ans = options.index(ans) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_subject_type(question_obj, ans):
    question = "In what person are we referring to the subject?"
    options = ["First person", "Second person", "Third person"]
    form_ans = options.index(ans) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_formality(question_obj, ans):
    if ans == "-1": return ("N/A", -1, -1)
    question = "Should the subject be referred to formally or informally?"
    options = ["Formal", "Informal"]
    form_ans = options.index(ans) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_gender_matter(question_obj, ans):
    question = "Does the gender of the subject matter in the conjugation of the verb?"
    options =  ["Yes", "No"]
    form_ans = options.index(ans.capitalize()) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_gender(question_obj, ans):
    if ans == "-1": return ("N/A", -1, -1)
    question = "Is the subject masculine or feminine?"
    options =  ["Feminine", "Masculine"]
    form_ans = options.index(ans.capitalize()) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_plurality(question_obj, ans):
    question = "Is the subject a singular or plural?"
    options = ["Singular", "Plural"]
    form_ans = options.index(ans.capitalize()) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_conjugation(question_obj, ans):
    question = "What is the conjugation of the verb in context?"
    return (AnswerForm(question=question), ans, "N/A")


@login_required
def section2_questionpage(request, id, step):

    print(request)
    user = request.user
    participant = get_object_or_404(Participant, user=user)
    section = get_object_or_404(Section, id= 2)
    context = {}

    # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
    # progress = progress_list[0]
    # trial = progress.trial

    id = int(id)
    step = int(step)

    conj_practice = getattr(participant, "conj_practice")
    print("CONJ PRACTICE", conj_practice)
    if step == 0 and conj_practice != "":
        tenses = conj_practice.split(",")
        chance_practice = .33 * len(tenses)
        print("***chance practice", chance_practice)
        if random.random() <= chance_practice:
        #if random.random() <= 1:
            practice_tense = random.choice(tenses)
            print(practice_tense)
            question = ConjugationResponse.objects.filter(user=user).filter(correct=False).filter(tense=practice_tense).order_by('?').first()
            if question is not None:
                practice = question.question
                context['user'] = user
                context['conjugation'] = practice
                context['qid'] = id
            # any incorrect conjugationResponse 
            return render(request, 'storyboard/conjugation_practice.html', context)
    question = get_object_or_404(VerbQuestion, id = id)
    question.sentence = question.sentence.replace("[blank]", "____________")
    question.save()

    FORM_MAP = {
        'tense_broad': get_form_tense_broad, 
        'tense_specific': get_form_tense_specific, 
        'subject': get_form_subject, 
        "subject_type": get_form_subject_type, 
        "formality": get_form_formality, 
        "gender_matter": get_form_gender_matter, 
        "gender": get_form_gender, 
        "plurality": get_form_plurality, 
        "conjugation": get_form_conjugation
    }

    ordered_fields = [
        'tense_broad', 'tense_specific', 'subject', 'subject_type', 
        'formality', 'gender_matter', 'gender', 'plurality', 'conjugation'
    ]
    
    active_fields = []
    for field in ordered_fields:
        field_ans = getattr(question, field)
        print(FORM_MAP[field](question_obj=question, ans=field_ans))
        form, form_ans, form_options = FORM_MAP[field](question_obj=question, ans=field_ans)
        if form != "N/A":
            active_fields.append((field, form, form_ans, form_options))

    # If step is past the last sub-Q → go to next VerbQuestion
    if step >= len(active_fields):
    # Finish this verb question → redirect to summary page
        return redirect(reverse("section2_summary", args=(id,)))

    # Unpack the current form
    current_field, current_form, current_form_ans, current_form_options = active_fields[step]

    perf = Section2Performance.objects.get(user=user, question=question)

    context.update({
        "user": user,
        "question": question,
        "form": current_form,
        "qid": id,
        "step": step,
        "section": section,
        "total_steps": len(active_fields),
        "field": current_field,
        "form_ans": current_form_ans,
        "options": (current_form_options if current_form_options != "N/A" else None),
        "performance": perf,
    })
    return render(request, 'storyboard/questionpage2_one.html', context)
    
@login_required
def nextquestion2(request):
    user = request.user
    qid = int(request.POST.get("qid", 0))
    step = int(request.POST.get("step", 0))

    form_ans = request.POST.get("form_ans", "0")
    form_ans = int(form_ans) if form_ans.isdigit() else form_ans.lower()

    user_ans = request.POST.get("response", "0")
    user_ans = int(user_ans) if user_ans.isdigit() else user_ans.lower()

    field = request.POST.get("field", "")

    question = get_object_or_404(VerbQuestion, id=qid)
    response = VerbResponse.objects.get(student=user, question=question)

    response_field = getattr(response, field)

    attempt_value = 1 if form_ans == user_ans else 0

    temp_list = request.session.get("temp_correct_list", [])
    temp_list.append(attempt_value)
    request.session["temp_correct_list"] = temp_list

    # Update per-question performance (for priority queue)
    perf, _ = Section2Performance.objects.get_or_create(
        user=user,
        question=question
    )
    perf.accuracy_history.append(attempt_value)
    perf.update_score()  # updates priority_score
    perf.save()

    # Save student's raw answer sequence
    response_ans = ast.literal_eval(response.initial_ans_current)
    if len(response_ans) <= step:
        if field != "conjugation":
            options = ast.literal_eval(request.POST.get("options", "[]"))
            response_ans.append(options[user_ans - 1])
        else:
            response_ans.append(user_ans)

        response.initial_ans_current = response_ans
        response.save()

    # Save correctness trace on the VerbResponse
    if response_field == "":
        response_field = f"{attempt_value}"
    else:
        response_field += f",{attempt_value}"

    setattr(response, field, response_field)
    response.save()

    if attempt_value == 0:
        messages.error(request, "Hmm...That answer isn't quite right...")
        return redirect(reverse("section2_questionpage", args=(qid, step)))

    # To test: count how many active sub-questions there were originally
    ordered_fields = [
        'tense_broad','tense_specific','subject','subject_type',
        'formality','gender_matter','gender','plurality','conjugation'
    ]

    # Mapping of Section 2 sub-questions → form generator functions
    QUESTION_2 = {
        'tense_broad': get_form_tense_broad,
        'tense_specific': get_form_tense_specific,
        'subject': get_form_subject,
        'subject_type': get_form_subject_type,
        'formality': get_form_formality,
        'gender_matter': get_form_gender_matter,
        'gender': get_form_gender,
        'plurality': get_form_plurality,
        'conjugation': get_form_conjugation,
    }

    active_fields = []
    for f in ordered_fields:
        ans = getattr(question, f)
        form, _, _ = QUESTION_2[f](question_obj=question, ans=ans)
        if form != "N/A":
            active_fields.append(f)

    is_last_step = (step + 1 == len(active_fields))

    if is_last_step:
        # Compute correct % for the whole question
        correct_rate = sum(temp_list) / len(temp_list)

        # Add ONE clean history row
        Section2HistoryEntry.objects.create(
            user=user,
            question=question,
            timestamp=timezone.now(),
            sentence=question.sentence,
            verb=question.verb,
            context=question.context,
            tense_broad=question.tense_broad,
            tense_specific=question.tense_specific,
            subject=question.subject,
            subject_type=question.subject_type,
            correct_rate=correct_rate,
            priority_after=perf.priority_score,
        )


        # Clear temp list for next question
        request.session["temp_correct_list"] = []

    # --- Next sub-question ---
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

    resp = VerbResponse.objects.get(student=user, question=question)
    user_answers = ast.literal_eval(resp.initial_ans_current)
    print("USER ANS", user_answers)
    ans_idx = 0

    # Collect results
    summary_items = []
    running_correct = True
    for field in ordered_fields:
        correct_answer = getattr(question, field)

        if correct_answer == "-1":
            continue  # Skip disabled sub-questions

        user_answer = user_answers[ans_idx]
        is_correct = str(user_answer).strip().capitalize() == str(correct_answer).strip().capitalize()
        if(field=='conjugation' and running_correct and (not is_correct)):
            print("REGISTERING THAT LAST IS ONLY INCORRECT")
            tense = getattr(question, 'tense_broad')
            student_prog, _ = ConjugationPerformace.objects.get_or_create(
                user=user, tense=tense
            )
            print("student progress practice mode", getattr(student_prog, "practice_mode"))
            if getattr(student_prog, "practice_mode") == 0:
                print("here")
                setattr(student_prog, "practice_mode", 5)
                student_prog.save()
                participant = get_object_or_404(Participant, user=user)
                current_practice = getattr(participant, "conj_practice")
                comma = "," if current_practice != "" else ""
                current_practice += comma + tense
                print("setting the participant conj_practice to:", current_practice)
                setattr(participant, "conj_practice", current_practice)
                participant.save()


        summary_items.append({
            "subq_label": field.replace("_", " ").title(),
            "correct_answer": correct_answer.capitalize(),
            "user_answer": user_answer,
            "is_correct": is_correct
        })
        ans_idx += 1
        running_correct = running_correct and is_correct
    setattr(resp, "initial_ans_current", "[]")
    resp.save()

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
def check_conj_practice(request):
    print("hi")
    user = request.user
    conj_practice_id = request.POST["conj_id"]
    practice_question = get_object_or_404(ConjugationPractice, id=conj_practice_id)
    tense_convert = {"present": "present", "imparfait (imperfect)": "past", "futur simple (the simple future)": "future"}
    broad_tense = tense_convert[practice_question.tense]
    practice_response = ConjugationResponse.objects.get(user=user, conj_id=conj_practice_id)
    performance = ConjugationPerformace.objects.get(user=user, tense=broad_tense)
    
    num_practice_left = getattr(performance, "practice_mode") - 1
    print("NUM LEFT", num_practice_left)
    if(num_practice_left >= 0): # gets negative sometimes in debugging
        setattr(performance, "practice_mode", num_practice_left)
        performance.save()
    #num_practice_left = 1
    if num_practice_left <= 0:
        participant = get_object_or_404(Participant, user=user)
        user_conj_practice = getattr(participant, "conj_practice").split(",")
        print("USSER CONJ PRACTICE", getattr(participant, "conj_practice"))
        print("SPLIT", getattr(participant, "conj_practice").split(","))
        updated_conj_practice = ""
        if len(user_conj_practice) > 1:
            user_conj_practice.remove(broad_tense)
            updated_conj_practice = ",".join(user_conj_practice)
        setattr(participant, "conj_practice", updated_conj_practice)
        participant.save()

    field_names = ['je', 'tu', 'il_elle_on', 'nous', 'vous', 'ils_elles']
    print(request.POST)
    fields = request.POST.getlist("conjugations[]")
    print("FIELDS", fields)
    incorrect_fields = []
    for i in range(len(field_names)):
        correct_ans = getattr(practice_question, field_names[i])
        user_ans = fields[i]
        if correct_ans.lower() != user_ans.lower():
            incorrect_fields.append(field_names[i])
    if len(incorrect_fields) == 0:
        setattr(practice_response, "correct", True)
        practice_response.save()
        response = json.dumps([{'correct':True, "output":"Great job! You got all the conjugations correct!"}])
    else:
        setattr(practice_response, "correct", False)
        practice_response.save()
        incorrect = ", ".join(incorrect_fields)
        incorrect = incorrect.replace("_", "/")
        response = json.dumps([{'correct':False, 'output':f"Double check your answers for the following conjugations: {incorrect}"}])
    print(response)
    return HttpResponse(response, 'application/javascript')


@login_required
def section3_questionpage(request, id, step=0):
    user = request.user
    section = get_object_or_404(Section, id=3)

    id = int(id)
    step = int(step)

    question = get_object_or_404(StructureQuestion, id=id)
    question.sentence = question.sentence.replace("[blank]", "____________")
    question.save()

    active_fields = []
    for field in STRUCTURE_FIELDS:
        ans = getattr(question, field)
        form, form_ans, form_options = STRUCTURE_FORMS[field](question_obj=question, ans=ans)
        if form != "N/A":
            active_fields.append((field, form, form_ans, form_options))

    if step >= len(active_fields):
        return redirect(reverse("section3_summary", args=(id,)))

    current_field, current_form, current_form_ans, current_form_options = active_fields[step]

    context = {
        "user": user,
        "question": question,
        "form": current_form,
        "qid": id,
        "section": section,
        "step": step,
        "total_steps": len(active_fields),
        "form_ans": current_form_ans,
        "field": current_field
    }
    if current_form_options != "N/A":
        context['options'] = current_form_options

    concepts = ConceptPerformance.objects.filter(user=user).order_by("-priority_score")
    context["concepts"] = concepts

    return render(request, "storyboard/questionpage3_one.html", context)

def get_form_subject_matter(question_obj, ans):
    if ans == "-1": return ("N/A", -1, -1)
    question = "Does the subject of the sentence need to also be considered to ensure agreement with the missing word?"
    options =  ["Yes", "No"]
    if ans in ["", None]:
        # Missing → no correct option; skip subquestion entirely
        return ("N/A", -1, -1)

    # Normalize stored answer
    correct_text = ans.strip().lower()

    # Convert “yes”/“no” to index 1/2
    form_ans = options.index(correct_text.capitalize()) + 1


    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_noun(question_obj, ans):
    if ans == "-1": return ("N/A", -1, -1)
    question = "What is the noun which the missing word in the sentence refers to?"
    if question_obj.noun_options == "":
        sentence = question_obj.sentence
        stripped_sent = sentence.translate(str.maketrans('', '', string.punctuation))
        words = stripped_sent.split(" ")
        words = [word for word in words if word not in ["", ans]]
        options = [ans]
        for i in range(3):
            random_index = random.randrange(len(words))
            word = words.pop(random_index)
            options.append(word)
        question_obj.noun_options = str(options)
        question_obj.save()
    else:
        options = ast.literal_eval(question_obj.noun_options)
    form_ans = options.index(ans) + 1
    return (QuestionFormMC(question=question, optionlist=options), form_ans, options)

def get_form_answer(question_obj, ans):
    question = "What is the correct missing word?"
    return (AnswerForm(question=question), ans, "N/A")

@login_required
def nextquestion3(request):
    user = request.user
    qid = int(request.POST.get("qid"))
    step = int(request.POST.get("step"))

    question = get_object_or_404(StructureQuestion, id=qid)
    response = StructureResponse.objects.get(student=user, question=question)

    field = request.POST.get("field")
    correct_text = getattr(question, field).strip().lower()
    raw_user_ans = request.POST.get("response")

    # Determine MC vs free response
    if field == "answer":
        user_text = raw_user_ans.strip().lower()
    else:
        options = ast.literal_eval(request.POST.get("options"))
        user_choice_index = int(raw_user_ans) - 1
        user_text = options[user_choice_index].strip().lower()

    # Score it
    attempt_value = 1 if user_text == correct_text else 0

    # --- Update per-question performance (priority queue) ---
    perf, _ = Section3Performance.objects.get_or_create(
        user=user, question=question
    )
    perf.accuracy_history.append(attempt_value)
    perf.update_score()  # recalculates priority_score
    perf.save()

    # --- Update concept-level performance ---
    concept_perf, _ = ConceptPerformance.objects.get_or_create(
        user=user,
        concept=field,
    )
    concept_perf.accuracy_history.append(attempt_value)
    concept_perf.update_score()
    concept_perf.save()

    # --- Save attempt history to StructureResponse ---
    response_field = getattr(response, field)
    if response_field == "":
        response_field = str(attempt_value)
    else:
        response_field += f",{attempt_value}"
    setattr(response, field, response_field)
    response.save()

    # --- Save student's raw answer sequence ---
    answers = ast.literal_eval(response.initial_ans_current)
    if len(answers) <= step:
        answers.append(user_text)
        response.initial_ans_current = answers
        response.save()

    # Wrong → repeat same step of same question
    if attempt_value == 0:
        messages.error(request, "Hmm...That answer isn't quite right...")
        return redirect(reverse("section3_questionpage", args=(qid, step)))

    # Determine enabled fields for this question
    active_fields = []
    for f in STRUCTURE_FIELDS:
        ans = getattr(question, f)
        form, _, _ = STRUCTURE_FORMS[f](question_obj=question, ans=ans)
        if form != "N/A":
            active_fields.append(f)

    is_last_step = (step + 1 == len(active_fields))

    # --- If last step: create a HISTORY ENTRY ---
    if is_last_step:
        # Compute correct rate for this question
        temp_correct = request.session.get("temp_correct_list_3", [])
        temp_correct.append(attempt_value)
        correct_rate = sum(temp_correct) / len(temp_correct)

        Section3HistoryEntry.objects.create(
            user=user,
            question=question,
            timestamp=timezone.now(),
            correct_rate=correct_rate,
            priority_after=perf.priority_score,

            sentence=question.sentence,
            context=question.context,
            noun=question.noun,
            subject_matter=question.subject_matter,
            subject=question.subject,
            gender=question.gender,
            plurality=question.plurality,
        )

        # Reset correct list for next question
        request.session["temp_correct_list_3"] = []

        # Choose NEXT QUESTION using your priority logic
        next_q = get_next_section3_question(user)
        return redirect(reverse("section3_questionpage", args=(next_q.id, 0)))

    # Continue same question, next sub-question
    return redirect(reverse("section3_questionpage", args=(qid, step + 1)))


@login_required
def section3_summary(request, id):
    user = request.user
    question = get_object_or_404(StructureQuestion, id=id)
    section = get_object_or_404(Section, id=3)

    summary_items = []
    resp = StructureResponse.objects.get(student=user, question=question)
    user_answers = ast.literal_eval(resp.initial_ans_current)
    ans_idx = 0

    for field in STRUCTURE_FIELDS:
        correct_answer = getattr(question, field)

        if correct_answer == "-1":
            continue

        if ans_idx < len(user_answers):
            user_answer = user_answers[ans_idx]
        else:
            user_answer = "(no response)"


        summary_items.append({
            "subq_label": field.replace("_", " ").title(),
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "is_correct": (str(user_answer).strip().capitalize() == str(correct_answer).strip().capitalize())
        })
        ans_idx += 1
    setattr(resp, "initial_ans_current", "[]")
    resp.save()

    is_last = (id + 1 >= section.numberofquestions)

    return render(request, "storyboard/section3_summary.html", {
        "question": question,
        "summary_items": summary_items,
        "qid": id,
        "is_last_question": is_last,
    })

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

STRUCTURE_FIELDS = [
    "noun",
    "subject_matter",
    "subject",
    "gender",
    "plurality",
    "answer",
]

STRUCTURE_FORMS = {
    "noun": get_form_noun,
    "subject_matter": get_form_subject_matter,
    "subject": get_form_subject,
    "gender": get_form_gender,
    "plurality": get_form_plurality,
    "answer": get_form_answer,
}

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

        empty_responses = StructureResponse.objects.filter(student =user).filter(correct = False).order_by("-updated_at")
        response = empty_responses[0]
        question = response.question
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
        print("here")
        print (request.POST)
        # sectionid = int(request.POST['sectionid'])
        # print (sectionid)
        # section = get_object_or_404(Section, id= sectionid)
        
        # progress_list = Progress.objects.filter(student = user).filter(section = section).order_by("-trial")
        # progress = progress_list[0]
        # trial = progress.trial

        questionid =int(request.POST["qid"])
        question = get_object_or_404(VerbQuestion, pk = questionid)

        response = Response.objects.filter(student= user).filter(question = question)[0]
        # if response.response!=0:
        #     alertmessage = "True"
        #     response_text = '{ "alertmessage": "'+alertmessage+'"}'
        #     print ("yesyes")
        #     return HttpResponse(response_text, 'application/json')

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
    for i in [1, 2, 3, 4]:
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
        question = StructureQuestion(id=i, sentence = entry["sentence"], context = entry["context"], type = entry["type"], subject_matter = entry["subject_matter"], subject = entry["subject"], noun = entry["noun"], gender = entry["gender"], plurality = entry["plurality"], answer = entry["answer"])
        question.save()

    successmessage = "section 3 questions imported"
    return successmessage

def import_verb_conj_questions():
    data = pd.read_csv("french-verb-conjugation.csv")
    section = get_object_or_404(Section, pk=2)
    section.numberofverbs = len(data)
    section.save()
    users = Participant.objects.all()

    id = 0
    for i in range(len(data)):
        entry = data.iloc[i]
        verb = entry["infinitive"]
        tenses = {"present": "present", "past": "imparfait (imperfect)", "future": "futur simple (the simple future)"}
        for tense in tenses:
            verb_tense = tenses[tense]
            conj = ConjugationPractice(
                id = id,
                verb = verb,
                tense = verb_tense,
                je = entry[f"je|{tense}"],
                tu = entry[f"tu|{tense}"],
                il_elle_on = entry[f"il_elle_on|{tense}"],
                nous = entry[f"nous|{tense}"],
                vous = entry[f"vous|{tense}"],
                ils_elles = entry[f"ils_elles|{tense}"]
            )
            conj.save()
            for user in users:
                resp = ConjugationResponse(conj_id=id, user=user.user, question=conj, tense=tense)
                resp.save()
            id += 1
    successmessage = "verb conjugations imported"
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
    print (import_verb_conj_questions())


def group1():
    print (batchregister_group1())

