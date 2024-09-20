from django.core.cache import cache


def set_training_members():
    from irhrs.training.models import Training

    trainings = Training.objects.all()

    training_members = {}

    for training in trainings:
        training_members.update({
            training.id: set(training.user_trainings.all().values_list('user', flat=True))
        })
    cache.set('training_members', training_members)


def find_training_members(training):
    """
    find members of the training

    :param training: training_id
    :return:
    """
    training_members = cache.get('training_members', ...)
    if training_members is ...:
        set_training_members()
        training_members = cache.get('training_members')

    return training_members.get(training, [])
