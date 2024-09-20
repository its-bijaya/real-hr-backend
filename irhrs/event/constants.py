PENDING = 'Pending'
ACCEPTED = 'Accepted'
REJECTED = 'Rejected'
MAYBE = 'Maybe'

MEMBERS_INVITATION_STATUS = (
    (PENDING, 'Pending'),
    (ACCEPTED, 'Accepted'),
    (REJECTED, 'Rejected'),
    (MAYBE, 'Maybe')
)

PRIVATE = 'Private'
PUBLIC = 'Public'

EVENT_TYPE_CHOICES = (
    (PRIVATE, 'Private'),
    (PUBLIC, 'Public'),
)

# Leave Category choices
SEMINAR = 'Seminar'
WORKSHOP = 'Workshop'
MEETING = 'Meeting'
CONFERENCE = 'Conference'
INTERVIEW = 'Interview'
REFRESHMENT = 'Refreshment'
RECREATION = 'Recreation'
TRAINING = 'Training'
GROUP_DISCUSSION = 'Group Discussion'
PANEL_DISCUSSION = 'Panel Discussion'
CELEBRATION = 'Celebration'
DEVELOPMENT_PROGRAMS = 'Development Programs'
OTHERS = 'Others'

EVENT_CATEGORY_CHOICES = (
    (SEMINAR, SEMINAR),
    (WORKSHOP, WORKSHOP),
    (MEETING, MEETING),
    (CONFERENCE, CONFERENCE),
    (INTERVIEW, INTERVIEW),
    (REFRESHMENT, REFRESHMENT),
    (RECREATION, RECREATION),
    (TRAINING, TRAINING),
    (PANEL_DISCUSSION, 'Panel Discussion'),
    (GROUP_DISCUSSION, 'Group Discussion'),
    (CELEBRATION, CELEBRATION),
    (DEVELOPMENT_PROGRAMS, 'Development Programs'),
    (OTHERS, OTHERS)
)

INSIDE = 'Inside'
OUTSIDE = 'Outside'

EVENT_LOCATION = (
    (INSIDE, INSIDE),
    (OUTSIDE, OUTSIDE)
)


MEETING_DOCUMENT_MAX_UPLOAD_SIZE = 2 * 1024 * 1024


MEETING_ORGANIZER = 'Meeting Organizer'
TIME_KEEPER = 'Time Keeper'
TIME_KEEPER_AND_MINUTER = 'Time Keeper / Minuter'
MINUTER = 'Minuter'
MEMBER = 'Member'

MEMBER_POSITION = (
    (MEETING_ORGANIZER, MEETING_ORGANIZER),
    (TIME_KEEPER_AND_MINUTER, TIME_KEEPER_AND_MINUTER),
    (TIME_KEEPER, TIME_KEEPER),
    (MINUTER, MINUTER),
    (MEMBER, MEMBER)
)