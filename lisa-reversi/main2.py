#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import logging
import random
import webapp2
import numpy as np
import signal
import time

BOARD = np.array([[ 30, -12,   0,  -1,  -1,   0, -12,  30],
                  [-12, -15,  -3,  -3,  -3,  -3, -15, -12],
                  [  0,  -3,   0,  -1,  -1,   0,  -3,   0],
                  [ -1,  -3,  -1,  -1,  -1,  -1,  -3,  -1],
                  [ -1,  -3,  -1,  -1,  -1,  -1,  -3,  -1],
                  [  0,  -3,   0,  -1,  -1,   0,  -3,   0],
                  [-12, -15,  -3,  -3,  -3,  -3, -15, -12],
                  [ 30, -12,   0,  -1,  -1,   0, -12,  30]])
BOARD_2 = np.array([[ 45, -11,  4, -1, -1,  4, -11,  45],
                    [-11, -16, -1, -3, -3, -1, -16, -11],
                    [  4,  -1,  2, -1, -1,  2,  -1,   4],
                    [ -1,  -3, -1,  0,  0, -1,  -3,  -1],
                    [ -1,  -3, -1,  0,  0, -1,  -3,  -1],
                    [  4,  -1,  2, -1, -1,  2,  -1,   4],
                    [-11, -16, -1, -3, -3, -1, -16, -11],
                    [ 45, -11,  4, -1, -1,  4, -11,  45]])

BOARD_FIN = np.ones((8,8))

# Reads json description of the board and provides simple interface.
class Game:
	# Takes json or a board directly.
	def __init__(self, body=None, board=None, count=4):
                if body:
		        game = json.loads(body)
                        self._board = game["board"]
                else:
                        self._board = board
                self.count = count

	# Returns piece on the board.
	# 0 for no pieces, 1 for player 1, 2 for player 2.
	# None for coordinate out of scope.
	def Pos(self, x, y):
		return Pos(self._board["Pieces"], x, y)

	# Returns who plays next.
	def Next(self):
		return self._board["Next"]

	# Returns the array of valid moves for next player.
	# Each move is a dict
	#   "Where": [x,y]
	#   "As": player number
	def ValidMoves(self):
                moves = []
                for y in xrange(1,9):
                        for x in xrange(1,9):
                                move = {"Where": [x,y],
                                        "As": self.Next()}
                                if self.NextBoardPosition(move):
                                        moves.append(move)
                return moves
                                

	# Helper function of NextBoardPosition.  It looks towards
	# (delta_x, delta_y) direction for one of our own pieces and
	# flips pieces in between if the move is valid. Returns True
	# if pieces are captured in this direction, False otherwise.
	def __UpdateBoardDirection(self, new_board, x, y, delta_x, delta_y):
		player = self.Next()
		opponent = 3 - player
		look_x = x + delta_x
		look_y = y + delta_y
		flip_list = []
		while Pos(new_board, look_x, look_y) == opponent:
			flip_list.append([look_x, look_y])
			look_x += delta_x
			look_y += delta_y
		if Pos(new_board, look_x, look_y) == player and len(flip_list) > 0:
                        # there's a continuous line of our opponents
                        # pieces between our own pieces at
                        # [look_x,look_y] and the newly placed one at
                        # [x,y], making it a legal move.
			SetPos(new_board, x, y, player)
			for flip_move in flip_list:
				flip_x = flip_move[0]
				flip_y = flip_move[1]
				SetPos(new_board, flip_x, flip_y, player)
                        return True
                return False

	# Takes a move dict and return the new Game state after that move.
	# Returns None if the move itself is invalid.
	def NextBoardPosition(self, move):
		x = move["Where"][0]
		y = move["Where"][1]
                if self.Pos(x, y) != 0:
                        # x,y is already occupied.
                        return None
		new_board = copy.deepcopy(self._board)
                pieces = new_board["Pieces"]

		if not (self.__UpdateBoardDirection(pieces, x, y, 1, 0)
                        | self.__UpdateBoardDirection(pieces, x, y, 0, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 0)
		        | self.__UpdateBoardDirection(pieces, x, y, 0, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, 1)
		        | self.__UpdateBoardDirection(pieces, x, y, 1, -1)
		        | self.__UpdateBoardDirection(pieces, x, y, -1, -1)):
                        # Nothing was captured. Move is invalid.
                        return None
                
                # Something was captured. Move is valid.
                new_board["Next"] = 3 - self.Next()
		return Game(board=new_board)

# Returns piece on the board.
# 0 for no pieces, 1 for player 1, 2 for player 2.
# None for coordinate out of scope.
#
# Pos and SetPos takes care of converting coordinate from 1-indexed to
# 0-indexed that is actually used in the underlying arrays.
def Pos(board, x, y):
	if 1 <= x and x <= 8 and 1 <= y and y <= 8:
		return board[y-1][x-1]
	return None

# Set piece on the board at (x,y) coordinate
def SetPos(board, x, y, piece):
	if x < 1 or 8 < x or y < 1 or 8 < y or piece not in [0,1,2]:
		return False
	board[y-1][x-1] = piece

# Debug function to pretty print the array representation of board.
def PrettyPrint(board, nl="<br>"):
	s = ""
	for row in board:
		for piece in row:
			s += str(piece)
		s += nl
	return s

def PrettyMove(move):
	m = move["Where"]
	return '%s%d' % (chr(ord('A') + m[0] - 1), m[1])

def signal_handler(signum, frame):
        raise Exception('time out')
                
class MainHandler(webapp2.RequestHandler):
    # Handling GET request, just for debugging purposes.
    # If you open this handler directly, it will show you the
    # HTML form here and let you copy-paste some game's JSON
    # here for testing.
    def get(self):
        if not self.request.get('json'):
          self.response.write("""
<body><form method=get>
Paste JSON here:<p/><textarea name=json cols=80 rows=24></textarea>
<p/><input type=submit>
</form>
</body>
""")
          return
        else:
          g = Game(self.request.get('json'))
          self.pickMove2(g)

    def post(self):
    	# Reads JSON representation of the board and store as the object.
    	g = Game(self.request.body)
        # Do the picking of a move and print the result.
        self.pickMove2(g)

    def pickMove2(self, g):
    	# Gets all valid moves.
    	valid_moves = g.ValidMoves()
    	if len(valid_moves) == 0:
    		# Passes if no valid moves.
    		self.response.write("PASS")
    	else:
                empty = np.sum([[1 if g.Pos(x, y) == 0 else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                if empty < 7:
                        result = self.choose_final(g, empty, g.Next())
                else:
                        result = self.choose(g, 2, g.Next())
    		move = result['best_move']
                self.response.write(PrettyMove(move))

    def choose(self, g, depth, next, open_point=0):
        move_list = []
        while depth > 0:
                validmove = g.ValidMoves()
                if not validmove:
                        if g.Next() == next:
                                return {'point': 100, 'best_move': None}
                        else:
                                return {'point': -100, 'best_move': None}
                elif g.Next() == next:
                        for move in validmove:
                                g_next = g.NextBoardPosition(move)
                                openness = self.calculateOpenness(g, g_next)
                                
                                result = self.choose(g_next, depth - 1, next, open_point + openness)
                                if result['point'] > point:
                                        point = result['point']
                                        best_move = move

                                        
        if depth == 0:
            final_open = 0
            if validmove:
                    for move in validmove:
                            open = self.calculateOpenness(g, g.NextBoardPosition(move))
                            if open > final_open:
                                    final_open = open
            return {'point': self.calculatePoint(g) + open_point + final_open, 'best_move': None}
        
        best_move = random.choice(validmove)
        if g.Next() == next: # next is me 
            point = -100
            for move in validmove:
                g_next = g.NextBoardPosition(move)
                openness = self.calculateOpenness(g, g_next)
                result = self.choose(g_next, depth - 1, next, open_point + openness)
                if result['point'] > point:
                    point = result['point']
                    best_move = move
            #logging.info("hey, depth%d, point%d, next%d", depth, point, next)

        elif g.Next() != next: # next is enemy
            point = 100
            for move in validmove:
                g_next = g.NextBoardPosition(move)
                openness = self.calculateOpenness(g, g_next)
                result = self.choose(g_next, depth - 1, next, open_point - openness)
                if result['point'] < point:
                    point = result['point']
                    best_move = move
        return {'point': point, 'best_move': best_move}

    def choose_final(self, g, depth, next):
        validmove = g.ValidMoves()
        if depth == 0:
                board_me = np.array([[1 if h.Pos(x, y) == h.Next() else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                board_enemy = np.array([[1 if h.Pos(x, y) not in [h.Next(), 0] else 0 for x in xrange(1,9)] for y in xrange(1,9)])
                point = np.sum(board_me * BOARD_FIN) - np.sum(board_enemy * BOARD_FIN)
                return {'point': point, 'best_move': None}
        
        if not validmove:
            if g.Next() == next:
                return {'point': 100, 'best_move': None}
            else:
                return {'point': -100, 'best_move': None}
        
        best_move = random.choice(validmove)
        if g.Next() == next: # next is me 
            point = -100
            for move in validmove:
                g_next = g.NextBoardPosition(move)
                result = self.choose(g_next, depth - 1, next)
                if result['point'] > point:
                    point = result['point']
                    best_move = move

        elif g.Next() != next: # next is enemy
            point = 100
            for move in validmove:
                g_next = g.NextBoardPosition(move)
                result = self.choose(g_next, depth - 1, next, open_point - openness)
                if result['point'] < point:
                    point = result['point']
                    best_move = move
        return {'point': point, 'best_move': best_move}


    def calculatePoint(self, h):
        # more is better
        board_me = np.array([[1 if h.Pos(x, y) == h.Next() else 0 for x in xrange(1,9)] for y in xrange(1,9)])
        board_enemy = np.array([[1 if h.Pos(x, y) not in [h.Next(), 0] else 0 for x in xrange(1,9)] for y in xrange(1,9)])
        #empty = np.array([[1 if h_next.Pos(x, y) == 0 else 0 for x in range(1,9)] for y in range(1,9)])
        #empty = np.sum(empty)
        point = len(h.ValidMoves()) + np.sum(board_me * BOARD_2) - np.sum(board_enemy * BOARD_2)
        #logging.info("len=%d, point=%d, enemy=%d", len(h.ValidMoves()), np.sum(board_me*BOARD_2), np.sum(board_enemy*BOARD_2))
        #if empty < 7:
        #        point += np.sum(board * BOARD_FIN)
        #else:
        #        point += np.sum(board * BOARD_2)
        return point

    def calculateOpenness(self, h, h_next):
        change_list = [[x, y] if h.Pos(x, y) != h_next.Pos(x, y) and h.Pos(x, y) != 0 else [] for x in range(1, 9) for y in range(1, 9)]
        change_list = filter(lambda s:s != [], change_list)
        openness = 0
        for change in change_list:
                x, y = change
                openness += np.sum([1 if h.Pos(p, q) == 0 else 0 for p in xrange(max(x-1, 1), min(x+2, 9)) for q in xrange(max(y-1, 1), min(y+2, 9))])
        return openness * (-1)
                
app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
