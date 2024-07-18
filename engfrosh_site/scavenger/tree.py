from common_models.models import Puzzle, PuzzleStream, Team, TeamPuzzleActivity, Setting


def generate_tree(team: Team):
    lookahead = Setting.objects.get_or_create(id="Scav Lookahead", defaults={"value": "2"})[0]
    lookahead = int(lookahead.value)
    branch_lookahead = Setting.objects.get_or_create(id="Scav Branch Lookahead", defaults={"value": "1"})[0]
    branch_lookahead = int(branch_lookahead.value)
    fow_on_branches = Setting.objects.get_or_create(id="Fog Of War On Branches", defaults={"value": "True"})[0]
    fow_on_branches = bool(fow_on_branches.value)
    result = {}
    streams = PuzzleStream.objects.filter(enabled=True)
    activities = TeamPuzzleActivity.objects.select_related()
    activities = activities.filter(puzzle__stream__in=streams, puzzle__enabled=True, team=team)
    unlocked_branches = []
    for activity in activities:
        if activity.puzzle.stream not in unlocked_branches:
            unlocked_branches += [activity.puzzle.stream]
    pending_branches = []  # Branches that will be unlocked by an active puzzle
    pending_puzzles = []  # Puzzles that will be unlockedby an active puzzle on a new branch
    orders = {}  # Cache to look up puzzle order by name without hitting db
    for branch in unlocked_branches:
        branch_dict = {}
        branch_activities = activities.filter(puzzle__stream=branch).order_by('puzzle__order')
        if len(branch_activities) > 0:  # Populate puzzles that are before the first active puzzle
            # mostly useful for puzzles that open specific branch puzzles
            first_order = branch_activities[0].puzzle.order
            pre_puzzles = Puzzle.objects.filter(enabled=True, stream=branch, order__lt=first_order).order_by('order')
            for puzzle in pre_puzzles:
                puzzle_arr = ["hidden", "", ""]
                branch_dict[puzzle.name] = puzzle_arr
        for activity in branch_activities:
            puzzle = activity.puzzle
            orders[puzzle.name] = puzzle.order
            puzzle_arr = []
            if activity.is_completed:
                puzzle_arr += ["solved"]
            else:
                puzzle_arr += ["active"]
                if puzzle.stream_branch is not None:
                    pending_branches += [puzzle.stream_branch]
                if puzzle.stream_puzzle is not None:
                    pending_puzzles += [puzzle.stream_puzzle]
            if branch.default:
                if activity == branch_activities[0]:
                    puzzle_arr += ["start"]
                elif activity == branch_activities[len(branch_activities)-1]:
                    puzzle_arr += ["end"]
                else:
                    puzzle_arr += [""]
            else:
                if activity == branch_activities[0]:
                    puzzle_set = branch.branch_puzzle.all()
                    if len(puzzle_set) == 0:
                        puzzle_set = puzzle.puzzle_opener.all()
                        if len(puzzle_set) == 0:
                            puzzle_arr += [""]
                        else:
                            puzzle_arr += [puzzle_set[0].name]
                    else:
                        puzzle_arr += [puzzle_set[0].name]
                else:
                    puzzle_set = puzzle.puzzle_opener.all()
                    if len(puzzle_set) == 0:
                        puzzle_arr += [""]
                    else:
                        puzzle_arr += [puzzle_set[0].name]
            puzzle_arr += [str(puzzle.secret_id)]
            branch_dict[puzzle.name] = puzzle_arr
        last_order = -100000  # Puzzle orders should never be smaller than this
        if len(branch_activities) > 0:
            last = branch_activities[len(branch_activities)-1]
            last_order = last.puzzle.order
        puzzles_ahead = Puzzle.objects.filter(enabled=True, stream=branch, order__gt=last_order)
        if not fow_on_branches and not branch.default:
            puzzles_ahead = puzzles_ahead.order_by('order')
        else:
            puzzles_ahead = puzzles_ahead.order_by('order')[:lookahead]
        for puzzle in puzzles_ahead:
            orders[puzzle.name] = puzzle.order
            puzzle_arr = ["hidden", "", ""]
            branch_dict[puzzle.name] = puzzle_arr
        result[branch.name] = branch_dict
    for branch in pending_branches:
        branch_dict = {}
        puzzles = Puzzle.objects.filter(enabled=True, stream=branch).order_by('order')[:branch_lookahead]
        for puzzle in puzzles:
            orders[puzzle.name] = puzzle.order
            if puzzle == puzzles[0]:
                branch_dict[puzzle.name] = ["hidden", branch.branch_puzzle.all()[0].name, ""]
            else:
                branch_dict[puzzle.name] = ["hidden", "", ""]
        result[branch.name] = branch_dict
    for puzzle in pending_puzzles:
        old_order = orders.get(puzzle.name, None)
        orders[puzzle.name] = puzzle.order
        puzzles_ahead = Puzzle.objects.filter(enabled=True, stream=puzzle.stream, order__gt=puzzle.order)
        puzzles_ahead = puzzles_ahead.order_by('order')[:branch_lookahead]
        if puzzle.stream.name not in result.keys():
            branch_dict = {}
            puzzles_before = Puzzle.objects.filter(enabled=True, stream=puzzle.stream, order__lt=puzzle.order)
            puzzles_before = puzzles_before.order_by('order')
            for puzzle2 in puzzles_before:
                orders[puzzle2.name] = puzzle2.order
                branch_dict[puzzle2.name] = ["hidden", "", ""]
            branch_dict[puzzle.name] = ["hidden", puzzle.puzzle_opener.all()[0].name, ""]
            for puzzle2 in puzzles_ahead:
                orders[puzzle2.name] = puzzle2.order
                branch_dict[puzzle2.name] = ["hidden", "", ""]
            result[puzzle.stream.name] = branch_dict
        else:
            old_dict = result[puzzle.stream.name]
            if orders[old_dict[0][0]] > puzzle.order:
                branch_dict = {}
                branch_dict[puzzle.name] = ["hidden", puzzle.puzzle_opener[0].name, ""]
                for puzzle2 in puzzles_ahead:
                    branch_dict[puzzle2.name] = ["hidden", "", ""]
                branch_dict.update(old_dict)
                result[puzzle.stream.name] = branch_dict
            elif orders[old_dict[-1][0]] < puzzle.order:
                branch_dict = old_dict
                branch_dict[puzzle.name] = ["hidden", puzzle.puzzle_opener[0].name, ""]
                for puzzle2 in puzzles_ahead:
                    branch_dict[puzzle2.name] = ["hidden", "", ""]
                result[puzzle.stream.name] = branch_dict
            else:
                if old_order is not None:
                    continue
                branch_dict = {}
                before = None
                for name, value in old_dict.items():
                    order = orders[name]
                    if order > puzzle.order:
                        before = name
                        break
                    else:
                        branch_dict[name] = value
                branch_dict[puzzle.name] = ["hidden", puzzle.puzzle_opener[0].name, ""]
                for puzzle2 in puzzles_ahead:
                    branch_dict[puzzle2.name] = ["hidden", "", ""]
                found = False
                for name, value in old_dict.items():
                    if name == before:
                        found = True
                    if found:
                        branch_dict[name] = value
                result[puzzle.stream.name] = branch_dict
    return result
