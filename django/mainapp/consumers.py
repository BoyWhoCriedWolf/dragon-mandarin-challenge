import textwrap
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from mainapp import gpt
from mainapp.models import Article, PhraseAnnotation, Word, CharacterPinyin


def get_client_ip_ws(consumer):
    print(str(consumer.scope))
    x_real_ip = dict(consumer.scope['headers']).get(b'x-real-ip')
    if x_real_ip:
        return x_real_ip.decode()
    else:
        return consumer.scope['client'][0]


# Updates the article loading page (while data is being scraped from article URL, before article content is there)
class ArticleLoadingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        article_pk = self.scope['url_route']['kwargs']['pk']
        self.article = await database_sync_to_async(self.get_article)(article_pk)

        # Add this consumer to the group for this article
        await self.channel_layer.group_add(
            self.article.loading_channel_name,
            self.channel_name
        )

        await self.accept()

        # If the article has already finished loading, send this (solves the problem where the html page loads
        # before the article is ready, then the job finishes, then the websocket loads (but doesn't see the finished message)
        self.article = await database_sync_to_async(self.get_article)(article_pk)
        if self.article.is_ready_to_view:
            await self.send(text_data=json.dumps({
                'type': 'success',
            }))

    def get_article(self, pk):
        return Article.objects.get(pk=pk)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.article.loading_channel_name,
            self.channel_name
        )

    async def status_success(self, event):
        await self.send(text_data=json.dumps({
            'type': 'success',
        }))

    async def status_error(self, event):
        await self.send(text_data=json.dumps({
            'type': 'error',
        }))


# Updates the article detail page with summary and translations
class ArticleProgressConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        article_pk = self.scope['url_route']['kwargs']['pk']
        self.article = await database_sync_to_async(self.get_article)(article_pk)

        # Add this consumer to the group for this article
        await self.channel_layer.group_add(
            self.article.channel_name,
            self.channel_name
        )

        await self.accept()

    def get_article(self, pk):
        return Article.objects.get(pk=pk)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.article.channel_name,
            self.channel_name
        )

    async def phrase_update(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'phrase',
            'data': message
        }))

    async def summary_update(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'summary',
            'data': message
        }))

    async def inflated_update(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'inflatedUpdate',
            'data': message
        }))

    async def inflated_refresh(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'inflatedRefresh',
            'data': message
        }))


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        article_pk = self.scope['url_route']['kwargs']['pk']
        self.article = await database_sync_to_async(self.get_article)(article_pk)

        query_params = parse_qs(self.scope['query_string'].decode())
        phrase_pk = query_params.get('phrasePk', [None])[0]
        obj_pk = query_params.get('objPk', [None])[0]
        obj_type = query_params.get('objType', [None])[0]

        await self.get_prompt_context(phrase_pk, obj_pk, obj_type)

        self.conversation = []
        await self.accept()

    def get_article(self, pk):
        return Article.objects.get(pk=pk)

    @database_sync_to_async
    def get_prompt_context(self, phrase_pk, obj_pk, obj_type):
        assert phrase_pk
        self.phrase_str = PhraseAnnotation.objects.get(pk=phrase_pk).text
        if obj_pk:
            if obj_type == 'word':
                self.word_str = Word.objects.get(pk=obj_pk).char_string
            elif obj_type == 'cp':
                self.word_str = CharacterPinyin.objects.get(pk=obj_pk).char_string
        else:
            self.word_str = None


    async def disconnect(self, close_code):
        pass

    @property
    def conversation_with_prompt(self):

        prompt = textwrap.dedent("""
        You are a Chinese language tutor. Together, we are focusing on this sentence:

        {phrase}
        
        {word_prompt}

        Answer all questions as concisely as possible, in the style of a Chinese language teacher. If my question is in English,
        you should respond in English (except when using Chinese words to explain things). If my question is entirely in Chinese, respond in Chinese.
        
        If I say something completely off-topic (unrelated to Chinese), or it seems like I don't understand what the purpose of this chat is, respond instead with either
        
        1. "Ask me anything about words or grammar in this sentence!"
        2. "Hi! Ask me anything about words or grammar in this sentence."
        
        depending which is more appropriate for the context.

        First question:
        {msg}
        """).strip()

        if self.word_str:
            word_prompt = f"Specifically, we're focusing on the word \"{self.word_str}\""
        else:
            word_prompt = ""

        return [
            {
                "sender": self.conversation[0]['sender'],
                "message": prompt.format(
                    phrase=self.phrase_str,
                    word_prompt=word_prompt,
                    msg=self.conversation[0],
                ),
            }
        ] + self.conversation[1:]

    def get_messages(self):
        # Convert self.conversation to OpenAI format
        messages = [{"role": "system", "content": "You are a helpful language tutor."}]
        for msg in self.conversation_with_prompt:
            if msg['sender'] == 'assistant':
                messages.append({"role": "assistant", "content": msg['message']})
            else:
                messages.append({"role": "user", "content": msg['message']})
        return messages


    async def receive(self, text_data):

        text_data_json = json.loads(text_data)

        if 'resetConversation' in text_data_json:
            self.conversation = text_data_json['resetConversation']
        elif 'message' in text_data_json:
            msg = text_data_json['message']
            self.conversation.append({'sender': 'user', 'message': msg})

        assistant_response = gpt.get_conversation_response(self.get_messages(), model="gpt-4o")
        self.conversation.append({'sender': 'assistant', 'message': assistant_response})

        await self.send(text_data=json.dumps({
            'message': assistant_response,
        }))

