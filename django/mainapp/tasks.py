import traceback
import requests

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction

from cndict.settings import OPENAI_API_KEY

from mainapp import gpt
from mainapp.gpt import GPTError
from mainapp.models import Article, update_atomic
from mainapp.reading import annotate
from mainapp.reading import inflate
from mainapp.reading.utils import strip_tags



@shared_task
def generate_audio(article_pk):
    article = Article.objects.get(pk=article_pk)
    audio_url = gpt.request_tts(article.plaintext)

    try:
        article.url = audio_url
        article.save()

        # Notify frontend about the new audio
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            article.channel_name,
            {
                'type': 'audio_update',
                'audio_url': audio_url,
            }
        )
    except Exception as e:
        print(f"Error generating audio: {e}")
        
@shared_task
def update_article_summary(article_pk):
    article = Article.objects.get(pk=article_pk)
    prompt = f"""
    Summarise the following article in English, in one or two sentences. Keep your summary short and simple.
    
    Return json in the form: {{"english_summary": <your summary>}}, with no additional text or explanation.
    
    ---START OF ARTICLE---
    {article.plaintext}
    ---END OF ARTICLE---
    """
    try:
        response = gpt.get_response(prompt=prompt, json_keys=['english_summary'], model="gpt-4o")
        summary = response['english_summary']
    except GPTError:
        summary = "Article summary unavailable."

    print(f"About to save. Summary: {summary}")
    update_atomic(article, 'english_summary', summary)
    print(f"Finished save: {article.english_summary}")

    # Without on_commit, the update might be sent before the update is saved to the DB. This means the frontend
    # might never load the update (if it goes ws_send -> client_ws_connect -> client_fetch -> transaction_commit)
    def send_update_to_ws():

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            article.channel_name,
            {
                'type': 'summary_update',
                'message': article.english_summary,
            }
        )
    transaction.on_commit(send_update_to_ws)


@shared_task
def update_phrase_annotations(article_pk):

    async def cb(phrase):
        # This is run whenever an updated phrase translation has been saved

        await get_channel_layer().group_send(
            phrase.annotation.article.channel_name,
            {
                'type': 'phrase_update',
                'message': phrase.compute_client_obj(),
            }
        )

    article = Article.objects.get(pk=article_pk)
    async_to_sync(annotate.phrases.update_phrase_annotations)(article, cb)

    print("All phrase annotations updated")


@shared_task
def process_article(article_pk):

    channel_layer = get_channel_layer()

    def send_success():
        def send_update_to_ws():
            async_to_sync(channel_layer.group_send)(
                article.loading_channel_name,
                {'type': 'status_success'}
            )
        transaction.on_commit(send_update_to_ws)

    def send_error():
        def send_update_to_ws():
            async_to_sync(channel_layer.group_send)(
                article.loading_channel_name,
                {'type': 'status_error'}
            )
        transaction.on_commit(send_update_to_ws)


    article = Article.objects.get(pk=article_pk)

    if article.url and not article.body:
        raise NotImplementedError()

    try:

        update_atomic(article, 'plaintext', strip_tags(f"{article.title or ''}\n\n{article.body or ''}").strip())
        annotate.words.fast_annotate(article)
        annotate.phrases.annotate_phrases_with_placeholders(article)
        inflate.save_inflated(article)

        # We can open the article detail page before the results of the below are complete - so we run them
        # as separate tasks and pipe the results to the user in realtime
        update_article_summary.delay_on_commit(article.pk)

        update_phrase_annotations.delay_on_commit(article.pk)

        update_atomic(article, 'is_ready_to_view', True)

        # Call the new TTS task
        generate_audio.delay_on_commit(article.pk)

    except Exception:
        send_error()
        raise

    return send_success()



