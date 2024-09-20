"""@irhrs_docs"""


def valid_instance_from_model(instance_id, model):
    """
    Raises an assertion error if the instance id doesn't belongs to the
    model
    """
    try:
        value = model.objects.get(id=instance_id)
    except model.DoesNotExist:
        raise AssertionError(f'Not an instance from {model.__name__}')
    return value
