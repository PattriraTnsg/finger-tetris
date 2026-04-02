# """
# test_piece.py — Unit tests for Piece and PieceBag

# Run:  pytest tests/test_piece.py -v
# """

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'game'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from piece import Piece, PieceBag


class TestPieceBasics:
    def test_all_piece_types_have_4_rotations(self):
        for pt in ["I","O","T","S","Z","J","L"]:
            p = Piece(pt)
            for rot in range(4):
                p2 = Piece(pt, rotation=rot)
                cells = p2.get_cells()
                assert len(cells) == 4, f"{pt} rot {rot} should have 4 cells"

    def test_color_id_unique_per_type(self):
        ids = [Piece(t).color_id for t in ["I","O","T","S","Z","J","L"]]
        assert len(set(ids)) == 7

    def test_moved_does_not_mutate_original(self):
        p = Piece("T", x=3, y=5)
        p2 = p.moved(1, 2)
        assert p.x == 3 and p.y == 5
        assert p2.x == 4 and p2.y == 7

    def test_rotated_cw_increments_state(self):
        p = Piece("T", rotation=0)
        p2 = p.rotated(clockwise=True)
        assert p2.rotation == 1
        assert p.rotation == 0   # original unchanged

    def test_rotated_ccw_decrements_state(self):
        p = Piece("T", rotation=0)
        assert p.rotated(clockwise=False).rotation == 3

    def test_rotation_wraps_around(self):
        p = Piece("T", rotation=3)
        assert p.rotated(clockwise=True).rotation == 0

    def test_o_piece_all_rotations_identical(self):
        cells = [Piece("O", rotation=r).get_cells() for r in range(4)]
        assert cells[0] == cells[1] == cells[2] == cells[3]

    def test_wall_kicks_returns_list(self):
        p = Piece("T")
        kicks = p.get_wall_kicks(0, 1)
        assert isinstance(kicks, list)
        assert len(kicks) > 0
        assert all(len(k) == 2 for k in kicks)


class TestPieceBag:
    def test_bag_produces_all_7_pieces(self):
        bag = PieceBag(seed=42)
        types_seen = set()
        for _ in range(7):
            types_seen.add(bag.next().piece_type)
        assert len(types_seen) == 7

    def test_bag_never_repeats_within_7(self):
        bag = PieceBag(seed=0)
        for _ in range(3):   # test 3 consecutive bags
            types = [bag.next().piece_type for _ in range(7)]
            assert len(set(types)) == 7, f"Duplicate in bag: {types}"

    def test_peek_does_not_consume(self):
        bag = PieceBag(seed=1)
        peeked = bag.peek()
        assert bag.next().piece_type == peeked

    def test_seeded_bag_is_deterministic(self):
        bag1 = PieceBag(seed=99)
        bag2 = PieceBag(seed=99)
        seq1 = [bag1.next().piece_type for _ in range(14)]
        seq2 = [bag2.next().piece_type for _ in range(14)]
        assert seq1 == seq2

    def test_spawn_position_is_col3(self):
        bag = PieceBag(seed=5)
        p = bag.next()
        assert p.x == 3
        assert p.y == 0