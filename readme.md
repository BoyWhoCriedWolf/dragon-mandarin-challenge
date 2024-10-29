
## Setup

1. Run the project:

```docker compose -f dev.compose.yml up```

2. Populate the database with test data:

```docker compose -f dev.compose.yml exec postgres bash -c "gunzip -c /test_db/data.sql.gz | psql -U testuser -d dragontest"```

3. Visit `localhost:8000`, enter some text, and click 'Read now'. The article should load in the interactive reader.


## Task

This project is a slimmed-down version of the live Dragon Mandarin reading app. The user inputs any Chinese text, the
text is loaded into the interactive reader, and the user can read it with pinyin, tone markings, etc.

**Your task is to add playable audio to the submitted article.** This will involve:

1. Performing text-to-speech (TTS) on the submitted article. You can do this using the OpenAI API with the API key provided.
2. Updating the UI to display the audio player in an attractive way.

From the user's perspective, they should submit an article, see it in the interactive reader, and then get the option to hear their
article being read aloud.

Since the audio takes some time to generate, you should **render the article first**, and update the UI with the audio
when it is ready. Do not delay the initial render of the article while waiting for the TTS response. Check how this
is done in `tasks.py` for other live updates.

Other than that, it's an open-ended task and the design and implementation of the feature is up to you. 


## Submission

Please bundle your solution as a single compressed archive (`.zip`, `.tar.gz`, etc), upload it to a cloud hosting provider
(e.g. Google Drive), and submit using the same exam link I sent you.

On the submission form there is space to include a description or video explaining your solution. Please do this, as it is a big
factor in how I will assess the task. I want to know whether you understand the code you
wrote, so the more thorough your explanation the better. The fastest way to do this is with a Loom recording
of your screen, while you talk me through your solution.

## Grading

I will look at:
* General quality of your code
* Visual look and feel of the feature
* Your explanation video or summary
* How fast you completed the task.

Good luck!
