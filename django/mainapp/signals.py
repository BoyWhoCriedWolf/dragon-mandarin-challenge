
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from mainapp.models import Annotation


@receiver(post_delete, sender=Annotation)
def delete_phrase_annotation(sender, instance, **kwargs):
    # If there is a PhraseAnnotation associated with the Annotation, delete it
    if instance.phrase:
        instance.phrase.delete()

# Connect the signal
post_delete.connect(delete_phrase_annotation, sender=Annotation)


