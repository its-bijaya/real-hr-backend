ADMIN = "Admin"
NORMAL_USER = "User"
SUPERVISOR = "Supervisor"

EXPORTED_AS_CHOICES = (
    (ADMIN, "Admin"),
    (NORMAL_USER, "User"),
    (SUPERVISOR, "Supervisor")
)

QUEUED, PROCESSING, FAILED, COMPLETED = "Queued", "Processing", "Failed", "Completed"

EXPORT_STATUS_CHOICES = (
    (QUEUED, "Queued"),
    (PROCESSING, "Processing"),
    (FAILED, "Failed"),
    (COMPLETED, "Completed")
)
