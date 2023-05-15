from PIL import Image, ImageDraw
from common_models.models import Puzzle, PuzzleStream, Team, TeamPuzzleActivity
from random import randint

HSPACING = 500
VSPACING = 500

XOFFSET = 750
YOFFSET = 750

CIRC_WIDTH = 200
LINE_WIDTH = 20

BRANCH_COLOR = (0, 0, 255)
DEFAULT_COLOR = (0, 255, 0)
COMPLETED_COLOR = (0, 255, 255)

MAX_LOOKAHEAD = 100


def generate_tree(team: Team):
    streams = PuzzleStream.objects.filter(enabled=True)
    v_count = len(streams)
    unlocks = {}
    enabled_streams = {}
    for j in range(1):  # This is really hacky
        for stream in streams:
            if stream.default:
                unlocks[stream.id] = 0
                enabled_streams[stream.id] = True
            puzzles = Puzzle.objects.filter(stream=stream, enabled=True)
            index = unlocks.get(stream.id, 0)
            for puzzle in puzzles:
                index += 1
                if puzzle.stream_branch is not None and unlocks.get(puzzle.stream_branch, 0) < index:
                    unlocks[puzzle.stream_branch.id] = index
                    act = TeamPuzzleActivity.objects.filter(team=team, puzzle=puzzle).first()
                    if act is not None and act.is_completed:
                        enabled_streams[puzzle.stream_branch.id] = True
    h_count = 0
    for key, value in unlocks.items():
        if value > h_count:
            h_count = value
    width = HSPACING * h_count + 2 * XOFFSET
    height = VSPACING * v_count + 2 * YOFFSET

    img = Image.new("RGB", (width, height))
    d = ImageDraw.Draw(img)
    # Draw all streams first
    direction = 1
    index = v_count/2
    count = 1
    streams = PuzzleStream.objects.filter(enabled=True)
    starts = {}
    completed = {}
    circles = []
    heads = []
    logo = None
    if team.logo is not None and team.logo:
        team.logo.open()
        logo = Image.open(team.logo)
        logo = logo.resize((CIRC_WIDTH, CIRC_WIDTH))
    for i in range(len(streams)):
        lowest = None
        for s in streams:
            if completed.get(s.id, False) is False:
                if lowest is None or unlocks[s.id] < unlocks[lowest.id]:
                    lowest = s
        stream = lowest
        if not enabled_streams.get(stream.id, False):
            continue
        completed[stream.id] = True
        xindex = unlocks[stream.id]
        if not lowest.default:
            xindex -= 1
        puzzles = Puzzle.objects.filter(stream=stream, enabled=True).order_by('order')
        first = True
        firstEnabled = True
        lastShown = None
        for j in range(len(puzzles)):
            puzzle = puzzles[j]
            if lastShown is not None and lastShown.order < puzzle.order:
                continue
            color = BRANCH_COLOR
            if stream.default:
                color = DEFAULT_COLOR
            try:
                if puzzle.is_completed_for_team(team):
                    color = COMPLETED_COLOR
            except Exception:
                pass
            x = xindex * HSPACING + XOFFSET
            y = index * VSPACING + YOFFSET
            starts[puzzle.id] = (x+CIRC_WIDTH/2, y+CIRC_WIDTH/2)
            xy = [(x, y), (x+CIRC_WIDTH, y+CIRC_WIDTH)]
            if not first:
                mid_y = (2*y+CIRC_WIDTH)/2
                rxy = [(x, mid_y), (x-HSPACING, mid_y)]
                d.line(rxy, color, LINE_WIDTH)
            # d.ellipse(xy, color)
            activity = TeamPuzzleActivity.objects.filter(team=team, puzzle=puzzle).first()
            if activity is not None and firstEnabled and not activity.is_completed:
                r = randint(0, 255)
                g = randint(0, 255)
                b = randint(0, 255)
                color = (r, g, b)
                circles += [(xy, color, True)]
                heads += [(puzzle, color)]
                if not (j + MAX_LOOKAHEAD) >= len(puzzles):
                    lastShown = puzzles[j + MAX_LOOKAHEAD]
                firstEnabled = False
            else:
                circles += [(xy, color, False)]
            xindex += 1
            first = False
        index += direction
        count += 1
        direction = (abs(direction)/direction) * -1 * count
    for puzzle in Puzzle.objects.filter(stream_branch__isnull=False):
        stream = puzzle.stream_branch
        if not enabled_streams.get(stream.id, False) and not enabled_streams.get(puzzle.stream.id, False):
            continue
        stream_puzzle = stream.first_enabled_puzzle
        if starts.get(puzzle.id, None) is None or starts.get(stream_puzzle.id, None) is None:
            continue
        d.line([starts[puzzle.id], starts[stream_puzzle.id]], (255, 0, 0), LINE_WIDTH)
    for i in range(len(circles)):
        cir = circles[i]
        if cir[2] and logo is not None:
            box = cir[0]
            offset = (int((box[0][0] + box[1][0]) // 2 - CIRC_WIDTH // 2),
                      int((box[0][1] + box[1][1]) // 2 - CIRC_WIDTH // 2))
            img.paste(logo, offset)
        else:
            d.ellipse(cir[0], cir[1])
    return img
