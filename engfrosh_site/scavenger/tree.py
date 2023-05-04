from PIL import Image, ImageDraw
from common_models.models import Puzzle, PuzzleStream, Team

HSPACING = 50
VSPACING = 50

XOFFSET = 75
YOFFSET = 75

CIRC_WIDTH = 20
LINE_WIDTH = 2


def generate_tree(team: Team):
    streams = PuzzleStream.objects.filter(enabled=True)
    v_count = len(streams)
    unlocks = {}
    for j in range(1):  # This is really hacky
        for stream in streams:
            if stream.default:
                unlocks[stream.id] = 0
            puzzles = Puzzle.objects.filter(stream=stream, enabled=True)
            index = unlocks.get(stream.id, 0)
            for puzzle in puzzles:
                index += 1
                if puzzle.stream_branch is not None and unlocks.get(puzzle.stream_branch, 0) < index:
                    unlocks[puzzle.stream_branch.id] = index
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
    index = 0
    count = 1
    streams = PuzzleStream.objects.filter(default=True, enabled=True)
    starts = {}
    for stream in streams:
        xindex = unlocks[stream.id]
        puzzles = Puzzle.objects.filter(stream=stream, enabled=True)
        first = True
        for puzzle in puzzles:
            x = xindex * HSPACING + XOFFSET
            y = index * VSPACING + YOFFSET
            starts[puzzle.id] = (x+CIRC_WIDTH/2, y+CIRC_WIDTH/2)
            xy = [(x, y), (x+CIRC_WIDTH, y+CIRC_WIDTH)]
            if not first:
                mid_y = (2*y+CIRC_WIDTH)/2
                rxy = [(x, mid_y), (x-HSPACING, mid_y)]
                d.line(rxy, (0, 255, 0), LINE_WIDTH)
            d.ellipse(xy, (0, 255, 0))
            xindex += 1
            first = False
        index += direction
        # direction *= -1 * int(count/2)
        count += 1
    streams = PuzzleStream.objects.filter(default=False, enabled=True)
    for stream in streams:
        xindex = unlocks[stream.id]-1
        puzzles = Puzzle.objects.filter(stream=stream, enabled=True)
        for puzzle in puzzles:
            x = xindex * HSPACING + XOFFSET
            y = index * VSPACING + YOFFSET
            starts[puzzle.id] = (x+CIRC_WIDTH/2, y+CIRC_WIDTH/2)
            xy = [(x, y), (x+CIRC_WIDTH, y+CIRC_WIDTH)]
            d.ellipse(xy, fill=(0, 0, 255), outline=(0, 0, 0))
            xindex += 1
        index += direction
        # direction *= -1 * int(count/2)
        count += 1
    for puzzle in Puzzle.objects.filter(stream_branch__isnull=False):
        stream = puzzle.stream_branch
        stream_puzzle = stream.first_enabled_puzzle
        d.line([starts[puzzle.id], starts[stream_puzzle.id]], (255, 0, 0), LINE_WIDTH)
    img.save("tree.png", "PNG")
