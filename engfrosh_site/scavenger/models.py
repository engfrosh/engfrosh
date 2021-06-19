from django.db import models

from django.contrib.auth.models import Group
from django.db.models.deletion import CASCADE, PROTECT

import random
import os
import string

SCAVENGER_DIR = "scav/"
QUESTION_DIR = "questions/"
HINT_DIR = "hint/"

FILE_RAND_LENGTH = 128


def random_path(instance, filename, base=""):
    _, ext = os.path.splitext(filename)
    rnd = "".join(random.choice(string.ascii_letters + string.digits) for i in range(FILE_RAND_LENGTH))
    return base + rnd + ext


def question_path(instance, filename):
    return random_path(instance, filename, SCAVENGER_DIR + QUESTION_DIR)


def hint_path(instance, filename):
    return random_path(instance, filename, SCAVENGER_DIR + HINT_DIR)


class Question(models.Model):
    identifier = models.CharField(max_length=32, blank=True, unique=True)
    enabled = models.BooleanField(default=True)
    id = models.AutoField("Question ID", primary_key=True, editable=False)
    text = models.CharField("Text", blank=True, max_length=2000)
    file = models.FileField(upload_to=question_path, blank=True)
    image = models.ImageField(upload_to=question_path, blank=True)
    display_filename = models.CharField(max_length=256, blank=True)
    weight = models.IntegerField("Order Number", unique=True, default=0, db_index=True)

    def __str__(self):
        if self.identifier:
            return self.identifier
        else:
            return f"Question-{hex(self.id)}"


class Hint(models.Model):
    id = models.AutoField("Hint ID", primary_key=True)
    question = models.ForeignKey(Question, CASCADE, db_index=True)
    text = models.CharField("Hint Text", blank=True, max_length=2000)
    file = models.FileField(upload_to=hint_path, blank=True)
    image = models.ImageField(upload_to=hint_path, blank=True)
    weight = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.question} - Hint {self.weight}"


class Team(models.Model):
    group = models.OneToOneField(Group, CASCADE, primary_key=True)
    current_question = models.OneToOneField(Question, on_delete=PROTECT, blank=True, related_name="scavenger_team", null=True)
    locked_out_until = models.DateTimeField("Locked Out Until", blank=True, null=True)
    last_hint = models.ForeignKey(Hint, blank=True, on_delete=PROTECT, null=True)
    last_hint_time = models.DateTimeField(blank=True, null=True)

    def __str__(self) -> str:
        return self.group.name


class QuestionTime(models.Model):
    id = models.AutoField(primary_key=True)
    team = models.ForeignKey(Team, CASCADE)
    question = models.ForeignKey(Question, PROTECT)
    end_time = models.DateTimeField("Completed At")
