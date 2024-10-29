from .core import \
    CharacterPinyin, \
    CharacterVariant, \
    Character, \
    Syllable, \
    Pinyin, \
    Word, \
    WordChar, \
    Definition, \
    Meaning

from .articles import Article, Annotation, PhraseAnnotation


from django.db import transaction

def update_atomic(model_instance, field_name, new_value):
    """
    Update a specific field of a Django model instance atomically.

    Parameters:
    model_instance (models.Model): The Django model instance to update.
    field_name (str): The name of the field to update.
    new_value (Any): The new value to assign to the field.
    """

    # Also set this, so when we use instance.field_name later it's set as expected
    setattr(model_instance, field_name, new_value)

    with transaction.atomic():
        obj = model_instance.__class__.objects.select_for_update().get(pk=model_instance.pk)
        setattr(obj, field_name, new_value)
        obj.save()

