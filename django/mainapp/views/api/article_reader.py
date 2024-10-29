"""
REST API for react article reader.
"""
import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, serializers

from mainapp.models import Article, Word, CharacterPinyin, PhraseAnnotation


class WordSerializer(serializers.ModelSerializer):

    class Meta:
        model = Word
        fields = ['pk', 'client_obj']


class CharacterPinyinSerializer(serializers.ModelSerializer):

    class Meta:
        model = CharacterPinyin
        fields = ['pk', 'client_obj']


class PhraseSerializer(serializers.ModelSerializer):

    client_obj = serializers.SerializerMethodField()

    def get_client_obj(self, obj):
        return obj.compute_client_obj()

    class Meta:
        model = PhraseAnnotation
        fields = ['pk', 'client_obj']


class ArticleSerializer(serializers.ModelSerializer):

    words = serializers.SerializerMethodField()
    cps = serializers.SerializerMethodField()
    phrases = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['pk', 'english_summary', 'inflated', 'words', 'cps', 'phrases']

    def get_words(self, obj):
        words = obj.get_words()
        return WordSerializer(words, many=True).data

    def get_cps(self, obj):
        cps = obj.get_cps()
        return CharacterPinyinSerializer(cps, many=True).data

    def get_phrases(self, obj):
        phrases = obj.get_phrases()
        return PhraseSerializer(phrases, many=True).data

    def to_representation(self, instance):
        # Return dicts instead of lists
        representation = super().to_representation(instance)
        representation['words'] = {x['pk']: x['client_obj'] for x in representation['words']}
        representation['cps'] = {x['pk']: x['client_obj'] for x in representation['cps']}
        representation['phrases'] = {x['pk']: x['client_obj'] for x in representation['phrases']}
        return representation


class ArticleReaderAPIView(generics.RetrieveAPIView):
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()


@method_decorator(csrf_exempt, name='dispatch')
class ReaderFeedbackAPIView(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)

            return JsonResponse({'status': 'success', 'message': 'Thank you for your feedback!'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': "Unknown error"}, status=500)

