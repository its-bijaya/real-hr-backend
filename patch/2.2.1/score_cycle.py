from irhrs.task.models.task import TaskAssociation, TaskVerificationScore


def arrange_score_as_cycle_form():
    for assoc in TaskAssociation.objects.filter(association='R',
                                                score__isnull=False):
        print("doing for {}".format(assoc))
        if TaskVerificationScore.objects.filter(association=assoc).exists():
            print("skipping....")
            continue
        _instance = TaskVerificationScore()
        _instance.score = assoc.score
        _instance.remarks = assoc.remarks or assoc.score
        _instance.ack = assoc.ack
        _instance.ack_remarks = assoc.ack_remarks
        _instance.ack_at = assoc.modified_at if assoc.ack is not None else None
        _instance.association = assoc
        _instance.created_by = assoc.created_by
        if _instance.ack:
            _instance.modified_by = assoc.user
        else:
            _instance.modified_by = assoc.created_by
        _instance.save()

        if not assoc.ack:
            assoc.efficiency_from_priority = None
            assoc.efficiency_from_timely = None
            assoc.efficiency_from_score = None
            assoc.efficiency = None
            assoc.save()
