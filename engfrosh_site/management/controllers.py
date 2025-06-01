from common_models.models import UserDetails, Team, FacilShift, FacilShiftSignup, BooleanSetting, \
                                 DiscordChannel, Puzzle, TeamPuzzleActivity, Setting
from django.contrib.auth.models import User
from datetime import datetime


def create_bus_shifts():
    for team in Team.objects.all():
        shifts = FacilShift.objects.filter(name=team.display_name + "-BusMorning")
        if len(shifts) > 0:
            shift = shifts.first()
        else:
            shift = FacilShift(name=team.display_name + "-BusMorning", desc="bus",
                               flags="bus", type="wt", max_facils=0, administrative=True)
            shift.save()
        for signup in FacilShiftSignup.objects.filter(shift=shift):
            signup.delete()
        for user in team.group.user_set.all():
            signup = FacilShiftSignup(shift=shift, user=user)
            signup.save()


def complete_waiver(details: UserDetails):
    details.waiver_completed = True
    details.save()

def complete_wt_waiver(details: UserDetails):
    details.wt_waiver_completed = True
    details.save()

def shift_check_in(signup: FacilShiftSignup, attendance: bool):
    if signup is None:
        return (False, "Signup not found!")
    shift = signup.shift
    if shift.type == "wt" and not (signup.user.details.waiver_completed and signup.user.details.wt_waiver_completed):
        return (False, "Incomplete waiver!")
    signup.attendance = attendance
    signup.save()
    return (True,)


def global_toggle_weeklongs(audit_user: str):
    scav = BooleanSetting.objects.get(id="SCAVENGER_ENABLED")
    tradeup = BooleanSetting.objects.get(id="TRADE_UP_ENABLED")
    scav.value = not scav.value
    tradeup.value = not tradeup.value
    scav.save()
    tradeup.save()
    scav_txt = "locked"
    if scav.value:
        scav_txt = "unlocked"
    tradeup_txt = "locked"
    if tradeup.value:
        tradeup_txt = "unlocked"
    DiscordChannel.send_to_updates_channels("@everyone - " + audit_user +
                                            ": Scav is now " + scav_txt + ". Trade Up is now " + tradeup_txt)


def get_user_shifts(user: User):
    my_shifts = []
    if not user.is_staff:
        my_shifts_i = FacilShiftSignup.objects.filter(user=user, shift__administrative=False) \
                                      .select_related().order_by('shift__start')
    else:
        my_shifts_i = FacilShiftSignup.objects.filter(user=user) \
                                      .select_related().order_by('shift__start')
    for shift in my_shifts_i:
        my_shifts += [shift.shift]
    return my_shifts


def get_eligible_shifts(user: User):
    max_shifts = int(Setting.objects.get_or_create(id="MAX_FACIL_SHIFTS",
                                                   defaults={"value": "2"})[0].value)
    shift_count = len(FacilShiftSignup.objects.filter(user=user, shift__administrative=False))
    if shift_count >= max_shifts:
        return []
    rshifts = []
    shifts = list(FacilShift.objects.filter(administrative=False).order_by('start').all())
    my = FacilShiftSignup.objects.filter(user=user)
    for shift in shifts:
        found = False
        signups = shift.facil_count
        for s in my:
            if s.shift == shift:
                found = True
                break
        if signups < shift.max_facils and not found and not shift.is_passed:
            rshifts += [shift]
    return rshifts


def user_add_shift(user: User, shift: FacilShift):
    if shift is None:
        return (False, "Shift not found")
    max_shifts = int(Setting.objects.get_or_create(id="MAX_FACIL_SHIFTS",
                                                   defaults={"value": "2"})[0].value)
    shift_count = len(FacilShiftSignup.objects.filter(user=user, shift__administrative=False))
    if shift_count >= max_shifts:
        return (False, "At shift limit")
    if shift.is_passed:
        return (False, "Shift has passed")
    if shift.facil_count >= shift.max_facils:
        return (False, "Shift is at capacity")
    signup = FacilShiftSignup.objects.filter(user=user, shift=shift).first()
    if signup is not None:
        return (False, "You have already signed up for this shift")
    signup = FacilShiftSignup(user=user, shift=shift)
    signup.save()
    return (True,)


def user_remove_shift(user: User, shift: FacilShift):
    lockout_time = int(Setting.objects.get_or_create(id="Facil Shift Drop Deadline",
                                                     defaults={"value": "0"})[0].value)
    if shift is None:
        return (False, "Shift not found!")
    can_remove = True
    if datetime.utcfromtimestamp(lockout_time) <= datetime.now() and lockout_time != 0:
        can_remove = False
    if not can_remove:
        return (False, "Removing shifts is disabled")
    signup = FacilShiftSignup.objects.filter(shift=shift, user=user).first()
    if signup is None:
        return (False, "Signup not found!")
    if shift.is_cutoff:
        return (False, "Shift is cut off!")
    signup.delete()
    return (True,)


def copy_shift(shift: FacilShift):
    if shift is None:
        return False
    signups = FacilShiftSignup.objects.filter(shift=shift)
    shift.pk = None  # Copy to new shift per
    # https://stackoverflow.com/questions/4733609/how-do-i-clone-a-django-model-instance-object-and-save-it-to-the-database
    shift.id = None
    shift.name += "-copy"
    shift.save()
    for signup in signups:
        if signup.attendance:
            new_signup = FacilShiftSignup(shift=shift, user=signup.user)
            new_signup.save()
    return True


def run_report(requirements):
    users = UserDetails.objects.select_related('user').all()
    data = []
    for user in users:
        met = True
        for r in requirements:
            d = r[0].split(".")
            obj = d[0]
            name = d[1]
            if obj == "details":
                value = str(getattr(user, name))
                if callable(value):
                    value = value()
            elif obj == "user":
                value = str(getattr(user.user, name))
                if callable(value):
                    value = value()
            if r[2] == "=" and value.lower() != str(r[1]).lower():
                met = False
                break
            elif r[2] == "!=" and value.lower() == str(r[1]).lower():
                met = False
                break
            elif r[2] == "ew" and not value.lower().endswith(str(r[1]).lower()):
                met = False
                break
            elif r[2] == "new" and value.lower().endswith(str(r[1]).lower()):
                met = False
                break
        if met:
            data += [user]
    return data


def toggle_scav_puzzle(puzzle: Puzzle):
    if puzzle is None:
        return (False, "Puzzle does not exist")
    if puzzle.stream_branch is not None or puzzle.stream_puzzle is not None:
        return (False, "This will break things! Aborting.")
    teams = Team.objects.all()
    next_puzzle = puzzle.stream.get_next_enabled_puzzle(puzzle)
    for team in teams:
        activity = TeamPuzzleActivity.objects.filter(puzzle=puzzle, team=team, puzzle_completed_at=None)
        print(team.display_name, len(activity))
        if len(activity) == 0:
            continue
        activity = activity.first()
        if next_puzzle is None:
            activity.delete()
        else:
            activity.puzzle = next_puzzle
            activity.save()
        team.invalidate_tree = True
        team.save()
    if puzzle.enabled:
        puzzle.enabled = False
        puzzle.save()
    else:
        puzzle.enabled = True
        puzzle.save()
    return (True,)
