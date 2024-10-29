
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/articles/(?P<pk>\d+)$', consumers.ArticleProgressConsumer.as_asgi()),
    re_path(r'^ws/chat/(?P<pk>\d+)$', consumers.ChatConsumer.as_asgi()),
    re_path(r'^ws/loading/(?P<pk>\d+)$', consumers.ArticleLoadingConsumer.as_asgi()),

]
