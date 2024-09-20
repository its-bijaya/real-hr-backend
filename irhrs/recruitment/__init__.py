"""@irhrs_docs"""

"""

Following are the steps of selection process of candidate

1. Candidates Apply the job

2. Candidates are listed and candidate can be rejected or marked as duplicate
    * If candidate are rejected status of candidate set to rejected status. JobApply status is set
      to rejected and new JobApplyStage is created with rejected status.
    * If candidate are marked as duplicate then candidate are set to rejected status with above
      process and extra field is added in data field of JobApply with duplicate=True

3. After the rejection and mark as duplicate process candidates are initialized for further process
   which is PreScreening and PreScreening object is initialized for those candidates who are
   not rejected.

4. Candidate PreScreening is updated with respective responsible person and question set.

5. Responsible person fill up the question answer Form where question answer is derived from
   question set and response are preserved in data field.

6. Hr verifies the response and set PreScreening as completed.

7. Completed PreScreening can be forwarded to Post Screening on the basis of score or category
   where we mark applications fall under the score or category as screened and Post Screening is
   initialized for those applications [this process can be repeated multiple times].

4. Candidate PostScreening is updated with respective responsible person and question set.

5. Responsible person fill up the question answer Form where question answer is derived from
   question set and response are preserved in data field.

6. Hr verifies the response and set PostScreening as completed.

7. Hr initialize NoObjection with responsible person, stage as shortlisted, email, template and
   stage is determined as job apply stage where the candidate will be after verification of
   NoObjection.

8. Responsible Person verifies NoObjection and candidate with post_screening verified status
   set to shortlisted who falls under the score and category mentioned in NoObjection. JobApply
   status set to shortlisted and new JobApply Stage is created with shortlisted stage.
   NoObjectionViewSet's forward_candidates handles this logic. Now those who are not selected are
   set to rejected JobApply status set to rejected and new JobApply Stage is created with rejected
   stage. NoObjectionViewSet's reject_candidates handles this logic. New Step is initialized i.e
   PreScreening Interview with email_template_id mentioned in hiring info of job for those
   candidate whose status is shortlisted or who are successfully forwarded.

9. PreScreeningInterview is updated with multiple responsible person differentiate as internal
   and external and question set. Internal user will be notified with notification and external
   user will get email with unique link that they can fill up the form.

10. After form fill up from certain responsible persons, application can be mark as completed where
    aggregate score is calculated.

11. Candidate can be forwarded to next step i.e Assessment by forwarding them on the basis of score
    where we mark applications fall under the score or category as pre_screening_interviewed and
    Assessment is initialized for those applications
    [this process can be repeated multiple times].

12. Step 9, 10 and 11 is repeated for Assessment where next step is Interview and applications are
    marked as assessment_taken.

13. Step 9 and 10 is repeated for Interview hr initialize no objection as step 7.

14. In this step can candidate can be mark as rostered which is preserved in data field of JobApply
    as rostered and rostered candidate are separated and will not move forward to reference check
    until moved forward from rostered candidate list.

14. Responsible Person verifies NoObjection and candidate with assessment_taken verified status
    set to interviewed who falls under the score and category mentioned in NoObjection. JobApply
    status set to interviewed and new JobApply Stage is created with interviewed stage.
    NoObjectionViewSet's forward_candidates handles this logic. Now those who are not selected are
    set to rejected JobApply status set to rejected and new JobApply Stage is created with rejected
    stage. NoObjectionViewSet's reject_candidates handles this logic. New Step is initialized i.e
    ReferenceCheck with email_template_id mentioned in hiring info of job for those
    candidate whose status is interviewed or who are successfully forwarded.

15. Step 9, 10 and 11 is repeated for ReferenceCheck where next step is SalaryDeclaration and
    applications are marked as reference_verified.

16. SalaryDeclaration is updated with email template and email are sent to respective candidate
    where submit expected salary and multiple attachments.

17. Hr verifies those response and set SalaryDeclaration as mark as completed.

18. Hr initialize NoObjection for completed candidates and pass through no objection verification
    process where NoObjection Verifier verify individual candidate and candidate move towards
    eligible candidate list.

18. Candidate can be rejected or selected from this process and email can be send to candidate and
    this data is preserved in data of job apply tagged as confirmation_email_sent.
"""
