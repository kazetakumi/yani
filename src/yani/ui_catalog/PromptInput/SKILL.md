---
name: PromptInput
description: A free-text checkpoint input with a one-tap escape — the guess box after a hook, the try-one box after a worked example.
---

# PromptInput

A prompt, a textarea, a submit button, and (optionally) a quiet one-tap
escape. This is the participation component: the learner writes something
of their own — a guess, a worked answer — and it reaches the mentor as a
UI action carrying `context.text`.

Use it where the lesson hands the learner the floor and wants *their
words*: the Guess checkpoint (escape: "No idea — show me") and the
practice try-one (escape: "Skip for now"). ExplainBack remains the
dedicated component for the explain-back block; QuizBlock for quizzes.

Rules:

- The escape must cost one tap and read as fully acceptable — a guess is
  a gift, never a toll ("never demand one").
- Submitting or escaping disables the component; a checkpoint is answered
  once.
- Empty text never submits.
