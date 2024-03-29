from common_models.models import Puzzle, PuzzleStream, Team, TeamPuzzleActivity
from random import randint
from django.template.loader import render_to_string
import base64

HSPACING = 100
VSPACING = 150

XOFFSET = 200
YOFFSET = 400

CIRC_WIDTH = 65
IMG_WIDTH = CIRC_WIDTH * 1.5
LINE_WIDTH = 6

BRANCH_COLOR = (19, 102, 105)
DEFAULT_COLOR = (26, 163, 74)
COMPLETED_COLOR = (79, 34, 110)

MAX_LOOKAHEAD = 1


def generate_tree(team: Team):
    streams = PuzzleStream.objects.filter(enabled=True)
    # v_count = len(streams)
    unlocks = {}
    enabled_streams = {}
    for j in range(1):  # This is really hacky
        for stream in streams:
            if unlocks.get(stream.id, None) is not None:
                continue
            if stream.default:
                unlocks[stream.id] = 0
                enabled_streams[stream.id] = True
            puzzles = Puzzle.objects.filter(stream=stream, enabled=True).order_by('order')
            index = unlocks.get(stream.id, 0)
            for puzzle in puzzles:
                index += 1
                if puzzle.stream_branch is not None and unlocks.get(puzzle.stream_branch, 0) < index:
                    unlocks[puzzle.stream_branch.id] = index
                    act = TeamPuzzleActivity.objects.filter(team=team, puzzle=puzzle).first()
                    if act is not None and act.is_completed:
                        enabled_streams[puzzle.stream_branch.id] = True
    h_count = 0
    for stream in streams:
        cnt = len(TeamPuzzleActivity.objects.filter(team=team).exclude(puzzle_completed_at=None)) + 1
        if cnt > h_count:
            h_count = cnt
    height = HSPACING * h_count + XOFFSET + 150
    width = VSPACING * 3 + YOFFSET

    # Draw all streams first
    index = 1
    count = 1
    streams = PuzzleStream.objects.filter(enabled=True)
    starts = {}
    completed = {}
    circles = []
    heads = []
    logo = None
    logo_dat = None
    rectangles_svg = []
    circles_svg = []
    images_svg = []
    if team.logo is not None and team.logo:
        team.logo.open()
        logo = open(team.logo.path, "rb")
        logo_dat = base64.b64encode(logo.read()).decode('ASCII')
    for i in range(len(streams)):
        lowest = None
        for s in streams:
            if completed.get(s.id, False) is False:
                if s.id not in unlocks:
                    continue
                if lowest is None or unlocks[s.id] < unlocks[lowest.id]:
                    lowest = s
        stream = lowest
        if lowest is None:
            continue
        completed[stream.id] = True
        if not enabled_streams.get(stream.id, False):
            continue
        xindex = unlocks[stream.id]
        if not lowest.default:
            xindex -= 1
        puzzles = Puzzle.objects.filter(stream=stream, enabled=True).order_by('order')
        first = True
        firstEnabled = True
        lastShown = None
        curr_count = 0
        stream_active = True
        for j in range(len(puzzles)):
            puzzle = puzzles[j]
            if lastShown is not None and lastShown.order < puzzle.order:
                continue
            if not stream_active and curr_count > MAX_LOOKAHEAD and lastShown is None:
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
                # rxy = [(x, mid_y), (x-HSPACING, mid_y)]
                # d.line(rxy, color, LINE_WIDTH)
                line = {"x1": int(mid_y), "y1": int(x), "x2": int(mid_y), "y2": int(x-HSPACING),
                        "width": LINE_WIDTH, "colour": rgb2hex(color[0], color[1], color[2]), "id": 0}
                rectangles_svg += [line]
            # d.ellipse(xy, color)
            activity = TeamPuzzleActivity.objects.filter(team=team, puzzle=puzzle).first()
            if first and activity is None:
                stream_active = False
            if activity is not None and firstEnabled and not activity.is_completed:
                r = randint(0, 255)
                g = randint(0, 255)
                b = randint(0, 255)
                color = (r, g, b)
                circles += [(xy, color, True, puzzle)]
                heads += [(puzzle, color)]
                if not (j + MAX_LOOKAHEAD) >= len(puzzles):
                    lastShown = puzzles[j + MAX_LOOKAHEAD]
                firstEnabled = False
            else:
                circles += [(xy, color, False, puzzle)]
            xindex += 1
            curr_count += 1
            first = False
        if index == 1:
            index = 2
        elif index == 2:
            index = 0
        else:
            index = 2
        count += 1
    for puzzle in Puzzle.objects.filter(stream_branch__isnull=False):
        stream = puzzle.stream_branch
        if not enabled_streams.get(stream.id, False) and not enabled_streams.get(puzzle.stream.id, False):
            continue
        stream_puzzle = stream.first_enabled_puzzle
        if stream_puzzle is None:
            continue
        if starts.get(puzzle.id, None) is None or starts.get(stream_puzzle.id, None) is None:
            continue
        line = {"x1": int(starts[puzzle.id][1]), "y1": int(starts[puzzle.id][0]),
                "x2": int(starts[stream_puzzle.id][1]), "y2": int(starts[stream_puzzle.id][0]),
                "width": LINE_WIDTH, "colour": rgb2hex(19, 102, 105), "id": 0}
        rectangles_svg += [line]
        # d.line([starts[puzzle.id], starts[stream_puzzle.id]], (255, 0, 0), LINE_WIDTH)
    for i in range(len(circles)):
        cir = circles[i]
        box = cir[0]
        cx = (box[0][0] + box[1][0])/2
        cy = (box[0][1] + box[1][1])/2
        radius = CIRC_WIDTH/2
        circ = {"radius": radius, "x": int(cy), "y": int(cx), "colour": rgb2hex(cir[1][0], cir[1][1], cir[1][2]),
                "id": cir[3].secret_id}
        if cir[2] and logo is not None:
            offset = (int((box[0][0] + box[1][0]) // 2 - IMG_WIDTH // 2),
                      int((box[0][1] + box[1][1]) // 2 - IMG_WIDTH // 2))
            svgimg = {"id": cir[3].secret_id, "x": int(offset[1]), "y": int(offset[0]), "width": IMG_WIDTH,
                      "height": IMG_WIDTH, "encoded": logo_dat}
            # img.paste(logo, offset)
            images_svg += [svgimg]
        else:
            circles_svg += [circ]
    txt = render_to_string("tree.html", {"rectangles": rectangles_svg, "circles": circles_svg,
                           "images": images_svg, "width": int(width), "height": int(height)})
    return txt


def rgb2hex(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(r, g, b)
