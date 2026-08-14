"""
Management command: python manage.py seed
Creates demo users, employee levels, letters, movements, and comments.
Safe to run multiple times — uses get_or_create throughout.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, Role, EmployeeLevel
from apps.letters.models import Letter, LetterStatus
from apps.workflow.models import Movement, Comment


PASSWORD = "Fms@2026"


class Command(BaseCommand):
    help = "Seed the database with demo users, levels, and correspondence."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== FileFlow Seed Data ==="))

        # ── 1. Users ──────────────────────────────────────────────────────────
        self.stdout.write("Creating users…")

        director, _ = User.objects.get_or_create(username="director", defaults={
            "first_name": "Niranjan", "last_name": "Vishwakarma",
            "email": "director@gmail.com",
            "role": Role.DIRECTOR, "is_staff": True, "is_superuser": True,
        })
        if not director.has_usable_password() or _:
            director.set_password(PASSWORD)
            director.save()

        minister, _ = User.objects.get_or_create(username="minister", defaults={
            "first_name": "Kunal", "last_name": "Sinha",
            "email": "minister@gmail.com",
            "role": Role.MINISTER,
        })
        if not minister.has_usable_password() or _:
            minister.set_password(PASSWORD)
            minister.save()

        emp1, _ = User.objects.get_or_create(username="emp1", defaults={
            "first_name": "Dilip", "last_name": "Kumar",
            "email": "dilip@gmail.com",
            "role": Role.EMPLOYEE, "level": 1,
        })
        if not emp1.has_usable_password() or _:
            emp1.set_password(PASSWORD)
            emp1.save()

        emp2, _ = User.objects.get_or_create(username="emp2", defaults={
            "first_name": "Pankaj", "last_name": "Singh",
            "email": "pankaj@gmail.com",
            "role": Role.EMPLOYEE, "level": 2,
        })
        if not emp2.has_usable_password() or _:
            emp2.set_password(PASSWORD)
            emp2.save()

        emp3, _ = User.objects.get_or_create(username="emp3", defaults={
            "first_name": "Deepak", "last_name": "Kumar",
            "email": "deepak@gmail.com",
            "role": Role.EMPLOYEE, "level": 3,
        })
        if not emp3.has_usable_password() or _:
            emp3.set_password(PASSWORD)
            emp3.save()

        self.stdout.write(self.style.SUCCESS(
            "  ✓ 5 users created (director / minister / emp1 / emp2 / emp3)"
        ))

        # ── 2. Employee levels ────────────────────────────────────────────────
        self.stdout.write("Creating employee levels…")
        EmployeeLevel.objects.get_or_create(level=1, defaults={
            "name": "Initial Review",
            "description": "First-stage examination of the correspondence — checks completeness and basic eligibility.",
        })
        EmployeeLevel.objects.get_or_create(level=2, defaults={
            "name": "Senior Review",
            "description": "In-depth technical assessment by a senior officer.",
        })
        EmployeeLevel.objects.get_or_create(level=3, defaults={
            "name": "Final Approval",
            "description": "Final sign-off by the highest-level officer in the chain before completion.",
        })
        self.stdout.write(self.style.SUCCESS("  ✓ 3 employee levels configured"))

        # ── 3. Letters ────────────────────────────────────────────────────────
        self.stdout.write("Creating correspondence…")

        def make_letter(title, description):
            """Create a letter in DRAFT state; returns the letter."""
            letter = Letter(
                title=title,
                description=description,
                created_by=director,
                current_holder=director,
            )
            letter.save()  # sets reference_no; status=DRAFT
            return letter

        def move(letter, from_user, to_user, action, comment=""):
            Movement.objects.create(
                letter=letter, from_user=from_user, to_user=to_user,
                action=action, comment=comment,
            )

        def bypass_status(letter, status, holder):
            """Bypass FSM protection for seed data only."""
            Letter.objects.filter(pk=letter.pk).update(
                status=status, current_holder=holder,
            )

        if Letter.objects.filter(created_by=director).count() >= 6:
            self.stdout.write(self.style.WARNING(
                "  ⚠ Letters already exist — skipping to avoid duplicates."
            ))
        else:
            # Letter 1 — WITH_MINISTER
            l1 = make_letter(
                "Budget Approval Request FY 2026",
                "Request for approval of the revised departmental budget for the financial year 2026. "
                "Includes capital expenditure projections and headcount adjustments.",
            )
            move(l1, director, director, "CREATE")
            bypass_status(l1, LetterStatus.WITH_MINISTER, minister)
            move(l1, director, minister, "FORWARD", "Please review and advise at your earliest convenience.")
            Comment.objects.create(letter=l1, author=director,
                body="Attached supporting financials for reference.")

            # Letter 2 — WITH_EMPLOYEE L1
            l2 = make_letter(
                "Staff Recruitment Authorization",
                "Authorization request to recruit 12 new technical officers across three departments "
                "as part of the 2026 headcount plan.",
            )
            move(l2, director, director, "CREATE")
            bypass_status(l2, LetterStatus.WITH_EMPLOYEE, emp1)
            move(l2, director, emp1, "FORWARD", "Please conduct initial screening of the recruitment criteria.")

            # Letter 3 — COMPLETE (went through all levels)
            l3 = make_letter(
                "Annual Departmental Report Submission",
                "Formal submission of the annual departmental performance report covering all KPIs, "
                "budget utilisation, and outcome metrics for FY 2025.",
            )
            move(l3, director, director, "CREATE")
            bypass_status(l3, LetterStatus.WITH_EMPLOYEE, emp1)
            move(l3, director, emp1, "FORWARD", "Please begin initial review.")
            bypass_status(l3, LetterStatus.WITH_EMPLOYEE, emp2)
            move(l3, emp1, emp2, "FORWARD", "Initial review complete. Forwarding for senior assessment.")
            Comment.objects.create(letter=l3, author=emp1,
                body="All KPIs confirmed accurate against the source data provided.")
            bypass_status(l3, LetterStatus.WITH_EMPLOYEE, emp3)
            move(l3, emp2, emp3, "FORWARD", "Senior review passed. Ready for final approval.")
            Comment.objects.create(letter=l3, author=emp2,
                body="Budget utilisation figures verified against the finance ledger.")
            bypass_status(l3, LetterStatus.COMPLETE, emp3)
            move(l3, emp3, emp3, "COMPLETE", "Final review complete. Report approved for submission.")

            # Letter 4 — WITH_DIRECTOR (returned from Minister)
            l4 = make_letter(
                "Equipment Procurement Order #EPO-2026-004",
                "Procurement order for 40 desktop workstations and associated peripherals "
                "for the new operations centre.",
            )
            move(l4, director, director, "CREATE")
            bypass_status(l4, LetterStatus.WITH_MINISTER, minister)
            move(l4, director, minister, "FORWARD", "Seeking ministerial approval before issuing the tender.")
            bypass_status(l4, LetterStatus.WITH_DIRECTOR, director)
            move(l4, minister, director, "RETURN",
                 "Please revise the specifications to include energy-efficient models and resubmit.")
            Comment.objects.create(letter=l4, author=minister,
                body="Recommend sourcing certified green-energy compliant hardware per the new policy circular.")

            # Letter 5 — WITH_EMPLOYEE L2
            l5 = make_letter(
                "Training Programme Approval — Leadership Series",
                "Approval for the 2026 Leadership Development Training Programme for 25 mid-level officers. "
                "Training provider: National Leadership Academy.",
            )
            move(l5, director, director, "CREATE")
            bypass_status(l5, LetterStatus.WITH_EMPLOYEE, emp1)
            move(l5, director, emp1, "FORWARD")
            Comment.objects.create(letter=l5, author=emp1,
                body="Eligibility criteria reviewed. All 25 nominees meet the prerequisites.")
            bypass_status(l5, LetterStatus.WITH_EMPLOYEE, emp2)
            move(l5, emp1, emp2, "FORWARD", "Level 1 review complete.")

            # Letter 6 — WITH_MINISTER (second minister letter)
            l6 = make_letter(
                "Office Renovation Clearance — Block C",
                "Clearance request for renovation works at Block C, second floor. "
                "Works include structural repairs, HVAC replacement, and accessibility upgrades.",
            )
            move(l6, director, director, "CREATE")
            bypass_status(l6, LetterStatus.WITH_MINISTER, minister)
            move(l6, director, minister, "FORWARD",
                 "Works scheduled to commence Q3 2026 — ministerial sign-off required.")
            Comment.objects.create(letter=l6, author=director,
                body="Three contractor quotes attached for the minister's reference.")

            self.stdout.write(self.style.SUCCESS("  ✓ 6 letters created with movements and comments"))

        # ── Summary ───────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed data ready. Login credentials:"))
        self.stdout.write(self.style.SUCCESS(f"  username=director   password={PASSWORD}  (Director / Super Admin)"))
        self.stdout.write(self.style.SUCCESS(f"  username=minister   password={PASSWORD}  (Minister)"))
        self.stdout.write(self.style.SUCCESS(f"  username=emp1       password={PASSWORD}  (Employee Level 1)"))
        self.stdout.write(self.style.SUCCESS(f"  username=emp2       password={PASSWORD}  (Employee Level 2)"))
        self.stdout.write(self.style.SUCCESS(f"  username=emp3       password={PASSWORD}  (Employee Level 3)"))
        self.stdout.write("")
